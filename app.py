from flask import Flask
from extensions import db
import os

# ✅ Import from package (since __init__.py exports blueprint)
from website import website_bp
from portal import portal_bp
from admin import admin_bp


def create_app():
    app = Flask(__name__)

    # Secret key (should be environment variable in production)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "aasc_secret_key")

    # Get database URL from Render
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable not set")

    # Fix Render old postgres:// format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize database
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(website_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(admin_bp)

    return app


# For Gunicorn / Render
app = create_app()