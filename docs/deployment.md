# Инструкция по развертыванию (Docker)

Для запуска приложения в изолированном контейнере выполните следующие команды:

1. Соберите Docker-образ:
   docker build -t restaurant-reservation:v1.0.0 .

2. Запустите контейнер:
   docker run -p 5000:5000 restaurant-reservation:v1.0.0

3. Приложение будет доступно по адресу: http://localhost:5000
