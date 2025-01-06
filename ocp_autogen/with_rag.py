import os
os.environ["AUTOGEN_USE_DOCKER"] = "0"


from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
import pprint
import tempfile
from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor
from autogen import ConversableAgent, UserProxyAgent, GroupChat, GroupChatManager, AssistantAgent
from autogen import register_function
import chromadb
import json
import subprocess


config_list = [{"model": "gpt-4o-mini", "temperature": 0.7, "api_key": os.environ["OPENAI_KEY"]}]

assistant = AssistantAgent(
    name="assistant",
    system_message="You are a helpful assistant.",
    llm_config={
        "timeout": 600,
        "config_list": config_list,
    },
)
ragproxyagent = RetrieveUserProxyAgent(
    name="ragproxyagent",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    retrieve_config={
        "task": "code",
        "docs_path": [
            "/home/ometelka/projects/ols-autogen/ocp_autogen/rag/htpasswd.md",
            "/home/ometelka/projects/ols-autogen/ocp_autogen/rag/registry_mirror.md",
        ],
        "custom_text_types": ["mdx"],
        "chunk_token_size": 2000,
        "model": config_list[0]["model"],
        "client": chromadb.PersistentClient(path="/tmp/chromadb"),
        "embedding_model": "all-mpnet-base-v2",
        "get_or_create": True,  # set to False if you don't want to reuse an existing collection, but you'll need to remove the collection manually
        "overwrite": True,
    },
    code_execution_config=False,  # set to False if you don't want to execute the code
)


import argparse
parser = argparse.ArgumentParser(description="OpenShift Lightspeed")
parser.add_argument("-p", "--prompt", type=str, help="user prompt", default=None)
args = parser.parse_args()
prompt = args.prompt

# code_problem = "what are prerequisites for mirroring registries?"
code_problem = prompt
ragproxyagent.initiate_chat(
    assistant, message=ragproxyagent.message_generator, problem=code_problem
)