import sys
import json

# ==== import other source files ====
from providers.provider_manager import generate_completion


secrets_file="secrets.js"

temperature=0
seed=1234
max_tokens=2000

outfile="gptresults.js" # the results will be appended to this file

debug=False # set to True to get a printout of data, call and result

helptext="""Usage example: ./problem_solver.py --provider <provider_name> --model <model_name> <problem_file.js> [max_rows]
Example: ./problem_solver.py --provider openai --model gpt-4o-2024-11-20 someprop.js 10
Arguments:
  --provider : The LLM provider to use (e.g., 'openai', 'anthropic'). Required.
  --model    : The specific model name for the provider. Required.
  <problem_file.js>: Path to the problem file. Required.
  [max_rows] : Optional maximum number of rows to process from the problem file.
"""

def main():
  if len(sys.argv) < 5: # Check for minimum required arguments
    print("Error: Insufficient arguments provided.")
    print(helptext)
    return

  provider = None
  model_name = None
  problemfile = None
  max_rows = 1000000000 # Default large number

  # --- Updated Argument Parsing ---
  args = sys.argv[1:]
  i = 0
  while i < len(args):
      arg = args[i]
      if arg == "--provider":
          if i + 1 < len(args):
              provider = args[i+1].lower()
              i += 1
          else:
              show_error("--provider requires a value")
      elif arg == "--model":
          if i + 1 < len(args):
              model_name = args[i+1]
              i += 1
          else:
              show_error("--model requires a value")
      elif arg.strip().isnumeric():
           # Assuming the number is max_rows if it's not associated with a flag
           # This might need refinement if other numeric args are added
           max_rows = int(arg.strip())
      elif problemfile is None and ".js" in arg or ".json" in arg: # Basic check for problem file
          problemfile = arg
      else:
          # If it's not a recognized flag or the problem file, treat as potential problem file path if still None
          if problemfile is None and not arg.startswith("--"):
             problemfile = arg
          # else: ignore unrecognized arguments or handle as error
      i += 1

  if not provider:
      show_error("Missing required argument: --provider")
  if not model_name:
      show_error("Missing required argument: --model")
  if not problemfile:
     show_error("Problem file not specified or identified.")
  # --- End Updated Argument Parsing ---

  # read problemfile rows line by line, ignoring the first one
  try:
    f=open(problemfile, "r")
  except Exception as e:
    show_error(f"Could not read problem file {problemfile}: {e}")
  problems=[]
  rowcount=0
  try: # Added try-except around file reading loop
      while True:
          row=f.readline()
          if not row: break # End of file
          row = row.strip()
          if not row: continue # Skip empty lines

          rowcount+=1
          if rowcount < 2: continue # Skip header row
          if rowcount-1 > max_rows: break # Respect max_rows

          parsedrow=json.loads(row)
          problems.append(parsedrow)
  except json.JSONDecodeError as e:
      show_error(f"Error parsing JSON on line {rowcount} in {problemfile}: {e}")
  except Exception as e:
      show_error(f"Error reading line {rowcount} from {problemfile}: {e}")
  finally:
      f.close()

  # open output file
  try:
    of=open(outfile, "w") # Using "w" to overwrite results for each run, consider "a" if appending is desired
  except Exception as e:
    show_error(f"Could not open output file {outfile}: {e}")

  # run problems read, one by one
  count=0
  processed=0
  correct=0
  correctsat=0
  correctunsat=0
  for problem in problems:
    count+=1
    #if count<249: continue # Example conditional skip
    #if count>285: break # Example conditional break
    sysprompt=None # System prompts can still be defined if needed, or passed via args
    # Choose which prompt creation function to use
    # prompt = makeprompt(problem) # Use the more compact prompt representation
    prompt = makeprompt_v1(problem) # Use the verbose "is true/false" representation

    debug_print("Provider:", provider)
    debug_print("Model:", model_name)
    #debug_print("sysprompt:",sysprompt) # Uncomment if sysprompt is used
    debug_print("prompt:",prompt)

    # --- Updated call to use new function name and arguments ---
    try:
        result = get_llm_response(provider, model_name, prompt, sysprompt, max_tokens)
        processed += 1
    except NotImplementedError as e:
        show_error(f"Provider '{provider}' is not implemented in provider_manager: {e}")
    except ValueError as e: # Catch unknown provider error from manager
        show_error(f"Error with provider '{provider}': {e}")
    except Exception as e: # Catch other potential errors from API calls
        show_error(f"Error during LLM call for problem {count}: {e}")
        # Decide if you want to continue to the next problem or exit
        continue # Example: skip this problem and continue

    # --- End Updated call ---

    #print("result:",result)
    parsedres=parse_result(result)
    iscorrect=None
    if parsedres==problem[4]: # Index 4 should be 'issatisfiable' (0 or 1)
      iscorrect=True
      correct+=1
      if problem[4]: correctsat+=1
      else: correctunsat+=1
    else: # Handle case where parse_result returns 2 (unknown)
        iscorrect = False # Treat unknown as incorrect for stats, or handle differently

    cleanres=result.replace("\\n"," ").replace("\\r"," ") # Keep basic cleaning
    newdata=[parsedres,cleanres]
    outdata=problem+newdata
    try:
        of.write(json.dumps(outdata)+"\\n")
        of.flush() # Ensure data is written immediately
    except Exception as e:
        print(f"Warning: Could not write result for problem {count} to {outfile}: {e}")

    if iscorrect is True: print(f"Problem {count}: Correct")
    elif iscorrect is False: print(f"Problem {count}: Wrong (Expected: {problem[4]}, Got: {parsedres})")
    # print(outdata) # Optionally print full data for each problem

  of.close()
  print("\n--- Summary ---")
  print(f"Processed problems: {processed} (out of {count} attempted)")
  # Calculate accuracy safely, avoiding division by zero and formatting issues within f-string
  accuracy_percentage = (correct / processed * 100) if processed > 0 else 0
  print(f"Correct answers altogether: {correct} ({accuracy_percentage:.2f}% accuracy)")
  # Assuming half are satisfiable and half unsatisfiable if processed is even and reflects total problems intended
  total_satisfiable = sum(1 for p in problems[:processed] if p[4] == 1)
  total_unsatisfiable = processed - total_satisfiable
  print(f"Correct satisfiable: {correctsat} (out of {total_satisfiable})")
  print(f"Correct unsatisfiable: {correctunsat} (out of {total_unsatisfiable})")
  print(f"Results saved to: {outfile}")


