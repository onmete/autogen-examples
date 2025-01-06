import chromadb
from typing_extensions import Annotated
from autogen import register_function
import os
import autogen
from autogen import AssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from ocp_autogen.tool import list_pods, pod_logs, openshift_cli


def termination_msg(x):
    return isinstance(x, dict) and "TERMINATE" == str(x.get("content", ""))[-9:].upper()


config_list = [{"model": "gpt-4o-mini", "api_key": os.environ["OPENAI_KEY"]}]
llm_config = {"config_list": config_list, "timeout": 60, "temperature": 0.8, "seed": 1234}


user = autogen.UserProxyAgent(
    name="User",
    is_termination_msg=termination_msg,
    human_input_mode="NEVER",
    code_execution_config=False,  # we don't want to execute code in this case.
    default_auto_reply="Reply `TERMINATE` if the task is done.",
    description="The user who ask questions and give tasks.",
)

user_aid = RetrieveUserProxyAgent(
    name="User_Assistant",
    is_termination_msg=termination_msg,
    human_input_mode="NEVER",
    default_auto_reply="Reply `TERMINATE` if the task is done.",
    max_consecutive_auto_reply=3,
    retrieve_config={
        "task": "code",
        "docs_path": [
            # "/home/ometelka/projects/ols-autogen/ocp_autogen/rag/htpasswd.md",
            "/home/ometelka/projects/ols-autogen/ocp_autogen/rag/registry_mirror.md",
        ],
        "custom_text_types": ["mdx"],
        "chunk_token_size": 2000,
        "model": config_list[0]["model"],
        # "client": chromadb.PersistentClient(path="/tmp/chromadb"),
        "embedding_model": "all-mpnet-base-v2",
        "get_or_create": True,  # set to False if you don't want to reuse an existing collection, but you'll need to remove the collection manually
    },
    code_execution_config=False,  # we don't want to execute code in this case.
    description="""User Assistant who has extra content retrieval power for openshift questions.
    For example mirror registry setup.""",
)

assistant = AssistantAgent(
    name="OpenShift_Assistant",
    is_termination_msg=termination_msg,
    system_message="""
You are OpenShift Lightspeed, an intelligent assistant and expert on all things OpenShift.
If the context of the question is not clear, consider it to be OpenShift.

You have been given ability to execute commands on OpenShift cluster via `oc` cli.
Note that this ability is ONLY for `oc` cli commands (not generic scripts or shell commands).
    """,
    llm_config=llm_config,
    description="Executes openshift cli (`oc`) commands.",
)

import argparse
parser = argparse.ArgumentParser(description="OpenShift Lightspeed")
parser.add_argument("-p", "--prompt", type=str, help="user prompt", default=None)
args = parser.parse_args()
PROBLEM = args.prompt



if os.environ.get("OFFLINE_MODE", False):
    print("OFFLINE_MODE IS ON")
    register_function(
        list_pods,
        caller=assistant,
        executor=user,
        description=openshift_cli.__doc__,
    )
else:
    print("OFFLINE_MODE IS OFF")
    register_function(
        openshift_cli,
        caller=assistant,
        executor=user,
        description=list_pods.__doc__,
    )


def _reset_agents():
    user.reset()
    user_aid.reset()
    assistant.reset()


def rag_chat():
    _reset_agents()
    groupchat = autogen.GroupChat(
        agents=[user_aid, assistant], messages=[], max_round=4, speaker_selection_method="auto"
    )
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Start chatting with user_aid as this is the user proxy agent.
    user_aid.initiate_chat(
        manager,
        message=user_aid.message_generator,
        problem=PROBLEM,
        n_results=3,
    )

def norag_chat():
    _reset_agents()
    groupchat = autogen.GroupChat(
        agents=[user, assistant],
        messages=[],
        max_round=12,
        speaker_selection_method="auto",
        allow_repeat_speaker=False,
    )
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Start chatting with the user as this is the user proxy agent.
    user.initiate_chat(
        manager,
        message=PROBLEM,
    )


def call_rag_chat():
    _reset_agents()

    # In this case, we will have multiple user proxy agents and we don't initiate the chat
    # with RAG user proxy agent.
    # In order to use RAG user proxy agent, we need to wrap RAG agents in a function and call
    # it from other agents.
    def retrieve_content(
        message: Annotated[
            str,
            "Refined message which keeps the original meaning and can be used to retrieve content for code generation and question answering.",
        ],
        n_results: Annotated[int, "number of results"] = 3,
    ) -> str:
        user_aid.n_results = n_results  # Set the number of results to be retrieved.
        _context = {"problem": message, "n_results": n_results}
        ret_msg = user_aid.message_generator(user_aid, None, _context)
        return ret_msg or message

    user_aid.human_input_mode = "NEVER"  # Disable human input for user_aid since it only retrieves content.

    register_function(
        retrieve_content,
        caller=assistant,
        executor=user,
        description="retrieve content for code generation and question answering.",
    )

    groupchat = autogen.GroupChat(
        agents=[user, assistant],
        messages=[],
        max_round=4,
        speaker_selection_method="auto",
        allow_repeat_speaker=False,
    )

    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Start chatting with the user as this is the user proxy agent.
    user.initiate_chat(
        manager,
        message=PROBLEM,
    )

# norag_chat()
# rag_chat()
call_rag_chat()
