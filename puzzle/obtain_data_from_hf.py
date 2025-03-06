import os
import json
import random
from typing import List, Tuple

import datasets
from tqdm import tqdm


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

def parse_open_thoughts_puzzle(dataset: datasets.Dataset) -> Tuple[List[dict], str]:
    reward_type = "match"
    res_data = []
    for item in tqdm(dataset):
        question = item["question"].strip()
        answer = item["answer"].strip()
        if not answer in ["A", "B", "C", "D", "E"]:
            print(f"skip {question} - {answer}")
            continue
        lines = question.split("\n")
        answer_index_map = { "A": 1, "B": 2, "C": 3, "D": 4, "E": 5 }
        assert all(
            lines[answer_index_map[i]].startswith(f"{i}: ")
            for i in ["A", "B", "C", "D", "E"]
        ), (lines, answer)
        question = lines[0]
        answer = lines[answer_index_map[answer]].strip()[len("A:"):].strip()
        res_data.append({
            "question": question,
            "answer": answer,
        })
    return res_data, reward_type

def parse_maze_reasoning(dataset: datasets.Dataset) -> Tuple[List[dict], str]:
    reward_type = "match"
    res_data = []
    for item in tqdm(dataset):
        res_data.append({
            "question": item["Prompt"].strip(),
            "answer": item["Response"].strip(),
        })
    res_data = random.sample(res_data, 20*1000)
    return res_data, reward_type

def parse_lichess_puzzles(dataset: datasets.Dataset) -> Tuple[List[dict], str]:
    reward_type = "match"
    res_data = []
    for item in tqdm(dataset):
        ctx = item["ctx"].strip()
        prompt = f"""
Standard Algebraic Notationis a concise method of recording chess moves. It uses the following letters to represent pieces: K (King), Q (Queen), R (Rook), B (Bishop), N (Knight), while pawns are not represented by a letter (i.e., omitted). Moves are generally recorded in the format [Piece][Destination], with pawn moves omitting the piece notation and showing only the destination square. The capture of a piece is denoted by "x", formatted as [Piece] x [Destination]; for pawn captures, the starting file must also be specified. When a pawn reaches the eighth rank, it can be promoted to another piece, recorded as [Destination]=[New Piece], with the = sometimes omitted. Castling is written as either kingside castling (O-O) or queenside castling (O-O-O). En passant captures are recorded in the standard capture format as [Starting File] x [Destination] e.p.. Special game conditions are marked with symbols: "+" (check), "#" (checkmate), "=" (stalemate), "½–½" (draw), "1-0" (White wins), "0-1" (Black wins). If two identical pieces can move to the same square, additional notation is needed: different files are distinguished by the file letter, and different ranks by the rank number.
""".strip()
        prompt += f"\n\nHere is a chess puzzle in Standard Algebraic Notation.\n{ctx}"
        prompt += "\n\nDetermine the best move for the side to move."
        res_data.append({
            "question": prompt,
            "answer": item["target"].strip(),
        })
    res_data = random.sample(res_data, 20*1000)
    return res_data, reward_type

TYPE_LIST = ["match"]

DATA_INFO_FUNCS = {
    "trungtvu/open-thoughts-puzzle": parse_open_thoughts_puzzle,
    "homebrewltd/Maze-Reasoning-GRPO-v0.1": parse_maze_reasoning,
    "EleutherAI/lichess-puzzles": parse_lichess_puzzles,
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
        print(f"obtain data {data_name} done! ({len(data)})")
        for item in data:
            if len(item[1]["value"].strip()) == 0 or len(item[0]["value"].strip()) == 0:
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
                    # longer = all_data[index][1]["value"].strip()\
                    #     if len(all_data[index][1]["value"].strip()) >= len(item[1]["value"].strip())\
                    #         else item[1]["value"].strip()
                    # if longer.startswith("$") and longer.endswith("$"):
                    #     longer = longer[1:-1]

                    if all_data[index][1]["value"].strip() == item[1]["value"].strip():
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
