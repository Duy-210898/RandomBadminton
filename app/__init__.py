from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

db = SQLAlchemy()

def create_app():
    # Chỉ load .env khi chạy local
    if os.environ.get("RENDER") != "true":
        load_dotenv()  # Load từ .env nếu có

    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")

    # Ưu tiên dùng internal DB khi chạy trên Render
    db_url = os.getenv("DATABASE_INTERNAL_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("❌ Thiếu DATABASE_URL hoặc DATABASE_INTERNAL_URL.")

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Đăng ký Blueprint
    from .routes import main
    app.register_blueprint(main)

    # Khởi tạo bảng
    with app.app_context():
        from .models import Tournament, Group, Team, Match
        db.create_all()
        try:
            db.session.execute("SELECT 1")
            print("✅ Đã kết nối database thành công.")
        except Exception as e:
            print("❌ Lỗi kết nối database:", e)

    return app
