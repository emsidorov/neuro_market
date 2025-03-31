import sqlite3
import openai
import json
import pandas as pd
from agent.sql_func import SQLFunc
from agent.utils import format_table_for_telegram, transpose_table
from agent.functions_desc import functions
from agent.function import WebSearchFunc, GetTable, DisplayResults, CompareLaptops


class LaptopAgent:
    def __init__(self, model="gpt-3.5-turbo", max_steps=5):
        self.model = model
        self.max_steps = max_steps
        self.messages = [
            {
                "role": "system", 
                "content": (
                    "Ты агент, специализирующийся на подборе ноутбуков для маркетплейса. Отвечай на русском языке."
                    "Все товары, которые ты рекомендуешь и возвращаешь пользователю, должны быть только из нашей Базы и получены из search_db. "
                )
            }
        ]
        self.functions = functions
        self.name2func = {
            'web_search': WebSearchFunc(),
            'search_db': SQLFunc(),
            'get_table': GetTable(),
            'display_results': DisplayResults(),
            'compare_laptops': CompareLaptops()
        }
        self.cache = dict()
    
    def compare_laptops(self, laptops: list[int]) -> str:
        compare_df = self.last_df.iloc[laptops].copy()
        compare_df = transpose_table(compare_df, "Laptop")
        return format_table_for_telegram(compare_df)

    def process_message(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

        for _ in range(self.max_steps):
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=self.messages,
                functions=self.functions,
                function_call="auto"
            )
            message = response["choices"][0]["message"]
            print(json.dumps(message, ensure_ascii=False, indent=2))

            # Если модель запрашивает вызов функции
            if message.get("function_call"):
                func_name = message["function_call"]["name"]
                try:
                    func_args = json.loads(message["function_call"]["arguments"])
                except Exception as _:
                    func_args = {}

                if func_name in self.name2func:
                    func_desc = None
                    for desc in self.functions:
                        if desc['name'] == func_name:
                            func_desc = desc

                    args = {}
                    for param in func_desc['parameters']['properties']:
                        args[param] = func_args.get(param, None)

                    results = self.name2func[func_name](cache=self.cache, **args)
                    self.messages.append(message)
                    self.messages.append({
                        "role": "function",
                        "name": func_name,
                        "content": results['log']
                    })
                    print(f"{func_name}: f{results['log']}")
                    self.cache.update(results)

                    if results.get("return2user", False):
                        return results['content']
            else:
                # Если функция не вызывается, значит получен финальный ответ
                final_answer = message["content"]
                return final_answer