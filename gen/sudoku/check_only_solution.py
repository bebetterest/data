import random
from typing import List
from copy import deepcopy
from datetime import datetime

import json
from tqdm import tqdm


def str2sudoku(s: str) -> List[List[int]]:
    s = s.strip().replace("\n\n", "\n").replace(" ", "")
    return [
        [
            int(c) if c != "." else 0
            for c in row
        ]
        for row in s.split()
    ]


def sudoku2str(sudoku: list) -> str:
    return "\n".join(
        [
            "".join([str(x) if x != 0 else "." for x in row])
            for row in sudoku
        ]
    )


def search_all_solution(
        soduku: List[List[int]],
) -> List[List[List[int]]]:
    rows = [[] for _ in range(9)]
    cols = [[] for _ in range(9)]
    blocks = [[] for _ in range(9)]
    for i in range(9):
        for j in range(9):
            if soduku[i][j] != 0:
                rows[i].append(soduku[i][j])
                cols[j].append(soduku[i][j])
                blocks[i // 3 * 3 + j // 3].append(soduku[i][j])

    def dfs(i, j):
        if i == 9:
            return [deepcopy(soduku)]
        if j == 9:
            return dfs(i + 1, 0)
        if soduku[i][j] != 0:
            return dfs(i, j + 1)
        block_idx = i // 3 * 3 + j // 3

        res = []
        for num in range(1, 10):
            if num in rows[i] or num in cols[j] or num in blocks[block_idx]:
                continue
            rows[i].append(num)
            cols[j].append(num)
            blocks[block_idx].append(num)
            soduku[i][j] = num
            res += dfs(i, j + 1)
            rows[i].pop()
            cols[j].pop()
            blocks[block_idx].pop()
            soduku[i][j] = 0
        return res
    
    return dfs(0, 0)


if __name__ == "__main__":
    with open("sudoku_data_v20250308094513.json") as f:
        data = json.load(f)
    for i, d in enumerate(tqdm(data)):
        sudoku = str2sudoku(d[0]["metadata"]["sudoku"])
        solutions = search_all_solution(sudoku)
        assert len(solutions) == 1
        assert sudoku2str(solutions[0]) == d[1]["value"]
        # print(d[0]["metadata"]["sudoku"])
        # print("---")
        # print(sudoku2str(solutions[0]))
        # print("---")
        # print(d[1]["value"])
        # print("------")
    print("All tests passed!")
