from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AnyMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing import TypedDict, Any, Dict, List, Optional, Annotated
import asyncio
import os
import pprint
import re

load_dotenv()

langfuse = Langfuse(
  secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
  public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
  host=os.environ.get("LANGFUSE_HOST")
)

class PlatformAgentState(TypedDict):
    """
    State object for LangGraph agent execution.
    Holds all relevant context and history for the current run.
    """
    # The full list of messages exchanged (user, assistant, tool, etc.)
    messages: Annotated[list[AnyMessage], add_messages]

    # List of tools available to the agent
    tools_list: List[BaseTool]

    # The number of iterations the agent has made
    iteration_count: int

mcp_client = MultiServerMCPClient(
    {
        "platform": {
            "command": "/Users/adrego/personal/ai-meets-platform-engineering/mcp/mcp-server",
            "transport": "stdio",
            "args": [],
        },
        "kubernetes": {
            "command": "npx",
            "args": ["mcp-server-kubernetes"],
            "env": {
                "ALLOW_ONLY_NON_DESTRUCTIVE_TOOLS": "true",
                "K8S_CONTEXT": "kind-kind"
            },
            "transport": "stdio",
        }
    }
)

def analyze_and_select_tool(state: PlatformAgentState) -> PlatformAgentState:
    """
    Validate the question and select the most appropriate tool(s) in a single step.
    """

    state["iteration_count"] = state.get("iteration_count", 0) + 1
    if state["iteration_count"] > 5:
        return state

    system_prompt = f"""
    If the user question is answered, return the answer.

    Step 0. Before making a tool call, always check whether the information has already been retrieved from a previous tool response.
    Step 1. If the tool results already contain the answer to the user's question, extract and present that answer directly to the user.
    Step 2. If the answer is not present, select the most appropriate tool(s) and arguments to learn more and answer the user question.
    Step 3. If the question is not valid, return "Not possible to answer the question."

    Remember that Kubernetes resources are namespaced. Search across all namespaces if the namespace is not specified.

    Do not guess or make up information.
    """
    
    state["messages"].append(SystemMessage(content=system_prompt))

    model = ChatOllama(model="qwen3:1.7b", temperature=0).bind_tools(state["tools_list"])
    response = model.invoke(state["messages"])
    
    state["messages"].append(response)

    has_tool_calls = hasattr(response, 'tool_calls') and response.tool_calls
    if has_tool_calls:
        print(f"🔧 Tools to be called: {[call['name'] for call in response.tool_calls]}")
    else:
        print("🔧 No tools to be called")

    return state

async def main():
    print("🔄 Connecting to MCP servers and fetching tools...")
    tools = await mcp_client.get_tools()
    print(f"✅ Found {len(tools)} tools")

    system_prompt = f"""
    You are a Platform Engineer Assistant.

    You are connected to a Platform API and to a Kubernetes cluster.
    The Platform API is used to get general information about the platform.
    The Kubernetes cluster is used to host some of those applications, but not all.

    Your answers should be helpful and concise.
    Make the answers as visually readable as possible (use lists, etc. if appropriate).

    Multiple tools can be called at the same time.
    """
    user_question = input("🤖 Hello, how can I assist you? \n > ")
    if not user_question:
        print("❌ No question provided. Exiting.")
        return

    state = PlatformAgentState(
        messages=[SystemMessage(content=system_prompt), HumanMessage(content=user_question)],
        tools_list=tools,
        iteration_count=0,
    )

    langfuse_handler = CallbackHandler()

    print("🏗️  Building workflow graph...")
    platform_graph = StateGraph(PlatformAgentState)

    platform_graph.add_node("analyze_and_select_tool", analyze_and_select_tool)
    platform_graph.add_node("tools", ToolNode(tools))

    platform_graph.add_edge(START, "analyze_and_select_tool")

    platform_graph.add_conditional_edges("analyze_and_select_tool", tools_condition, {"tools": "tools", "__end__": END})
    platform_graph.add_edge("tools", "analyze_and_select_tool")

    print("⚡ Running workflow...")
    compiled_graph = platform_graph.compile()
    result = await compiled_graph.ainvoke(state, config={"callbacks": [langfuse_handler]})

    filtered_content = re.sub(r'<think>[\s\S]*?</think>|</?think>', '', result.get("messages")[-1].content, flags=re.IGNORECASE)
    
    print("🤖 ", filtered_content)

    print(f"📊 Workflow completed in {result.get('iteration_count', 0)} iterations")
    
    #print("\n=== State ===")
    #pprint.pprint(result, indent=2, width=120)

    try:
        print("🎨 Generating workflow graph...")
        png = compiled_graph.get_graph().draw_mermaid_png()
        with open("graph.png", "wb") as f:
            print("✅ Graph image saved as graph.png. Open this file to view the graph.")
            f.write(png)
    except Exception as e:
        print(f"❌ Error generating graph: {e}")

if __name__ == "__main__":
    asyncio.run(main())
