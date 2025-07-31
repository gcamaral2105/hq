"""
MineService – business logic for Mine entities
==============================================

Adds validation, smart caching and metrics on top of **MineRepository**.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Optional

from app.lib.services.base import BaseService
from app.lib.utils.validators import ValidationUtils
from app.lib.utils.helpers import StringUtils
from app.product.repository.mine_repository import MineRepository


class MineService(BaseService):
    """High-level service for **Mine** operations."""

    # --------------------------------------------------------------------- #
    # constructor & hooks                                                   #
    # --------------------------------------------------------------------- #
    def __init__(self) -> None:
        repo = MineRepository()
        super().__init__(repo)

        self.validator = ValidationUtils()

        # custom hooks
        self.add_hook("before_create", self._before_create)
        self.add_hook("after_create", self._after_change)
        self.add_hook("before_update", self._before_update)
        self.add_hook("after_update", self._after_change)

    # ===================================================================== #
    # CRUD with validation                                                  #
    # ===================================================================== #
    def create_mine(self, name: str) -> Dict[str, Any]:
        """Create a new mine, returning a standard envelope."""
        def op():
            payload = {"name": name}
            val = self.validator.validate(payload, self._rules())
            if not val["valid"]:
                return self.validation_error(val["errors"])

            clean_name = StringUtils.clean_whitespace(name)
            mine = self.repository.create_with_validation(clean_name)

            return self.ok(
                f"Mine “{clean_name}” successfully created",
                self._dto(mine),
                metadata={"mine_id": mine.id},
            )

        return self.safe_repository_operation("create_mine", op)

    def update_mine(self, mine_id: int, name: str) -> Dict[str, Any]:
        """Update an existing mine."""
        def op():
            if not (mine := self.repository.get_by_id(mine_id)):
                return self.error("Mine not found", error_code="MINE_NOT_FOUND")

            payload = {"name": name}
            val = self.validator.validate(payload, self._rules())
            if not val["valid"]:
                return self.validation_error(val["errors"])

            clean_name = StringUtils.clean_whitespace(name)
            mine = self.repository.update_with_validation(mine_id, clean_name)

            return self.ok(
                f"Mine “{clean_name}” successfully updated",
                self._dto(mine),
                metadata={"mine_id": mine_id},
            )

        return self.safe_repository_operation("update_mine", op)

    def delete_mine(self, mine_id: int) -> Dict[str, Any]:
        """Delete a mine (with FK checks inside the repository)."""
        def op():
            if not (mine := self.repository.get_by_id(mine_id)):
                return self.error("Mine not found", error_code="MINE_NOT_FOUND")

            if self.repository.delete_with_validation(mine_id):
                return self.ok(
                    f"Mine “{mine.name}” deleted",
                    metadata={"mine_id": mine_id},
                )
            return self.error("Delete failed", error_code="DELETE_FAILED")

        return self.safe_repository_operation("delete_mine", op)

    # ===================================================================== #
    # FETCH helpers                                                         #
    # ===================================================================== #
    def get_mine(self, mine_id: int) -> Dict[str, Any]:
        cache_key = f"mine:{mine_id}"
        if cached := self._cache_get(cache_key):
            return self.ok("Mine found", cached)

        mine = self.repository.get_by_id(mine_id)
        if mine is None:
            return self.error("Mine not found", error_code="MINE_NOT_FOUND")

        dto = self._dto(mine)
        self._cache_set(cache_key, dto, timeout=300)
        return self.ok("Mine found", dto)

    def get_mine_with_subtypes(self, mine_id: int) -> Dict[str, Any]:
        cache_key = f"mine_subtypes:{mine_id}"
        if cached := self._cache_get(cache_key):
            return self.ok("Mine with sub-types", cached)

        mine = self.repository.get_mine_with_subtypes(mine_id)
        if mine is None:
            return self.error("Mine not found", error_code="MINE_NOT_FOUND")

        dto = {
            **self._dto(mine),
            "subtypes": [
                {
                    "id": st.id,
                    "name": st.name,
                    "category_id": st.category_id,
                    "category_name": st.category.name if st.category else None,
                }
                for st in mine.subtypes
            ],
            "subtypes_count": len(mine.subtypes),
        }
        self._cache_set(cache_key, dto, timeout=600)
        return self.ok("Mine with sub-types", dto)

    def list_mines(
        self,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
    ) -> Dict[str, Any]:
        try:
            if search:
                matches = self.repository.search_by_name_pattern(search)
                start, end = (page - 1) * per_page, page * per_page
                items = matches[start:end]
                total = len(matches)
                paged = {
                    "items": [self._dto(m) for m in items],
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "pages": (total + per_page - 1) // per_page,
                    "has_next": end < total,
                    "has_prev": page > 1,
                }
            else:
                paged = self.paginate(page=page, per_page=per_page)
                paged["items"] = [self._dto(m) for m in paged["items"]]

            return self.ok(
                "Mines listed",
                paged,
                metadata={"search_term": search, "total_found": paged["total"]},
            )
        except Exception as exc:  # noqa: BLE001
            return self.error("Listing failed", errors=[str(exc)], error_code="LIST_FAILED")

    def get_mines_for_select(self) -> Dict[str, Any]:
        if cached := self._cache_get("mines_select"):
            return self.ok("Mines for select", cached)

        data = self.repository.get_mines_for_select()
        self._cache_set("mines_select", data, timeout=600)
        return self.ok("Mines for select", data)

    def get_mine_statistics(self) -> Dict[str, Any]:
        if cached := self._cache_get("mine_stats"):
            return self.ok("Mine stats", cached)

        stats = self.repository.get_mine_stats()
        self._cache_set("mine_stats", stats, timeout=900)
        return self.ok("Mine stats", stats)

    # bulk
    def bulk_create_mines(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        def op():
            errs: List[str] = []
            for idx, row in enumerate(items, start=1):
                val = self.validator.validate(row, self._rules())
                if not val["valid"]:
                    errs.extend([f"Item {idx}: {e}" for e in val["errors"]])
            if errs:
                return self.validation_error(errs)

            clean = [{"name": StringUtils.clean_whitespace(r["name"])} for r in items]
            created = self.repository.bulk_create_mines(clean)
            return self.ok(
                f"{len(created)} mines created",
                [self._dto(m) for m in created],
                metadata={"total_created": len(created), "requested": len(items)},
            )

        return self.safe_repository_operation("bulk_create_mines", op)

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
    def _dto(mine) -> Dict[str, Any]:
        return {
            "id": mine.id,
            "name": mine.name,
            "created_at": getattr(mine, "created_at", None) and mine.created_at.isoformat(),
            "updated_at": getattr(mine, "updated_at", None) and mine.updated_at.isoformat(),
        }

    # --------------------------------------------------------------------- #
    # hooks                                                                 #
    # --------------------------------------------------------------------- #
    def _before_create(self, *_a, **_kw):
        self.logger.info("Creating mine…")

    def _before_update(self, *_a, **_kw):
        self.logger.info("Updating mine…")

    def _after_change(self, result: Dict[str, Any], *_a, **_kw):
        if not result.get("success"):
            return

        mine_id = result.get("metadata", {}).get("mine_id")
        # purge related cache
        for key in (
            "mines_select",
            "mine_stats",
            f"mine:{mine_id}",
            f"mine_subtypes:{mine_id}",
        ):
            self.clear_cache(key)
        self.logger.info("Mine cache cleared")
