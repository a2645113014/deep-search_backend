import shutil
from pathlib import Path

from deepagents import create_deep_agent

from agent.llm import llm
from agent.load_prompt import main_config
from agent.sub_agents.db_sub_agent import db_sub_agent
from agent.sub_agents.internet_sub_agent import internet_sub_agent
from agent.sub_agents.rag_sub_agent import rag_sub_agent
from api.context import set_session_context, set_thread_context, reset_session_context
from api.monitor import monitor
from tools.markdown_tool import generate_markdown
from tools.pdf_tool import convert_md_to_pdf
from tools.upload_file_read_tool import read_file_content
from utils.logger_utils import logger

main_agent = create_deep_agent(
    model=llm,
    system_prompt=main_config["system_prompt"],
    subagents=[db_sub_agent,rag_sub_agent,internet_sub_agent],
    tools=[read_file_content, generate_markdown, convert_md_to_pdf]
)

if __name__ == '__main__':
    result = main_agent.invoke({"messages": [{"role": "user", "content": "列表2条重要的刑法规则？"}]})
    print(result["messages"][-1].content)

# 运行main_agent的函数
async def run_deep_agent(query: str, thread_id:str):
    # 生成session目录
    project_dir = Path(__file__).parents[1].resolve() # 项目的路径
    session_dir = project_dir / "output" / f"session_{thread_id}" # 当前会话的目录
    session_dir.mkdir(parents=True, exist_ok=True) # 创建当前会话的目录
    session_dir_relative_str = str(session_dir.relative_to(project_dir)) # 得到当前会话的目录相对项目的路径
    session_dir_str = str(session_dir) # 会话目录的绝对路径
    # 将会话目录的绝对路径保存到当前协和的ontext中
    session_token = set_session_context(session_dir_str)
    # 将thread_id保存到当前协和的ontext中
    thread_token = set_thread_context(thread_id)
    # 将当前会话目录的绝对目录报告给客户端
    monitor.report_session_dir(session_dir_str)

    # 将upload中的当前会话目录下的所有文件拷贝到ouput当前会话目录下， 得到所有文件名列表
    upload_files_info = ""
    upload_session_dir = project_dir / "upload" / f"session_{thread_id}" # 上传会话目录
    if upload_session_dir.exists():
        file_names:list[str] = [item.name for item in upload_session_dir.iterdir() if item.is_file()]
        for file_name in file_names:
            shutil.copy2(upload_session_dir/file_name, session_dir/file_name)  # 拷贝文件

        upload_files_info = (
            "[已上传文件]："
            f"\n{'\n'.join([f"	- {name}" for name in file_names])}\n"
            "请优先使用工具读取并参考这些文件"
        )
    path_instruction = f"""
【工作环境指令】
[工作目录]：{session_dir_relative_str}

{upload_files_info}

[规则]：
	1. 新生成文件必须保存到工作目录：'{session_dir_relative_str}'
	2. 读取已上传的文件时，请直接将文件名作为 filename 参数传入（read_file_content）读取工具，不要带上任何目录前缀。
	3. 使用相对路径，禁止使用绝对路径
	4. 若存在上传文件，请先分析内容    
    """
    try:
        async for chunk in main_agent.astream({"messages": [{
            "role": "user",
            "content": f"问题：{query},补充描述: {path_instruction}"
        }]}):
            for key,value in chunk.items():
                if key not in ["model", "tools"]: continue
                # 得到当前message对象
                message = value["messages"][0]
                if key=="model":  # 模型处理的返回
                    tool_calls = message.tool_calls
                    if tool_calls: # 准备去调用工具
                        for tool_call in tool_calls:
                            name = tool_call["name"]
                            if name=="task": # 准备调用子agent (task tool)
                                args = tool_call["args"]
                                print(f"---模型返回，准备调用子智能体[{args["subagent_type"]}],传入的参数：{args["description"]}")
                                # 报告给客户端，要调用子智能体了
                                monitor.report_assistant(args["subagent_type"], args["description"])
                            else: # 准备调用tool  =》 问题：只能遍历到主智能体tool的调用，看不到子智能体tool
                                # print(f"---模型返回，准备调用工具[{name}], 参数为：{tool_call["args"]}")
                                # 报告给客户端，要调用工具了
                                monitor.report_tool(name, tool_call["args"])
                    else: # 返回最终的结果
                        # print(f"---模型返回最终结果：{message.content}")
                        # 将结果报告给客户端
                        monitor.report_task_result(message.content)
    except Exception as e:
        logger.error(f"智能体执行最终失败：{e}")
        monitor.report_error(f"智能体执行最终失败：{e}")
        raise
    finally:  # 最终都要重置保存的thread_id和session_dir
        reset_session_context(session_token, thread_token)
