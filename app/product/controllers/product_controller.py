"""
product/controllers/product_controller.py
=========================================

Central controller that wires HTML views and AJAX endpoints
to the Product* service layer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from flask import (
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
    flash,
)
from app.product.services import (
    ProductCategoryService,
    MineService,
    ProductSubtypeService,
)
from app.product.forms.forms import CategoryForm, MineForm, SubtypeForm


class ProductController:
    """Aggregate controller for *all* product-related UI and API endpoints."""

    # ─────────────────────────── constructor ──────────────────────────── #
    def __init__(self) -> None:
        self.category_service = ProductCategoryService()
        self.mine_service = MineService()
        self.subtype_service = ProductSubtypeService()

    # ==================================================================== #
    # CATEGORY ACTIONS                                                     #
    # ==================================================================== #
    def category_list(self):
        """HTML page – list all categories (with sub-types)."""
        try:
            cats = self.category_service.get_all_categories(include_subtypes=True)
            return render_template("product/category_list.html", categories=cats)
        except Exception as exc:  # noqa: BLE001
            flash(f"Failed to load categories: {exc}", "error")
            return render_template("product/category_list.html", categories=[])

    def category_create(self):
        """HTML form – create a new category."""
        form = CategoryForm()
        if form.validate_on_submit():
            res = self.category_service.create_category(form.name.data)
            flash(res["message"], "success" if res["success"] else "error")
            return redirect(url_for("product_bp.category_list"))
        return render_template(
            "product/category_form.html", form=form, title="New Category"
        )

    def category_edit(self, category_id: int):
        """HTML form – edit an existing category."""
        cat = self.category_service.get_category(category_id)
        if cat is None:
            flash("Category not found", "error")
            return redirect(url_for("product_bp.category_list"))

        form = CategoryForm(obj=cat)
        if form.validate_on_submit():
            res = self.category_service.update_category(category_id, form.name.data)
            flash(res["message"], "success" if res["success"] else "error")
            return redirect(url_for("product_bp.category_list"))

        return render_template(
            "product/category_form.html",
            form=form,
            title="Edit Category",
            category=cat,
        )

    def category_delete(self, category_id: int):
        """Delete a category and redirect back to the list."""
        res = self.category_service.delete_category(category_id)
        flash(res["message"], "success" if res["success"] else "error")
        return redirect(url_for("product_bp.category_list"))

    # ==================================================================== #
    # MINE ACTIONS                                                         #
    # ==================================================================== #
    def mine_list(self):
        try:
            mines = self.mine_service.get_all_mines(include_subtypes=True)
            return render_template("product/mine_list.html", mines=mines)
        except Exception as exc:  # noqa: BLE001
            flash(f"Failed to load mines: {exc}", "error")
            return render_template("product/mine_list.html", mines=[])

    def mine_create(self):
        form = MineForm()
        if form.validate_on_submit():
            res = self.mine_service.create_mine(form.name.data)
            flash(res["message"], "success" if res["success"] else "error")
            return redirect(url_for("product_bp.mine_list"))
        return render_template("product/mine_form.html", form=form, title="New Mine")

    def mine_edit(self, mine_id: int):
        mine = self.mine_service.get_mine(mine_id)
        if mine is None:
            flash("Mine not found", "error")
            return redirect(url_for("product_bp.mine_list"))

        form = MineForm(obj=mine)
        if form.validate_on_submit():
            res = self.mine_service.update_mine(mine_id, form.name.data)
            flash(res["message"], "success" if res["success"] else "error")
            return redirect(url_for("product_bp.mine_list"))

        return render_template(
            "product/mine_form.html", form=form, title="Edit Mine", mine=mine
        )

    def mine_delete(self, mine_id: int):
        res = self.mine_service.delete_mine(mine_id)
        flash(res["message"], "success" if res["success"] else "error")
        return redirect(url_for("product_bp.mine_list"))

    # ==================================================================== #
    # SUBTYPE ACTIONS                                                      #
    # ==================================================================== #
    def subtype_list(self):
        try:
            sts = self.subtype_service.get_all_subtypes(include_relationships=True)
            return render_template("product/subtype_list.html", subtypes=sts)
        except Exception as exc:  # noqa: BLE001
            flash(f"Failed to load sub-types: {exc}", "error")
            return render_template("product/subtype_list.html", subtypes=[])

    def subtype_create(self):
        form = SubtypeForm()
        form.category_id.choices = [(0, "Select a category")] + [
            (cid, name) for cid, name in self.category_service.get_categories_for_select()
        ]
        form.mine_id.choices = [(0, "Select a mine (optional)")] + [
            (mid, name) for mid, name in self.mine_service.get_mines_for_select()
        ]

        if form.validate_on_submit():
            mine_id = form.mine_id.data or None
            res = self.subtype_service.create_subtype(
                form.name.data, form.category_id.data, mine_id
            )
            flash(res["message"], "success" if res["success"] else "error")
            return redirect(url_for("product_bp.subtype_list"))

        return render_template(
            "product/subtype_form.html", form=form, title="New Sub-type"
        )

    def subtype_edit(self, subtype_id: int):
        st = self.subtype_service.get_subtype(
            subtype_id, include_relationships=True
        )
        if st is None:
            flash("Sub-type not found", "error")
            return redirect(url_for("product_bp.subtype_list"))

        form = SubtypeForm(obj=st)
        form.category_id.choices = [(0, "Select a category")] + [
            (cid, name) for cid, name in self.category_service.get_categories_for_select()
        ]
        form.mine_id.choices = [(0, "Select a mine (optional)")] + [
            (mid, name) for mid, name in self.mine_service.get_mines_for_select()
        ]
        form.category_id.data = st.category_id
        form.mine_id.data = st.mine_id or 0

        if form.validate_on_submit():
            mine_id = form.mine_id.data or None
            res = self.subtype_service.update_subtype(
                subtype_id,
                form.name.data,
                form.category_id.data,
                mine_id,
            )
            flash(res["message"], "success" if res["success"] else "error")
            return redirect(url_for("product_bp.subtype_list"))

        return render_template(
            "product/subtype_form.html",
            form=form,
            title="Edit Sub-type",
            subtype=st,
        )

    def subtype_delete(self, subtype_id: int):
        res = self.subtype_service.delete_subtype(subtype_id)
        flash(res["message"], "success" if res["success"] else "error")
        return redirect(url_for("product_bp.subtype_list"))

    # ==================================================================== #
    # AJAX / API ENDPOINTS                                                 #
    # ==================================================================== #
    def get_subtypes_by_category(self, category_id: int):
        """AJAX – return sub-types for a given category."""
        try:
            sts = self.subtype_service.get_subtypes_for_select_by_category(category_id)
            return jsonify(
                {
                    "success": True,
                    "subtypes": [{"id": sid, "name": name} for sid, name in sts],
                }
            )
        except Exception as exc:  # noqa: BLE001
            return jsonify({"success": False, "message": str(exc)}), 500

    def search_products(self):
        """AJAX / HTML – search across categories, mines, and sub-types."""
        term: str = request.args.get("q", default="")
        cat_id: int | None = request.args.get("category_id", type=int)
        mine_id: int | None = request.args.get("mine_id", type=int)

        try:
            ctx: Dict[str, Any] = {
                "categories": self.category_service.search_categories(term),
                "mines": self.mine_service.search_mines(term),
                "subtypes": self.subtype_service.search_subtypes(
                    term, cat_id, mine_id
                ),
                "search_term": term,
            }
            return render_template("product/search_results.html", **ctx)
        except Exception as exc:  # noqa: BLE001
            flash(f"Search failed: {exc}", "error")
            return redirect(url_for("product_bp.category_list"))
