import os
from flask import Flask, redirect, url_for, session, render_template, abort
from flask_compress import Compress
from config import Config
from app.firebase.firebase_admin import FirebaseLoader
from app.firebase.firestore_service import FirestoreService
from whitenoise import WhiteNoise
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps


def admin_required(f):
    """Decorator to restrict routes to admin users only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth_bp.login'))
        if session.get('user_role') != 'ADMIN':
            abort(404)  # Show 404 instead of 403 to hide the existence of the page
        return f(*args, **kwargs)
    return decorated_function


def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config_class)

    # Enable response compression (gzip)
    Compress(app)

    # Middleware setup
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    app.wsgi_app = WhiteNoise(app.wsgi_app, root='app/static/', prefix='static/', max_age=604800)

    # Initialize Firebase
    FirebaseLoader.get_instance(app.config['FIREBASE_SERVICE_ACCOUNT'])

    @app.route('/')
    def index():
        if not session.get('logged_in'):
            return redirect(url_for('auth_bp.login'))
        return redirect(url_for('blog.home'))

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/404.html'), 404  # Show 404 to hide existence

    # Blueprint Registration
    from app.routes.blog_routes import blog_bp
    from app.routes.auth import auth_bp
    from app.routes.user_mgmt import user_bp
    from app.routes.site_routes import site_bp
    from app.routes.newsletter_routes import newsletter_bp

    app.register_blueprint(blog_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(site_bp)
    app.register_blueprint(newsletter_bp)

    # FIX: Register with url_prefix to match your JS calls (/users/list, etc.)
    app.register_blueprint(user_bp, url_prefix='/users')

    return app