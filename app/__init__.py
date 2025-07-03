from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

db = SQLAlchemy()

def create_app():
    # Tự động load .env nếu không chạy trên Render
    if os.environ.get("RENDER") != "true":
        load_dotenv()  # Dành cho local dev

    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")

    # Ưu tiên dùng DATABASE_INTERNAL_URL nếu có, sau đó đến DATABASE_URL
    db_url = (
        os.environ.get("DATABASE_INTERNAL_URL")
        or os.environ.get("DATABASE_URL")
    )

    if not db_url:
        raise RuntimeError("❌ Thiếu biến môi trường DATABASE_URL hoặc DATABASE_INTERNAL_URL.")

    # Thiết lập kết nối SQLAlchemy
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Đăng ký route (Blueprint)
    from .routes import main
    app.register_blueprint(main)

    # Tạo bảng nếu chưa có
    with app.app_context():
        from .models import Tournament, Group, Team, Match
        db.create_all()

        # Kiểm tra kết nối DB
        try:
            db.session.execute("SELECT 1")
            print("✅ Đã kết nối database thành công.")
        except Exception as e:
            print(f"❌ Lỗi kết nối database: {e}")

    return app
