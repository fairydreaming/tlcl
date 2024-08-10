# tlcl
`tlcl.py` is a simple script for testing tool calling capabilities of Llama 3.1 models running on llama.cpp server.

The script checks if the model has invoked the tool by looking for `<|python_tag|>` and `<|eom_id|>` tokens in the generated tokens.
When the script finds these tokens, it extracts the text between them and runs it as a Python program in the IPython environment.
Text outputted during the program execution is passed back to the model by using the `ipython` role.
Finally, the model generates its response based on the tool call and the tool text output.

Read https://llama.meta.com/docs/model-cards-and-prompt-formats/llama3_1/ for more details.

## Features

Currently supported tools are:
* code interpreter
* brave search

## Usage

1. Run Llama 3.1 model on `llama-server`. Make sure to add `--special` option.
2. Set BRAVE_API_KEY environment variable to your Brave API key if you want to use brave search tool.
3. Run `tlcl.py`. Use `--help` to list available options. 

## Usage examples

### Model using code interpreter tool

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

### Model using brave search tool

```
$ python3 tlcl.py --url "http://127.0.0.1:8080/completion" --prompt "what is the latest release of Meta's llama model?" --stream
################################ role: system     ################################
<|start_header_id|>system<|end_header_id|>

Environment: ipython
Tools: brave_search

# Tool Instructions
- You have access to the stateful ipython environment
- After executing the python program summarize its output for the user
<|eot_id|>
################################ role: user       ################################
<|start_header_id|>user<|end_header_id|>

what is the latest release of Meta's llama model?<|eot_id|>
################################ role: assistant  ################################
<|start_header_id|>assistant<|end_header_id|>

<|python_tag|>brave_search.call(query="latest release Meta llama model")<|eom_id|>
################################ role: ipython    ################################
<|start_header_id|>ipython<|end_header_id|>

Out[1]: 
[{'title': 'Llama (language model) - Wikipedia',
  'url': 'https://en.wikipedia.org/wiki/Llama_(language_model)',
  'description': 'Llama (acronym for Large Language Model Meta AI, and formerly stylized as LLaMA) is a family of autoregressive large language models (LLMs) released by Meta AI starting in February 2023. The latest version is <strong>Llama 3.1</strong>, released in July 2024. Model weights for the first version of Llama were ...'},
 {'title': "Meta's New Llama 3.1 AI Model Is Free, Powerful, and Risky | WIRED",
  'url': 'https://www.wired.com/story/meta-ai-llama-3/',
  'description': 'Stella Biderman, executive director of EleutherAI, an open source AI project, also notes that <strong>Llama 3</strong> is not fully open source. But Biderman notes that a change to Meta’s latest license will let developers train their own models using <strong>Llama 3</strong>, something that most AI companies currently prohibit.'},
 {'title': 'Meta debuts newest Llama AI model with help from Nvidia and cloud partners',
  'url': 'https://www.cnbc.com/2024/07/23/meta-debuts-newest-llama-ai-model-with-help-from-nvidia-and-others.html',
  'description': 'Instead, similar to when Meta released Llama 2 last summer, the company is partnering with a handful of tech companies that will offer their customers access to <strong>Llama 3.1</strong> via their respective cloud computing platforms, as well as sell security and management tools that work with the new software.'}]
<|eot_id|>
################################ role: assistant  ################################
<|start_header_id|>assistant<|end_header_id|>

The latest release of Meta's llama model is Llama 3.1, which was released in July 2024.<|eot_id|>
```

## Requirements
tlcl uses the following Python modules:
* requests
* ipython
