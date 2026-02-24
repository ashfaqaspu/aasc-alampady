from flask import Blueprint, render_template
from database import get_db
website_bp = Blueprint(
    "website",
    __name__,
    template_folder="templates"
)

@website_bp.route("/")
def home():
    return render_template("home.html")

# ======================================================
# PUBLIC EVENTS
# ======================================================
@website_bp.route("/events")
def public_events():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT * FROM events
        ORDER BY pinned DESC, event_date DESC, created_at DESC
    """)
    events = cur.fetchall()
    cur.close()
    db.close()
    return render_template("events.html", events=events)


# ======================================================
# PUBLIC SPORTS
# ======================================================
@website_bp.route("/sports")
def public_sports():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT * FROM sports
        ORDER BY pinned DESC, event_date DESC, created_at DESC
    """)
    sports = cur.fetchall()
    cur.close()
    db.close()
    return render_template("sports.html", items=sports)


# ======================================================
# PUBLIC CHARITY
# ======================================================
@website_bp.route("/charity")
def public_charity():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT * FROM charity
        ORDER BY pinned DESC, event_date DESC, created_at DESC
    """)
    charity = cur.fetchall()
    cur.close()
    db.close()
    return render_template("charity.html", items=charity)


# ======================================================
# PUBLIC AWARDS
# ======================================================
@website_bp.route("/awards")
def public_awards():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT * FROM awards
        ORDER BY pinned DESC, year DESC, created_at DESC
    """)
    awards = cur.fetchall()
    cur.close()
    db.close()
    return render_template("awards.html", awards=awards)


# ======================================================
# STATIC PAGES (No DB change needed)
# ======================================================
@website_bp.route("/committee")
def committee():
    return render_template("committee.html")


@website_bp.route("/contact")
def contact():
    return render_template("contact.html")


@website_bp.route("/building")
def building():
    return render_template("building.html")

@website_bp.route("/admin", methods=["GET", "POST"])
def admin_login():
    error = None

    if request.method == "POST":
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "SELECT * FROM admin WHERE username=%s",
            (request.form["username"],)
        )
        admin = cur.fetchone()
        cur.close()
        db.close()

        if admin and check_password_hash(admin["password"], request.form["password"]):
            session["admin_logged_in"] = True
            return redirect("/admin/dashboard")
        else:
            error = "Invalid credentials"

    return render_template("admin/login.html", error=error)


@website_bp.route("/admin/dashboard")
def admin_dashboard():
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM events")
    event_count = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) FROM sports")
    sports_count = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) FROM charity")
    charity_count = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) FROM awards")
    award_count = cur.fetchone()["count"]

    cur.close()
    db.close()

    return render_template(
        "admin/dashboard.html",
        event_count=event_count,
        sports_count=sports_count,
        charity_count=charity_count,
        award_count=award_count
    )

@website_bp.route("/admin/events")
def admin_events():
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM events ORDER BY created_at DESC")
    events = cur.fetchall()
    cur.close()
    db.close()

    return render_template("admin/events.html", events=events)