def parse_result(txt):
  # Simplified cleaning, focusing on the last word
  txt = txt.strip().lower()
  # Remove trailing punctuation that might interfere
  if txt.endswith(('.', '!', '?')):
      txt = txt[:-1]

  # Split by whitespace and check the last part
  sp = txt.split()
  if not sp: return 2 # Handle empty response as unknown

  last_word = sp[-1]

  if last_word in ["contradiction","contradictory","false","wrong", "unsatisfiable"]:
    return 0
  elif last_word in ["satisfiable","true","satisfied", "consistent"]:
    return 1
  # Consider adding handling for explicit "unknown" or "uncertain" if models might return that
  # elif last_word in ["unknown", "uncertain"]:
  #   return 2 # Or map to 1 depending on desired behavior
  else:
    # If the last word isn't recognized, maybe check the second to last?
    # Or just return unknown.
    print(f"Warning: Unrecognized last word in response: '{last_word}'. Full text: '{txt}'")
    return 2 # Default to unknown/error


# ========= prompt creation =======

def makeprompt(problem):
  clauses=problem[5]
  prefix="Your task is to solve a problem in propositional logic.\\n"
  prefix+="You will get a list of statements and have to determine whether the statements form a logical contradiction or not.\\n"
  prefix+="If the statements form a contradiction, the last word of your answer should be 'contradiction',\\n"
  prefix+="otherwise the last word should be either 'satisfiable' or 'unknown'.\\n"

  details="Propositional variables are represent as 'pN' where N is a number. They are either true or false.\\n"
  details+="pN means that pN is true. not(pN) means that pN is false.\\n"
  details+="'X or Y' means that X is true or Y is true or both X and Y are true.\\n"
  details+="All the given statements are implicitly connected with 'and': they are all claimed to be true.\\n"
  
  example="Two examples:\\n"
  example+="Example 1. Statements: p1. not(p1) or p2. not(p2). Answer: contradiction.\\n"
  example+="Example 2. Statements: p1. p1 or p2. not(p2). Answer: satisfiable.\\n"

  statements="Statements:\\n"
  for clause in clauses:
    statement=""
    for var in clause:
      if var>0: s="p"+str(var)
      else: s="not("+"p"+str(0-var)+")"
      if statement: statement+=" or "+s
      else: statement=s
    statement=statement+".\\n"
    statements=statements+statement

  final="\\nPlease think step by step and answer whether the given statements form a logical contradiction or is satisfiable.\\n"  

  prompt=prefix+details+example+statements+final
  return prompt  

