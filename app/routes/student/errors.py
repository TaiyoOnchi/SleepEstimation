from flask import Blueprint, render_template

error_bp = Blueprint('errors', __name__)

@error_bp.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@error_bp.errorhandler(500)
def internal_error(e):
    return render_template('errors/500.html'), 500
