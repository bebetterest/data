import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
load_dotenv()


import jsonlines
from tqdm import tqdm
from openai import OpenAI


def parse_pred(response):
    response = response.strip()
    if "\\answer{" in response:
        response = response.split("\\answer{")[-1]
        count = 1
        res = ""
        for char in response:
            if char == "}":
                count -= 1
                if count == 0:
                    break
            if char == "{":
                count += 1
            if count > 0:
                res += char
        
        res = res.strip()
        while res.startswith("`"):
            res = res[1:]
        while res.endswith("`"):
            res = res[:-1]
        
        res = res.strip()

        # just for sudoku. But it would not conflict with multiplication. Adjust it if adding more tasks.
        if "," in res:
            res = res.replace(",", "\n")
        lines = [_.strip() for _ in res.split("\n") if len(_.strip()) > 0]
        res = "\n".join(lines)
        if " " in res:
            res.replace(" ", "")
        return res
    else:
        print(f"No answer found in response: {response.strip()}")
        return response.strip()


def call_model(
        item,
        model_name
):
    prompt = item["item"][0]["value"].strip()
    answer = item["item"][1]["value"].strip()
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    completion = client.chat.completions.create(
        # extra_headers={
        #     "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
        #     "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
        # },
        model=model_name,
        messages=[
            {
            "role": "user",
            "content": prompt + "\nfill the final answer inside \\answer{}"
            }
        ]
    )
    pred = parse_pred(completion.choices[0].message.content.strip())
    print(completion)
    pass_flag = (pred.strip() == answer.strip())
    return {
        "pass_flag": pass_flag,
        "pred": pred,
        "answer": answer,
        "prompt": prompt,
        "response": completion.choices[0].message.content.strip(),
        "reasoning": completion.choices[0].message.reasoning.strip()\
            if hasattr(completion.choices[0].message, "reasoning") else None,
        "idx": item["idx"],
    }


def main_proc(file_path, model_name, max_workers=1):
    with open(file_path, "r") as f:
        data = json.load(f)

    file_name = file_path.split("/")[-1].split(".")[0].strip()
    tmp_path = os.path.join(file_name, "_tmp.jsonl")
    if os.path.exists(tmp_path):
        with jsonlines.open(tmp_path, "r") as reader:
            res = list(reader)
    else:
        res = []
    
    todo = [
        {
            "idx": idx,
            "item": item,
        }
        for idx, item in enumerate(data)
        if idx not in [_["idx"] for _ in res]
    ]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(call_model, _, model_name)
            for _ in todo
        ]
        td = tqdm(total=len(todo))
        for future in as_completed(futures):
            single_result = future.result()
            res.append(single_result)
            with jsonlines.open(tmp_path, "a") as writer:
                writer.write(single_result)
            td.update(1)


def test_call_model():
    # item = {
    #     "idx": 0,
    #     "item": [
    #         {
    #             "value": "question: a = 111, b = 222, determine the value of a * b",
    #         },
    #         {
    #             "value": "24642"
    #         }
    #     ]
    # }
    item = {
        "idx": 0,
        "item": [
            {
                "value": "The Sudoku puzzle uses a 9*9 grid, which is divided into 9 non-overlapping 3*3 subgrids (each subgrid consists of 3 rows and 3 columns, totaling 9 cells). The game follows these rules: each row, each column, and each 3*3 subgrid must contain the numbers 1-9 without repetition. At the start of the game, some cells are pre-filled with numbers (which cannot be changed), while empty cells are represented by \".\".Here is a sudoku puzzle:\n2.1364895\n358729461\n469851732\n835497126\n127683549\n69451.378\n98.176254\n716245983\n54293.6.7\nYou need to deduce the solution based on the given numbers and output the complete 9*9 grid.",
            },
            {
                "value": "271364895\n358729461\n469851732\n835497126\n127683549\n694512378\n983176254\n716245983\n542938617"
            }
        ]
    }
    # "openai/gpt-4o-2024-11-20"

    # "deepseek/deepseek-r1"
    # "openai/o1"
    # "anthropic/claude-3.7-sonnet:thinking"
    # "google/gemini-2.0-flash-thinking-exp:free"

    # ""
    model_name = "deepseek/deepseek-r1"
    res = call_model(item, model_name)
    print(json.dumps(res, indent=2))


def test_main_proc():
    file_path = "sudoku_data_v20250310212219.json"
    model_name = "deepseek/deepseek-r1"
    main_proc(file_path, model_name)


if __name__ == "__main__":
    test_call_model()

    # test_main_proc()
