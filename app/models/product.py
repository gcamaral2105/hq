from app.extensions import db

class ProductCategory(db.Model):

    __tablename__ = 'product_category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    subtypes = db.relationship('ProductSubtype', back_populates='category',
                               cascade='all, delete-orphan', lazy='select')
    
    def __repr__(self):
        return f"<Product Category: {self.name!r}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subtypes': [st.to_dict() for st in self.subtypes]
        }

class Mine(db.Model):

    __tablename__ = 'mine'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    subtypes = db.relationship('ProductSubtype', back_populates='mine', cascade='all, delete-orphan', lazy='select')

    def __repr__(self):
        return f"<Mine: {self.name!r}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subtypes': [st.to_dict() for st in self.subtypes]
        }

class ProductSubtype(db.Model):

    __tablename__ = 'product_subtype'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.id', ondelete='CASCADE'), nullable=True)
    mine_id = db.Column(db.Integer, db.ForeignKey('mine.id', ondelete='SET NULL'), nullable=True)
    category = db.relationship('ProductCategory', back_populates='subtypes')
    mine = db.relationship('Mine', back_populates='subtypes')

    __table_args__ = (
        db.UniqueConstraint('name', 'category_id', 'mine_id',
                            name='uq_subtype_category_mine'),
    )

    def __repr__(self):
        mine_name = self.mine.name if self.mine else '-'
        return f"<Product Subtype: {mine_name} / {self.name!r}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category_id': self.category_id,
            'mine_id': self.mine_id,
            'category': {'id': self.category.id, 'name': self.category.name},
            'mine': {'id': self.mine.id, 'name': self.mine.name} if self.mine else None
        }
