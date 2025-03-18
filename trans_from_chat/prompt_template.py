JUDGE_PROMPT_TEMPLATE = """
You are an expert in question selection. Please evaluate the given question based on the following criteria:
**The answer should be convertible into a fill-in-the-blank format, and the answer should be verifiable through matching (e.g., a unique phrase, number, etc.).**
Solving the question should require logical reasoning.
The answer derived from the question should be unique.
The question should not be in the form of "Which of the following is correct?" or "Which of the following is incorrect?" where multiple answers could be valid.
Please analyze the question and write your judge in the last line.

If you believe the question meets the criteria, output:
<judge>pass

If you believe the question does not meet the criteria, output:
<judge>fail



Example1:
Question:
Which statement about antigens is INCORRECT:\nA. Is foreign to the body\nB. They cannot by themselves induce antibodies formation.\nC. Have high molecular weight.\nD. Possess some degree of complexity.
Answer:
B
Analysis and judge:
The question is in the form of "Which of the following is incorrect?" where not all information is included in the question. This question cannot translate into a fill-in-the-blank format. Therefore, the question fails the criteria.
<judge>fail



Input:
Question:
{question}

Answer:
{answer}

Analysis and judge:
""".strip()


REWRITE_PROMPT_TEMPLATE = """
You are an expert in creating questions. You need to modify the questions and answers to meet the following standards:
Convert the entire question into one fill-in-the-blank format. If there are multiple questions, just keep the hardest one.
The answer must be directly matchable through string comparison (e.g., numbers, very short phrases, etc.).
The answer derived from the question should be unique.
The question and answer should be clear and complete.
If the question and answer already meet the standards, output them as they are.

Please rewrite your revised question and answer, as shown below:
<question> your new question
<answer> your new answer


Example1:
Question:
A small power station supplies 2000 incandescent lamps connected in parallel. Each lamp requires 110 V and has a resistance of 220 Ω. (a) Find the total current supplied by the station. (b) Find the total power dissipated by the 2000 lamps.
Answer:
(a) For each lamp, apply Ohm’s law. I = V/R = 110/220 = 0.5 A per lamp. For lamps in parallel, the individual currents add: I = 2000I = 2000(0.5) = 1000 A (total current) (b) R_i = V/I = 110/1000 = 0.11 Ω for the lamps. P_t = I^2R_i = (1000^2)(0.11) = 1.1 × 10^5 W = 110 kW.
Rewrite:
<question> A small power station supplies 2000 incandescent lamps connected in parallel. Each lamp requires 110 V and has a resistance of 220 Ω. Find the total current supplied by the station.
<answer> 1000 A



Input:
Question:
{question}

Answer:
{answer}


Rewrite:
""".strip()


def judge_parser(res: str) -> [dict, bool]:
    if "<judge>" in res:
        res = res.split("<judge>")[-1].split("\n")[0].strip().lower()
        if res.startswith("pass"):
            return {"pass": True}, True
        elif res.startswith("fail"):
            return {"pass": False}, True
        else:
            return {"pass": False}, False
    else:
        return {"pass": False}, False
    

def rewrite_parser(res: str) -> [dict, bool]:
    assert "<question>" in res and "<answer>" in res
    question = res.split("<question>")[-1].split("<answer>")[0].strip()
    answer = res.split("<answer>")[-1].strip()
    assert len(question) > 0 and len(answer) > 0
    return {"question": question, "answer": answer}, True
