from flask import render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
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
# SPORTS (MULTI IMAGE + PIN)
# ===================================================

@admin_bp.route("/sports")
def sports():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    items = Sport.query.order_by(Sport.created_at.desc()).all()
    return render_template("admin/sports.html", items=items)


@admin_bp.route("/sports/add", methods=["GET", "POST"])
def add_sport():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    if request.method == "POST":

        images = request.files.getlist("images[]")
        image_paths = []

        if len(images) > 6:
            return "Maximum 6 images allowed"

        upload_folder = os.path.join("static", "uploads", "sports")
        os.makedirs(upload_folder, exist_ok=True)

        for image in images:
            if image and image.filename:
                filename = f"{datetime.now().timestamp()}_{secure_filename(image.filename)}"
                image.save(os.path.join(upload_folder, filename))
                image_paths.append(f"uploads/sports/{filename}")

        sport = Sport(
            title=request.form["title"],
            description=request.form["description"],
            event_date=datetime.strptime(
                request.form["event_date"], "%Y-%m-%d"
            ).date(),
            image=",".join(image_paths),
            pinned=True if request.form.get("pinned") else False,
            created_at=datetime.now()
        )

        db.session.add(sport)
        db.session.commit()

        return redirect(url_for("admin.sports"))

    return render_template("admin/add_sport.html")


