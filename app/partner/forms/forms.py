from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from app.models.partner import EntityTypeEnum, PartnerEntity

class PartnerForm(FlaskForm):
    """Form to register new Partner"""
    
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    code = StringField("As Known", validators=[DataRequired(), Length(max=20)])
    description = TextAreaField("Description", validators=[Optional()])
    
    entity_id = SelectField("Entity", coerce=int, validators=[DataRequired()])
    minimum_volume_three_mt = IntegerField("Minimum Tonnage", validators=[Optional()])
    
    submit = SubmitField("Save")
    
    def set_entity_choices(self):
        "Populates the entity dropdown from the database"
        self.entity_id.choices = [
            (entity.id, f"{entity.name} ({entity.entity_type.value})")
            for entity in PartnerEntity.query.order_by(PartnerEntity.name).all()
        ]
        
class PartnerEntityForm(FlaskForm):
    """Form to register PartnerEntity"""
    
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    code = StringField("Code", validators=[DataRequired(), Length(max=20)])
    description = TextAreaField("Description", validators=[Optional()])

    entity_type = SelectField("Entity Type", choices=[
        (et.value, et.name.capitalize()) for et in EntityTypeEnum
    ], validators=[DataRequired()])

    submit = SubmitField("Save")