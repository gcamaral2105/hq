from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional

class CategoryForm(FlaskForm):
    name = StringField('Category', validators=[DataRequired()])
    submit = SubmitField('Save')

class MineForm(FlaskForm):
    name = StringField('Mine', validators=[DataRequired()])
    submit = SubmitField('Save')

class SubtypeForm(FlaskForm):
    name = StringField('Sub-type', validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    mine_id = SelectField('Mine (Optional)', coerce=int, validators=[Optional()])
    submit = SubmitField('Save')