import re
import secrets
from abc import ABC, abstractmethod
from datetime import date

SLOTS = ["10:00", "12:00", "14:00", "16:00", "18:00", "20:00"]

# --- ПАТТЕРН СТРАТЕГИЯ ДЛЯ УВЕДОМЛЕНИЙ ---
class NotificationStrategy(ABC):
    @abstractmethod
    def send(self, phone: str, name: str, number: str):
        pass

class SMSNotification(NotificationStrategy):
    def send(self, phone: str, name: str, number: str):
        # В реальном проекте здесь был бы вызов API SMS-шлюза
        print(f"[SMS] Уважаемый(ая) {name}, ваша бронь {number} успешно создана!")

class EmailNotification(NotificationStrategy):
    def send(self, phone: str, name: str, number: str):
        # В реальном проекте здесь была бы отправка через smtplib
        print(f"[EMAIL] Отправлено письмо для {name}. Номер брони: {number}")

class Notifier:
    def __init__(self, strategy: NotificationStrategy):
        self._strategy = strategy

    def notify(self, phone, name, number):
        self._strategy.send(phone, name, number)
# -----------------------------------------

def create_booking(con, table_id, day, slot, guests, name, phone):
    """Возвращает ('ok', номер) | ('busy', None) | ('invalid', текст ошибки)."""
    try:
        d = date.fromisoformat(day)
    except ValueError:
        return "invalid", "Некорректная дата"
    if d < date.today():
        return "invalid", "Нельзя бронировать на прошедшую дату"
    if slot not in SLOTS:
        return "invalid", "Ресторан работает с 10:00 до 23:00: выберите время из списка"
    if not name.strip():
        return "invalid", "Укажите имя"
    if not re.fullmatch(r"\+?\d{10,15}", re.sub(r"[ ()-]", "", phone)):
        return "invalid", "Телефон: от 10 до 15 цифр"
    
    t = con.execute("SELECT seats FROM tables WHERE id=?", (table_id,)).fetchone()
    if t is None:
        return "invalid", "Такого столика нет"
    if not 1 <= guests <= t["seats"]:
        return "invalid", f"За этим столиком от 1 до {t['seats']} гостей"

    number = "B-" + secrets.token_hex(3).upper()
    con.execute("BEGIN IMMEDIATE")
    try:
        busy = con.execute(
            "SELECT 1 FROM bookings WHERE table_id=? AND booking_date=? AND booking_time=? "
            "AND status IN ('ОЖИДАЕТ','ПОДТВЕРЖДЕНА')", (table_id, day, slot)).fetchone()
        if busy:
            con.execute("ROLLBACK")
            return "busy", None
        
        con.execute(
            "INSERT INTO bookings(number,table_id,booking_date,booking_time,guests,name,phone) "
            "VALUES (?,?,?,?,?,?,?)", (number, table_id, day, slot, guests, name.strip(), phone.strip()))
        con.execute("COMMIT")
        
        # Вызов уведомления через паттерн Стратегия
        notifier = Notifier(SMSNotification()) # Можно менять на EmailNotification
        notifier.notify(phone, name, number)
        
        return "ok", number
    except Exception:
        con.execute("ROLLBACK")
        raise
