import sqlite3
import openai
import json
import pandas as pd
from agent.sql_agent import SQLAgent


class LaptopAgent:
    def __init__(self, model="gpt-3.5-turbo", sql_agent=SQLAgent()):
        self.model = model
        self.sql_agent = sql_agent
        self.messages = [
            {
                "role": "system", 
                "content": (
                    "Ты агент, специализирующийся на подборе ноутбуков для маркетплейса. Отвечай на русском языке."
                    "Все товары, которые ты рекомендуешь и возвращаешь пользователю, должны быть только из нашей Базы и получены из search_db. "
                )
            }
        ]
        self.functions = [
            {
                "name": "search_db",
                "description": "Выполняет поиск ноутбуков по запросу пользователя и возвращает список товаров.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Запрос для поиска ноутбуков."
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "display_results",
                "description": (
                    "Используй данную функцию для отображения списка ноутбуков из базы, НИКОГДА НЕ ОТОБРАЖАЙ ЕГО САМ"
                    "ИСПОЛЬЗУЙ ДАННУЮ ФУНКЦИЮ ТОЛЬКО ЕСЛИ get_table ВОЗВРАЩАЕТ НЕПУСТОЙ СПИСОК "
                    "Формирует итоговый ответ пользователю состоящие из комментарией от агента и выдачи товара.\n"
                    "Функциия завершает итерацию работы агента."
                    "ИСПОЛЬЗУЙ ДАННУЮ ФУНКЦИЮ ТОЛЬКО ЕСЛИ get_table ВОЗВРАЩАЕТ НЕПУСТОЙ СПИСОК "
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_query": {
                            "type": "string",
                            "description": "Небольшой комментарий к выдаче из нашей базы. Ответь на вопрос, почему именно эти ноутбуки рекомендуешь?"
                        },
                        "display_laptops": {
                            "type": "boolean",
                            "description": "True - отобразить последнюю выдачу из search_db пользователю, False - не отображать выдачу пользователю"
                        }
                    },
                    "required": ["agent_query", "display_laptops"]
                }
            },
            {
                "name": "web_search",
                "description": (
                    "Выполняет веб-поиск для получения дополнительной информации о ноутбуке или обогощении информацией запроса пользователя, используя модель gpt-4o-search-preview."
                    "Используй данную функцию, чтобы искать дополнительную информацию по запросам пользователей. Например, какой ноутбук сейчас самый популярный"
                    "Воспользуйся поиском, если запрос сложный и тебе нужно поискать дополнительную информацию"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Запрос для веб-поиска дополнительной информации о ноутбуке или обогощении информацией запроса пользователя."
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_table",
                "description": (
                    "Если тебе важно посмотреть на последнюю выдачу из search_db для решения задачи пользователя, воспользуйся этой функцией. "
                    "Она возвращает информацию о последнем SQL запросе и последней выдаче"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]   
        self.last_df = None
        self.last_sql_query = None
        self.last_sql_content = None

    def search_db(self, query: str) -> list[pd.DataFrame, str]:
        return self.sql_agent.process_message(query)

    def display_results(self, agent_query: str, display_laptops: bool) -> str:
        output = f"{agent_query}\n\n"

        if display_laptops:
            for i, row in self.last_df.iterrows():
                output += f"{i+1}. {row['Laptop']}\n"

                for col in self.last_df.columns:
                    if col == 'Laptop':
                        continue

                    output += f" - {col}: {row[col]}\n"

                output += "\n"
            output += "\n"

        return output + "Могу ли я чем то еще помочь?)"
    
    def web_search(self, query: str) -> str:
        """
        Использует модель gpt-4o-search-preview для веб-поиска.
        Эта функция обращается к OpenAI API с параметром web_search_options и возвращает результат веб-поиска.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4o-search-preview",
            web_search_options={},  # Используйте параметры по умолчанию или настройте их по необходимости
            messages=[{"role": "user", "content": query}]
        )
        return response["choices"][0]["message"]["content"].strip()
    
    def get_table(self) -> str:
        return self.last_sql_content

    def process_message(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

        # Цикл, в котором агент запрашивает функцию, если требуется, или сразу выдаёт финальный ответ.
        while True:
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

                if func_name == "search_db":
                    query = func_args.get("query", "")
                    results = self.search_db(query)
                    self.last_df = results['dataframe']
                    self.last_sql_query = results['sql_query']
                    self.last_sql_content = results['content']
                    # Добавляем вызов функции и результат в историю
                    self.messages.append(message)
                    self.messages.append({
                        "role": "function",
                        "name": "search_db",
                        "content": results['content']
                    })
                    print(results['content'])

                elif func_name == "display_results":
                    agent_query = func_args.get("agent_query", "")
                    display_laptops = func_args.get("display_laptops", True)
                    formatted = self.display_results(agent_query, display_laptops)
                    self.messages.append(message)
                    self.messages.append({
                        "role": "function",
                        "name": "display_results",
                        "content": formatted
                    })
                    return formatted
                
                elif func_name == "web_search":
                    query = func_args.get("query", "")
                    web_result = self.web_search(query)
                    self.messages.append(message)
                    self.messages.append({
                        "role": "function",
                        "name": "web_search",
                        "content": web_result
                    })
                    # print("Результат web_search:", web_result)

                elif func_name == "get_table":
                    content = self.get_table()
                    self.messages.append(message)
                    self.messages.append({
                        "role": "function",
                        "name": "web_search",
                        "content": content
                    })
            else:
                # Если функция не вызывается, значит получен финальный ответ
                final_answer = message["content"]

                if "1. " in final_answer:
                    final_answer += "\n\n НИКОГДА НЕ ВОЗВРАЩАЙ список ноутбуков сам, используй search_db и disaply_results"
                    self.messages.append(message)
                    continue
                
                return final_answer