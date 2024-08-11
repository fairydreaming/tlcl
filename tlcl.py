#!/usr/bin/env python3

import re
import io
import sys
import requests
import argparse
import json
import time
import signal

from IPython import InteractiveShell
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from pathlib import Path

DEFAULT_SYSTEM_PROMPT="""Environment: ipython
Tools: brave_search

# Tool Instructions
- You have access to the stateful ipython environment
- After executing the python program summarize its output for the user
"""

def generate_log_file_name():
    current_time = time.strftime("%Y-%m-%d-%H-%M-%S")
    log_filename = f"tlcl-{current_time}.log"
    return log_filename

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--url", help="URL of the llama.cpp server completion endpoint", default="http://127.0.0.1:8080/completion", type=str)
parser.add_argument("-s", "--system-prompt", help = "System prompt", default=DEFAULT_SYSTEM_PROMPT, type=str)
parser.add_argument("-p", "--prompt", help="User prompt", default=None, type=str)
parser.add_argument("-i", "--interactive", help="Run in interactive mode", action='store_true')
parser.add_argument("-a", "--autonomous", help="Run in autonomous mode", action='store_true')
parser.add_argument("-t", "--stream", help="Print received tokens in real time", action='store_true')
parser.add_argument("-l", "--log", help="Log standard output to a file", const=generate_log_file_name(), default=None, nargs='?')
parser.add_argument("-v", "--verbose", help="Increase verbosity of the output", action='store_true')

args = parser.parse_args()
llama_endpoint = args.url
system_prompt = args.system_prompt
user_prompt = args.prompt
is_interactive = args.interactive
is_verbose = args.verbose
is_stream = args.stream
is_auto = args.autonomous
log_file = args.log

system_prompt_file = None

if system_prompt and Path(system_prompt).is_file():
    system_prompt_file = system_prompt
    system_prompt_mtime = Path(system_prompt_file).stat().st_mtime
    with open(system_prompt, 'r') as file:
        system_prompt = file.read()

if user_prompt and Path(user_prompt).is_file():
    with open(user_prompt, 'r') as file:
        user_prompt = file.read()

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
                    return f"Error during execution:\n{buffer.getvalue()}"
            except Exception as e:
                return f"Exception: {e}"

class Tee(object):
    def __init__(self, log_file_name):
        self.log_file = open(log_file_name, "w")
        self.stdout = sys.stdout
        sys.stdout = self

    def close(self):
        sys.stdout = self.stdout
        self.log_file.close()

    def write(self, data):
        self.log_file.write(data)
        self.stdout.write(data)

    def flush(self):
        self.log_file.flush()
        self.stdout.flush()

tee = Tee(log_file) if log_file is not None else None

def signal_handler(signum, frame):
    print("\nExiting...")
    global tee
    if tee is not None:
        tee.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def apply_prompt_template(role, prompt = None):
    if prompt:
        return f"<|start_header_id|>{role}<|end_header_id|>\n\n{prompt}<|eot_id|>"
    else:
        return f"<|start_header_id|>{role}<|end_header_id|>\n\n"

def create_request_data(prompt):
    return { 
        "cache_prompt": True,
        "stream": is_stream,
        "prompt": prompt,
    }

def print_role_header(role):
    print("#" * 32 + f" role: {role:<10} " + "#" * 32)

def print_last_message(conversation, is_verbose, end="\n"):
    last_message_index = conversation.rfind("<|start_header_id|>")
    assert(last_message_index >= 0)
    last_message = conversation[last_message_index:]
    print(last_message, end=end)

def input_if_none(user_prompt):
    if user_prompt is None:
        return input("User prompt: ")
    else:
        return user_prompt

headers = { "Content-Type": "application/json" }

python_tag_regex = re.compile(re.escape("<|python_tag|>") + "(.*?)" + re.escape("<|eom_id|>"), re.DOTALL)

ipython_session = IPythonSession()
ipython_session.execute("import brave_search")

print_role_header("system")
conversation = apply_prompt_template("system", system_prompt)
print_last_message(conversation, is_verbose)

if is_auto:
    print_role_header("user")
    conversation += apply_prompt_template("user")
    last_role = "user"
else:
    print_role_header("user")
    conversation += apply_prompt_template("user", input_if_none(user_prompt))
    print_last_message(conversation, is_verbose)
    conversation += apply_prompt_template("assistant")
    last_role = "assistant"

while(True):
    response = requests.post(llama_endpoint, json=create_request_data(conversation), headers=headers, stream=is_stream)
    assert(response.status_code == 200)

    if is_stream:
        print_last_message(conversation, is_verbose, end="")

        response_content = ""
        for line in response.iter_lines():
            # filter out keep-alive new lines
            if line:
                decoded_line = line.decode("utf-8")
                decoded_json = json.loads(decoded_line.removeprefix("data: "))
                if "content" in decoded_json:
                    partial_content = decoded_json["content"]
                    response_content += partial_content
                    conversation += partial_content
                    print(partial_content, flush=True, end="")
        print()
    else:
        response_content = response.json()["content"]
        conversation += response_content
        print_last_message(conversation, is_verbose)

    if system_prompt_file:
        prev_system_prompt_mtime = system_prompt_mtime
        system_prompt_mtime = Path(system_prompt_file).stat().st_mtime
        if system_prompt_mtime > prev_system_prompt_mtime:
            print_role_header("system")
            with open(system_prompt_file, 'r') as file:
                system_prompt = file.read()
            conversation = apply_prompt_template("system", system_prompt)
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
        elif is_auto:
            if last_role == "assistant":
                print_role_header("user")
                conversation += apply_prompt_template("user")
                last_role = "user"
            elif last_role == "user":
                print_role_header("assistant")
                conversation += apply_prompt_template("assistant")
                last_role = "assistant"
        else:
            break

