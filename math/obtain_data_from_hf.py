import os
import json
from typing import List, Tuple

import datasets
from tqdm import tqdm
from math_verify import parse, verify


def parse_synthetic_code_understanding(dataset: datasets.Dataset) -> Tuple[List[dict], str]:
    reward_type = "match"
    res_data = []
    for item in dataset:
        if item["gold_standard_solution"].startswith("{'output': \""):
            item["gold_standard_solution"] = item["gold_standard_solution"].replace("{'output': \"", "{'output': '")
            assert item["gold_standard_solution"].endswith("\"}"), item["gold_standard_solution"]
        else:
            assert item["gold_standard_solution"].startswith("{'output': '"), item["gold_standard_solution"]
            assert item["gold_standard_solution"].endswith("'}"), item["gold_standard_solution"]
        answer = item["gold_standard_solution"][len("{'output': '"):-len("'}")]
        res_data.append({
            "question": item["prompt"].strip(),
            "answer": answer.strip(),
            "id": item["problem_id"],
        })
    return res_data, reward_type


def parse_numina_math(dataset: datasets.Dataset) -> Tuple[List[dict], str]:
    reward_type = "match"
    res_data = []
    for idx, item in enumerate(tqdm(dataset)):
        if item["answer"] in ["proof", "MCQ"]:
            continue
        if item["answer"] is None:
            continue
        if item["answer"].startswith("\$") and not item["answer"].endswith("\$"):
            item["answer"] = item["answer"][len("\$"):]
        res_data.append({
            "question": item["problem"].strip(),
            "answer": item["answer"].strip(),
            "id": idx,
        })
    return res_data, reward_type


def parse_deepscale_r_preview_dataset(dataset: datasets.Dataset) -> Tuple[List[dict], str]:
    reward_type = "match"
    res_data = []
    for idx, item in enumerate(tqdm(dataset)):
        res_data.append({
            "question": item["problem"].strip(),
            "answer": item["answer"].strip(),
            "id": idx
        })
    return res_data, reward_type


def parse_rlvr_gsm(dataset: datasets.Dataset) -> Tuple[List[dict], str]:
    reward_type = "match"
    res_data = []
    for item in tqdm(dataset):
        assert item["messages"][0]["content"].strip().startswith("Question: "), item
        res_data.append({
            "question": item["messages"][0]["content"].split("Question: ")[-1].strip(),
            "answer": item["ground_truth"].strip(),
        })
    
    return res_data, reward_type


def parse_rlvr_math(dataset: datasets.Dataset) -> Tuple[List[dict], str]:
    reward_type = "match"
    res_data = []
    for item in tqdm(dataset):
        assert "\nQuestion: " in item["messages"][0]["content"].strip(), item
        res_data.append({
            "question": item["messages"][0]["content"].split("\nQuestion: ")[-1].strip(),
            "answer": item["ground_truth"].strip(),
        })
    
    return res_data, reward_type


def parse_big_math_rl_verified(dataset: datasets.Dataset) -> Tuple[List[dict], str]:
    reward_type = "match"
    res_data = []
    for item in tqdm(dataset):
        if item["answer"].startswith("$\\hspace{.05in}") and item["answer"].endswith("$"):
            item["answer"] = item["answer"][len("$\\hspace{.05in}"):-len("$")]
        res_data.append({
            "question": item["problem"].strip(),
            "answer": item["answer"].strip(),
        })
    return res_data, reward_type


def parse_custom_json(dataset: datasets.Dataset) -> Tuple[List[dict], str]:
    reward_type = "match"
    res_data = []
    for item in tqdm(dataset):
        assert item[0]["from"].strip() in ["human", "Human"], item
        assert item[1]["from"].strip() in ["assistant", "Assistant"], item
        res_data.append({
            "question": item[0]["value"].strip(),
            "answer": item[1]["ground_truth"]["value"].strip(),
        })
    return res_data, reward_type



TYPE_LIST = ["match"]

