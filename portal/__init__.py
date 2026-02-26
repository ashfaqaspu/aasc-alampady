from flask import Blueprint

portal_bp = Blueprint(
    "portal",
    __name__,
    url_prefix="/portal",
    template_folder="templates"
)
from . import routes
