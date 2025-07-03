# Sử dụng base image
FROM python:3.11-slim

# Cài đặt OS dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev gcc

# Tạo thư mục cho app
WORKDIR /app

# Copy file vào container
COPY . /app

# Cài đặt Python packages
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Cấu hình biến môi trường
ENV PYTHONUNBUFFERED=1

# Mở port 8000
EXPOSE 8000

# Command để chạy app
CMD ["gunicorn", "-b", "0.0.0.0:8000", "run:app"]
