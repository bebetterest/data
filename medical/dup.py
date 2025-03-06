import os
import sys
path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
print(path)
sys.path.append(path)

import jsonlines

from duplication import dup_by_minhash


if __name__ == "__main__":
    metric = []
    for idx in range(48,100,10)[::-1]:
        threshold = idx / 100
        print(f"threshold: {threshold}")
        unwarped_data, before_num, after_num = dup_by_minhash(
            load_json_path="all_data.json",
            threshold=threshold,
        )
        metric.append({
            "threshold": threshold,
            "before_num": before_num,
            "after_num": after_num,
            "delta_num": before_num - after_num,
        })
        with jsonlines.open(f"minhash_metric.jsonl", "a") as f:
            f.write({
                "threshold": threshold,
                "before_num": before_num,
                "after_num": after_num,
                "delta_num": before_num - after_num,
            })

    # threshold = 0.93
    # unwarped_data, before_num, after_num = dup_by_minhash(threshold=threshold)
    # print(f"threshold: {threshold}, before_num: {before_num}, after_num: {after_num}")
    # with open(f"all_data_after_minhash.json", "w") as f:
    #     json.dump(unwarped_data, f, indent=2)
