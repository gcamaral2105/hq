"""
Settings Routes
===============

Routes for the Settings hub that manages product CRUD operations
and system configuration.
"""

from flask import render_template, request, redirect, url_for
from app.settings import settings_bp
from app.settings.controllers.settings_controller import SettingsController

# Initialize controller
controller = SettingsController()

# ========== DASHBOARD ==========

@settings_bp.route("/", methods=['GET'])
def dashboard():
    """Settings dashboard with overview and quick actions."""
    return controller.dashboard()

# ========== PRODUCT CATEGORIES ==========

@settings_bp.route("/products/categories", methods=['GET'])
def categories_list():
    """List all product categories."""
    return controller.categories_list()

@settings_bp.route("/products/categories/new", methods=['GET', 'POST'])
def category_create():
    """Create new product category."""
    return controller.category_create()

@settings_bp.route("/products/categories/<int:category_id>/edit", methods=['GET', 'POST'])
def category_edit(category_id):
    """Edit existing product category."""
    return controller.category_edit(category_id)

@settings_bp.route("/products/categories/<int:category_id>/delete", methods=['POST'])
def category_delete(category_id):
    """Delete product category."""
    return controller.category_delete(category_id)

# ========== MINES ==========

@settings_bp.route("/products/mines", methods=['GET'])
def mines_list():
    """List all mines."""
    return controller.mines_list()

@settings_bp.route("/products/mines/new", methods=['GET', 'POST'])
def mine_create():
    """Create new mine."""
    return controller.mine_create()

@settings_bp.route("/products/mines/<int:mine_id>/edit", methods=['GET', 'POST'])
def mine_edit(mine_id):
    """Edit existing mine."""
    return controller.mine_edit(mine_id)

@settings_bp.route("/products/mines/<int:mine_id>/delete", methods=['POST'])
def mine_delete(mine_id):
    """Delete mine."""
    return controller.mine_delete(mine_id)

# ========== PRODUCT SUBTYPES ==========

@settings_bp.route("/products/subtypes", methods=['GET'])
def subtypes_list():
    """List all product subtypes."""
    return controller.subtypes_list()

@settings_bp.route("/products/subtypes/new", methods=['GET', 'POST'])
def subtype_create():
    """Create new product subtype."""
    return controller.subtype_create()

@settings_bp.route("/products/subtypes/<int:subtype_id>/edit", methods=['GET', 'POST'])
def subtype_edit(subtype_id):
    """Edit existing product subtype."""
    return controller.subtype_edit(subtype_id)

@settings_bp.route("/products/subtypes/<int:subtype_id>/delete", methods=['POST'])
def subtype_delete(subtype_id):
    """Delete product subtype."""
    return controller.subtype_delete(subtype_id)

# ========== AJAX/API ENDPOINTS ==========

@settings_bp.route("/api/categories", methods=['GET'])
def api_categories():
    """Get categories as JSON."""
    return controller.get_categories_json()

@settings_bp.route("/api/mines", methods=['GET'])
def api_mines():
    """Get mines as JSON."""
    return controller.get_mines_json()

@settings_bp.route("/api/subtypes/category/<int:category_id>", methods=['GET'])
def api_subtypes_by_category(category_id):
    """Get subtypes for a specific category as JSON."""
    return controller.get_subtypes_by_category_json(category_id)

# ========== LEGACY ROUTE ==========

@settings_bp.route("/index", methods=['GET'])
def index():
    """Legacy index route - redirect to dashboard."""
    return redirect(url_for('settings_bp.dashboard'))