DATA_INFO_FUNCS = {
    "orz_math_57k_collected.json": parse_custom_json,
    # "PrimeIntellect/synthetic-code-understanding": parse_synthetic_code_understanding,
    "AI-MO/NuminaMath-1.5": parse_numina_math,
    "agentica-org/DeepScaleR-Preview-Dataset": parse_deepscale_r_preview_dataset,
    "allenai/RLVR-GSM": parse_rlvr_gsm,
    "allenai/RLVR-MATH": parse_rlvr_math,
    "SynthLabsAI/Big-Math-RL-Verified": parse_big_math_rl_verified,
}



def obtain_data(data_name: str, save_dir: str = "./tmp"):
    print(f"obtain data {data_name} to {save_dir}")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if data_name.endswith(".json"):
        with open(data_name, "r") as f:
            dataset = json.load(f)
    else:
        dataset = datasets.load_dataset(data_name)
        if "train" in dataset:
            dataset = dataset["train"]
        else:
            print(dataset)
            raise ValueError(f"dataset {data_name} has no train split")
    processed_data, reward_type = DATA_INFO_FUNCS[data_name](dataset)
    assert reward_type in TYPE_LIST
    formated_data = [
        [
            {
                "from": "human",
                "value": item["question"].strip(),
                "metadata": {
                    "source": [data_name],
                    "reward_type": reward_type,
                    "id": item.get("id", f"{data_name}-{i}"),
                    **item.get("metadata", {})
                }
            },
            {
                "from": "assistant",
                "value": item["answer"].strip(),
            }
        ]
        for i, item in enumerate(processed_data)
        if len(item["question"].strip()) > 0 and len(item["answer"].strip()) > 0
    ]

    with open(os.path.join(save_dir, f"obtained_{data_name.replace("/", "__")}.json"), "w") as f:
        json.dump(formated_data, f, indent=2)
    print(f"obtain data {data_name} done!")
    return formated_data


if __name__ == "__main__":
    all_data = []
    question_list = {}
    dup_count = {}
    rubbish_bin = {}
    for data_name in DATA_INFO_FUNCS.keys():
        # input("press anything to continue")
        data = obtain_data(data_name)
        for item in data:
            if len(item[1]["value"].strip()) == 0:
                continue

            if item[0]["value"].strip() in question_list:
                index = question_list[item[0]["value"].strip()]
                if index in rubbish_bin:
                    rubbish_bin[index].append(item)
                    continue
                assert all_data[index][0]["value"].strip() == item[0]["value"].strip(), (all_data[index], item)

                if all_data[index][1]["value"].strip() != item[1]["value"].strip():
                    shorter = all_data[index][1]["value"].strip()\
                        if len(all_data[index][1]["value"].strip()) < len(item[1]["value"].strip())\
                            else item[1]["value"].strip()
                    if shorter.startswith("$") and shorter.endswith("$"):
                        shorter = shorter[1:-1]
                    # longer = all_data[index][1]["value"].strip()\
                    #     if len(all_data[index][1]["value"].strip()) >= len(item[1]["value"].strip())\
                    #         else item[1]["value"].strip()
                    # if longer.startswith("$") and longer.endswith("$"):
                    #     longer = longer[1:-1]

                    if data_name=="orz_math_57k_collected.json" or verify(
                        parse("$"+all_data[index][1]["value"].strip()+"$"),
                        parse("$"+item[1]["value"].strip()+"$"),
                        strict=False,
                    ):  # keep the shorter answer if answers are consistant
                        all_data[index][1]["value"] = shorter
                    else:
                        rubbish_bin[index] = [
                            all_data,
                            item,
                        ]
                        print("---\n", all_data[index], "\n", item)
                all_data[index][0]["metadata"]["source"].append(data_name)
                if data_name not in dup_count:
                    dup_count[data_name] = 0
                dup_count[data_name] += 1
            else:
                question_list[item[0]["value"].strip()] = len(all_data)
                all_data.append(item)
    all_data = [item for i, item in enumerate(all_data) if i not in rubbish_bin.keys()]
    with open("all_data.json", "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"dup: {dup_count}")
    print(f"all data done! ({len(all_data)})")
    # with open("rubbish_bin.json", "w") as f:
    #     json.dump(rubbish_bin, f, indent=2)
    print(f"rubbish bin done! ({len(rubbish_bin)})")
