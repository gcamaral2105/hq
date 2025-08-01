"""
MineRepository – manage Mine entities
=====================================

Concrete repository built on top of the *advanced* internal library:

* Generic CRUD from **BaseRepository**
* Extra helpers from **SearchMixin**, **AuditMixin**, **StatsMixin**
* Decorators for caching, logging and performance metrics
* Custom hooks for business‑specific side effects
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import joinedload

from app.lib.repository.base import BaseRepository
from app.lib.repository.mixins import SearchMixin, AuditMixin, StatsMixin
from app.lib.repository.decorators import (
    cached_result,
    logged_operation,
    measure_performance,
)
from app.models.product import Mine


class MineRepository(
    BaseRepository[Mine],
    SearchMixin[Mine],
    AuditMixin[Mine],
    StatsMixin[Mine],
):
    """Specialised repository for the **Mine** model."""

    # --------------------------------------------------------------------- #
    # constructor & hook registration                                       #
    # --------------------------------------------------------------------- #
    def __init__(self) -> None:
        super().__init__(Mine)

        # feature flags inherited from BaseRepository / CacheMixin
        self.ENABLE_AUDIT = True
        self.ENABLE_SOFT_DELETE = False

        # custom hooks
        self.add_hook("after_create", self._log_creation)
        self.add_hook("before_delete", self._validate_deletion)
        self.add_hook("after_update", self._purge_related_cache)

    # --------------------------------------------------------------------- #
    # generic “search by criteria”                                          #
    # --------------------------------------------------------------------- #
    @measure_performance()
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Mine]:
        """AND‑combined multi‑criteria search."""
        return self.find_by_multiple_criteria(criteria, operator="AND")

    # --------------------------------------------------------------------- #
    # simple look‑ups                                                       #
    # --------------------------------------------------------------------- #
    @cached_result(timeout=300)
    @measure_performance()
    def find_by_name(self, name: str) -> Optional[Mine]:
        """Exact‑name lookup with cache."""
        return self.model_class.query.filter_by(name=name).first()

    def find_by_name_like(self, text: str) -> List[Mine]:
        """ILIKE search using **SearchMixin**."""
        return self.search(text, ["name"])

    def name_exists(self, name: str, *, exclude_id: int | None = None) -> bool:
        """True if another Mine already owns *name*."""
        q = self.model_class.query.filter_by(name=name)
        if exclude_id:
            q = q.filter(self.model_class.id != exclude_id)
        return q.first() is not None

    # --------------------------------------------------------------------- #
    # eager‑loaded queries                                                  #
    # --------------------------------------------------------------------- #
    @cached_result(timeout=600)
    def get_mines_with_subtypes(self) -> List[Mine]:
        """Return all mines with their sub‑types eagerly loaded."""
        return (
            self.model_class.query.options(joinedload(Mine.subtypes))  # type: ignore[arg-type]
            .all()
        )

    def get_mine_with_subtypes(self, mine_id: int) -> Optional[Mine]:
        """Return one mine + sub‑types (or *None*)."""
        return (
            self.model_class.query.options(joinedload(Mine.subtypes))
            .get(mine_id)
        )

    # --------------------------------------------------------------------- #
    # light DTO helpers                                                     #
    # --------------------------------------------------------------------- #
    @cached_result(timeout=300)
    def get_mines_for_select(self) -> List[Dict[str, Any]]:
        """`[{id:‑, name:‑}, …]` – handy for drop‑downs."""
        return [{"id": m.id, "name": m.name} for m in self.get_all()]

    def get_mines_by_ids(self, ids: List[int]) -> List[Mine]:
        return self.model_class.query.filter(Mine.id.in_(ids)).all()

    def get_ordered_by_name(self, ascending: bool = True) -> List[Mine]:
        order = Mine.name.asc() if ascending else Mine.name.desc()
        return self.model_class.query.order_by(order).all()

    def search_by_name_pattern(self, pattern: str) -> List[Mine]:
        return self.search(pattern, ["name"])

    # --------------------------------------------------------------------- #
    # statistics                                                            #
    # --------------------------------------------------------------------- #
    @cached_result(timeout=900)
    def get_mine_stats(self) -> Dict[str, Any]:
        """High‑level dashboard stats."""
        total = self.count()
        with_sub = (
            self.model_class.query.filter(self.model_class.subtypes.any()).count()
        )

        basic = self.get_basic_stats()  # from StatsMixin

        return {
            "total_mines": total,
            "mines_with_subtypes": with_sub,
            "mines_without_subtypes": total - with_sub,
            "created_today": basic.get("created_today", 0),
            "created_this_week": basic.get("created_this_week", 0),
            "created_this_month": basic.get("created_this_month", 0),
        }

    # --------------------------------------------------------------------- #
    # CRUD with extra validation                                            #
    # --------------------------------------------------------------------- #
    @logged_operation(log_level="INFO", include_args=True)
    def create_with_validation(self, name: str) -> Mine:
        name = (name or "").strip()
        if self.name_exists(name):
            raise self.DuplicateError("Mine", "name", name)  # type: ignore[attr-defined]
        return self.create(name=name)

    @logged_operation(log_level="INFO", include_args=True)
    def update_with_validation(self, mine_id: int, name: str) -> Optional[Mine]:
        mine = self.get_by_id(mine_id)
        if mine is None:
            return None

        name = (name or "").strip()
        if self.name_exists(name, exclude_id=mine_id):
            raise self.DuplicateError("Mine", "name", name)  # type: ignore[attr-defined]
        return self.update(mine_id, name=name)

    def delete_with_validation(self, mine_id: int) -> bool:
        mine = self.get_by_id(mine_id)
        if mine is None:
            return False
        return self.delete(mine_id)  # integrity is checked in hook

    # --------------------------------------------------------------------- #
    # bulk create                                                           #
    # --------------------------------------------------------------------- #
    def bulk_create_mines(self, payload: List[Dict[str, Any]]) -> List[Mine]:
        # upfront validation
        for item in payload:
            name = (item.get("name") or "").strip()
            if not name:
                raise self.ValidationError("name is required")  # type: ignore[attr-defined]
            if self.name_exists(name):
                raise self.DuplicateError("Mine", "name", name)  # type: ignore[attr-defined]

        return self.bulk_create([{"name": (p["name"]).strip()} for p in payload])

    # --------------------------------------------------------------------- #
    # custom hooks                                                          #
    # --------------------------------------------------------------------- #
    # after_create
    def _log_creation(self, entity: Mine, **_) -> None:
        self.logger.info("Mine created: %s (ID %s)", entity.name, entity.id)

    # before_delete
    def _validate_deletion(self, entity: Mine, **_) -> None:
        if getattr(entity, "subtypes", None):  # any FK rows?
            raise self.IntegrityError(  # type: ignore[attr-defined]
                "Cannot delete a Mine that has sub‑types",
                constraint="fk_subtypes",
            )

    # after_update
    def _purge_related_cache(self, *_args, **_kw) -> None:
        self.clear_cache(pattern="mine")  # method from CacheMixin
