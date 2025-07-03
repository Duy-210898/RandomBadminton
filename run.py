from app import create_app

app = create_app()

if __name__ == "__main__":
    # Khi chạy local, bật debug
    app.run(debug=True)
