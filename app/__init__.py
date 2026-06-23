from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    with app.app_context():
        # Import models here so SQLAlchemy knows about them
        from app import models
        # Import routes
        from app import routes
        
        # Create all tables (useful for local development with SQLite)
        db.create_all()

    return app
