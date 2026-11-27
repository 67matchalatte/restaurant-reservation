FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Открываем порт, на котором работает Flask
EXPOSE 5000

# Запускаем приложение
CMD ["python", "app.py"]
