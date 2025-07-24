from flask import render_template, redirect, url_for, flash, request
from app.product import product_bp
from app.extensions import db
from app.models.product import ProductCategory, Mine, ProductSubtype
from .forms.forms import CategoryForm, MineForm, SubtypeForm

@product_bp.route('/categories')
def category_list():
    cats = ProductCategory.query.all()
    return render_template('category_list.html', cats=cats)