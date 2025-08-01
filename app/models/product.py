from app.extensions import db
from app.lib import BaseModel
from typing import Dict, Any, List, Optional


class ProductCategory(BaseModel):
    """
    Product Category Model
    
    Represents different categories of bauxite products.
    Each category can have multiple subtypes associated with it.
    """

    __tablename__ = 'product_category'

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(
        db.String(50), 
        unique=True, 
        nullable=False,
        comment="Unique name of the product category"
    )
    
    # Relationships
    subtypes = db.relationship(
        'ProductSubtype', 
        back_populates='category',
        cascade='all, delete-orphan', 
        lazy='select'
    )
    
    def __repr__(self) -> str:
        return f"<ProductCategory: {self.name!r}>"
    
    def to_dict(self, include_subtypes: bool = False, include_audit: bool = True) -> Dict[str, Any]:
        """
        Convert to dictionary with optional subtype inclusion.
        
        Args:
            include_subtypes: Whether to include related subtypes
            include_audit: Whether to include audit fields
            
        Returns:
            Dictionary representation of the category
        """
        result = super().to_dict(include_audit=include_audit)
        
        if include_subtypes:
            result['subtypes'] = [st.to_dict(include_audit=include_audit) for st in self.subtypes]
        else:
            result['subtypes_count'] = len(self.subtypes)
            
        return result


class Mine(BaseModel):
    """
    Mine Model
    
    Represents mining locations where bauxite is extracted.
    Each mine can produce multiple product subtypes.
    """

    __tablename__ = 'mine'
    
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(
        db.String(100), 
        unique=True, 
        nullable=False,
        comment="Unique name of the mine"
    )

    # Relationships
    subtypes = db.relationship(
        'ProductSubtype', 
        back_populates='mine', 
        cascade='all, delete-orphan', 
        lazy='select'
    )

    def __repr__(self) -> str:
        return f"<Mine: {self.name!r}>"
    
    def to_dict(self, include_subtypes: bool = False, include_audit: bool = True) -> Dict[str, Any]:
        """
        Convert to dictionary with optional subtype inclusion.
        
        Args:
            include_subtypes: Whether to include related subtypes
            include_audit: Whether to include audit fields
            
        Returns:
            Dictionary representation of the mine
        """
        result = super().to_dict(include_audit=include_audit)
        
        if include_subtypes:
            result['subtypes'] = [st.to_dict(include_audit=include_audit) for st in self.subtypes]
        else:
            result['subtypes_count'] = len(self.subtypes)
            
        return result


class ProductSubtype(BaseModel):
    """
    Product Subtype Model
    
    Represents specific subtypes of bauxite products.
    Each subtype belongs to a category and is associated with a mine.
    """

    __tablename__ = 'product_subtype'

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(
        db.String(100), 
        nullable=False, 
        index=True,
        comment="Name of the product subtype"
    )
    
    # Foreign Keys
    category_id: int = db.Column(
        db.Integer, 
        db.ForeignKey('product_category.id', ondelete='CASCADE'), 
        nullable=True,
        comment="ID of the associated product category"
    )
    mine_id: int = db.Column(
        db.Integer, 
        db.ForeignKey('mine.id', ondelete='SET NULL'), 
        nullable=True,
        comment="ID of the associated mine"
    )
    
    # Relationships
    category = db.relationship('ProductCategory', back_populates='subtypes')
    mine = db.relationship('Mine', back_populates='subtypes')

    # Table constraints
    __table_args__ = (
        db.UniqueConstraint(
            'name', 'category_id', 'mine_id',
            name='uq_subtype_category_mine'
        ),
        db.Index('idx_subtype_category', 'category_id'),
        db.Index('idx_subtype_mine', 'mine_id'),
    )

    def __repr__(self) -> str:
        mine_name = self.mine.name if self.mine else '-'
        return f"<ProductSubtype: {mine_name} / {self.name!r}>"
    
    def to_dict(self, include_relations: bool = True, include_audit: bool = True) -> Dict[str, Any]:
        """
        Convert to dictionary with optional relation details.
        
        Args:
            include_relations: Whether to include category and mine details
            include_audit: Whether to include audit fields
            
        Returns:
            Dictionary representation of the subtype
        """
        result = super().to_dict(include_audit=include_audit)
        
        if include_relations:
            result['category'] = {
                'id': self.category.id, 
                'name': self.category.name
            } if self.category else None
            
            result['mine'] = {
                'id': self.mine.id, 
                'name': self.mine.name
            } if self.mine else None
        
        return result
    
    def validate(self) -> List[str]:
        """
        Validate the product subtype data.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("Product subtype name is required")
            
        if len(self.name) > 100:
            errors.append("Product subtype name must be 100 characters or less")
            
        # Business rule: subtype should have either category or mine (or both)
        if not self.category_id and not self.mine_id:
            errors.append("Product subtype must be associated with either a category or a mine")
            
        return errors