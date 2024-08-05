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
- After executing the python program summarize its output for the user
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

def print_role_header(role):
    print("#" * 32 + f" role: {role:<10} " + "#" * 32)

def print_last_message(conversation, is_verbose):
    last_message_index = conversation.rfind("<|start_header_id|>")
    assert(last_message_index >= 0)
    last_message = conversation[last_message_index:]
    print(last_message)

def input_if_none(user_prompt):
    if user_prompt is None:
        return input("User prompt: ")
    else:
        return user_prompt

headers = { "Content-Type": "application/json" }

python_tag_regex = re.compile(re.escape("<|python_tag|>") + "(.*?)" + re.escape("<|eom_id|>"), re.DOTALL)

ipython_session = IPythonSession()

print_role_header("system")
conversation = apply_prompt_template("system", system_prompt)
print_last_message(conversation, is_verbose)

print_role_header("user")
conversation += apply_prompt_template("user", input_if_none(user_prompt))
print_last_message(conversation, is_verbose)

conversation += apply_prompt_template("assistant")

while(True):
    response = requests.post(llama_endpoint, json=create_request_data(conversation), headers=headers)
    assert(response.status_code == 200)

    response_content = response.json()["content"]
    print_role_header("assistant")
    conversation += response_content
    print_last_message(conversation, is_verbose)

    match = python_tag_regex.search(response_content)
    if match:
        tool_request = match.group(1)
        tool_response = ipython_session.execute(tool_request)

        print_role_header("ipython")
        conversation += apply_prompt_template("ipython", tool_response)
        print_last_message(conversation, is_verbose)

        conversation += apply_prompt_template("assistant")
    else:
        if is_interactive:
            print_role_header("user")
            user_input = input("Prompt: ")
            conversation += apply_prompt_template("user", user_input)
            print_last_message(conversation, is_verbose)

            conversation += apply_prompt_template("assistant")
        else:
            break

