import os
import time
import random

from openai import OpenAI
from dotenv import load_dotenv


class Caller:
    def __init__(self, base_url_list, api_key_list):
        assert len(base_url_list) == len(api_key_list)
        self.clients = [
            OpenAI(
                base_url=base_url,
                api_key=api_key
            )
            for base_url, api_key in zip(base_url_list, api_key_list)
        ]
    
    def __call__(self, model, messages, parser_func, max_time=8, interval=1):
        for _ in range(max_time):
            try:
                client = random.choice(self.clients)
                completion = client.chat.completions.create(
                    model=model,
                    messages=messages,
                )
                print(f"completion: {completion}")
                res, flag = parser_func(completion.choices[0].message.content.strip())
                if flag:
                    return res
                else:
                    print('parser_func flag is False')
                    print(f"completion: {completion}")
                    print(f"failed {_}")
                    time.sleep(interval)
            except Exception as e:
                print(f'Error: {e}')
                print(f"failed {_}")
                time.sleep(interval)
        print('Failed to get response')
        raise Exception('Failed to get response')

    def call_w_tail(self, model, messages, parser_func, tail, max_time=8, interval=1):
        res = self(model, messages, parser_func, max_time, interval)
        return res, tail


if __name__ == "__main__":
    load_dotenv()
    base_url_list = [os.getenv('BASE_URL')]
    api_key_list = [os.getenv('API_KEY')]
    caller = Caller(base_url_list, api_key_list)
    model = 'gpt-3.5-turbo'
    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'What is the capital of Japan?'}
    ]
    def parser_func(res):
        if res:
            return res, True
        else:
            return None, False
    res = caller(model, messages, parser_func)
    print(res)