# makeprompt_v1 is the old method for exp1

def makeprompt_v1(problem):
  clauses=problem[5]
  prefix="Your task is to solve a problem in propositional logic.\\n"
  prefix+="You will get a list of statements and have to determine whether the statements form a logical contradiction or not.\\n"
  prefix+="If the statements form a contradiction, the last word of your answer should be 'contradiction',\\n"
  prefix+="otherwise the last word should be either 'satisfiable' or 'unknown'.\\n"

  details="Propositional variables are represent as 'pN' where N is a number. They are either true or false.\\n"
  details+="'X or Y' means that X is true or Y is true or both X and Y are true.\\n"
  details+="All the given statements are implicitly connected with 'and': they are all claimed to be true.\\n"
  
  example="Two examples:\\n"
  example+="Example 1. Statements: p1 is true. p1 is false or p2 is true. p2 is false. Answer: contradiction.\\n"
  example+="Example 2. Statements: p1 is true. p1 is true or p2 is true. p2 is false. Answer: satisfiable.\\n"

  statements="Statements:\\n"
  for clause in clauses:
    statement=""
    for var in clause:
      if var>0: s="p"+str(var)+" is true"
      else: s="p"+str(0-var)+" is false"
      if statement: statement+=" or "+s
      else: statement=s
    statement=statement+".\\n"
    statements=statements+statement

  final="\\nPlease think step by step and answer whether the given statements form a logical contradiction or is satisfiable.\\n"  

  prompt=prefix+details+example+statements+final
  return prompt  



  

  return str(clauses)

# --- Renamed function and updated signature ---
def get_llm_response(provider, model_name, sentences, sysprompt, max_tokens):
    # Compose the complete prompt by combining the optional system prompt and the user text.
    # This prompt composition logic stays here as it's part of how the problem is presented.
    if sysprompt:
        complete_prompt = sysprompt + "\\n" + sentences
    else:
        complete_prompt = sentences

    debug_print("Generated prompt for LLM:", complete_prompt)

    # Delegate the API call to the provider manager using the specified provider and model_name
    # Pass relevant LLM parameters kwargs
    result = generate_completion(
        provider,
        complete_prompt,
        model=model_name,
        max_tokens=max_tokens,
        temperature=temperature,
        seed=seed
        # Add any other parameters needed by generate_completion as kwargs
    )
    return result
# --- End Renamed function ---

def debug_print(a,b):
  if debug:
    # Ensure b is converted to string for printing, especially if it could be complex objects
    print(f"{a} {str(b)}")

def show_error(a):
  print(f"Error: {a}")
  exit(1) # Use non-zero exit code for errors

if __name__ == "__main__":
  main()