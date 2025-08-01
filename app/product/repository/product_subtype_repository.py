"""
ProductSubtypeRepository – manage ProductSubtype entities
=========================================================

Built on the *advanced* internal repository stack:

* CRUD & bulk helpers from **BaseRepository**
* Extra helpers from **SearchMixin**, **AuditMixin**, **StatsMixin**
* Caching / logging / performance via decorators
* Custom hooks for integrity checks and cache eviction
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
from app.models.product import ProductSubtype


class ProductSubtypeRepository(
    BaseRepository[ProductSubtype],
    SearchMixin[ProductSubtype],
    AuditMixin[ProductSubtype],
    StatsMixin[ProductSubtype],
):
    """Concrete repository for **ProductSubtype**."""

    # ───────────────────── constructor & hook registration ────────────────── #
    def __init__(self) -> None:
        super().__init__(ProductSubtype)

        self.ENABLE_AUDIT = True
        self.ENABLE_SOFT_DELETE = False  # real deletes

        self.add_hook("after_create", self._log_creation)
        self.add_hook("before_delete", self._validate_delete)
        self.add_hook("after_update", self._purge_related_cache)

    # ───────────────────────── generic searching  ─────────────────────────── #
    @measure_performance()
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[ProductSubtype]:
        return self.find_by_multiple_criteria(criteria, operator="AND")

    # ───────────────────── simple look‑ups with cache  ────────────────────── #
    @cached_result(timeout=300)
    @measure_performance()
    def find_by_name(self, name: str) -> Optional[ProductSubtype]:
        return self.model_class.query.filter_by(name=name).first()

    def find_by_name_like(self, text: str) -> List[ProductSubtype]:
        return self.search(text, ["name"])

    def name_exists(self, name: str, *, exclude_id: int | None = None) -> bool:
        q = self.model_class.query.filter_by(name=name)
        if exclude_id:
            q = q.filter(self.model_class.id != exclude_id)
        return q.first() is not None

    # compound uniqueness
    def combination_exists(
        self,
        name: str,
        category_id: int,
        mine_id: int,
        *,
        exclude_id: int | None = None,
    ) -> bool:
        q = self.model_class.query.filter_by(
            name=name,
            category_id=category_id,
            mine_id=mine_id,
        )
        if exclude_id:
            q = q.filter(self.model_class.id != exclude_id)
        return q.first() is not None

    # ───────────────────── eager‑loaded queries  ──────────────────────────── #
    @cached_result(timeout=600)
    def get_subtypes_with_relationships(self) -> List[ProductSubtype]:
        return (
            self.model_class.query.options(
                joinedload(ProductSubtype.category),  # type: ignore[arg-type]
                joinedload(ProductSubtype.mine),      # type: ignore[arg-type]
            ).all()
        )

    def get_subtype_with_relationships(self, subtype_id: int) -> Optional[ProductSubtype]:
        return (
            self.model_class.query.options(
                joinedload(ProductSubtype.category),
                joinedload(ProductSubtype.mine),
            ).get(subtype_id)
        )

    # ───────────────────── look‑ups by foreign key  ───────────────────────── #
    @cached_result(timeout=300)
    def get_subtypes_by_category(self, category_id: int) -> List[ProductSubtype]:
        return self.model_class.query.filter_by(category_id=category_id).all()

    @cached_result(timeout=300)
    def get_subtypes_by_mine(self, mine_id: int) -> List[ProductSubtype]:
        return self.model_class.query.filter_by(mine_id=mine_id).all()

    # select / dropdown helper
    @cached_result(timeout=300)
    def get_subtypes_for_select(self) -> List[Dict[str, Any]]:
        subtypes = self.get_subtypes_with_relationships()
        return [
            {
                "id": s.id,
                "name": s.name,
                "category_name": s.category.name if s.category else "",
                "mine_name": s.mine.name if s.mine else "",
                "display_name": f"{s.name} "
                f"({s.category.name if s.category else ''} - "
                f"{s.mine.name if s.mine else ''})",
            }
            for s in subtypes
        ]

    def get_subtypes_by_ids(self, ids: List[int]) -> List[ProductSubtype]:
        return self.model_class.query.filter(ProductSubtype.id.in_(ids)).all()

    def get_ordered_by_name(self, ascending: bool = True) -> List[ProductSubtype]:
        order = ProductSubtype.name.asc() if ascending else ProductSubtype.name.desc()
        return self.model_class.query.order_by(order).all()

    def search_by_name_pattern(self, pattern: str) -> List[ProductSubtype]:
        return self.search(pattern, ["name"])

    # ───────────────────────── statistics  ────────────────────────────────── #
    @cached_result(timeout=900)
    def get_subtype_stats(self) -> Dict[str, Any]:
        total = self.count()

        by_category, by_mine = {}, {}
        for (cat_id,) in self.model_class.query.with_entities(
            ProductSubtype.category_id
        ).distinct():
            if cat_id:
                by_category[cat_id] = (
                    self.model_class.query.filter_by(category_id=cat_id).count()
                )

        for (mine_id,) in self.model_class.query.with_entities(
            ProductSubtype.mine_id
        ).distinct():
            if mine_id:
                by_mine[mine_id] = (
                    self.model_class.query.filter_by(mine_id=mine_id).count()
                )

        basic = self.get_basic_stats()
        return {
            "total_subtypes": total,
            "subtypes_by_category": by_category,
            "subtypes_by_mine": by_mine,
            "created_today": basic.get("created_today", 0),
            "created_this_week": basic.get("created_this_week", 0),
            "created_this_month": basic.get("created_this_month", 0),
        }

    # ────────────────── CRUD with compound‑key validation ─────────────────── #
    @logged_operation(log_level="INFO", include_args=True)
    def create_with_validation(
        self,
        name: str,
        category_id: int,
        mine_id: int,
    ) -> ProductSubtype:
        name = (name or "").strip()
        if self.combination_exists(name, category_id, mine_id):
            raise self.DuplicateError(  # type: ignore[attr-defined]
                "ProductSubtype",
                "name+category+mine",
                f"{name} ({category_id}, {mine_id})",
            )
        return self.create(name=name, category_id=category_id, mine_id=mine_id)

    @logged_operation(log_level="INFO", include_args=True)
    def update_with_validation(
        self,
        subtype_id: int,
        name: str,
        category_id: int,
        mine_id: int,
    ) -> Optional[ProductSubtype]:
        st = self.get_by_id(subtype_id)
        if st is None:
            return None

        name = (name or "").strip()
        if self.combination_exists(name, category_id, mine_id, exclude_id=subtype_id):
            raise self.DuplicateError(  # type: ignore[attr-defined]
                "ProductSubtype",
                "name+category+mine",
                f"{name} ({category_id}, {mine_id})",
            )
        return self.update(
            subtype_id,
            name=name,
            category_id=category_id,
            mine_id=mine_id,
        )

    def delete_with_validation(self, subtype_id: int) -> bool:
        st = self.get_by_id(subtype_id)
        if st is None:
            return False
        return self.delete(subtype_id)  # custom logic in before_delete hook

    # bulk
    def bulk_create_subtypes(
        self, payload: List[Dict[str, Any]]
    ) -> List[ProductSubtype]:
        for item in payload:
            name = (item.get("name") or "").strip()
            cat_id = item.get("category_id")
            mine_id = item.get("mine_id")
            if not (name and cat_id and mine_id):
                raise self.ValidationError(  # type: ignore[attr-defined]
                    "name, category_id and mine_id are required"
                )
            if self.combination_exists(name, cat_id, mine_id):
                raise self.DuplicateError(  # type: ignore[attr-defined]
                    "ProductSubtype",
                    "name+category+mine",
                    f"{name} ({cat_id}, {mine_id})",
                )

        return self.bulk_create(
            [
                {
                    "name": (p["name"]).strip(),
                    "category_id": p["category_id"],
                    "mine_id": p["mine_id"],
                }
                for p in payload
            ]
        )

    # ───────────────────────── custom hooks  ─────────────────────────────── #
    def _log_creation(self, entity: ProductSubtype, **_) -> None:
        self.logger.info("Subtype created: %s (ID %s)", entity.name, entity.id)

    def _validate_delete(self, entity: ProductSubtype, **_) -> None:
        # Add FK checks here (e.g. products referencing this subtype)
        pass

    def _purge_related_cache(self, entity: ProductSubtype, **_) -> None:
        self.clear_cache(pattern="subtype")
        self.clear_cache(pattern="subtype_stats")
        self.clear_cache(pattern=f"category_{entity.category_id}")
        self.clear_cache(pattern=f"mine_{entity.mine_id}")
