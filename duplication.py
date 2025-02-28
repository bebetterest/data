# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "distilabel",
#     "datasketch",
#     "matplotlib",
#     "jsonlines",
#     "nltk",
#     "bs4",
# ]
# ///
import json
from typing import Union

# import nltk
# nltk.download('punkt_tab')
import jsonlines
from matplotlib import pyplot as plt
from distilabel.pipeline import Pipeline
from distilabel.steps import LoadDataFromDicts, MinHashDedup

        
def main_proc(
        load_json_path: str="all_data.json",
        threshold: float=0.9,
):
    with open(load_json_path, "r") as f:
        all_data = json.load(f)
    
    warped_data = [
        {
            "text": item[0]["value"],
            "idx": idx,
        } for idx, item in enumerate(all_data)
    ]

    with Pipeline("simple") as pipeline:
        loaded_data = LoadDataFromDicts(
            data=warped_data,
            batch_size=1024,
        )

        minhash_dedup = MinHashDedup(
            tokenizer="words",
            threshold=threshold,      # lower values will increase the number of duplicates
            storage="dict",
        )

        loaded_data >> minhash_dedup

    distiset = pipeline.run(use_cache=False)
    tmp = distiset["default"]["train"]
    print("Number of original data:", len(all_data))
    tmp = tmp.filter(lambda x: x["keep_row_after_minhash_filtering"])
    print("Number of unique data:", len(tmp))

    unwarped_data = [
        all_data[item["idx"]] for item in tmp
    ]
    return unwarped_data, len(all_data), len(tmp)


if __name__ == "__main__":
    # metric = []
    # for threshold in [0.98, 0.95]:
    #     unwarped_data, before_num, after_num = main_proc(
    #         load_json_path="all_data.json",
    #         threshold=threshold,
    #     )
    #     metric.append({
    #         "threshold": threshold,
    #         "before_num": before_num,
    #         "after_num": after_num,
    #         "delta_num": before_num - after_num,
    #     })
    #     with jsonlines.open(f"minhash_metric.jsonl", "a") as f:
    #         f.write({
    #             "threshold": threshold,
    #             "before_num": before_num,
    #             "after_num": after_num,
    #             "delta_num": before_num - after_num,
    #         })

    # fig = plt.figure()
    # plt.plot([item["threshold"] for item in metric], [item["delta_num"] for item in metric])
    # plt.xlabel("threshold")
    # plt.ylabel("delta_num")
    # plt.savefig("delta_num_vs_threshold.png")
    # plt.show()

    threshold = 0.8
    unwarped_data, before_num, after_num = main_proc(threshold=threshold)
    print(f"threshold: {threshold}, before_num: {before_num}, after_num: {after_num}")
    with open(f"all_data_after_minhash.json", "w") as f:
        json.dump(unwarped_data, f, indent=2)
