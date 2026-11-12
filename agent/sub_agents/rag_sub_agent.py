from agent.load_prompt import sub_agents_config
from tools.ragflow_tools import get_assistant_list, create_ask_delete

rag_sub_agent = {
    "name": sub_agents_config["ragflow"]["name"],
    "description": sub_agents_config["ragflow"]["description"],
    "system_prompt": sub_agents_config["ragflow"]["system_prompt"],
    "tools": [get_assistant_list, create_ask_delete]
}