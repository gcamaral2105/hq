from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models.product import ProductCategory, Mine, ProductSubtype


class ProductCategoryForm(FlaskForm):
    """
    Form to register and edit Product Categories.
    
    Fields:
    - name: Category name (required, max 50 chars)
    - description: Optional detailed description
    
    Usage:
    form = ProductCategoryForm()
    if form.validate_on_submit():
        category = ProductCategory(name=form.name.data)
    """
    
    name = StringField(
        "Category Name", 
        validators=[
            DataRequired(message="Category name is required"),
            Length(max=50, message="Category name must be 50 characters or less")
        ],
        render_kw={"placeholder": "Enter category name"}
    )
    
    description = TextAreaField(
        "Description", 
        validators=[Optional()],
        render_kw={"placeholder": "Optional description of the category", "rows": 3}
    )
    
    submit = SubmitField("Save Category")
    
    def validate_name(self, field):
        """Custom validation to ensure category name is unique."""
        # Skip validation if this is an edit form (would need to pass category_id)
        existing = ProductCategory.query.filter_by(name=field.data).first()
        if existing:
            raise ValidationError("A category with this name already exists")


class MineForm(FlaskForm):
    """
    Form to register and edit Mining Locations.
    
    Fields:
    - name: Mine name (required, max 100 chars)
    - description: Optional detailed description
    
    Usage:
    form = MineForm()
    if form.validate_on_submit():
        mine = Mine(name=form.name.data)
    """
    
    name = StringField(
        "Mine Name", 
        validators=[
            DataRequired(message="Mine name is required"),
            Length(max=100, message="Mine name must be 100 characters or less")
        ],
        render_kw={"placeholder": "Enter mine name"}
    )
    
    description = TextAreaField(
        "Description", 
        validators=[Optional()],
        render_kw={"placeholder": "Optional description of the mine location", "rows": 3}
    )
    
    submit = SubmitField("Save Mine")
    
    def validate_name(self, field):
        """Custom validation to ensure mine name is unique."""
        existing = Mine.query.filter_by(name=field.data).first()
        if existing:
            raise ValidationError("A mine with this name already exists")


class ProductSubtypeForm(FlaskForm):
    """
    Form to register and edit Product Subtypes.
    
    Fields:
    - name: Subtype name (required, max 100 chars)
    - category_id: Associated category (required)
    - mine_id: Associated mine (optional)
    - description: Optional detailed description
    
    Usage:
    form = ProductSubtypeForm()
    form.set_choices()
    if form.validate_on_submit():
        subtype = ProductSubtype(name=form.name.data, ...)
    """
    
    name = StringField(
        "Subtype Name", 
        validators=[
            DataRequired(message="Subtype name is required"),
            Length(max=100, message="Subtype name must be 100 characters or less")
        ],
        render_kw={"placeholder": "Enter product subtype name"}
    )
    
    category_id = SelectField(
        "Product Category", 
        coerce=int, 
        validators=[DataRequired(message="Please select a category")],
        render_kw={"class": "form-select"}
    )
    
    mine_id = SelectField(
        "Mine Location", 
        coerce=int, 
        validators=[Optional()],
        render_kw={"class": "form-select"}
    )
    
    description = TextAreaField(
        "Description", 
        validators=[Optional()],
        render_kw={"placeholder": "Optional description of the product subtype", "rows": 3}
    )
    
    submit = SubmitField("Save Subtype")
    
    def set_category_choices(self):
        """Populate the category dropdown from the database."""
        categories = ProductCategory.query.order_by(ProductCategory.name).all()
        self.category_id.choices = [(0, "-- Select Category --")] + [
            (category.id, category.name) for category in categories
        ]
    
    def set_mine_choices(self):
        """Populate the mine dropdown from the database."""
        mines = Mine.query.order_by(Mine.name).all()
        self.mine_id.choices = [(0, "-- No Mine Selected --")] + [
            (mine.id, mine.name) for mine in mines
        ]
    
    def set_choices(self):
        """Convenience method to populate all dropdown choices."""
        self.set_category_choices()
        self.set_mine_choices()
    
    def validate_category_id(self, field):
        """Validate that a valid category is selected."""
        if field.data == 0:
            raise ValidationError("Please select a valid category")
    
    def validate_mine_id(self, field):
        """Convert 0 to None for optional mine selection."""
        if field.data == 0:
            field.data = None
    
    def validate_name(self, field):
        """Custom validation for unique subtype name within category/mine combination."""
        # This validation ensures the unique constraint is respected
        existing = ProductSubtype.query.filter_by(
            name=field.data,
            category_id=self.category_id.data if self.category_id.data != 0 else None,
            mine_id=self.mine_id.data if self.mine_id.data != 0 else None
        ).first()
        
        if existing:
            raise ValidationError(
                "A subtype with this name already exists for the selected category and mine combination"
            )


# Additional forms for enhanced functionality

class ProductSearchForm(FlaskForm):
    """
    Form for searching and filtering products.
    
    Provides search capabilities across categories, mines, and subtypes.
    """
    
    search_term = StringField(
        "Search", 
        validators=[Optional()],
        render_kw={"placeholder": "Search by name..."}
    )
    
    category_filter = SelectField(
        "Filter by Category", 
        coerce=int, 
        validators=[Optional()],
        render_kw={"class": "form-select"}
    )
    
    mine_filter = SelectField(
        "Filter by Mine", 
        coerce=int, 
        validators=[Optional()],
        render_kw={"class": "form-select"}
    )
    
    submit = SubmitField("Search")
    
    def set_filter_choices(self):
        """Populate filter dropdown choices."""
        # Categories
        categories = ProductCategory.query.order_by(ProductCategory.name).all()
        self.category_filter.choices = [(0, "All Categories")] + [
            (cat.id, cat.name) for cat in categories
        ]
        
        # Mines
        mines = Mine.query.order_by(Mine.name).all()
        self.mine_filter.choices = [(0, "All Mines")] + [
            (mine.id, mine.name) for mine in mines
        ]


class BulkProductImportForm(FlaskForm):
    """
    Form for bulk importing product data.
    
    Allows users to upload CSV files with product information
    for batch processing.
    """
    
    import_type = SelectField(
        "Import Type",
        choices=[
            ("categories", "Product Categories"),
            ("mines", "Mine Locations"),
            ("subtypes", "Product Subtypes")
        ],
        validators=[DataRequired(message="Please select import type")]
    )
    
    # Note: File upload field would be added here in a real implementation
    # file = FileField("CSV File", validators=[DataRequired()])
    
    overwrite_existing = SelectField(
        "If Record Exists",
        choices=[
            ("skip", "Skip existing records"),
            ("update", "Update existing records"),
            ("error", "Show error for duplicates")
        ],
        default="skip",
        validators=[DataRequired()]
    )
    
    submit = SubmitField("Import Data")