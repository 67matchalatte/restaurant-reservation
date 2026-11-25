import pytest

from db import connect, init_db
from services import create_booking


@pytest.fixture
def setup_db(tmp_path):
    """Создает временную БД для тестов, чтобы не трогать основную."""
    import db
    original_path = db.DB_PATH
    db.DB_PATH = str(tmp_path / "test.db")
    init_db()
    con = connect()
    yield con
    con.close()
    db.DB_PATH = original_path

def test_booking_invalid_date(setup_db):
    status, msg = create_booking(setup_db, 1, "2020-01-01", "18:00", 2, "Иван", "+79991234567")
    assert status == "invalid"
    assert "прошедшую дату" in msg

def test_booking_invalid_phone(setup_db):
    status, msg = create_booking(setup_db, 1, "2030-01-01", "18:00", 2, "Иван", "123")
    assert status == "invalid"
    assert "Телефон" in msg

def test_booking_success(setup_db):
    status, number = create_booking(setup_db, 1, "2030-01-01", "18:00", 2, "Иван", "+79991234567")
    assert status == "ok"
    assert number.startswith("B-")

def test_booking_busy(setup_db):
    # Первая бронь
    create_booking(setup_db, 1, "2030-01-01", "18:00", 2, "Иван", "+79991234567")
    # Вторая бронь на тот же столик, в тот же слот
    status, msg = create_booking(setup_db, 1, "2030-01-01", "18:00", 2, "Петр", "+79997654321")
    assert status == "busy"
    assert msg is None
