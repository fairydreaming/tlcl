#!/usr/bin/env python3

import re
import io
import requests
import argparse

from IPython import InteractiveShell
from contextlib import contextmanager, redirect_stdout, redirect_stderr

DEFAULT_SYSTEM_PROMPT="""Environment: ipython

# Tool Instructions
- You have access to the stateful ipython environment
"""

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--url", help="URL of the llama.cpp server completion endpoint", default="http://127.0.0.1:8080/completion", type=str)
parser.add_argument("-s", "--system-prompt", help = "System prompt", default=DEFAULT_SYSTEM_PROMPT, type=str)
parser.add_argument("-p", "--prompt", help="User prompt", default=None, type=str)
parser.add_argument("-i", "--interactive", help="Run in interactive mode", action='store_true')
parser.add_argument("-v", "--verbose", help="Increase verbosity of the output", action='store_true')

args = parser.parse_args()
llama_endpoint = args.url
system_prompt = args.system_prompt
user_prompt = args.prompt
is_interactive = args.interactive
is_verbose = args.verbose

@contextmanager
def capture_output():
    buffer = io.StringIO()
    with redirect_stdout(buffer), redirect_stderr(buffer):
        yield buffer

class IPythonSession:
    def __init__(self):
        # Create an instance of InteractiveShell
        self.shell = InteractiveShell.instance()

    def execute(self, code: str) -> str:
        """Execute code and return the output or error message."""
        with capture_output() as buffer:
            try:
                result = self.shell.run_cell(code)
                if result.success:
                    output = buffer.getvalue()
                    return output if output else "No output"
                else:
                    return f"Error during execution: {result.error_in_exec}"
            except Exception as e:
                return f"Exception: {e}"

def apply_prompt_template(role, prompt = None):
    if prompt:
        return f"<|start_header_id|>{role}<|end_header_id|>\n\n{prompt}<|eot_id|>"
    else:
        return f"<|start_header_id|>{role}<|end_header_id|>\n\n"

def create_request_data(prompt):
    return { 
        "cache_prompt": True,
        "prompt": prompt 
    }

headers = { "Content-Type": "application/json" }

python_tag_regex = re.compile(re.escape("<|python_tag|>") + "(.*?)" + re.escape("<|eom_id|>"), re.DOTALL)

ipython_session = IPythonSession()

conversation = apply_prompt_template("system", system_prompt)

if user_prompt is not None:
    print(user_prompt)
    user_input = user_prompt
else:
    user_input = input("Prompt: ")
conversation += apply_prompt_template("user", user_input)
conversation += apply_prompt_template("assistant")

while(True):
    if is_verbose:
        print(conversation)
    response = requests.post(llama_endpoint, json=create_request_data(conversation), headers=headers)
    assert(response.status_code == 200)

    response_content = response.json()["content"]
    print(response_content)
    conversation += response_content

    match = python_tag_regex.search(response_content)
    if match:
        tool_request = match.group(1)
        tool_response = ipython_session.execute(tool_request)
        print(tool_response)

        conversation += apply_prompt_template("ipython", tool_response)
        conversation += apply_prompt_template("assistant")
    else:
        if is_interactive:
            user_input = input("Prompt: ")
            conversation += apply_prompt_template("user", user_input)
            conversation += apply_prompt_template("assistant")
        else:
            break

