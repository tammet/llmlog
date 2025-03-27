# llmlog

** Experiments with LLMs and logic: what can LLMs solve? **

## Code and files

`makeproblems.py` prints out a configurable number of different propositional logic problem distributions along with their proofs or satisfying valuations.
The global configuration variables are at the beginning of the code. The first printed line describes the format of following lines.
Each following line is one propositional problem along with the metainformation and a proof or a satisfying valuation, as a json / python nested list of integers.
The meaning of the list elements, as indicated on the first line:

    ["id","maxvarnr","maxlen","mustbehorn","issatisfiable","problem", 
    "proof_of_inconsistency_or_satisfying_valuation","units_derived_by_horn_clauses"]

* Here "maxvarnr","maxlen","mustbehorn","issatisfiable" indicate the concrete distribution. 
* Problems are represented as clauses, each clause being a list of positive/negative integers. 
* A proof is a list of input and derived clauses in the format 
["clause_number_in_proof","parent_clause_numbers","derived_clause"]. 
* A valuation is a list of positive/negative integers satisfying the problem.
* The "units_derived_by_horn_clauses" is a list of integers representing units derivable by horn clauses in a linear manner. Zero at the end signifies that a a contradiction was derived.

The outer loop of distribution generation is the maximal number of variables allowed (from 3 to 15), followed by the maximal length of a clause (2,3 or 4), followed by horn or not (1 or 0). Inside a distribution the provable/satisfiable clauses are interleaved, with exactly the same number of provable and satisfiable clauses.

`someprop.js` is an example file created by `makeproblems.py`, with 10 provable and 10 satisfiable problems for each distribution.

`gpt.py` is for trying out prompts over the GPT API from the command line. Run without arguments to get a help text.

`askllm.py` is for GPT-solving the problems created by `makeproblems.py`. It reads the file row by row, makes a prompt and asks GPT API.
Run without arguments to get a help text. The output is both printed and written to a file `gptresults.js` row-by-row as json lists. Each list
contains the original full input problem along with metainfo and proofs/valuations, to which is appended the parsed answer, either 0 (GPT claims contradiction) or 1 (GPT claims satisfiable) and finally the whole textual answer given by LLM.

`analyze.py` is for creating statistics about one askllm.py output.

## Subfolders and separate experiments 

The *exp* subfolders contain code and data for specific separate experiments. They do typically have their own README.

These exp folders are all use the problem file `problems_dist20_v1.js`:

* exp1 : base experiment with GPT-4o and 800 problems
* exp2 : a more compact representation than used in exp1: seems slightly better
* exp3 : just 200 first horn clauses only, asking for a linear p1, p2, ... etc CoT output with derived variables printed out one by one
* exp4 : just 200 first horn clauses only, asking for a linear p1 [parents], p2 [parents], ... etc CoT output with concrete derivation steps