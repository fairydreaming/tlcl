# tlcl
tlcl is a simple tool caller for llama.cpp
It currently only supports llama 3.1 models and ipython environment.

## Usage

Example usage:

```python3 ./tlcl.py --url "http://127.0.0.1:8080/completion" --prompt "run a python program checking the python version" --verbose```

Example output:

```
$ python3 ./tlcl.py --url "http://127.0.0.1:8080/completion" --prompt "run a python program checking the python version"
run a python program checking the python version
<|python_tag|>import sys

print("Python version: ", sys.version)<|eom_id|>
Python version:  3.12.4 | packaged by Anaconda, Inc. | (main, Jun 18 2024, 15:12:24) [GCC 11.2.0]

This program will print the version of Python that is currently running.<|eot_id|>
```

## Requirements
requests, ipython.
