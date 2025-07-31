"""
ProductSubtypeService – business logic for ProductSubtype entities
==================================================================

Adds validation, smart caching and metrics on top of
**ProductSubtypeRepository**.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.lib.services.base import BaseService
from app.lib.utils.validators import ValidationUtils
from app.lib.utils.helpers import StringUtils
from app.product.repository.product_subtype_repository import ProductSubtypeRepository
from app.product.repository.product_category_repository import ProductCategoryRepository
from app.product.repository.mine_repository import MineRepository


class ProductSubtypeService(BaseService):
    """High-level service for **ProductSubtype** operations."""

    # ───────────────────────── constructor & hooks ──────────────────────── #
    def __init__(self) -> None:
        repo = ProductSubtypeRepository()
        super().__init__(repo)

        self.validator = ValidationUtils()
        self.category_repo = ProductCategoryRepository()
        self.mine_repo = MineRepository()

        self.add_hook("before_create", self._before_create)
        self.add_hook("after_create", self._after_change)
        self.add_hook("before_update", self._before_update)
        self.add_hook("after_update", self._after_change)

    # ===================================================================== #
    # CRUD with validation                                                  #
    # ===================================================================== #
    def create_subtype(
        self, name: str, category_id: int, mine_id: int
    ) -> Dict[str, Any]:
        """Create a new sub-type (compound-key uniqueness)."""
        def op():
            payload = {"name": name, "category_id": category_id, "mine_id": mine_id}
            val = self.validator.validate(payload, self._rules())
            if not val["valid"]:
                return self.validation_error(val["errors"])

            rel_errors = self._validate_relationships(category_id, mine_id)
            if rel_errors:
                return self.validation_error(rel_errors)

            clean_name = StringUtils.clean_whitespace(name)
            st = self.repository.create_with_validation(
                clean_name, category_id, mine_id
            )

            return self.ok(
                f"Sub-type “{clean_name}” created",
                self._dto(st),
                metadata={"subtype_id": st.id},
            )

        return self.safe_repository_operation("create_subtype", op)

    def update_subtype(
        self, subtype_id: int, name: str, category_id: int, mine_id: int
    ) -> Dict[str, Any]:
        """Update an existing sub-type."""
        def op():
            st = self.repository.get_by_id(subtype_id)
            if st is None:
                return self.error("Sub-type not found", error_code="SUBTYPE_NOT_FOUND")

            payload = {"name": name, "category_id": category_id, "mine_id": mine_id}
            val = self.validator.validate(payload, self._rules())
            if not val["valid"]:
                return self.validation_error(val["errors"])

            rel_errors = self._validate_relationships(category_id, mine_id)
            if rel_errors:
                return self.validation_error(rel_errors)

            clean_name = StringUtils.clean_whitespace(name)
            st = self.repository.update_with_validation(
                subtype_id, clean_name, category_id, mine_id
            )

            return self.ok(
                f"Sub-type “{clean_name}” updated",
                self._dto(st),
                metadata={"subtype_id": subtype_id},
            )

        return self.safe_repository_operation("update_subtype", op)

    def delete_subtype(self, subtype_id: int) -> Dict[str, Any]:
        """Delete a sub-type (FK checks live in the repository)."""
        def op():
            st = self.repository.get_by_id(subtype_id)
            if st is None:
                return self.error("Sub-type not found", error_code="SUBTYPE_NOT_FOUND")

            if self.repository.delete_with_validation(subtype_id):
                return self.ok(
                    f"Sub-type “{st.name}” deleted", metadata={"subtype_id": subtype_id}
                )
            return self.error("Delete failed", error_code="DELETE_FAILED")

        return self.safe_repository_operation("delete_subtype", op)

    # ===================================================================== #
    # READ helpers (single + lists)                                         #
    # ===================================================================== #
    def get_subtype(self, subtype_id: int) -> Dict[str, Any]:
        return self._cached_entity(
            f"subtype:{subtype_id}",
            fetch_fn=lambda: self.repository.get_subtype_with_relationships(
                subtype_id
            ),
            not_found_msg="Sub-type not found",
            error_code="SUBTYPE_NOT_FOUND",
        )

    def list_subtypes(
        self,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        category_id: int | None = None,
        mine_id: int | None = None,
    ) -> Dict[str, Any]:
        try:
            extra_filters = {
                k: v for k, v in (("category_id", category_id), ("mine_id", mine_id)) if v
            }
            if search:
                matches = self.repository.search_by_name_pattern(search)
                if extra_filters:
                    matches = [
                        st
                        for st in matches
                        if all(getattr(st, f, None) == v for f, v in extra_filters.items())
                    ]
                start, end = (page - 1) * per_page, page * per_page
                items, total = matches[start:end], len(matches)
                data = {
                    "items": [self._dto(s) for s in items],
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "pages": (total + per_page - 1) // per_page,
                    "has_next": end < total,
                    "has_prev": page > 1,
                }
            else:
                data = self.paginate(page=page, per_page=per_page, **extra_filters)
                data["items"] = [self._dto(s) for s in data["items"]]

            return self.ok(
                "Sub-types listed",
                data,
                metadata={
                    "search_term": search,
                    **extra_filters,
                    "total_found": data["total"],
                },
            )
        except Exception as exc:  # noqa: BLE001
            return self.error("Listing failed", errors=[str(exc)], error_code="LIST_FAILED")

    # quick-select helpers
    def get_subtypes_by_category(self, category_id: int) -> Dict[str, Any]:
        return self._cached_simple(
            f"subtypes_by_cat:{category_id}",
            success_msg=f"Sub-types for category {category_id}",
            cache_ttl=300,
            fetch_fn=lambda: [
                self._dto(s) for s in self.repository.get_subtypes_by_category(category_id)
            ],
        )

    def get_subtypes_by_mine(self, mine_id: int) -> Dict[str, Any]:
        return self._cached_simple(
            f"subtypes_by_mine:{mine_id}",
            success_msg=f"Sub-types for mine {mine_id}",
            cache_ttl=300,
            fetch_fn=lambda: [
                self._dto(s) for s in self.repository.get_subtypes_by_mine(mine_id)
            ],
        )

    def get_subtypes_for_select(self) -> Dict[str, Any]:
        return self._cached_simple(
            "subtypes_select",
            success_msg="Sub-types for select",
            cache_ttl=600,
            fetch_fn=self.repository.get_subtypes_for_select,
        )

    def get_subtype_statistics(self) -> Dict[str, Any]:
        return self._cached_simple(
            "subtype_stats",
            success_msg="Subtype statistics",
            cache_ttl=900,
            fetch_fn=self.repository.get_subtype_stats,
        )

    # bulk
    def bulk_create_subtypes(
        self, rows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        def op():
            errs: List[str] = []
            for idx, r in enumerate(rows, start=1):
                val = self.validator.validate(r, self._rules())
                if not val["valid"]:
                    errs.extend([f"Item {idx}: {e}" for e in val["errors"]])
                errs.extend(
                    [f"Item {idx}: {e}" for e in self._validate_relationships(r["category_id"], r["mine_id"])]
                )
            if errs:
                return self.validation_error(errs)

            clean_rows = [
                {
                    "name": StringUtils.clean_whitespace(r["name"]),
                    "category_id": int(r["category_id"]),
                    "mine_id": int(r["mine_id"]),
                }
                for r in rows
            ]
            created = self.repository.bulk_create_subtypes(clean_rows)
            return self.ok(
                f"{len(created)} sub-types created",
                [self._dto(s) for s in created],
                metadata={"total_created": len(created), "requested": len(rows)},
            )

        return self.safe_repository_operation("bulk_create_subtypes", op)

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
                },
                "category_id": {"type": "integer", "required": True, "min_value": 1},
                "mine_id": {"type": "integer", "required": True, "min_value": 1},
            }
        }

    def _validate_relationships(self, category_id: int, mine_id: int) -> List[str]:
        errs: List[str] = []
        if self.category_repo.get_by_id(category_id) is None:
            errs.append(f"Category {category_id} does not exist")
        if self.mine_repo.get_by_id(mine_id) is None:
            errs.append(f"Mine {mine_id} does not exist")
        return errs

    @staticmethod
    def _dto(st) -> Dict[str, Any]:
        return {
            "id": st.id,
            "name": st.name,
            "category_id": st.category_id,
            "category_name": st.category.name if st.category else None,
            "mine_id": st.mine_id,
            "mine_name": st.mine.name if st.mine else None,
            "created_at": getattr(st, "created_at", None) and st.created_at.isoformat(),
            "updated_at": getattr(st, "updated_at", None) and st.updated_at.isoformat(),
        }

    # --------------------------------------------------------------------- #
    # caching wrappers (shared with category / mine services)               #
    # --------------------------------------------------------------------- #
    def _cached_entity(
        self,
        cache_key: str,
        *,
        fetch_fn,
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
        self.logger.info("Creating sub-type…")

    def _before_update(self, *_a, **_kw):
        self.logger.info("Updating sub-type…")

    def _after_change(self, result: Dict[str, Any], *_a, **_kw):
        if not result.get("success"):
            return
        st_id = result.get("metadata", {}).get("subtype_id")
        data = result.get("data", {})
        cat_id, mine_id = data.get("category_id"), data.get("mine_id")

        for key in (
            "subtypes_select",
            "subtype_stats",
            f"subtype:{st_id}",
            f"subtypes_by_cat:{cat_id}" if cat_id else "",
            f"subtypes_by_mine:{mine_id}" if mine_id else "",
        ):
            if key:
                self.clear_cache(key)
        self.logger.info("Subtype cache cleared")
