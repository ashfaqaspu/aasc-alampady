from flask import Flask
from extensions import db

from website.routes import website_bp
from portal.routes import portal_bp
from admin.routes import admin_bp

app = Flask(__name__)

app.config["SECRET_KEY"] = "aasc_secret_key"

# Use SQLite for now (simplest)
app.config["SQLALCHEMY_DATABASE_URI"] = \
    "postgresql://postgres:Secretkey20@localhost/aasc_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

app.register_blueprint(website_bp)
app.register_blueprint(portal_bp)
app.register_blueprint(admin_bp)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()   # 🔥 creates tables automatically
    app.run()