def verify_chemistry_qa(
        answer, ground_truth, question=None
) -> bool:
    answer = answer.replace(" ", "").strip()
    ground_truth = ground_truth.replace(" ", "").strip()

    if "->" in ground_truth: # allow different order of elements in each side
        assert ground_truth.count("->") == 1, (ground_truth, question)
        if answer.count("->") != 1 or not "->" in answer:
            return False
        answer_left, answer_right = answer.split("->")
        ground_truth_left, ground_truth_right = ground_truth.split("->")

        # check left
        answer_left_list = [
            x.strip() for x in answer_left.split("+")
        ]
        ground_truth_left_list = [
            x.strip() for x in ground_truth_left.split("+")
        ]
        left_wrong = False
        for tmp in ground_truth_left_list:
            if tmp in answer_left_list:
                answer_left_list.remove(tmp)
            else:
                left_wrong = True
                break
        if left_wrong == False and len(answer_left_list) != 0:
            left_wrong = True
        if left_wrong:
            return False
    
        # check right
        answer_right_list = [
            x.strip() for x in answer_right.split("+")
        ]
        ground_truth_right_list = [
            x.strip() for x in ground_truth_right.split("+")
        ]
        right_wrong = False
        for tmp in ground_truth_right_list:
            if tmp in answer_right_list:
                answer_right_list.remove(tmp)
            else:
                right_wrong = True
                break
        if right_wrong == False and len(answer_right_list) != 0:
            right_wrong = True
        if right_wrong:
            return False

        return True
    else: # just match
        ground_truth = ground_truth.replace(" ", "").strip()
        answer = answer.replace(" ", "").strip()
        return ground_truth == answer


if __name__ == "__main__":
    from tqdm import tqdm
    from datasets import load_dataset

    ds = load_dataset("avaliev/ChemistryQA")["train"]
    for item in tqdm(ds):
        if item["answer"].replace(" ", "").count("->") > 1: # filter out multi-step reaction
            continue
        assert verify_chemistry_qa(item["answer"], item["answer"], item["question"]), item
    print("all pass")