@admin_bp.route("/sports/edit/<int:id>", methods=["GET", "POST"])
def edit_sport(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    sport = Sport.query.get_or_404(id)

    if request.method == "POST":

        sport.title = request.form["title"]
        sport.description = request.form["description"]
        sport.event_date = datetime.strptime(
            request.form["event_date"], "%Y-%m-%d"
        ).date()
        sport.pinned = True if request.form.get("pinned") else False

        images = request.files.getlist("images[]")
        image_paths = []

        upload_folder = os.path.join("static", "uploads", "sports")
        os.makedirs(upload_folder, exist_ok=True)

        for image in images:
            if image and image.filename:
                filename = f"{datetime.now().timestamp()}_{secure_filename(image.filename)}"
                image.save(os.path.join(upload_folder, filename))
                image_paths.append(f"uploads/sports/{filename}")

        if image_paths:
            sport.image = ",".join(image_paths)

        db.session.commit()
        return redirect(url_for("admin.sports"))

    return render_template("admin/edit_sport.html", item=sport)


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
# EVENTS (MULTI IMAGE + PIN)
# ===================================================

@admin_bp.route("/events")
def events():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    items = Event.query.order_by(Event.created_at.desc()).all()
    return render_template("admin/events.html", items=items)


@admin_bp.route("/events/add", methods=["GET", "POST"])
def add_event():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    if request.method == "POST":

        images = request.files.getlist("images[]")
        image_paths = []

        if len(images) > 6:
            return "Maximum 6 images allowed"

        upload_folder = os.path.join("static", "uploads", "events")
        os.makedirs(upload_folder, exist_ok=True)

        for image in images:
            if image and image.filename:
                filename = f"{datetime.now().timestamp()}_{secure_filename(image.filename)}"
                image.save(os.path.join(upload_folder, filename))
                image_paths.append(f"uploads/events/{filename}")

        event = Event(
            title=request.form["title"],
            description=request.form["description"],
            event_date=datetime.strptime(
                request.form["event_date"], "%Y-%m-%d"
            ).date(),
            image=",".join(image_paths),
            pinned=True if request.form.get("pinned") else False,
            created_at=datetime.now()
        )

        db.session.add(event)
        db.session.commit()

        return redirect(url_for("admin.events"))

    return render_template("admin/add_event.html")

# ===================================================
# EVENTS (CONTINUED)
# ===================================================

@admin_bp.route("/events/edit/<int:id>", methods=["GET", "POST"])
def edit_event(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    event = Event.query.get_or_404(id)

    if request.method == "POST":

        event.title = request.form["title"]
        event.description = request.form["description"]
        event.event_date = datetime.strptime(
            request.form["event_date"], "%Y-%m-%d"
        ).date()
        event.pinned = True if request.form.get("pinned") else False

        images = request.files.getlist("images[]")
        image_paths = []

        if len(images) > 6:
            return "Maximum 6 images allowed"

        upload_folder = os.path.join("static", "uploads", "events")
        os.makedirs(upload_folder, exist_ok=True)

        for image in images:
            if image and image.filename:
                filename = f"{datetime.now().timestamp()}_{secure_filename(image.filename)}"
                image.save(os.path.join(upload_folder, filename))
                image_paths.append(f"uploads/events/{filename}")

        if image_paths:
            event.image = ",".join(image_paths)

        db.session.commit()
        return redirect(url_for("admin.events"))

    return render_template("admin/edit_event.html", item=event)


@admin_bp.route("/events/delete/<int:id>")
def delete_event(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for("admin.events"))


@admin_bp.route("/events/pin/<int:id>")
def pin_event(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    event = Event.query.get_or_404(id)
    event.pinned = True
    db.session.commit()
    return redirect(url_for("admin.events"))


@admin_bp.route("/events/unpin/<int:id>")
def unpin_event(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    event = Event.query.get_or_404(id)
    event.pinned = False
    db.session.commit()
    return redirect(url_for("admin.events"))


# ===================================================
# CHARITY (MULTI IMAGE + PIN)
# ===================================================

@admin_bp.route("/charity")
def charity():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    items = Charity.query.order_by(Charity.created_at.desc()).all()
    return render_template("admin/charity.html", items=items)


@admin_bp.route("/charity/add", methods=["GET", "POST"])
def add_charity():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    if request.method == "POST":

        images = request.files.getlist("images[]")
        image_paths = []

        if len(images) > 6:
            return "Maximum 6 images allowed"

        upload_folder = os.path.join("static", "uploads", "charity")
        os.makedirs(upload_folder, exist_ok=True)

        for image in images:
            if image and image.filename:
                filename = f"{datetime.now().timestamp()}_{secure_filename(image.filename)}"
                image.save(os.path.join(upload_folder, filename))
                image_paths.append(f"uploads/charity/{filename}")

        charity = Charity(
            title=request.form["title"],
            description=request.form["description"],
            event_date=datetime.strptime(
                request.form["event_date"], "%Y-%m-%d"
            ).date(),
            image=",".join(image_paths),
            pinned=True if request.form.get("pinned") else False,
            created_at=datetime.now()
        )

        db.session.add(charity)
        db.session.commit()

        return redirect(url_for("admin.charity"))

    return render_template("admin/add_charity.html")


@admin_bp.route("/charity/edit/<int:id>", methods=["GET", "POST"])
def edit_charity(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    charity = Charity.query.get_or_404(id)

    if request.method == "POST":

        charity.title = request.form["title"]
        charity.description = request.form["description"]
        charity.event_date = datetime.strptime(
            request.form["event_date"], "%Y-%m-%d"
        ).date()
        charity.pinned = True if request.form.get("pinned") else False

        images = request.files.getlist("images[]")
        image_paths = []

        if len(images) > 6:
            return "Maximum 6 images allowed"

        upload_folder = os.path.join("static", "uploads", "charity")
        os.makedirs(upload_folder, exist_ok=True)

        for image in images:
            if image and image.filename:
                filename = f"{datetime.now().timestamp()}_{secure_filename(image.filename)}"
                image.save(os.path.join(upload_folder, filename))
                image_paths.append(f"uploads/charity/{filename}")

        if image_paths:
            charity.image = ",".join(image_paths)

        db.session.commit()
        return redirect(url_for("admin.charity"))

    return render_template("admin/edit_charity.html", item=charity)


@admin_bp.route("/charity/delete/<int:id>")
def delete_charity(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    charity = Charity.query.get_or_404(id)
    db.session.delete(charity)
    db.session.commit()
    return redirect(url_for("admin.charity"))


@admin_bp.route("/charity/pin/<int:id>")
def pin_charity(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    charity = Charity.query.get_or_404(id)
    charity.pinned = True
    db.session.commit()
    return redirect(url_for("admin.charity"))


@admin_bp.route("/charity/unpin/<int:id>")
def unpin_charity(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    charity = Charity.query.get_or_404(id)
    charity.pinned = False
    db.session.commit()
    return redirect(url_for("admin.charity"))


# ===================================================
# AWARDS (MULTI IMAGE + PIN)
# ===================================================

@admin_bp.route("/awards")
def awards():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    items = Award.query.order_by(Award.created_at.desc()).all()
    return render_template("admin/awards.html", awards=items)


@admin_bp.route("/awards/add", methods=["GET", "POST"])
def add_award():
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    if request.method == "POST":

        images = request.files.getlist("images[]")
        image_paths = []

        if len(images) > 6:
            return "Maximum 6 images allowed"

        upload_folder = os.path.join("static", "uploads", "awards")
        os.makedirs(upload_folder, exist_ok=True)

        for image in images:
            if image and image.filename:
                filename = f"{datetime.now().timestamp()}_{secure_filename(image.filename)}"
                image.save(os.path.join(upload_folder, filename))
                image_paths.append(f"uploads/awards/{filename}")

        award = Award(
            title=request.form["title"],
            year=request.form["year"],
            description=request.form["description"],
            image=",".join(image_paths),
            pinned=True if request.form.get("pinned") else False,
            created_at=datetime.now()
        )

        db.session.add(award)
        db.session.commit()

        return redirect(url_for("admin.awards"))

    return render_template("admin/add_award.html")


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
        image_paths = []

        if len(images) > 6:
            return "Maximum 6 images allowed"

        upload_folder = os.path.join("static", "uploads", "awards")
        os.makedirs(upload_folder, exist_ok=True)

        for image in images:
            if image and image.filename:
                filename = f"{datetime.now().timestamp()}_{secure_filename(image.filename)}"
                image.save(os.path.join(upload_folder, filename))
                image_paths.append(f"uploads/awards/{filename}")

        if image_paths:
            award.image = ",".join(image_paths)

        db.session.commit()
        return redirect(url_for("admin.awards"))

    return render_template("admin/edit_award.html", item=award)


@admin_bp.route("/awards/delete/<int:id>")
def delete_award(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    award = Award.query.get_or_404(id)
    db.session.delete(award)
    db.session.commit()
    return redirect(url_for("admin.awards"))


@admin_bp.route("/awards/pin/<int:id>")
def pin_award(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    award = Award.query.get_or_404(id)
    award.pinned = True
    db.session.commit()
    return redirect(url_for("admin.awards"))


@admin_bp.route("/awards/unpin/<int:id>")
def unpin_award(id):
    if not admin_logged_in():
        return redirect(url_for("admin.login"))

    award = Award.query.get_or_404(id)
    award.pinned = False
    db.session.commit()
    return redirect(url_for("admin.awards"))