def parse_result(txt):
  txt=(txt.replace("."," ").replace(","," ").replace(":"," ")
       .replace("\n"," ").replace("\r"," ").replace("**", " "))
  txt=txt.strip().lower()
  sp=txt.split(" ")
  if sp[-1] in ["satisfiable"]:
    return 1
  elif sp[-1] in ["contradiction"]:
    return 0
  else:
    return None

if __name__ == '__main__':
  print(parse_result("""
contradiction
"""))

def makeprompt(problem):
  clauses=problem[5]
  prefix="Your task is to solve a problem in propositional logic.\n"
  prefix+="You will get a list of statements and have to determine whether the statements form a logical contradiction or not.\n"
  prefix+="If the statements form a contradiction, the last word of your answer should be 'contradiction',\n"
  prefix+="otherwise the last word should be 'satisfiable.\n"

  details="Propositional variables are represent as 'pN' where N is a number. They are either true or false.\n"
  details+="'X or Y' means that X = true or Y = true or both X = Y = true.\n"
  details+="All the given statements are implicitly connected with 'and': they are all claimed to be true.\n"
  
  example="Two examples:\n"
  example+="Example 1. Statements: p1. neg p1 or p2. neg p2. Answer: contradiction.\n"
  example+="Example 2. Statements: p1. p1 or p2. neg p2. Answer: satisfiable.\n"

  statements="Statements:\n"
  for clause in clauses:
    statement=""
    for var in clause:
      if var>0: s="p"+str(var)
      else: s="neg p"+str(0-var)
      if statement: statement+=" or "+s
      else: statement=s
    statement=statement+".\n"
    statements=statements+statement

  final="\nPlease think step by step and answer whether the given statements form a logical contradiction or is satisfiable.\n"  

  prompt=prefix+details+example+statements+final
  return prompt  

  return str(clauses)
