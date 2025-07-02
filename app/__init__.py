from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

db = SQLAlchemy()  # ✅ tạo 1 lần duy nhất tại đây

def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "fallback")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)  # ✅ quan trọng!

    # Import & đăng ký routes
    from .routes import main
    app.register_blueprint(main)

    with app.app_context():
        from .models import Tournament, Group, Team, Match  # 👈 import models ở đây
        db.create_all()

    return app
