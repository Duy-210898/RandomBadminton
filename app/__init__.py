from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

db = SQLAlchemy()

def create_app():
    load_dotenv()  # Tải biến môi trường từ file .env

    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Import và đăng ký Blueprint
    from .routes import main
    app.register_blueprint(main)

    # Tạo bảng nếu chưa có (chỉ nên dùng cho dev/local)
    with app.app_context():
        from .models import Tournament, Group, Team, Match
        db.create_all()
        try:
            db.session.execute("SELECT 1")
            print("✅ Đã kết nối database thành công.")
        except Exception as e:
            print("❌ Lỗi kết nối database:", e)

    return app
