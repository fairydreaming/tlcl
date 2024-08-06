# tlcl
`tlcl.py` is a simple script for testing tool calling capabilities of Llama 3.1 models running on llama.cpp server.

The script checks if the model has invoked the tool by looking for `<|python_tag|>` and `<|eom_id|>` tokens in the generated tokens.
When the script finds these tokens, it extracts the text between them and runs it as a Python program in the IPython environment.
Text outputted during the program execution is passed back to the model by using the `ipython` role.
Finally, the model generates its response based on the tool call and the tool text output.

Read https://llama.meta.com/docs/model-cards-and-prompt-formats/llama3_1/ for more details.

## Usage

1. Run Llama 3.1 model on `llama-server`. Make sure to add `--special` option.
2. Run `tlcl.py`. Use `--help` to list available options. 

Example usage:

```
python3 tlcl.py --url "http://127.0.0.1:8080/completion" --prompt "run a python program checking the python version" --verbose
```

Example output:

```
$ python3 tlcl.py --url "http://127.0.0.1:8080/completion" --prompt "run a python program checking the python version"
################################ role: system     ################################
<|start_header_id|>system<|end_header_id|>

Environment: ipython

# Tool Instructions
- You have access to the stateful ipython environment
- After executing the python program summarize its output for the user
<|eot_id|>
################################ role: user       ################################
<|start_header_id|>user<|end_header_id|>

run a python program checking the python version<|eot_id|>
################################ role: assistant  ################################
<|start_header_id|>assistant<|end_header_id|>

<|python_tag|>import sys

print("Python version: ", sys.version)<|eom_id|>
################################ role: ipython    ################################
<|start_header_id|>ipython<|end_header_id|>

Python version:  3.12.4 | packaged by Anaconda, Inc. | (main, Jun 18 2024, 15:12:24) [GCC 11.2.0]
<|eot_id|>
################################ role: assistant  ################################
<|start_header_id|>assistant<|end_header_id|>

The Python version is 3.12.4.<|eot_id|>
```

## Requirements
tlcl uses the following Python modules:
* requests
* ipython
