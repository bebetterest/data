# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "matplotlib",
# ]
# ///
import json

from matplotlib import pyplot as plt


def show_source_distribution(data):
    source_count = {}
    for item in data:
        for source in item[0]["metadata"]["source"]:
            tmp = source[-5:]  # do not consider overlap for simplicity
            if tmp not in source_count:
                source_count[tmp] = 0
            source_count[tmp] += 1
    fig = plt.figure()
    plt.bar(source_count.keys(), source_count.values())
    plt.xlabel("source")
    plt.ylabel("count")
    plt.savefig("source_distribution.png")
    plt.show()


if __name__ == "__main__":
    with open("all_data_after_minhash.json") as fp:
        data = json.load(fp)
        print("Number of unique data:", len(data))
        for idx, item in enumerate(data[::-1]):
            print(idx)
            print(json.dumps(item, indent=2))
            q = input("Press q to quit, anything else to continue: ")
            if q == "q":
                break
        
        show_source_distribution(data)