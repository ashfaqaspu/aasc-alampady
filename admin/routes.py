from flask import render_template, request, redirect, session, url_for, flash
from werkzeug.security import check_password_hash
from datetime import datetime
import cloudinary
import cloudinary.uploader
import os

from extensions import db
from model import Event, Sport, Charity, Award, ADMIN
from . import admin_bp


# ===================================================
# ADMIN SESSION CHECK
# ===================================================

def admin_logged_in():
    return session.get("admin_id")


# ===================================================
# ADMIN LOGIN
# ===================================================

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        admin = ADMIN.query.filter_by(
            username=request.form["username"]
        ).first()

        if admin and check_password_hash(
            admin.password,
            request.form["password"]
        ):
            session["admin_id"] = admin.id
            return redirect(url_for("admin.dashboard"))
        else:
            error = "Invalid credentials"

    return render_template("admin/login.html", error=error)


@admin_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


# ===================================================
# DASHBOARD
# ===================================================

@admin_bp.route("/dashboard")
def dashboard():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    return render_template(
        "admin/dashboard.html",
        event_count=Event.query.count(),
        sports_count=Sport.query.count(),
        charity_count=Charity.query.count(),
        award_count=Award.query.count()
    )

# ===================================================
# SPORTS
# ===================================================

@admin_bp.route("/sports")
def sports():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    items = Sport.query.order_by(Sport.created_at.desc()).all()
    return render_template("admin/sports.html", items=items)


@admin_bp.route("/sports/add", methods=["GET", "POST"])
def add_sports():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    if request.method == "POST":

        images = request.files.getlist("images[]")
        image_urls = []

        if len(images) > 6:
            return "Maximum 6 images allowed"

        for image in images:
            if image and image.filename:
                result = cloudinary.uploader.upload(
                    image,
                    folder="aasc/sports",
                    transformation=[{"quality": "auto", "fetch_format": "auto"}]
                )
                image_urls.append(result["secure_url"])

        sport = Sport(
            title=request.form["title"],
            description=request.form["description"],
            date=request.form["date"],
            image=",".join(image_urls),
            pinned=True if request.form.get("pinned") else False,
            created_at=datetime.now()
        )

        db.session.add(sport)
        db.session.commit()

        flash("Sport added successfully", "success")
        return redirect(url_for("admin.sports"))

    return render_template("admin/add_sports.html")


