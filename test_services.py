import pytest

from datetime import date, timedelta
from db import connect, init_db
from services import create_booking


@pytest.fixture
def setup_db(tmp_path):
    """Создает временную БД для тестов."""
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
    create_booking(setup_db, 1, "2030-01-01", "18:00", 2, "Иван", "+79991234567")
    status, msg = create_booking(setup_db, 1, "2030-01-01", "18:00", 2, "Петр", "+79997654321")
    assert status == "busy"
    assert msg is None

@pytest.mark.parametrize("phone, expected_status", [
    ("+7999123456", "ok"),
    ("+799912345678901", "ok"),
    ("+799912345", "invalid"),
    ("+7999123456789012", "invalid"),
    ("телефон", "invalid"),
])
def test_phone_validation_parametrized(setup_db, phone, expected_status):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    status, _ = create_booking(setup_db, 1, tomorrow, "18:00", 2, "Иван", phone)
    assert status == expected_status

@pytest.mark.parametrize("guests, expected_status", [
    (1, "ok"),
    (2, "ok"),
    (0, "invalid"),
    (-1, "invalid"),
    (3, "invalid"),
])
def test_guests_validation_parametrized(setup_db, guests, expected_status):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    status, _ = create_booking(setup_db, 1, tomorrow, "18:00", guests, "Иван", "+79991234567")
    assert status == expected_status

@pytest.mark.parametrize("day_offset, expected_status", [
    (-1, "invalid"),
    (0, "ok"),
    (1, "ok"),
])
def test_date_validation_parametrized(setup_db, day_offset, expected_status):
    target_date = (date.today() + timedelta(days=day_offset)).isoformat()
    status, _ = create_booking(setup_db, 1, target_date, "18:00", 2, "Иван", "+79991234567")
    assert status == expected_status

def test_integration_booking_and_notification(setup_db, capsys):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    status, number = create_booking(setup_db, 1, tomorrow, "18:00", 2, "Иван", "+79991234567")
    
    assert status == "ok"
    
    captured = capsys.readouterr()
    assert f"ваша бронь {number}" in captured.out
