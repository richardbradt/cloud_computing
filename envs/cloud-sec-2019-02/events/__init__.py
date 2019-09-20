""" Create app and initialize blueprints """
from flask import Flask, redirect, url_for
import os, datetime

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.urandom(16)

    # blueprint for events routes
    from .events import events as events_blueprint
    app.register_blueprint(events_blueprint)

    # blueprint for auth routes
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # Add default route
    @app.route('/')
    def index():
        return redirect(url_for('events'))

    return app
