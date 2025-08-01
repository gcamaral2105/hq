from flask import render_template, redirect, url_for, flash, request
from app.product import product_bp
from app.extensions import db
from app.models.product import ProductCategory, Mine, ProductSubtype
from .forms.forms import ProductCategoryForm, MineForm, ProductSubtypeForm
from .controllers.product_controller import ProductController

# Instanciar o controller
controller = ProductController()

# ========== CATEGORY ROUTES ==========

@product_bp.route('/categories')
def category_list():
    return controller.category_list()

@product_bp.route('/categories/new', methods=['GET', 'POST'])
def category_create():
    return controller.category_create()

@product_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
def category_edit(category_id):
    return controller.category_edit(category_id)

@product_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
def category_delete(category_id):
    return controller.category_delete(category_id)

# ========== MINE ROUTES ==========

@product_bp.route('/mines')
def mine_list():
    return controller.mine_list()

@product_bp.route('/mines/new', methods=['GET', 'POST'])
def mine_create():
    return controller.mine_create()

@product_bp.route('/mines/<int:mine_id>/edit', methods=['GET', 'POST'])
def mine_edit(mine_id):
    return controller.mine_edit(mine_id)

@product_bp.route('/mines/<int:mine_id>/delete', methods=['POST'])
def mine_delete(mine_id):
    return controller.mine_delete(mine_id)

# ========== SUBTYPE ROUTES ==========

@product_bp.route('/subtypes')
def subtype_list():
    return controller.subtype_list()

@product_bp.route('/subtypes/new', methods=['GET', 'POST'])
def subtype_create():
    return controller.subtype_create()

@product_bp.route('/subtypes/<int:subtype_id>/edit', methods=['GET', 'POST'])
def subtype_edit(subtype_id):
    return controller.subtype_edit(subtype_id)

@product_bp.route('/subtypes/<int:subtype_id>/delete', methods=['POST'])
def subtype_delete(subtype_id):
    return controller.subtype_delete(subtype_id)

# ========== AJAX/API ROUTES ==========

@product_bp.route('/api/subtypes/category/<int:category_id>')
def get_subtypes_by_category(category_id):
    return controller.get_subtypes_by_category(category_id)

@product_bp.route('/search')
def search_products():
    return controller.search_products()

# ========== DASHBOARD ROUTE ==========

@product_bp.route('/')
def dashboard():
    """Dashboard principal de produtos."""
    try:
        categories_count = controller.category_service.repository.count()
        mines_count = controller.mine_service.repository.count()
        subtypes_count = controller.subtype_service.repository.count()
        
        return render_template('product/dashboard.html',
                             categories_count=categories_count,
                             mines_count=mines_count,
                             subtypes_count=subtypes_count)
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'error')
        return render_template('product/dashboard.html',
                             categories_count=0,
                             mines_count=0,
                             subtypes_count=0)