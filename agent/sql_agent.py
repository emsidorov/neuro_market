import sqlite3
import openai
import json
import pandas as pd
import re


class SQLAgent:
    def __init__(self, model="gpt-3.5-turbo", db_uri="data/datalaptops.db", max_attempts=3):
        self.model = model
        self.db_uri = db_uri
        self.max_attempts = max_attempts
        self.static_table_description = (
            "Описание таблицы 'laptops':\n"
            "Колонки:\n"
            " - 'Laptop': название товара (строка)\n"
            " - 'Status': статус товара (например, New)\n"
            " - 'Brand': бренд (строка)\n"
            " - 'Model': модель (строка)\n"
            " - 'CPU': процессор (строка)\n"
            " - 'RAM': оперативная память (число, в ГБ)\n"
            " - 'Storage': объем накопителя (число, в ГБ)\n"
            " - 'Storage type': тип накопителя (например, SSD)\n"
            " - 'GPU': видеокарта (строка, может быть пустой)\n"
            " - 'Screen': размер экрана (число, дюймы)\n"
            " - 'Touch': поддержка сенсорного экрана (Yes/No)\n"
            " - 'Final_Price': конечная цена (число, в долларах)\n\n"
            "Обрати внимание на названия КОЛОНОК!!!"
            "Пример строки из базы:\n"
            "\"ASUS ExpertBook B1 B1502CBA-EJ0436X Intel Core i5-1235U/8GB/512GB SSD/15.6\"\",New,Asus,ExpertBook,Intel Core i5,8,512,SSD,,15.6,No,1008.9999999999999"
        )
        self.prompt = (
            "Ты SQL-эксперт. Твоя задача по запросу пользователя сделать SQL запрос, который выдаст упорядочный список вариантов (только 5 вариантов). \n"
            "Сформулируй корректный SQL запрос для поиска ноутбуков в базе данных "
            "на основе следующего запроса на естественном языке:\n\n"
            f"{self.static_table_description}\n\n"
            "Запрос: \"{query}\"\n\n"
            "SQL-запрос:"
        )
        self.messages = [
            {
                "role": "system", 
                "content": "Ты SQL-эксперт. Отвечай только корректным SQL запросом."
            },
        ]

    def parse_sql(self, sql_query: str) -> str:
        output = sql_query
        if "```sql" in sql_query:
            pattern = r"```sql\s*(.*?)\s*```"
            match = re.search(pattern, sql_query, re.DOTALL | re.IGNORECASE)
            if match:
                output = match.group(1).strip()
            else:
                output = ""
        
        return output

    def execute_sql_query(self, query: str) -> list:
        """
        Подключается к базе данных (SQLite) по указанному URI, выполняет SQL-запрос и возвращает список результатов.
        Каждый результат форматируется как строка вида "col1: value1, col2: value2, ...".
        """

        conn = sqlite3.connect(self.db_uri)
        try:
            conn = sqlite3.connect(self.db_uri)
            df = pd.read_sql_query(query, conn)
        except Exception as e:
            df = pd.DataFrame({"Ошибка": [f"Ошибка выполнения запроса: {e}"]})
        finally:
            conn.close()
        return df

    def process_message(self, user_input: str) -> dict:
        self.messages.append({"role": "user", "content": self.prompt.format(query=user_input)})

        attempts = 0
        prev_sql_query = ""
        while attempts < self.max_attempts:
            response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=self.messages,
                    temperature=0
            )
            sql_query = response["choices"][0]["message"]["content"].strip()
            sql_query = self.parse_sql(sql_query)
            print(sql_query)
            df_results = self.execute_sql_query(sql_query)

            if "Ошибка" in df_results.columns:
                error_msg = df_results["Ошибка"].iloc[0]
                correction_prompt = (
                    f"SQL запрос вызвал ошибку: {error_msg}. "
                    "Пожалуйста, исправь SQL запрос, чтобы он корректно выполнялся на таблице 'laptops'."
                    "Ты SQL-эксперт. Отвечай только корректным SQL запросом."
                )
                self.messages.append({"role": "user", "content": correction_prompt})
                attempts += 1
            elif df_results.shape[0] == 0:
                correction_prompt = (
                    f"SQL вернул пустой результат, ослабь фильтры или урежь название ноутбука, чтобы результат был непустым. "
                    "Обязательно измени запрос в сравнении с предыдущим"
                    "Ты SQL-эксперт. Отвечай только корректным SQL запросом."
                )
                if prev_sql_query == sql_query:
                    correction_prompt += "ТЫ НЕ ИЗМЕНИЛ SQL ЗАПРОС, ИЗМЕНИ!!!"

                self.messages.append({"role": "user", "content": correction_prompt})
                attempts += 1
            else:
                # Если запрос выполнен успешно, выходим из цикла
                break

        # Формируем текстовый промпт с итоговой информацией
        results_text = df_results.to_string(index=False)

        if df_results.shape[0] == 0:
            text_prompt = "Поиск в Базе Данных не дал результата, попробуй переформулировать запрос или поискать дополнительную информацию в web_search."
        else:
            text_prompt = f"Итоговый SQL запрос:\n {sql_query}\n\nИтоговая выдача из базы данных товаров:\n{results_text}"
        
        return {
            "sql_query": sql_query, 
            "dataframe": df_results, 
            "content": text_prompt
        }
