from app.extensions import db
from app.lib import BaseModel
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from enum import Enum
import json


class ScenarioStatus(str, Enum):
    """Enumeration for production scenario status."""
    DRAFT = "draft"
    PLAN = "plan"
    FORECAST = 'forecast'
    COMPLETED = 'completed'
    ARCHIVED = 'archived'


class ProductionScenario(BaseModel):
    """
    Bauxite Production Scenario Model
    
    Represents different production scenarios for bauxite mining operations.
    Each scenario includes production volumes, partner allocations, and
    timeline information for planning and forecasting purposes.
    """

    __tablename__ = 'production_scenarios'

    id: int = db.Column(db.Integer, primary_key=True)
    
    # Basic scenario information
    name: str = db.Column(
        db.String(200), 
        nullable=False,
        comment="Name of the production scenario"
    )
    description: Optional[str] = db.Column(
        db.Text,
        comment="Detailed description of the scenario"
    )
    
    # Timeline information
    contractual_year: int = db.Column(
        db.Integer, 
        nullable=False,
        comment="Contractual year for this scenario"
    )
    start_date: date = db.Column(
        db.Date, 
        nullable=False,
        comment="Start date of the production scenario"
    )
    end_date: date = db.Column(
        db.Date, 
        nullable=False,
        comment="End date of the production scenario"
    )
    
    # Status tracking
    status: ScenarioStatus = db.Column(
        db.Enum(ScenarioStatus, name='production_scenario_status'),
        default=ScenarioStatus.DRAFT,
        nullable=False,
        comment="Current status of the scenario"
    )

    # Production data
    production_volume: Decimal = db.Column(
        db.Numeric(15, 2), 
        nullable=False,
        comment="Total production volume in metric tons"
    )
    moisture_percentage: Decimal = db.Column(
        db.Numeric(5, 2), 
        default=Decimal('3.0'),
        nullable=False,
        comment="Moisture percentage of the bauxite"
    )

    # Partner allocation data (JSON format for flexibility)
    partner_allocation_json: Optional[str] = db.Column(
        db.JSON,
        comment="JSON data containing partner allocation details"
    )

    # Scenario metadata
    is_baseline: bool = db.Column(
        db.Boolean, 
        default=False,
        nullable=False,
        comment="Whether this is a baseline scenario"
    )
    
    # Self-referential relationship for scenario variants
    parent_scenario_id: Optional[int] = db.Column(
        db.Integer, 
        db.ForeignKey('production_scenarios.id', ondelete='SET NULL'),
        nullable=True,
        comment="ID of the parent scenario if this is a variant"
    )

    # Relationships
    parent_scenario = db.relationship(
        'ProductionScenario', 
        remote_side=[id], 
        backref='derived_scenarios'
    )
    
    # Table constraints and indexes
    __table_args__ = (
        db.CheckConstraint(
            'production_volume > 0', 
            name='positive_production_volume'
        ),
        db.CheckConstraint(
            'moisture_percentage >= 0 AND moisture_percentage <= 100', 
            name='valid_moisture_percentage'
        ),
        db.CheckConstraint(
            'start_date <= end_date', 
            name='valid_date_range'
        ),
        db.CheckConstraint(
            'contractual_year >= 2020 AND contractual_year <= 2050', 
            name='valid_contractual_year'
        ),
        db.Index('idx_scenario_year_status', 'contractual_year', 'status'),
        db.Index('idx_scenario_dates', 'start_date', 'end_date'),
        db.Index('idx_scenario_baseline', 'is_baseline'),
    )

    def __repr__(self) -> str:
        return f"<ProductionScenario: {self.name} ({self.contractual_year})>"
    
    def to_dict(self, include_allocations: bool = True, include_audit: bool = True) -> Dict[str, Any]:
        """
        Convert to dictionary with optional allocation details.
        
        Args:
            include_allocations: Whether to include partner allocation data
            include_audit: Whether to include audit fields
            
        Returns:
            Dictionary representation of the scenario
        """
        result = super().to_dict(include_audit=include_audit)
        
        # Convert special types for JSON serialization
        result['status'] = self.status.value
        result['production_volume'] = float(self.production_volume)
        result['moisture_percentage'] = float(self.moisture_percentage)
        result['start_date'] = self.start_date.isoformat()
        result['end_date'] = self.end_date.isoformat()
        
        # Include parent scenario info if available
        if self.parent_scenario:
            result['parent_scenario'] = {
                'id': self.parent_scenario.id,
                'name': self.parent_scenario.name
            }
        
        # Include derived scenarios count
        result['derived_scenarios_count'] = len(self.derived_scenarios)
        
        # Include partner allocations if requested
        if include_allocations and self.partner_allocation_json:
            try:
                result['partner_allocations'] = json.loads(self.partner_allocation_json)
            except (json.JSONDecodeError, TypeError):
                result['partner_allocations'] = None
                
        return result
    
    def validate(self) -> List[str]:
        """
        Validate the production scenario data.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Basic field validation
        if not self.name or not self.name.strip():
            errors.append("Scenario name is required")
            
        if len(self.name) > 200:
            errors.append("Scenario name must be 200 characters or less")
            
        # Date validation
        if self.start_date >= self.end_date:
            errors.append("Start date must be before end date")
            
        # Year validation
        current_year = datetime.now().year
        if self.contractual_year < 2020 or self.contractual_year > current_year + 30:
            errors.append(f"Contractual year must be between 2020 and {current_year + 30}")
            
        # Production volume validation
        if self.production_volume <= 0:
            errors.append("Production volume must be positive")
            
        if self.production_volume > Decimal('1000000'):  # 1M metric tons
            errors.append("Production volume seems unreasonably high (>1M MT)")
            
        # Moisture percentage validation
        if self.moisture_percentage < 0 or self.moisture_percentage > 100:
            errors.append("Moisture percentage must be between 0 and 100")
            
        # Partner allocation validation
        if self.partner_allocation_json:
            allocation_errors = self._validate_partner_allocations()
            errors.extend(allocation_errors)
            
        # Business rule: baseline scenarios should not have parent scenarios
        if self.is_baseline and self.parent_scenario_id:
            errors.append("Baseline scenarios cannot have parent scenarios")
            
        return errors
    
    def _validate_partner_allocations(self) -> List[str]:
        """
        Validate partner allocation JSON data.
        
        Returns:
            List of validation errors for allocations
        """
        errors = []
        
        try:
            allocations = json.loads(self.partner_allocation_json)
            
            if not isinstance(allocations, dict):
                errors.append("Partner allocations must be a JSON object")
                return errors
                
            total_percentage = 0
            for partner_id, allocation in allocations.items():
                if not isinstance(allocation, dict):
                    errors.append(f"Allocation for partner {partner_id} must be an object")
                    continue
                    
                percentage = allocation.get('percentage', 0)
                volume = allocation.get('volume', 0)
                
                if not isinstance(percentage, (int, float)) or percentage < 0 or percentage > 100:
                    errors.append(f"Invalid percentage for partner {partner_id}")
                    
                if not isinstance(volume, (int, float)) or volume < 0:
                    errors.append(f"Invalid volume for partner {partner_id}")
                    
                total_percentage += percentage
            
            # Check if total percentage is approximately 100%
            if abs(total_percentage - 100) > 0.01:
                errors.append(f"Total allocation percentage must equal 100% (current: {total_percentage}%)")
                
        except json.JSONDecodeError:
            errors.append("Partner allocation data is not valid JSON")
        except Exception as e:
            errors.append(f"Error validating partner allocations: {str(e)}")
            
        return errors
    
    def get_partner_allocations(self) -> Dict[str, Any]:
        """
        Get parsed partner allocation data.
        
        Returns:
            Dictionary of partner allocations or empty dict if invalid
        """
        if not self.partner_allocation_json:
            return {}
            
        try:
            return json.loads(self.partner_allocation_json)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_partner_allocations(self, allocations: Dict[str, Any]) -> None:
        """
        Set partner allocation data from dictionary.
        
        Args:
            allocations: Dictionary containing partner allocation data
        """
        self.partner_allocation_json = json.dumps(allocations)
    
    def calculate_total_allocated_volume(self) -> Decimal:
        """
        Calculate total volume allocated to partners.
        
        Returns:
            Total allocated volume in metric tons
        """
        allocations = self.get_partner_allocations()
        total_volume = Decimal('0')
        
        for allocation in allocations.values():
            if isinstance(allocation, dict) and 'volume' in allocation:
                try:
                    volume = Decimal(str(allocation['volume']))
                    total_volume += volume
                except (ValueError, TypeError):
                    continue
                    
        return total_volume
    
    def get_duration_days(self) -> int:
        """
        Calculate scenario duration in days.
        
        Returns:
            Number of days between start and end date
        """
        return (self.end_date - self.start_date).days
    
    def is_active(self) -> bool:
        """
        Check if scenario is currently active.
        
        Returns:
            True if scenario is in active status
        """
        return self.status in {ScenarioStatus.PLAN, ScenarioStatus.FORECAST}
    
    def can_be_modified(self) -> bool:
        """
        Check if scenario can be modified.
        
        Returns:
            True if scenario is in a modifiable state
        """
        return self.status in {ScenarioStatus.DRAFT, ScenarioStatus.PLAN}
    
    def archive(self, user_id: Optional[int] = None) -> None:
        """
        Archive the scenario.
        
        Args:
            user_id: ID of the user performing the action
        """
        self.status = ScenarioStatus.ARCHIVED
        self.update_audit_fields(user_id)