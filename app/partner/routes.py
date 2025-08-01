from flask import render_template, flash, redirect, url_for
from app.extensions import db
from app.partner.forms import PartnerForm
from app.models.partner import Partner
from app.partner import partners_bp

@partners_bp.route("/partners/new", methods=["GET", "POST"])
def create_partner():
    form = PartnerForm()
    form.set_entity_choices()

    if form.validate_on_submit():
        partner = Partner(
            name=form.name.data,
            code=form.code.data,
            description=form.description.data,
            entity_id=form.entity_id.data,
            minimum_volume_three_mt=form.minimum_volume_three_mt.data
        )
        db.session.add(partner)
        db.session.commit()
        flash("Partner created successfully", "success")
        return redirect(url_for("partner.list_partners"))

    return render_template("partner/form.html", form=form)