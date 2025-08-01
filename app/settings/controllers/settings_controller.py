"""
Settings Controller
==================

Central controller for the Settings hub that manages product CRUD operations
and other system configuration features.
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from app.models.product import ProductCategory, Mine, ProductSubtype
from app.product.forms.forms import ProductCategoryForm, MineForm, ProductSubtypeForm
from app.extensions import db
from typing import Dict, Any, List


class SettingsController:
    """
    Controller for Settings hub functionality.
    
    Manages CRUD operations for:
    - Product Categories
    - Mines
    - Product Subtypes
    - Partners
    - Partner Entities
    """

    def __init__(self):
        """Initialize the settings controller."""
        pass

    # ========== DASHBOARD ==========
    
    def dashboard(self):
        """
        Settings dashboard with overview of all manageable entities.
        
        Returns:
            Rendered template with entity counts and quick actions
        """
        try:
            # Get counts for dashboard
            stats = {
                'categories': ProductCategory.query.count(),
                'mines': Mine.query.count(),
                'subtypes': ProductSubtype.query.count(),
            }
            
            # Get recent items for quick access
            recent_categories = ProductCategory.query.order_by(ProductCategory.created_at.desc()).limit(5).all()
            recent_mines = Mine.query.order_by(Mine.created_at.desc()).limit(5).all()
            
            return render_template('settings/dashboard.html',
                                 stats=stats,
                                 recent_categories=recent_categories,
                                 recent_mines=recent_mines)
        except Exception as e:
            flash(f'Error loading dashboard: {str(e)}', 'error')
            return render_template('settings/dashboard.html',
                                 stats={},
                                 recent_categories=[],
                                 recent_mines=[])

    # ========== PRODUCT CATEGORIES ==========
    
    def categories_list(self):
        """List all product categories with management options."""
        try:
            categories = ProductCategory.query.order_by(ProductCategory.name).all()
            return render_template('settings/products/categories.html', categories=categories)
        except Exception as e:
            flash(f'Error loading categories: {str(e)}', 'error')
            return render_template('settings/products/categories.html', categories=[])
    
    def category_create(self):
        """Create new product category."""
        form = ProductCategoryForm()
        
        if form.validate_on_submit():
            try:
                category = ProductCategory(
                    name=form.name.data,
                    description=form.description.data
                )
                db.session.add(category)
                db.session.commit()
                flash(f'Category "{category.name}" created successfully!', 'success')
                return redirect(url_for('settings_bp.categories_list'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating category: {str(e)}', 'error')
        
        return render_template('settings/products/category_form.html', form=form, action='Create')
    
    def category_edit(self, category_id: int):
        """Edit existing product category."""
        category = ProductCategory.query.get_or_404(category_id)
        form = ProductCategoryForm(obj=category)
        
        if form.validate_on_submit():
            try:
                category.name = form.name.data
                category.description = form.description.data
                category.update_audit_fields()
                db.session.commit()
                flash(f'Category "{category.name}" updated successfully!', 'success')
                return redirect(url_for('settings_bp.categories_list'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating category: {str(e)}', 'error')
        
        return render_template('settings/products/category_form.html', 
                             form=form, action='Edit', category=category)
    
    def category_delete(self, category_id: int):
        """Delete product category."""
        category = ProductCategory.query.get_or_404(category_id)
        
        try:
            # Check if category has subtypes
            if category.subtypes:
                flash(f'Cannot delete category "{category.name}" - it has {len(category.subtypes)} subtypes', 'error')
                return redirect(url_for('settings_bp.categories_list'))
            
            db.session.delete(category)
            db.session.commit()
            flash(f'Category "{category.name}" deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting category: {str(e)}', 'error')
        
        return redirect(url_for('settings_bp.categories_list'))

    # ========== MINES ==========
    
    def mines_list(self):
        """List all mines with management options."""
        try:
            mines = Mine.query.order_by(Mine.name).all()
            return render_template('settings/products/mines.html', mines=mines)
        except Exception as e:
            flash(f'Error loading mines: {str(e)}', 'error')
            return render_template('settings/products/mines.html', mines=[])
    
    def mine_create(self):
        """Create new mine."""
        form = MineForm()
        
        if form.validate_on_submit():
            try:
                mine = Mine(
                    name=form.name.data,
                    description=form.description.data
                )
                db.session.add(mine)
                db.session.commit()
                flash(f'Mine "{mine.name}" created successfully!', 'success')
                return redirect(url_for('settings_bp.mines_list'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating mine: {str(e)}', 'error')
        
        return render_template('settings/products/mine_form.html', form=form, action='Create')
    
    def mine_edit(self, mine_id: int):
        """Edit existing mine."""
        mine = Mine.query.get_or_404(mine_id)
        form = MineForm(obj=mine)
        
        if form.validate_on_submit():
            try:
                mine.name = form.name.data
                mine.description = form.description.data
                mine.update_audit_fields()
                db.session.commit()
                flash(f'Mine "{mine.name}" updated successfully!', 'success')
                return redirect(url_for('settings_bp.mines_list'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating mine: {str(e)}', 'error')
        
        return render_template('settings/products/mine_form.html', 
                             form=form, action='Edit', mine=mine)
    
    def mine_delete(self, mine_id: int):
        """Delete mine."""
        mine = Mine.query.get_or_404(mine_id)
        
        try:
            # Check if mine has subtypes
            if mine.subtypes:
                flash(f'Cannot delete mine "{mine.name}" - it has {len(mine.subtypes)} subtypes', 'error')
                return redirect(url_for('settings_bp.mines_list'))
            
            db.session.delete(mine)
            db.session.commit()
            flash(f'Mine "{mine.name}" deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting mine: {str(e)}', 'error')
        
        return redirect(url_for('settings_bp.mines_list'))

    # ========== PRODUCT SUBTYPES ==========
    
    def subtypes_list(self):
        """List all product subtypes with management options."""
        try:
            subtypes = ProductSubtype.query.order_by(ProductSubtype.name).all()
            return render_template('settings/products/subtypes.html', subtypes=subtypes)
        except Exception as e:
            flash(f'Error loading subtypes: {str(e)}', 'error')
            return render_template('settings/products/subtypes.html', subtypes=[])
    
    def subtype_create(self):
        """Create new product subtype."""
        form = ProductSubtypeForm()
        form.set_choices()
        
        if form.validate_on_submit():
            try:
                subtype = ProductSubtype(
                    name=form.name.data,
                    category_id=form.category_id.data,
                    mine_id=form.mine_id.data,
                    description=form.description.data
                )
                db.session.add(subtype)
                db.session.commit()
                flash(f'Subtype "{subtype.name}" created successfully!', 'success')
                return redirect(url_for('settings_bp.subtypes_list'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating subtype: {str(e)}', 'error')
        
        return render_template('settings/products/subtype_form.html', form=form, action='Create')
    
    def subtype_edit(self, subtype_id: int):
        """Edit existing product subtype."""
        subtype = ProductSubtype.query.get_or_404(subtype_id)
        form = ProductSubtypeForm(obj=subtype)
        form.set_choices()
        
        if form.validate_on_submit():
            try:
                subtype.name = form.name.data
                subtype.category_id = form.category_id.data
                subtype.mine_id = form.mine_id.data
                subtype.description = form.description.data
                subtype.update_audit_fields()
                db.session.commit()
                flash(f'Subtype "{subtype.name}" updated successfully!', 'success')
                return redirect(url_for('settings_bp.subtypes_list'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating subtype: {str(e)}', 'error')
        
        return render_template('settings/products/subtype_form.html', 
                             form=form, action='Edit', subtype=subtype)
    
    def subtype_delete(self, subtype_id: int):
        """Delete product subtype."""
        subtype = ProductSubtype.query.get_or_404(subtype_id)
        
        try:
            db.session.delete(subtype)
            db.session.commit()
            flash(f'Subtype "{subtype.name}" deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting subtype: {str(e)}', 'error')
        
        return redirect(url_for('settings_bp.subtypes_list'))

    # ========== AJAX/API ENDPOINTS ==========
    
    def get_categories_json(self):
        """Get categories as JSON for AJAX requests."""
        try:
            categories = ProductCategory.query.order_by(ProductCategory.name).all()
            return jsonify([cat.to_dict(include_audit=False) for cat in categories])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_mines_json(self):
        """Get mines as JSON for AJAX requests."""
        try:
            mines = Mine.query.order_by(Mine.name).all()
            return jsonify([mine.to_dict(include_audit=False) for mine in mines])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_subtypes_by_category_json(self, category_id: int):
        """Get subtypes for a specific category as JSON."""
        try:
            subtypes = ProductSubtype.query.filter_by(category_id=category_id).order_by(ProductSubtype.name).all()
            return jsonify([st.to_dict(include_audit=False) for st in subtypes])
        except Exception as e:
            return jsonify({'error': str(e)}), 500