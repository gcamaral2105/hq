from app.extensions import db
from datetime import date
from decimal import Decimal
from typing import Optional, Dict
from enum import Enum
import json

class ScenarioStatus(str, Enum):
    DRAFT = "draft"
    PLAN = "plan"
    FORECAST = 'forecast'
    COMPLETED = 'completed'
    ARCHIVED = 'archived'

class ProductionScenario(db.Model):
    """Bauxite Production Scenario Model"""

    __tablename__ = 'production_scenarios'

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(200), nullable=False)
    description: Optional[str] = db.Column(db.Text)
    contractual_year: int = db.Column(db.Integer, nullable=False)
    start_date: date = db.Column(db.Date, nullable=False)
    end_date: date = db.Column(db.Date, nullable=False)
    status: ScenarioStatus = db.Column(
        db.Enum(ScenarioStatus, name='production_scenario_stus'),
        default=ScenarioStatus.DRAFT,
        nullable=False
    )

    # Production Data
    production_volume: int = db.Column(db.Integer, nullable=False)
    moisture_percentage: Decimal = db.Column(db.Numeric(5,2), default=3.0)

    # Distribution per Partner (JSON)
    partner_allocation_json: json = db.Column(db.JSON)

    # Metadata
    is_baseline: bool = db.Column(db.Boolean, default=False)
    parent_scenario_id: int = db.Column(db.Integer, db.ForeignKey('production_scenarios.id'))

    # Relationships
    parent_scenario = db.relationship('ProductionScenario', remote_side=[id], backref='derived_scenarios')


