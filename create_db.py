from app import create_app, db
from app.models import Tournament, Group, Team, Match  # bắt buộc import để db.create_all() nhận model

app = create_app()

with app.app_context():
    db.create_all()
    print("✅ Database created successfully.")
