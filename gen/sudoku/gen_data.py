import random
from typing import List
from copy import deepcopy
from datetime import datetime

import json
from tqdm import tqdm


def is_valid_sudoku(sudoku, finish_flag=False):
    if finish_flag:
        tmp_list = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    else:
        tmp_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    def check(lst):
        lst = [x for x in lst if x != 0]
        return len(lst) == len(set(lst))

    if len(sudoku) != 9 or any([len(row) != 9 for row in sudoku]):
        return False
    if any([
        sudoku[i][j] not in tmp_list
        for i in range(9) for j in range(9)
    ]):
        return False

    for i in range(9):
        if not check(sudoku[i]):
            return False
        if not check([sudoku[j][i] for j in range(9)]):
            return False
    for i in range(3):
        for j in range(3):
            if not check([
                sudoku[m][n]
                for m in range(3*i, 3*i+3)
                for n in range(3*j, 3*j+3)
            ]):
                return False
    return True


def get_one_full_sudoku(
        sudoku=None, rows=None, cols=None, blocks=None,
):
    if sudoku is None:
        sudoku = [[0 for _ in range(9)] for __ in range(9)]
    if rows is None:
        rows = [[] for _ in range(9)]
    if cols is None:
        cols = [[] for _ in range(9)]
    if blocks is None:
        blocks = [[] for _ in range(9)]

    for i in range(9):
        for j in range(9):
            if sudoku[i][j] != 0:
                continue
            block_idx = i // 3 * 3 + j // 3

            selectable_nums = [
                x for x in range(1, 9+1)
                if x not in rows[i]\
                    and x not in cols[j]\
                        and x not in blocks[block_idx]
            ]
            if len(selectable_nums) == 0:
                return sudoku, False
            random.shuffle(selectable_nums)
            for num in selectable_nums:
                sudoku[i][j] = num
                rows[i].append(num)
                cols[j].append(num)
                blocks[block_idx].append(num)
                res_sudoku, flag = get_one_full_sudoku(
                    sudoku, rows, cols, blocks
                )
                # return res_sudoku, flag
                if flag:
                    return res_sudoku, True
                sudoku[i][j] = 0
                rows[i].remove(num)
                cols[j].remove(num)
                blocks[block_idx].remove(num)
            if is_valid_sudoku(sudoku, finish_flag=True):
                return sudoku, True
            else:
                return sudoku, False
    if is_valid_sudoku(sudoku, finish_flag=True):
        return sudoku, True
    else:
        return sudoku, False


def count_solution_num(sudoku, total_sum, sum_lim=1):
    rows = [[] for _ in range(9)]
    cols = [[] for _ in range(9)]
    blocks = [[] for _ in range(9)]
    for i in range(9):
        for j in range(9):
            if sudoku[i][j] != 0:
                num = sudoku[i][j]
                if num == 0:
                    continue
                block_idx = i // 3 * 3 + j // 3
                rows[i].append(num)
                cols[j].append(num)
                blocks[block_idx].append(num)
    
    for i in range(9):
        for j in range(9):
            if sudoku[i][j] != 0:
                continue

            block_idx = i // 3 * 3 + j // 3
            selectable_nums = [
                x for x in range(1, 9+1)
                if x not in rows[i]\
                    and x not in cols[j]\
                        and x not in blocks[block_idx]
            ]
            # print("selectable_nums", selectable_nums)
            if len(selectable_nums) == 0:
                return total_sum
            for num in selectable_nums:
                sudoku[i][j] = num
                if is_valid_sudoku(sudoku, finish_flag=True):
                    # print("here is a solution")
                    # print(sudoku2str(sudoku))
                    total_sum += 1
                else:
                    total_sum = count_solution_num(sudoku, total_sum, sum_lim)
                sudoku[i][j] = 0
                # if total_sum > sum_lim:
                #     return total_sum
            return total_sum
    return total_sum


def blank_sudoku(full_sudoku, blank_num):
    res = deepcopy(full_sudoku)

    selectable_pos = [
        (i, j) for i in range(9) for j in range(9)
        if res[i][j] != 0
    ]
    random.shuffle(selectable_pos)
    for i,j in selectable_pos:
        tmp = res[i][j]
        res[i][j] = 0
        blank_num -= 1
        solution_num = count_solution_num(deepcopy(res), 0)
        assert solution_num > 0, sudoku2str(res)
        if solution_num > 1:
            res[i][j] = tmp
            blank_num += 1
            continue
        if blank_num == 0:
            return res, True
        ans_sudoku, flag = blank_sudoku(res, blank_num)
        if flag:
            return ans_sudoku, True
        res[i][j] = tmp
        blank_num += 1
    return res, False


def sudoku2str(sudoku: list) -> str:
    return "\n".join(
        [
            "".join([str(x) if x != 0 else "." for x in row])
            for row in sudoku
        ]
    )


def sudoku_single_gen(
        blank_num: int,
        num: int,
        version_str: str,
):
    data: List[list] = []

    fail_num = 0
    td = tqdm(total=num, desc=f"blank_num={blank_num}, num={num}")
    while len(data) < num:
        td.set_postfix(fail_num=fail_num)
        full_sudoku, flag = get_one_full_sudoku()
        if not flag:
            fail_num += 1
            continue
        blanked_sudoku, flag = blank_sudoku(full_sudoku, blank_num)
        if not flag:
            fail_num += 1
            continue
        prompt = 'The Sudoku puzzle uses a 9*9 grid, which is divided into 9 non-overlapping 3*3 subgrids (each subgrid consists of 3 rows and 3 columns, totaling 9 cells). The game follows these rules: each row, each column, and each 3*3 subgrid must contain the numbers 1-9 without repetition. At the start of the game, some cells are pre-filled with numbers (which cannot be changed), while empty cells are represented by ".".'
        prompt += f"Here is a sudoku puzzle:\n{sudoku2str(blanked_sudoku)}"
        prompt += "\nYou need to deduce the solution based on the given numbers and output the complete 9*9 grid."
        data.append(
            [
                {
                    "from": "human",
                    "value": prompt,
                    "metadata": {
                        "sudoku": sudoku2str(blanked_sudoku),
                        "source": ["sudoku_single_gen"],
                        "reward_type": "match",
                        "id": f"{version_str}_{len(data)}",
                        "blank_num": blank_num,
                    }
                },
                {
                    "from": "assistant",
                    "value": sudoku2str(full_sudoku),
                }
            ]
        )
        td.update(1)
    td.close()
    return data


def sudoku_mix_gen(
        config: list,
        version_str: str,
):
    data = []
    for cfg_item in config:
        data.extend(
            sudoku_single_gen(
                cfg_item["blank_num"],
                cfg_item["num"],
                version_str,
            )
        )
    return data


if __name__ == "__main__":
    config = [
        {"blank_num": 5, "num": 100},
        {"blank_num": 10, "num": 100},
        {"blank_num": 15, "num": 100},
        {"blank_num": 40, "num": 100},
    ]
    version_str = datetime.now().strftime("%Y%m%d%H%M%S")
    data = sudoku_mix_gen(config, version_str)
    with open(f"sudoku_data_v{version_str}.json", "w") as f:
        json.dump(data, f, indent=4)
