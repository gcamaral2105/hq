"""
ProductCategoryRepository – manage ProductCategory entities
===========================================================

Concrete repository built on top of the *advanced* internal stack:

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
from app.models.product import ProductCategory


class ProductCategoryRepository(
    BaseRepository[ProductCategory],
    SearchMixin[ProductCategory],
    AuditMixin[ProductCategory],
    StatsMixin[ProductCategory],
):
    """Repository tailored for **ProductCategory**."""

    # ─────────────────────────── constructor / hooks ───────────────────────── #
    def __init__(self) -> None:
        super().__init__(ProductCategory)

        self.ENABLE_AUDIT = True
        self.ENABLE_SOFT_DELETE = False  # real deletes

        self.add_hook("after_create", self._log_creation)
        self.add_hook("before_delete", self._check_subtypes_on_delete)
        self.add_hook("after_update", self._purge_related_cache)

    # ───────────────────────── advanced querying helpers ───────────────────── #
    @measure_performance()
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[ProductCategory]:
        """AND‑combined multi‑criteria search."""
        return self.find_by_multiple_criteria(criteria, operator="AND")

    @cached_result(timeout=300)
    @measure_performance()
    def find_by_name(self, name: str) -> Optional[ProductCategory]:
        """Exact‑name lookup (cached)."""
        return self.model_class.query.filter_by(name=name).first()

    def find_by_name_like(self, text: str) -> List[ProductCategory]:
        """ILIKE search across *name* column."""
        return self.search(text, ["name"])

    def name_exists(self, name: str, *, exclude_id: int | None = None) -> bool:
        q = self.model_class.query.filter_by(name=name)
        if exclude_id:
            q = q.filter(self.model_class.id != exclude_id)
        return q.first() is not None

    # ───────────────────────── eager‑loaded fetches ────────────────────────── #
    @cached_result(timeout=600)
    def get_categories_with_subtypes(self) -> List[ProductCategory]:
        return (
            self.model_class.query.options(joinedload(ProductCategory.subtypes))  # type: ignore[arg-type]
            .all()
        )

    def get_category_with_subtypes(self, category_id: int) -> Optional[ProductCategory]:
        return (
            self.model_class.query.options(joinedload(ProductCategory.subtypes))
            .get(category_id)
        )

    # ───────────────────────── dto / select helpers ────────────────────────── #
    @cached_result(timeout=300)
    def get_categories_for_select(self) -> List[Dict[str, Any]]:
        return [{"id": c.id, "name": c.name} for c in self.get_all()]

    def get_categories_by_ids(self, ids: List[int]) -> List[ProductCategory]:
        return self.model_class.query.filter(ProductCategory.id.in_(ids)).all()

    def get_ordered_by_name(self, ascending: bool = True) -> List[ProductCategory]:
        order = ProductCategory.name.asc() if ascending else ProductCategory.name.desc()
        return self.model_class.query.order_by(order).all()

    def search_by_name_pattern(self, pattern: str) -> List[ProductCategory]:
        return self.search(pattern, ["name"])

    # ───────────────────────── statistics  ─────────────────────────────────── #
    @cached_result(timeout=900)
    def get_category_stats(self) -> Dict[str, Any]:
        total = self.count()
        with_sub = (
            self.model_class.query.filter(self.model_class.subtypes.any()).count()
        )
        basic = self.get_basic_stats()  # from StatsMixin
        return {
            "total_categories": total,
            "categories_with_subtypes": with_sub,
            "categories_without_subtypes": total - with_sub,
            "created_today": basic.get("created_today", 0),
            "created_this_week": basic.get("created_this_week", 0),
            "created_this_month": basic.get("created_this_month", 0),
        }

    # ─────────────────────── CRUD with validation ─────────────────────────── #
    @logged_operation(log_level="INFO", include_args=True)
    def create_with_validation(self, name: str) -> ProductCategory:
        name = (name or "").strip()
        if self.name_exists(name):
            raise self.DuplicateError("ProductCategory", "name", name)  # type: ignore[attr-defined]
        return self.create(name=name)

    @logged_operation(log_level="INFO", include_args=True)
    def update_with_validation(
        self,
        category_id: int,
        name: str,
    ) -> Optional[ProductCategory]:
        cat = self.get_by_id(category_id)
        if cat is None:
            return None
        name = (name or "").strip()
        if self.name_exists(name, exclude_id=category_id):
            raise self.DuplicateError("ProductCategory", "name", name)  # type: ignore[attr-defined]
        return self.update(category_id, name=name)

    def delete_with_validation(self, category_id: int) -> bool:
        cat = self.get_by_id(category_id)
        if cat is None:
            return False
        return self.delete(category_id)  # FK check inside hook

    # ─────────────────────── bulk creation helper ─────────────────────────── #
    def bulk_create_categories(
        self, payload: List[Dict[str, Any]]
    ) -> List[ProductCategory]:
        for item in payload:
            name = (item.get("name") or "").strip()
            if not name:
                raise self.ValidationError("name is required")  # type: ignore[attr-defined]
            if self.name_exists(name):
                raise self.DuplicateError("ProductCategory", "name", name)  # type: ignore[attr-defined]

        return self.bulk_create([{"name": (p["name"]).strip()} for p in payload])

    # ─────────────────────────── custom hooks ─────────────────────────────── #
    def _log_creation(self, entity: ProductCategory, **_) -> None:
        self.logger.info("Category created: %s (ID %s)", entity.name, entity.id)

    def _check_subtypes_on_delete(self, entity: ProductCategory, **_) -> None:
        if getattr(entity, "subtypes", None):
            raise self.IntegrityError(  # type: ignore[attr-defined]
                "Cannot delete a category that still has sub‑types",
                constraint="fk_subtypes",
            )

    def _purge_related_cache(self, *_args, **_kw) -> None:
        self.clear_cache(pattern="category")
