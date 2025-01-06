import os

from autogen import ConversableAgent
from autogen import GroupChat
from autogen import GroupChatManager
from autogen import register_function
from ocp_autogen.tool import list_pods, pod_logs, openshift_cli


config_list = {"config_list": [{"model": "gpt-4o-mini", "api_key": os.environ["OPENAI_KEY"]}]}


# The Number Agent always returns the same numbers.
assistant = ConversableAgent(
    name="ocp_assistant",
    system_message="""You are OpenShift Lightspeed, an intelligent assistant and expert on all things OpenShift.
If the context of the question is not clear, consider it to be OpenShift.
    """,
    llm_config=config_list,
    human_input_mode="NEVER",
    description="OpenShift Lightspeed intelligent assistant."
)

# The Adder Agent adds 1 to each number it receives.
oc_cli_agent = ConversableAgent(
    name="oc_cli_agent",
    system_message="""You have been given ability to execute commands on OpenShift cluster via `oc` cli.
Note that this ability is ONLY for `oc` cli commands (not generic scripts or shell commands).
""",
    llm_config=config_list,
    human_input_mode="NEVER",
    description="Executes openshift cli (`oc`) commands."
)

# The Multiplier Agent multiplies each number it receives by 2.
multiplier_agent = ConversableAgent(
    name="Multiplier_Agent",
    system_message="You multiply each number I give you by 2 and return me the new numbers, one number each line.",
    llm_config=config_list,
    human_input_mode="NEVER",
    description="Multiply each input number by 2."
)

# The Subtracter Agent subtracts 1 from each number it receives.
subtracter_agent = ConversableAgent(
    name="Subtracter_Agent",
    system_message="You subtract 1 from each number I give you and return me the new numbers, one number each line.",
    llm_config=config_list,
    human_input_mode="NEVER",
    description="Subtract 1 from each input number."
)

# The Divider Agent divides each number it receives by 2.
divider_agent = ConversableAgent(
    name="Divider_Agent",
    system_message="You divide each number I give you by 2 and return me the new numbers, one number each line.",
    llm_config=config_list,
    human_input_mode="NEVER",
    description="Divide each input number by 2."
)


group_chat = GroupChat(
    agents=[oc_cli_agent, multiplier_agent, subtracter_agent, divider_agent, assistant],
    messages=[],
    max_round=6,
    send_introductions=True,
)
group_chat_manager = GroupChatManager(
    groupchat=group_chat,
    llm_config=config_list,
)

if os.environ.get("OFFLINE_MODE", False):
    register_function(
        openshift_cli,
        caller=assistant,
        executor=oc_cli_agent,
        description=oc_cli_agent.description,
    )
else:
    register_function(
        list_pods,
        caller=assistant,
        executor=oc_cli_agent,
        description=list_pods.__doc__,
    )


import argparse
parser = argparse.ArgumentParser(description="OpenShift Lightspeed")
parser.add_argument("-p", "--prompt", type=str, help="user prompt", default=None)
args = parser.parse_args()
prompt = args.prompt


chat_result = assistant.initiate_chat(
    group_chat_manager,
    message=prompt,
    summary_method="reflection_with_llm",
)

print(chat_result.summary)