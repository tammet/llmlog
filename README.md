# llmlog
Experiments with LLMs and logic: what can LLMs solve?

`makeproblems.py` prints out a configurable number of different propositional logic problem distributions along with their proofs or satisfying valuations.
The global configuration variables are at the beginning of the code. The first printed line describes the format of following lines.
Each following line is one propositional problem along with the metainformation and a proof or a satisfying valuation, as a json / python nested list of integers.
The meaning of the list elements, as indicated on the first line:
* ["id","maxvarnr","maxlen","mustbehorn","issatisfiable","problem", "proof_of_inconsistency_or_satisfying_valuation","units_derived_by_horn_clauses"]
Here "maxvarnr","maxlen","mustbehorn","issatisfiable" indicate the concrete distribution. 
* Problems are represented as clauses, each clause being a list of positive/negative integers. 
* A proof is a list of input and derived clauses in the format 
["clause_number_in_proof","parent_clause_numbers","derived_clause"]. 
* A valuation is a list of positive/negative integers satisfying the problem.
* The "units_derived_by_horn_clauses" is a list of integers representing units derivable by horn clauses in a linear manner.

The outer loop of distribution generation is the maximal number of variables allowed (from 3 to 15), followed by the maximal length of a clause (2,3 or 4), followed by horn or not (1 or 0). Inside a distribution the provable/satisfiable clauses are interleaved, with exactly the same number of provable and satisfiable clauses.

`someprop.js` is an example file created by `makeproblems.py`, with 10 provable and 10 satisfiable problems for each distribution.

