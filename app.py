from flask import Flask
from extensions import db
import os

# Cloudinary
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Blueprints
from website import website_bp
from portal import portal_bp
from admin import admin_bp


def create_app():
    app = Flask(__name__)

    # ===============================
    # SECRET KEY
    # ===============================
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "aasc_secret_key")

    # ===============================
    # DATABASE CONFIG (Render)
    # ===============================
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable not set")

    # Fix old postgres:// issue
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # ===============================
    # CLOUDINARY CONFIG
    # ===============================
    cloudinary.config(
        cloud_name=os.environ.get("dhssjkykf"),
        api_key=os.environ.get("516981333178533"),
        api_secret=os.environ.get("**********"),
        secure=True
    )

    # ===============================
    # REGISTER BLUEPRINTS
    # ===============================
    app.register_blueprint(website_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(admin_bp)

    return app


# For Gunicorn / Render
app = create_app()