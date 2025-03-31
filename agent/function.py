import openai
import pandas as pd
from agent.utils import format_table_for_telegram, transpose_table


class Function:
    def __init__(self):
        pass

    def __call__(self):
        pass


class WebSearchFunc(Function):
    def __init__(self, model='gpt-4o-search-preview', prompt=''):
        super().__init__()
        self.model = model
        self.prompt_message = [
            {
                "role": "system", 
                "content": prompt
            }
        ] if prompt else []

    def __call__(self, cache: dict, query: str) -> dict:
        response = openai.ChatCompletion.create(
            model="gpt-4o-search-preview",
            web_search_options={},  # Используйте параметры по умолчанию или настройте их по необходимости
            messages=self.prompt_message + [{"role": "user", "content": query}]
        )

        return {
            'content': response["choices"][0]["message"]["content"].strip(),
            'log': response["choices"][0]["message"]["content"].strip()
        }
    

class GetTable(Function):
    def __init__(self):
        super().__init__()

    def __call__(self, cache: dict) -> dict:
        content = cache.get("df_str", "")
        return {
            'content': content,
            'log': content
        }
    

class DisplayResults(Function):
    def __init__(self):
        super().__init__()

    def __call__(self, cache: dict, agent_query: str, display_laptops: bool) -> dict:
        if 'dataframe' not in cache:
            content = "Функция search_db еще не вызывалась, поэтому нечего отображать. "
            return {
                'content': content,
                'log': content
            }

        df: pd.DataFrame = cache['dataframe']
        output = f"{agent_query}\n\n"

        if display_laptops:
            for i, row in df.iterrows():
                output += f"{i+1}. {row['Laptop']}\n"

                for col in df.columns:
                    if col == 'Laptop':
                        continue

                    output += f" - {col}: {row[col]}\n"

                output += "\n"
            output += "\n"

        output = output + "Могу ли я чем то еще помочь?)"
        return {
            'content': output,
            'log': output,
            'return2user': True
        }


class CompareLaptops(Function):
    def __init__(self, model='gpt-3.5-turbo'):
        self.model=model
        self.messages = [
            {
                "role": "system", 
                "content": (
                    "Ты функция сравнения двух ноутбуков. Твоя задача удобно для пользователя отобразить сравнение параметров 2 или более ноутбуков. "
                    "Данное сравнение будет возвращено пользователю в телеграмм, так что адаптируй его под этот мессенджер, чтобы оно там удобно и красиво отображалось. "
                )
            },
        ]
        super().__init__()

    def __call__(self, cache: dict, laptops: list[int]):
        if 'dataframe' not in cache:
            content = "Функция search_db еще не вызывалась, поэтому нечего сравнивать. "
            return {
                'content': content,
                'log': content
            }

        df: pd.DataFrame = cache['dataframe']
        compare_df = df.iloc[laptops].copy()
        compare = compare_df.to_string(index=False)

        self.messages.append({"role": "user", "content": compare})
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=self.messages,
            temperature=0
        )
        content = response["choices"][0]["message"]["content"].strip()
        return {
            'content': content,
            'log': content, 
            'return2user': True
        }