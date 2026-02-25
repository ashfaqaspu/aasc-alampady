from flask import Blueprint, render_template
from model import Event, Sport, Charity, Award

website_bp = Blueprint(
    "website",
    __name__,
    template_folder="templates"
)

@website_bp.route("/")
def home():
    return render_template("home.html")

@website_bp.route("/events")
def public_events():
    events = Event.query.order_by(
        Event.pinned.desc(),
        Event.event_date.desc(),
        Event.created_at.desc()
    ).all()
    return render_template("events.html", events=events)

@website_bp.route("/sports")
def public_sports():
    sports = Sport.query.order_by(
        Sport.pinned.desc(),
        Sport.event_date.desc(),
        Sport.created_at.desc()
    ).all()
    return render_template("sports.html", items=sports)

@website_bp.route("/charity")
def public_charity():
    charity = Charity.query.order_by(
        Charity.pinned.desc(),
        Charity.event_date.desc(),
        Charity.created_at.desc()
    ).all()
    return render_template("charity.html", items=charity)

@website_bp.route("/awards")
def public_awards():
    awards = Award.query.order_by(
        Award.pinned.desc(),
        Award.year.desc(),
        Award.created_at.desc()
    ).all()
    return render_template("awards.html", awards=awards)

@website_bp.route("/building")
def building():
    return render_template("building.html")


@website_bp.route("/committee")
def committee():
    return render_template("committee.html")

@website_bp.route("/contact")
def contact():
    return render_template("contact.html")

