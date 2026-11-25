from datetime import date, timedelta

import pytest

from db import connect, free_tables, init_db


@pytest.fixture
def setup_db(tmp_path):
    """Создает временную БД для тестов."""
    import db
    original_path = db.DB_PATH
    db.DB_PATH = str(tmp_path / "test_free_tables.db")
    init_db()
    con = connect()
    yield con
    con.close()
    db.DB_PATH = original_path

def test_free_tables_all_free(setup_db):
    """Тест: если броней нет, возвращаются все столики."""
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    tables = free_tables(setup_db, tomorrow, "18:00")
    # В нашей базе 8 столиков, значит должно вернуться 8
    assert len(tables) == 8

def test_free_tables_excludes_booked(setup_db):
    """Тест: занятый столик не должен попадать в список свободных."""
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Создаем бронь на столик №1 на 18:00
    setup_db.execute(
        "INSERT INTO bookings(number, table_id, booking_date, booking_time, guests, name, phone, status) "
        "VALUES ('B-TEST1', 1, ?, '18:00', 2, 'Тест', '+79990000000', 'ПОДТВЕРЖДЕНА')",
        (tomorrow,)
    )

    tables = free_tables(setup_db, tomorrow, "18:00")
    # Должно остаться 7 столиков (8 - 1 занятый)
    assert len(tables) == 7
    table_ids = [t["id"] for t in tables]
    assert 1 not in table_ids

def test_free_tables_by_guests(setup_db):
    """Тест: фильтрация по количеству гостей."""
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Ищем столики, вмещающие 6 гостей
    tables = free_tables(setup_db, tomorrow, "18:00", guests=6)

    # В нашей базе только столики с seats >= 6
    for t in tables:
        assert t["seats"] >= 6
