from app.extensions import db
from typing import Optional, Dict
from enum import Enum

class EntityTypeEnum(str, Enum):
    HALCO = 'halco_buyer'
    OFFTAKER = 'offtaker'

class PartnerEntity(db.Model):
    """Represents one of the buyer's entity"""

    __tablename__ = 'partner_entities'

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)
    code: str = db.Column(db.String(20), unique=True, nullable=False)
    description: Optional[str] = db.Column(db.Text)

    # Entity type
    entity_type: EntityTypeEnum = db.Column(
        db.Enum(EntityTypeEnum, name='entity_type_enum'),
        default=EntityTypeEnum.OFFTAKER,
        nullable=False
    )

    # Relationship
    partners = db.relationship('Partner', backref='entity', lazy='select', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f'<Entity {self.name}>'
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'entity_type': self.entity_type.value,
        }
        
class Partner(db.Model):
    """Represents a specific client within an entity"""

    __tablename__ = 'partners'

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)
    code: str = db.Column(db.String(20), unique=True, nullable=False)
    description: Optional[str] = db.Column(db.Text)

    # Father Entity
    entity_id: int = db.Column(db.Integer, db.ForeignKey('partner_entities.id'), ondelete='CASCADE', nullable=False)

    # Distribution within entity
    minimum_volume_three_mt: Optional[int] = db.Column(db.Integer)

    def __repr__(self) -> str:
        return f'Client {self.name} ({self.entity.name})>'
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'entity_id': self.entity_id,
            'entity_name': self.entity.name if self.entity else None,
            'entity_type': self.entity.entity_type.value if self.entity else None,
            'minimum_volume_three_mt': float(self.minimum_volume_three_mt) if self.minimum_volume_three_mt else None,
        }