@admin_bp.route("/sports/edit/<int:id>", methods=["GET", "POST"])
def edit_sports(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    sport = Sport.query.get_or_404(id)

    if request.method == "POST":

        sport.title = request.form["title"]
        sport.description = request.form["description"]
        sport.date = request.form["date"]
        sport.pinned = True if request.form.get("pinned") else False

        images = request.files.getlist("images[]")
        image_urls = []

        if len(images) > 6:
            return "Maximum 6 images allowed"

        for image in images:
            if image and image.filename:
                result = cloudinary.uploader.upload(
                    image,
                    folder="aasc/sports"
                )
                image_urls.append(result["secure_url"])

        if image_urls:
            sport.image = ",".join(image_urls)

        db.session.commit()
        return redirect(url_for("admin.sports"))

    return render_template("admin/edit_sports.html", item=sport)


@admin_bp.route("/sports/delete/<int:id>")
def delete_sport(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    sport = Sport.query.get_or_404(id)
    db.session.delete(sport)
    db.session.commit()
    return redirect(url_for("admin.sports"))


@admin_bp.route("/sports/pin/<int:id>")
def pin_sport(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    sport = Sport.query.get_or_404(id)
    sport.pinned = True
    db.session.commit()
    return redirect(url_for("admin.sports"))


@admin_bp.route("/sports/unpin/<int:id>")
def unpin_sport(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    sport = Sport.query.get_or_404(id)
    sport.pinned = False
    db.session.commit()
    return redirect(url_for("admin.sports"))

# ===================================================
# EVENTS (MULTI IMAGE + PIN - CLOUDINARY VERSION)
# ===================================================

@admin_bp.route("/events")
def events():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    items = Event.query.order_by(Event.created_at.desc()).all()
    return render_template("admin/events.html", items=items)


# ===================================================
# ADD EVENT
# ===================================================

@admin_bp.route("/events/add", methods=["GET", "POST"])
def add_event():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    if request.method == "POST":

        images = request.files.getlist("images[]")
        image_urls = []

        # Limit to 6 images
        if len(images) > 6:
            flash("Maximum 6 images allowed", "danger")
            return redirect(request.url)

        for image in images:
            if image and image.filename:
                result = cloudinary.uploader.upload(
                    image,
                    folder="aasc/events",
                    transformation=[
                        {"quality": "auto", "fetch_format": "auto"}
                    ]
                )
                image_urls.append(result["secure_url"])

        event = Event(
            title=request.form["title"],
            description=request.form["description"],
            event_date=datetime.strptime(
                request.form["event_date"], "%Y-%m-%d"
            ).date(),
            image=",".join(image_urls),  # Store comma separated
            pinned=True if request.form.get("pinned") else False,
            created_at=datetime.now()
        )

        db.session.add(event)
        db.session.commit()

        flash("Event added successfully!", "success")
        return redirect(url_for("admin.events"))

    return render_template("admin/add_event.html")


# ===================================================
# EDIT EVENT
# ===================================================

@admin_bp.route("/events/edit/<int:id>", methods=["GET", "POST"])
def edit_event(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    event = Event.query.get_or_404(id)

    if request.method == "POST":

        # Update basic details
        event.title = request.form["title"]
        event.description = request.form["description"]
        event.event_date = datetime.strptime(
            request.form["event_date"], "%Y-%m-%d"
        ).date()
        event.pinned = True if request.form.get("pinned") else False

        images = request.files.getlist("images[]")
        image_urls = []

        if len(images) > 6:
            flash("Maximum 6 images allowed", "danger")
            return redirect(request.url)

        for image in images:
            if image and image.filename:
                result = cloudinary.uploader.upload(
                    image,
                    folder="aasc/events",
                    transformation=[
                        {"quality": "auto", "fetch_format": "auto"}
                    ]
                )
                image_urls.append(result["secure_url"])

        # Replace images only if new ones uploaded
        if image_urls:
            event.image = ",".join(image_urls)

        db.session.commit()

        flash("Event updated successfully!", "success")
        return redirect(url_for("admin.events"))

    return render_template("admin/edit_event.html", item=event)


# ===================================================
# DELETE EVENT
# ===================================================

@admin_bp.route("/events/delete/<int:id>")
def delete_event(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()

    flash("Event deleted successfully!", "success")
    return redirect(url_for("admin.events"))


# ===================================================
# PIN EVENT
# ===================================================

@admin_bp.route("/events/pin/<int:id>")
def pin_event(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    event = Event.query.get_or_404(id)
    event.pinned = True
    db.session.commit()

    flash("Event pinned!", "success")
    return redirect(url_for("admin.events"))


# ===================================================
# UNPIN EVENT
# ===================================================

@admin_bp.route("/events/unpin/<int:id>")
def unpin_event(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    event = Event.query.get_or_404(id)
    event.pinned = False
    db.session.commit()

    flash("Event unpinned!", "success")
    return redirect(url_for("admin.events"))

# ===================================================
# CHARITY (MULTI IMAGE + PIN - CLOUDINARY VERSION)
# ===================================================

@admin_bp.route("/charity")
def charity():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    items = Charity.query.order_by(Charity.created_at.desc()).all()
    return render_template("admin/charity.html", items=items)


# ===================================================
# ADD CHARITY
# ===================================================

@admin_bp.route("/charity/add", methods=["GET", "POST"])
def add_charity():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    if request.method == "POST":

        images = request.files.getlist("images[]")
        image_urls = []

        # Limit to 6 images
        if len(images) > 6:
            flash("Maximum 6 images allowed", "danger")
            return redirect(request.url)

        for image in images:
            if image and image.filename:
                result = cloudinary.uploader.upload(
                    image,
                    folder="aasc/charity",
                    transformation=[
                        {"quality": "auto", "fetch_format": "auto"}
                    ]
                )
                image_urls.append(result["secure_url"])

        charity = Charity(
            title=request.form["title"],
            description=request.form["description"],
            event_date=datetime.strptime(
                request.form["event_date"], "%Y-%m-%d"
            ).date(),
            image=",".join(image_urls),
            pinned=True if request.form.get("pinned") else False,
            created_at=datetime.now()
        )

        db.session.add(charity)
        db.session.commit()

        flash("Charity event added successfully!", "success")
        return redirect(url_for("admin.charity"))

    return render_template("admin/add_charity.html")


# ===================================================
# EDIT CHARITY
# ===================================================

@admin_bp.route("/charity/edit/<int:id>", methods=["GET", "POST"])
def edit_charity(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    charity = Charity.query.get_or_404(id)

    if request.method == "POST":

        # Update basic fields
        charity.title = request.form["title"]
        charity.description = request.form["description"]
        charity.event_date = datetime.strptime(
            request.form["event_date"], "%Y-%m-%d"
        ).date()
        charity.pinned = True if request.form.get("pinned") else False

        images = request.files.getlist("images[]")
        image_urls = []

        if len(images) > 6:
            flash("Maximum 6 images allowed", "danger")
            return redirect(request.url)

        for image in images:
            if image and image.filename:
                result = cloudinary.uploader.upload(
                    image,
                    folder="aasc/charity",
                    transformation=[
                        {"quality": "auto", "fetch_format": "auto"}
                    ]
                )
                image_urls.append(result["secure_url"])

        # Replace images only if new images uploaded
        if image_urls:
            charity.image = ",".join(image_urls)

        db.session.commit()

        flash("Charity event updated successfully!", "success")
        return redirect(url_for("admin.charity"))

    return render_template("admin/edit_charity.html", item=charity)


# ===================================================
# DELETE CHARITY
# ===================================================

@admin_bp.route("/charity/delete/<int:id>")
def delete_charity(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    charity = Charity.query.get_or_404(id)
    db.session.delete(charity)
    db.session.commit()

    flash("Charity event deleted successfully!", "success")
    return redirect(url_for("admin.charity"))


# ===================================================
# PIN CHARITY
# ===================================================

@admin_bp.route("/charity/pin/<int:id>")
def pin_charity(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    charity = Charity.query.get_or_404(id)
    charity.pinned = True
    db.session.commit()

    flash("Charity pinned!", "success")
    return redirect(url_for("admin.charity"))


# ===================================================
# UNPIN CHARITY
# ===================================================

@admin_bp.route("/charity/unpin/<int:id>")
def unpin_charity(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    charity = Charity.query.get_or_404(id)
    charity.pinned = False
    db.session.commit()

    flash("Charity unpinned!", "success")
    return redirect(url_for("admin.charity"))

# ===================================================
# AWARDS (MULTI IMAGE + PIN - CLOUDINARY VERSION)
# ===================================================

@admin_bp.route("/awards")
def awards():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    items = Award.query.order_by(Award.created_at.desc()).all()
    return render_template("admin/awards.html", awards=items)


# ===================================================
# ADD AWARD
# ===================================================

@admin_bp.route("/awards/add", methods=["GET", "POST"])
def add_award():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    if request.method == "POST":

        images = request.files.getlist("images[]")
        image_urls = []

        # Limit to 6 images
        if len(images) > 6:
            flash("Maximum 6 images allowed", "danger")
            return redirect(request.url)

        for image in images:
            if image and image.filename:
                result = cloudinary.uploader.upload(
                    image,
                    folder="aasc/awards",
                    transformation=[
                        {"quality": "auto", "fetch_format": "auto"}
                    ]
                )
                image_urls.append(result["secure_url"])

        award = Award(
            title=request.form["title"],
            year=request.form["year"],
            description=request.form["description"],
            image=",".join(image_urls),
            pinned=True if request.form.get("pinned") else False,
            created_at=datetime.now()
        )

        db.session.add(award)
        db.session.commit()

        flash("Award added successfully!", "success")
        return redirect(url_for("admin.awards"))

    return render_template("admin/add_award.html")


# ===================================================
# EDIT AWARD
# ===================================================

@admin_bp.route("/awards/edit/<int:id>", methods=["GET", "POST"])
def edit_award(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    award = Award.query.get_or_404(id)

    if request.method == "POST":

        award.title = request.form["title"]
        award.year = request.form["year"]
        award.description = request.form["description"]
        award.pinned = True if request.form.get("pinned") else False

        images = request.files.getlist("images[]")
        image_urls = []

        if len(images) > 6:
            flash("Maximum 6 images allowed", "danger")
            return redirect(request.url)

        for image in images:
            if image and image.filename:
                result = cloudinary.uploader.upload(
                    image,
                    folder="aasc/awards",
                    transformation=[
                        {"quality": "auto", "fetch_format": "auto"}
                    ]
                )
                image_urls.append(result["secure_url"])

        # Replace only if new images uploaded
        if image_urls:
            award.image = ",".join(image_urls)

        db.session.commit()

        flash("Award updated successfully!", "success")
        return redirect(url_for("admin.awards"))

    return render_template("admin/edit_award.html", item=award)


# ===================================================
# DELETE AWARD
# ===================================================

@admin_bp.route("/awards/delete/<int:id>")
def delete_award(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    award = Award.query.get_or_404(id)
    db.session.delete(award)
    db.session.commit()

    flash("Award deleted successfully!", "success")
    return redirect(url_for("admin.awards"))


# ===================================================
# PIN AWARD
# ===================================================

@admin_bp.route("/awards/pin/<int:id>")
def pin_award(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    award = Award.query.get_or_404(id)
    award.pinned = True
    db.session.commit()

    flash("Award pinned!", "success")
    return redirect(url_for("admin.awards"))


# ===================================================
# UNPIN AWARD
# ===================================================

@admin_bp.route("/awards/unpin/<int:id>")
def unpin_award(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    award = Award.query.get_or_404(id)
    award.pinned = False
    db.session.commit()

    flash("Award unpinned!", "success")
    return redirect(url_for("admin.awards"))

