from dotenv import load_dotenv
import os
from langchain.chat_models import init_chat_model

load_dotenv()

llm = init_chat_model(
    model= "MiniMax-M2.5",
    model_provider="openai",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
)