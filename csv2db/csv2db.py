import pandas as pd
import sqlite3


def main():
    df = pd.read_csv("data/laptops.csv")
    


if __name__ == "__main__":
    main()

# Читаем CSV-файл с датасетом
# Убедитесь, что файл 'laptops_price_dataset.csv' находится в рабочей директории
df = pd.read_csv("laptops_price_dataset.csv")

# Просмотр первых строк для проверки данных
print(df.head())

# Создаём или открываем базу данных SQLite (файл laptops.db)
conn = sqlite3.connect("laptops.db")

# Записываем данные из DataFrame в таблицу 'laptops'
# Если таблица уже существует, она будет заменена
df.to_sql("laptops", conn, if_exists="replace", index=False)

# Закрываем соединение с базой данных
conn.close()

print("Данные успешно занесены в базу данных laptops.db, таблица 'laptops'.")
