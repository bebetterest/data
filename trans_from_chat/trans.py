import os
import json
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from llm_caller import Caller
from prompt_template import (
    JUDGE_PROMPT_TEMPLATE, REWRITE_PROMPT_TEMPLATE,
    judge_parser, rewrite_parser
)

from dotenv import load_dotenv
import jsonlines
from tqdm import tqdm


class Trans:
    def __init__(
            self, trans_name,
            base_url_list, api_key_list, model, parser_func
    ):
        self.trans_name = trans_name
        self.tmp_path = f"tmp_{trans_name}.jsonl"
        self.res_path = f"{trans_name}_res.jsonl"
        self.messages_key = f"{trans_name}_messages"
        self.trans_idx_key = f"{trans_name}_idx"
        self.trans_res_key = f"{trans_name}_res"

        self.caller = Caller(base_url_list, api_key_list)
        self.model = model
        self.parser_func = parser_func

    def _apply_template(self, data, q_key, a_key, template):
        for idx, item in enumerate(data):
            data[idx][self.messages_key] = [
                {
                    'role': 'user',
                    'content': template.format(
                        question=item[q_key], answer=item[a_key]
                    )
                },
            ]
            data[idx][self.trans_idx_key] = idx
        return data
    
    def __call__(
            self,
            data: List[dict], q_key, a_key, template,
            max_workers, batch_size
    ) -> List[dict]:
        print(f"Start {self.trans_name}")
        data = self._apply_template(data, q_key, a_key, template)
        res = {}
        if os.path.exists(self.tmp_path):
            input(f"tmp file {self.tmp_path} already exists. Please make sure it is the cache file you want to use. Press any key to continue.")
            with jsonlines.open(self.tmp_path) as reader:
                for item in reader:
                    res[item[self.trans_idx_key]] = item
        res_idx_list = list(res.keys())
        todos = [
            item for item in data
            if item[self.trans_idx_key] not in res_idx_list
        ]

        print(f"total_data: {len(data)}, todo_messages: {len(todos)}")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for start_idx in range(0, len(todos), batch_size):
                futures = []
                batch = todos[start_idx:min(start_idx + batch_size, len(todos))]
                for item in batch:
                    future = executor.submit(
                        self.caller.call_w_tail,
                        self.model, item[self.messages_key], self.parser_func, tail=item[self.trans_idx_key]
                    )
                    futures.append(future)
                for future in tqdm(as_completed(futures), total=len(futures)):
                    result, item_idx = future.result()
                    res[item_idx] = {
                        "res": result,
                        self.trans_idx_key: item_idx,
                    }
                    with jsonlines.open(self.tmp_path, 'a') as writer:
                        writer.write(res[item_idx])
        assert len(res) == len(data), f"len(res): {len(res)}, len(data): {len(data)}"
        for idx in range(len(data)):
            data[idx][self.trans_res_key] = res[idx]["res"]
        with jsonlines.open(self.res_path, 'w') as writer:
            for item in data:
                writer.write(item)
        return data


def main_proc(
        dataset_name="EricLu/SCP-116K",
        question_key="problem",
        answer_key="extract_solution",
        model_name="openai/gpt-4o-2024-11-20",
        max_workers=1,
        batch_size=16,
        debug_mode=False,
):
    load_dotenv()
    # support multiple servers
    base_url_list = [os.getenv('BASE_URL')]
    api_key_list = [os.getenv('API_KEY')]

    from datasets import load_dataset
    dataset = load_dataset(dataset_name, num_proc=16)["train"].to_list()
    dataset = [
        item for item in dataset
        if item[question_key] is not None and item[answer_key] is not None
        and len(item[question_key].strip()) > 0 and len(item[answer_key].strip()) > 0
    ]

    if debug_mode:
        print(json.dumps(dataset[0], indent=2))
        dataset = dataset[:32]
        input("debug mode (before judge). press any key to continue.")

    judge_trans = Trans(
        "judge", base_url_list, api_key_list, model_name, judge_parser
    )
    judge_res = judge_trans(
        dataset, question_key, answer_key, JUDGE_PROMPT_TEMPLATE, max_workers, batch_size
    )

    if debug_mode:
        print(json.dumps(judge_res[0], indent=2))
        input("debug mode (after judge). press any key to continue.")

    filtered_data = [item for item in judge_res if item["judge_res"]["pass"]]
    print(f"filtered_data: {len(filtered_data)} / {len(judge_res)}")

    if debug_mode:
        input("debug mode (after filtering). press any key to continue.")

    rewrite_trans = Trans(
        "rewrite", base_url_list, api_key_list, model_name, rewrite_parser
    )
    rewrite_res = rewrite_trans(
        filtered_data, question_key, answer_key, REWRITE_PROMPT_TEMPLATE, max_workers, batch_size
    )

    if debug_mode:
        print(json.dumps(rewrite_res[0], indent=2))
        input("debug mode (after rewrite). press any key to continue.")

    formatted_data = [
        [
            {
                "from": "human",
                "value": item["rewrite_res"]["question"],
                "metadata": {
                    "source": f"{dataset_name}_transed",
                    "judge_idx": item["judge_idx"],
                    "domain": item.get("domain", ""),
                    "promblem": item["problem"],
                }
            },
            {
                "from": "assistant",   
                "value": item["rewrite_res"]["answer"],
            },
        ]
        for item in rewrite_res
    ]
    with open(f"transed.json", 'w') as writer:
        json.dump(formatted_data, writer, indent=2)
    return rewrite_res


if __name__ == "__main__":
    main_proc(debug_mode=True)
