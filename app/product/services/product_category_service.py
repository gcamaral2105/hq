"""
ProductCategoryService – business logic for ProductCategory entities
====================================================================

Adds validation, smart caching and metrics on top of
**ProductCategoryRepository**.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.lib.services.base import BaseService
from app.lib.utils.validators import ValidationUtils
from app.lib.utils.helpers import StringUtils
from app.product.repository.product_category_repository import (
    ProductCategoryRepository,
)


class ProductCategoryService(BaseService):
    """High-level service for **ProductCategory** operations."""

    # ───────────────────────── constructor & hooks ──────────────────────── #
    def __init__(self) -> None:
        repo = ProductCategoryRepository()
        super().__init__(repo)

        self.validator = ValidationUtils()

        self.add_hook("before_create", self._before_create)
        self.add_hook("after_create", self._after_change)
        self.add_hook("before_update", self._before_update)
        self.add_hook("after_update", self._after_change)

    # ===================================================================== #
    # CRUD with validation                                                  #
    # ===================================================================== #
    def create_category(self, name: str) -> Dict[str, Any]:
        """Create a new category."""
        def op():
            payload = {"name": name}
            val = self.validator.validate(payload, self._rules())
            if not val["valid"]:
                return self.validation_error(val["errors"])

            clean_name = StringUtils.clean_whitespace(name)
            cat = self.repository.create_with_validation(clean_name)

            return self.ok(
                f"Category “{clean_name}” created",
                self._dto(cat),
                metadata={"category_id": cat.id},
            )

        return self.safe_repository_operation("create_category", op)

    def update_category(self, category_id: int, name: str) -> Dict[str, Any]:
        """Update an existing category."""
        def op():
            cat = self.repository.get_by_id(category_id)
            if cat is None:
                return self.error("Category not found", error_code="CATEGORY_NOT_FOUND")

            payload = {"name": name}
            val = self.validator.validate(payload, self._rules())
            if not val["valid"]:
                return self.validation_error(val["errors"])

            clean_name = StringUtils.clean_whitespace(name)
            cat = self.repository.update_with_validation(category_id, clean_name)

            return self.ok(
                f"Category “{clean_name}” updated",
                self._dto(cat),
                metadata={"category_id": category_id},
            )

        return self.safe_repository_operation("update_category", op)

    def delete_category(self, category_id: int) -> Dict[str, Any]:
        """Delete a category (FK checks live in the repository)."""
        def op():
            if not (cat := self.repository.get_by_id(category_id)):
                return self.error("Category not found", error_code="CATEGORY_NOT_FOUND")

            if self.repository.delete_with_validation(category_id):
                return self.ok(
                    f"Category “{cat.name}” deleted",
                    metadata={"category_id": category_id},
                )
            return self.error("Delete failed", error_code="DELETE_FAILED")

        return self.safe_repository_operation("delete_category", op)

    # ===================================================================== #
    # READ helpers                                                          #
    # ===================================================================== #
    def get_category(self, category_id: int) -> Dict[str, Any]:
        return self._cached_entity(
            cache_key=f"category:{category_id}",
            fetch_fn=lambda: self.repository.get_by_id(category_id),
            not_found_msg="Category not found",
            error_code="CATEGORY_NOT_FOUND",
        )

    def get_category_with_subtypes(self, category_id: int) -> Dict[str, Any]:
        def build():
            cat = self.repository.get_category_with_subtypes(category_id)
            if cat is None:
                return None
            return {
                **self._dto(cat),
                "subtypes": [
                    {
                        "id": st.id,
                        "name": st.name,
                        "mine_id": st.mine_id,
                        "mine_name": st.mine.name if st.mine else None,
                    }
                    for st in cat.subtypes
                ],
                "subtypes_count": len(cat.subtypes),
            }

        return self._cached_entity(
            cache_key=f"category_subtypes:{category_id}",
            fetch_fn=build,
            not_found_msg="Category not found",
            error_code="CATEGORY_NOT_FOUND",
            cache_ttl=600,
        )

    def list_categories(
        self,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
    ) -> Dict[str, Any]:
        """Paginated listing with optional search."""
        try:
            if search:
                matches = self.repository.search_by_name_pattern(search)
                start, end = (page - 1) * per_page, page * per_page
                items = matches[start:end]
                total = len(matches)
                data = {
                    "items": [self._dto(c) for c in items],
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "pages": (total + per_page - 1) // per_page,
                    "has_next": end < total,
                    "has_prev": page > 1,
                }
            else:
                data = self.paginate(page=page, per_page=per_page)
                data["items"] = [self._dto(c) for c in data["items"]]

            return self.ok(
                "Categories listed",
                data,
                metadata={"search_term": search, "total_found": data["total"]},
            )

        except Exception as exc:  # noqa: BLE001
            return self.error("Listing failed", errors=[str(exc)], error_code="LIST_FAILED")

    def get_categories_for_select(self) -> Dict[str, Any]:
        return self._cached_simple(
            "categories_select",
            fetch_fn=self.repository.get_categories_for_select,
            success_msg="Categories for select",
            cache_ttl=600,
        )

    def get_category_statistics(self) -> Dict[str, Any]:
        return self._cached_simple(
            "category_stats",
            fetch_fn=self.repository.get_category_stats,
            success_msg="Category statistics",
            cache_ttl=900,
        )

    # bulk
    def bulk_create_categories(
        self, items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        def op():
            errors: List[str] = []
            for idx, row in enumerate(items, start=1):
                val = self.validator.validate(row, self._rules())
                if not val["valid"]:
                    errors.extend([f"Item {idx}: {e}" for e in val["errors"]])
            if errors:
                return self.validation_error(errors)

            clean = [{"name": StringUtils.clean_whitespace(r["name"])} for r in items]
            created = self.repository.bulk_create_categories(clean)

            return self.ok(
                f"{len(created)} categories created",
                [self._dto(c) for c in created],
                metadata={"total_created": len(created), "requested": len(items)},
            )

        return self.safe_repository_operation("bulk_create_categories", op)

    # ===================================================================== #
    # INTERNAL helpers                                                      #
    # ===================================================================== #
    @staticmethod
    def _rules() -> Dict[str, Any]:
        return {
            "fields": {
                "name": {
                    "type": "string",
                    "required": True,
                    "min_length": 3,
                    "max_length": 100,
                    "pattern": r"^[A-Za-z0-9\s\-_À-ÿ]+$",
                    "pattern_name": "letters, numbers, spaces, – and _",
                }
            }
        }

    @staticmethod
    def _dto(cat) -> Dict[str, Any]:
        return {
            "id": cat.id,
            "name": cat.name,
            "created_at": getattr(cat, "created_at", None) and cat.created_at.isoformat(),
            "updated_at": getattr(cat, "updated_at", None) and cat.updated_at.isoformat(),
        }

    # --------------------------------------------------------------------- #
    # cache wrappers                                                        #
    # --------------------------------------------------------------------- #
    def _cached_entity(
        self,
        cache_key: str,
        fetch_fn,
        *,
        not_found_msg: str,
        error_code: str,
        cache_ttl: int = 300,
    ) -> Dict[str, Any]:
        if cached := self._cache_get(cache_key):
            return self.ok(not_found_msg.replace(" not found", ""), cached)

        data = fetch_fn()
        if data is None:
            return self.error(not_found_msg, error_code=error_code)

        self._cache_set(cache_key, data, cache_ttl)
        return self.ok(not_found_msg.replace(" not found", ""), data)

    def _cached_simple(
        self,
        cache_key: str,
        *,
        fetch_fn,
        success_msg: str,
        cache_ttl: int,
    ) -> Dict[str, Any]:
        if cached := self._cache_get(cache_key):
            return self.ok(success_msg, cached)

        data = fetch_fn()
        self._cache_set(cache_key, data, cache_ttl)
        return self.ok(success_msg, data)

    # --------------------------------------------------------------------- #
    # hooks                                                                 #
    # --------------------------------------------------------------------- #
    def _before_create(self, *_a, **_kw):
        self.logger.info("Creating category…")

    def _before_update(self, *_a, **_kw):
        self.logger.info("Updating category…")

    def _after_change(self, result: Dict[str, Any], *_a, **_kw):
        if not result.get("success"):
            return
        cat_id = result.get("metadata", {}).get("category_id")
        for key in (
            "categories_select",
            "category_stats",
            f"category:{cat_id}",
            f"category_subtypes:{cat_id}",
        ):
            self.clear_cache(key)
        self.logger.info("Category cache cleared")
