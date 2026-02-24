from flask import Flask
from extensions import db
import os

from website.routes import website_bp
from portal.routes import portal_bp
from admin.routes import admin_bp


def create_app():
    app = Flask(__name__)

    # Secret key (better to move to environment later)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "aasc_secret_key")

    # Get database URL from Render environment
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable not set")

    # Fix for Render postgres:// issue
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(website_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(admin_bp)

    return app


app = create_app()