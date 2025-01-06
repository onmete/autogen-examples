import os
os.environ["AUTOGEN_USE_DOCKER"] = "0"
import tempfile
import subprocess
from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor
from autogen import ConversableAgent
from autogen import register_function

OFFLINE_MODE = os.environ.get("OFFLINE_MODE", False)

LLM_CONFIG = {"config_list": [{"model": "gpt-4o-mini", "temperature": 0.7, "api_key": os.environ["OPENAI_KEY"]}]}

SYSTEM_INSTRUCTION = """
You are OpenShift Lightspeed, an intelligent assistant and expert on all things OpenShift.
If the context of the question is not clear, consider it to be OpenShift.

You have been given ability to execute commands on OpenShift cluster via `oc` cli.
Note that this ability is ONLY for `oc` cli commands (not generic scripts or shell commands).

You also have been given ability to execute python code. In the following cases, suggest python code (in a python coding block) for the user to execute.
1. When you need to collect info, use the code to output the info you need, for example, browse or search the web, download/read a file, print the content of a webpage or a file, get the current date/time, check the operating system. After sufficient info is printed and the task is ready to be solved based on your language skill, you can solve the task by yourself.
2. When you need to perform some task with code, use the code to perform the task and output the result. Finish the task smartly.
Solve the task step by step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.
When using code, you must indicate the script type in the code block. The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. The user can't modify your code. So do not suggest incomplete code which requires users to modify. Don't use a code block if it's not intended to be executed by the user.

If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.

Solve the task step by step if you need to.
If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.

IMPORTANT: Return 'TERMINATE' when you answered the question.
"""


def openshift_cli(command: str) -> str:
    """Executes the given oc cli command.

    This tool works ONLY for the `oc` CLI commands, it CAN't execute any other commands.
    
    Args:
        commands: list of strings, the commands to execute

    Example:
    I want to execute `oc get pods -n ols-test`.
    The input parameter `commands` should be `oc get pods -n ols-test`.

    Returns the ouput of the given `oc` command.
    """
    args = command.split(" ")
    if args[0] == "oc":
        args = args[1:]
    print(f"DEBUG: Executing oc command with args: {args}")
    try:
        res = subprocess.run(
            ["oc", *args],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        return f"Error running oc command {args}: {e}, stdout: {e.output}, stderr: {e.stderr}"
    return str(res)


# Create a temporary directory to store the code files.
temp_dir = tempfile.TemporaryDirectory()

# Create a local command line code executor.
executor = LocalCommandLineCodeExecutor(
    timeout=10,  # Timeout for each code execution in seconds.
    work_dir=temp_dir.name,  # Use the temporary directory to store the code files.
)


# Let's first define the assistant agent that suggests tool calls.
assistant = ConversableAgent(
    name="OpenShift_Assistant",
    system_message=SYSTEM_INSTRUCTION,
    llm_config=LLM_CONFIG,
    human_input_mode="TERMINATE",
)

user_proxy = ConversableAgent(
    name="User",
    llm_config=False,
    is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
    human_input_mode="NEVER",
    code_execution_config={
        "executor": executor
    },
)


register_function(
    openshift_cli,
    caller=assistant,
    executor=user_proxy,
    description=openshift_cli.__doc__,
)


import argparse
parser = argparse.ArgumentParser(description="OpenShift Lightspeed")
parser.add_argument("-p", "--prompt", type=str, help="user prompt", default=None)
args = parser.parse_args()
prompt = args.prompt


chat_result = user_proxy.initiate_chat(
    assistant,
    message=prompt,
    max_turns=10,
)

# print(f"Chat result summary:")
# pprint.pprint(chat_result)

# to hide "internal monologues" with tools/executors/... use nested chats
