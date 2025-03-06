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

        
def dup_by_minhash(
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
            batch_size=128,
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
