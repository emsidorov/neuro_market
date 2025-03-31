import pandas as pd
from tabulate import tabulate


def format_table_for_telegram(df: pd.DataFrame) -> str:
    """
    Форматирует DataFrame для удобного отображения в Telegram-чате.
    Таблица выводится в виде ASCII-таблицы с обрамлением в блок кода Markdown.
    
    :param df: Исходный DataFrame, например, транспонированный (параметры — индексы, ноутбуки — колонки)
    :return: Строка с таблицей, отформатированная в виде Markdown кода
    """
    # Используем формат "grid" для красивого отображения
    table_str = tabulate(df, headers="keys", tablefmt="fancy_grid", showindex=True)
    
    # Обрамляем таблицу в блок кода Markdown (тройные обратные кавычки)
    formatted = f"```\n{table_str}\n```"
    return formatted


def transpose_table(df: pd.DataFrame, index: str) -> pd.DataFrame:
    """
    Транспонирует таблицу, где каждая строка – это ноутбук с его параметрами.
    После транспонирования столбцы будут представлять ноутбуки, а индексы – параметры.
    
    Предполагается, что в исходной таблице есть столбец "Название ноутбук",
    который содержит уникальные идентификаторы (имена) ноутбуков.
    
    :param df: Исходный DataFrame с колонками: "Название ноутбук", "Стоимость", "Оперативная память", и т.д.
    :return: Транспонированный DataFrame, где индексы – параметры, а столбцы – названия ноутбуков.
    """
    # Установим столбец "Название ноутбук" в качестве индекса
    df_indexed = df.set_index(index)
    
    # Транспонируем DataFrame
    df_transposed = df_indexed.T
    
    return df_transposed