@website_bp.route("/admin/events/add", methods=["GET", "POST"])
def admin_add_event():
    if not admin_logged_in():
        return redirect("/admin")

    if request.method == "POST":
        images = request.files.getlist("images[]")
        paths = []

        pinned = 1 if request.form.get("pinned") else 0

        os.makedirs("static/uploads/events", exist_ok=True)

        for img in images:
            if img and img.filename:
                filename = f"{datetime.now().timestamp()}_{img.filename}"
                path = f"static/uploads/events/{filename}"
                img.save(path)
                paths.append(path)

        db = get_db()
        cur = db.cursor()

        cur.execute("""
            INSERT INTO events
            (title, event_date, description, image, pinned, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            request.form["title"],
            request.form["event_date"],
            request.form["description"],
            ",".join(paths),
            pinned,
            datetime.now().isoformat()
        ))

        db.commit()
        cur.close()
        db.close()

        return redirect("/admin/events")

    return render_template("admin/add_event.html")

@website_bp.route("/admin/events/pin/<int:id>")
def pin_event(id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE events SET pinned=1 WHERE id=%s", (id,))
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/events")

@website_bp.route("/admin/events/unpin/<int:id>")
def unpin_event(id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE events SET pinned=0 WHERE id=%s", (id,))
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/events")

@website_bp.route("/admin/events/delete/<int:id>")
def admin_delete_event(id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM events WHERE id=%s", (id,))
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/events")

@website_bp.route("/admin/events/edit/<int:id>", methods=["GET", "POST"])
def admin_edit_event(id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()

    # Fetch event
    cur.execute("SELECT * FROM events WHERE id=%s", (id,))
    event = cur.fetchone()

    if not event:
        cur.close()
        db.close()
        return redirect("/admin/events")

    if request.method == "POST":
        title = request.form["title"]
        event_date = request.form["event_date"]
        description = request.form["description"]

        existing_images = event["image"] or ""
        image_paths = existing_images.split(",") if existing_images else []

        new_images = request.files.getlist("images[]")
        os.makedirs("static/uploads/events", exist_ok=True)

        for image in new_images:
            if image and image.filename:
                filename = f"{datetime.now().timestamp()}_{image.filename}"
                path = f"static/uploads/events/{filename}"
                image.save(path)
                image_paths.append(path)

        cur.execute("""
            UPDATE events
            SET title=%s,
                event_date=%s,
                description=%s,
                image=%s
            WHERE id=%s
        """, (
            title,
            event_date,
            description,
            ",".join(image_paths),
            id
        ))

        db.commit()
        cur.close()
        db.close()

        return redirect("/admin/events")

    cur.close()
    db.close()
    return render_template("admin/edit_event.html", event=event)

@website_bp.route("/admin/sports")
def admin_sports():
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM sports ORDER BY created_at DESC")
    items = cur.fetchall()
    cur.close()
    db.close()

    return render_template("admin/sports.html", items=items)

@website_bp.route("/admin/sports/add", methods=["GET", "POST"])
def admin_add_sport():
    if not admin_logged_in():
        return redirect("/admin")

    if request.method == "POST":
        images = request.files.getlist("images[]")
        paths = []
        pinned = 1 if request.form.get("pinned") else 0

        os.makedirs("static/uploads/sports", exist_ok=True)

        for img in images[:6]:
            if img and img.filename:
                filename = f"{datetime.now().timestamp()}_{img.filename}"
                path = f"static/uploads/sports/{filename}"
                img.save(path)
                paths.append(path)

        db = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO sports
            (title, event_date, description, image, pinned, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            request.form["title"],
            request.form["event_date"],
            request.form["description"],
            ",".join(paths),
            pinned,
            datetime.now().isoformat()
        ))

        db.commit()
        cur.close()
        db.close()

        return redirect("/admin/sports")

    return render_template("admin/add_sport.html")

@website_bp.route("/admin/sports/edit/<int:id>", methods=["GET", "POST"])
def admin_edit_sport(id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM sports WHERE id=%s", (id,))
    item = cur.fetchone()

    if not item:
        cur.close()
        db.close()
        return redirect("/admin/sports")

    if request.method == "POST":
        title = request.form["title"]
        event_date = request.form["event_date"]
        description = request.form["description"]
        pinned = 1 if request.form.get("pinned") else 0

        existing_images = item["image"] or ""
        image_paths = existing_images.split(",") if existing_images else []

        new_images = request.files.getlist("images[]")
        os.makedirs("static/uploads/sports", exist_ok=True)

        for img in new_images[:6]:
            if img and img.filename:
                filename = f"{datetime.now().timestamp()}_{img.filename}"
                path = f"static/uploads/sports/{filename}"
                img.save(path)
                image_paths.append(path)

        cur.execute("""
            UPDATE sports
            SET title=%s,
                event_date=%s,
                description=%s,
                image=%s,
                pinned=%s
            WHERE id=%s
        """, (
            title,
            event_date,
            description,
            ",".join(image_paths),
            pinned,
            id
        ))

        db.commit()
        cur.close()
        db.close()

        return redirect("/admin/sports")

    cur.close()
    db.close()
    return render_template("admin/edit_sport.html", item=item)

@website_bp.route("/admin/sports/pin/<int:id>")
def pin_sport(id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE sports SET pinned=1 WHERE id=%s", (id,))
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/sports")

@website_bp.route("/admin/sports/unpin/<int:id>")
def unpin_sport(id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE sports SET pinned=0 WHERE id=%s", (id,))
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/sports")

@website_bp.route("/admin/sports/delete/<int:id>")
def admin_delete_sport(id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM sports WHERE id=%s", (id,))
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/sports")



@website_bp.route("/admin/charity")
def admin_charity():
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM charity ORDER BY created_at DESC")
    items = cur.fetchall()
    cur.close()
    db.close()

    return render_template("admin/charity.html", items=items)


@website_bp.route("/admin/charity/add", methods=["GET", "POST"])
def admin_add_charity():
    if not admin_logged_in():
        return redirect("/admin")

    if request.method == "POST":
        images = request.files.getlist("images[]")
        paths = []
        pinned = 1 if request.form.get("pinned") else 0

        os.makedirs("static/uploads/charity", exist_ok=True)

        for img in images[:6]:
            if img and img.filename:
                filename = f"{datetime.now().timestamp()}_{img.filename}"
                path = f"static/uploads/charity/{filename}"
                img.save(path)
                paths.append(path)

        db = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO charity
            (title, event_date, description, image, pinned, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            request.form["title"],
            request.form["event_date"],
            request.form["description"],
            ",".join(paths),
            pinned,
            datetime.now().isoformat()
        ))

        db.commit()
        cur.close()
        db.close()

        return redirect("/admin/charity")

    return render_template("admin/add_charity.html")

@website_bp.route("/admin/charity/edit/<int:id>", methods=["GET", "POST"])
def admin_edit_charity(id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM charity WHERE id=%s", (id,))
    item = cur.fetchone()

    if not item:
        cur.close()
        db.close()
        return redirect("/admin/charity")

    if request.method == "POST":
        title = request.form["title"]
        event_date = request.form["event_date"]
        description = request.form["description"]
        pinned = 1 if request.form.get("pinned") else 0

        existing_images = item["image"] or ""
        image_paths = existing_images.split(",") if existing_images else []

        new_images = request.files.getlist("images[]")
        os.makedirs("static/uploads/charity", exist_ok=True)

        for img in new_images:
            if img and img.filename:
                filename = f"{datetime.now().timestamp()}_{img.filename}"
                path = f"static/uploads/charity/{filename}"
                img.save(path)
                image_paths.append(path)

        cur.execute("""
            UPDATE charity
            SET title=%s,
                event_date=%s,
                description=%s,
                image=%s,
                pinned=%s
            WHERE id=%s
        """, (
            title,
            event_date,
            description,
            ",".join(image_paths),
            pinned,
            id
        ))

        db.commit()
        cur.close()
        db.close()

        return redirect("/admin/charity")

    cur.close()
    db.close()
    return render_template("admin/edit_charity.html", item=item)

@website_bp.route("/admin/awards")
def admin_awards():
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM awards ORDER BY created_at DESC")
    awards = cur.fetchall()
    cur.close()
    db.close()

    return render_template("admin/awards.html", awards=awards)

@website_bp.route("/admin/awards/add", methods=["GET", "POST"])
def admin_add_award():
    if not admin_logged_in():
        return redirect("/admin")

    if request.method == "POST":
        image = request.files.get("image")
        pinned = 1 if request.form.get("pinned") else 0
        path = None

        if image and image.filename:
            os.makedirs("static/uploads/awards", exist_ok=True)
            filename = f"{datetime.now().timestamp()}_{image.filename}"
            path = f"static/uploads/awards/{filename}"
            image.save(path)

        db = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO awards
            (title, year, description, image, pinned, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            request.form["title"],
            request.form["year"],
            request.form["description"],
            path,
            pinned,
            datetime.now().isoformat()
        ))

        db.commit()
        cur.close()
        db.close()

        return redirect("/admin/awards")

    return render_template("admin/add_award.html")

@website_bp.route("/admin/awards/pin/<int:id>")
def pin_award(id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE awards SET pinned=1 WHERE id=%s", (id,))
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/awards")

@website_bp.route("/admin/awards/unpin/<int:id>")
def unpin_award(id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE awards SET pinned=0 WHERE id=%s", (id,))
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/awards")


@website_bp.route("/admin/awards/delete/<int:id>")
def admin_delete_award(id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM awards WHERE id=%s", (id,))
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/awards")

@website_bp.route("/admin/awards/edit/<int:id>", methods=["GET", "POST"])
def admin_edit_award(id):
    if not admin_logged_in():
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM awards WHERE id=%s", (id,))
    award = cur.fetchone()

    if not award:
        cur.close()
        db.close()
        return redirect("/admin/awards")

    if request.method == "POST":
        title = request.form["title"]
        year = request.form["year"]
        description = request.form["description"]
        pinned = 1 if request.form.get("pinned") else 0

        image = request.files.get("image")
        image_path = award["image"]

        if image and image.filename:
            os.makedirs("static/uploads/awards", exist_ok=True)
            filename = f"{datetime.now().timestamp()}_{image.filename}"
            image_path = f"static/uploads/awards/{filename}"
            image.save(image_path)

        cur.execute("""
            UPDATE awards
            SET title=%s,
                year=%s,
                description=%s,
                image=%s,
                pinned=%s
            WHERE id=%s
        """, (
            title,
            year,
            description,
            image_path,
            pinned,
            id
        ))

        db.commit()
        cur.close()
        db.close()

        return redirect("/admin/awards")

    cur.close()
    db.close()
    return render_template("admin/edit_award.html", award=award)
