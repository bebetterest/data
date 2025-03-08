import random
from typing import List
from datetime import datetime

import json
from tqdm import tqdm


def multiplication_single_gen(
        k1: int, # number of digits
        k2: int,
        num: int, # number of data
        version_str: str, # version string
        ans_k_limit: int = 10000, # number of digits of answer
):
    data: List[list] = []

    td = tqdm(total=num, desc=f"k1={k1}, k2={k2}, ans_lim={ans_k_limit}, num={num}")
    while len(data) < num:
        a = random.randint(10 ** (k1 - 1), 10 ** k1 - 1)
        b = random.randint(10 ** (k2 - 1), 10 ** k2 - 1)
        ans = a * b
        if len(str(ans)) > ans_k_limit:
            print(f"k1={k1}, k2={k2}, ans_lim={ans_k_limit}, num={num}. ans = {ans} is too large")
            continue

        data.append(
            [
                {
                    "from": "human",
                    "value": f"a = {str(a)}, b = {str(b)}, Determine the value of a * b",
                    "metadata": {
                        "a": a,
                        "b": b,
                        "source": ["multiplication_single_gen"],
                        "reward_type": "match",
                        "id": f"{version_str}_{len(data)}"
                    }
                },
                {
                    "from": "assistant",
                    "value": str(ans),
                }
            ]
        )
        td.update(1)
    td.close()

    return data


def multiplication_mix_gen(
        config: list,
        version_str: str,
):
    data = []
    for c in config:
        data += multiplication_single_gen(
            k1=c["k1"],
            k2=c["k2"],
            num=c["num"],
            version_str=version_str,
        )
    return data
    

if __name__ == "__main__":
    config = [
        {"k1": i, "k2": i, "num": 1000}
        for i in range(3, 14 + 1) # 3 ~ 14 digits
    ]
    datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
    version_str = f"v{datetime_str}"
    data = multiplication_mix_gen(config, version_str)
    with open(f"multiplication_data_{version_str}.json", "w") as f:
        json.dump(data, f, indent=4)
