import sqlite3
import openai
import json
import pandas as pd
from agent.sql_func import SQLFunc
from agent.utils import format_table_for_telegram, transpose_table
from agent.functions_desc import functions
from agent.function import WebSearchFunc, GetTable, DisplayResults, CompareLaptops
from collections import defaultdict


class LaptopAgent:
    def __init__(self, model="gpt-3.5-turbo", max_steps=5):
        self.model = model
        self.max_steps = max_steps

        def get_system_message():
            return [
                {
                    "role": "system", 
                    "content": (
                        "Ты агент, специализирующийся на подборе ноутбуков для маркетплейса. Отвечай на русском языке."
                        "Все товары, которые ты рекомендуешь и возвращаешь пользователю, должны быть только из нашей Базы и получены из search_db. "
                    )
                }
            ]

        self.messages = defaultdict(get_system_message)
        self.cache = defaultdict(dict)
        self.functions = functions
        self.name2func = {
            'web_search': WebSearchFunc(),
            'search_db': SQLFunc(),
            'get_table': GetTable(),
            'display_results': DisplayResults(),
            'compare_laptops': CompareLaptops()
        }

    def process_message(self, user_input: str, user_id: int) -> str:
        self.messages[user_id].append(
            {"role": "user", "content": user_input}
        )

        for _ in range(self.max_steps):
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=self.messages[user_id],
                functions=self.functions,
                function_call="auto"
            )
            message: dict = response["choices"][0]["message"]
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

                    results: dict = self.name2func[func_name](cache=self.cache[user_id], **args)
                    self.messages[user_id].append(message)
                    self.messages[user_id].append({
                        "role": "function",
                        "name": func_name,
                        "content": results['log']
                    })
                    print(f"{func_name}: f{results['log']}")
                    self.cache[user_id].update(results)

                    if results.get("return2user", False):
                        return results['content']
            else:
                # Если функция не вызывается, значит получен финальный ответ
                final_answer = message["content"]
                return final_answer