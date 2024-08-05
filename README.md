# tlcl
tlcl is a simple tool caller for llama.cpp
It currently only supports llama 3.1 models and ipython environment.

## Usage

Example usage:

```python3 ./tlcl.py --url "http://127.0.0.1:8080/completion" --prompt "run a python program checking the python version" --verbose```

Example output:

```
$ python3 ./tlcl.py --url "http://127.0.0.1:8080/completion" --prompt "run a python program checking the python version"
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
requests, ipython.
