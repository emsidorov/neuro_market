# database.py
import pandas as pd
import sqlite3
import os
from dotenv import load_dotenv


# Загрузка переменных окружения
load_dotenv()
DB_PATH = os.getenv("DB_PATH")

def query_laptops(query_conditions: dict = None, sort_by: str = None, descending: bool = False, limit: int = 10):
    """Выполняет запрос к таблице ноутбуков с заданными условиями и сортировкой."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Формируем SQL-запрос на основе переданных критериев
    sql = "SELECT rowid, * FROM laptops"  # rowid будет использоваться как ID в выдаче
    conditions = []
    params = []
    if query_conditions:
        # Например, query_conditions = {"Brand": "ASUS", "RAM": "8"} для фильтрации
        for field, value in query_conditions.items():
            conditions.append(f"{field} LIKE ?")
            params.append(f"%{value}%")
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    if sort_by:
        sql += f" ORDER BY {sort_by}"
        if descending:
            sql += " DESC"
    if limit:
        sql += f" LIMIT {limit}"
    # Выполняем сформированный запрос
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_laptop_by_id(rowid: int):
    """Получает полные данные ноутбука по идентификатору (rowid) из последней выборки."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM laptops WHERE rowid = ?", (rowid,))
    row = cursor.fetchone()
    conn.close()
    return row
