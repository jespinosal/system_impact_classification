"""
Implement Nodes to build conversational grahp: based on langchain and langgraph libraries
"""
import os
from typing import List, Optional, Annotated
from typing_extensions import TypedDict
from operator import add
import pandas as pd
from dotenv import load_dotenv
from langchain.tools import  tool
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph.message import add_messages
from langgraph.graph import END, START, StateGraph, MessagesState



load_dotenv()
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT") 
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME") 

llm = AzureChatOpenAI(
    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)


# States definition
class GraphState(TypedDict):
    id: str
    table_equipment_naming_map = pd.DataFrame
    table_equipment_scores = pd.DataFrame
    current_human_messages = Annotated[List[SystemMessage]]
    current_ai_messages= Annotated[List[AIMessage]]
    question_1_to_7 = str
    question_8 = bool
    conversation_messages: Annotated[List[SystemMessage|HumanMessage|AIMessage|ToolMessage], add_messages]  # maybe only human messages are needed here


# Tools definition 
@tool
def get_reference_tables(path_map_equipment_groups, path_equipment_group_probs):
    #@todo parse to string or use langchain pandas parser
    df_map_equipment_group = pd.read_csv(path_map_equipment_groups)
    df_equipment_group_probs = pd.read_csv(path_equipment_group_probs)
    return df_map_equipment_group, df_equipment_group_probs


@tool
def mini_rag(df_equipment_group_probs, df_map_equipment_group, user_query):
    #@todo add mini rag logic or use langchain pandas parser and let LLM to decide 
    row = ' '
    return row

# Nodes definition #@todo add logic and states updates


def node_entrypoint(state:GraphState):
    """
    System introduction ask to user equipment name 
    """
    return {'current_human_messages': 'cooler'}


def node_context_rag(state:GraphState):
    """Try first direct match, other wise use GenAI/embeddings approach
    1. Load tables and user query
    2. Perform table query or GenAI/semantic search if needed
    3. Return question 1 to 7 and score of confidense (if score too low re-ask?)
    """
    return {'table_equipment_scores': 'xxx', 'table_equipment_naming_map': 'yyy'}


def node_generate_output(state:GraphState):
    return {'current_ai_messages': ' '}


def node_generare_next_question(state:GraphState):
    return {'current_ai_messages': ' '}


def question_8a0(state:GraphState):
    human_answer = state.get('answer', None)
    if human_answer == "Yes":
        return "node_question_8a1"
    else:
        return END 


def question_8a1(state:GraphState):
    human_answer = state.get('answer', None)
    if human_answer == "Yes":
        return "node_question_8a2"
    else:
        return END 

def question_8a2(state:GraphState):
    human_answer = state.get('answer', None)
    if human_answer == "Yes":
        pass
    else:
        pass
    return END


# Note: we can manage all the 8a question flow in one node. But having indivial flows will be benefitial for demo purposes and debugging.




if __name__ == "__main__":
   
    # Add nodes and edges 
    builder = StateGraph(GraphState)
    builder.add_node("node_entrypoint", node_entrypoint)
    builder.add_node("node_context_rag", node_context_rag)
    builder.add_node("node_generare_next_question", node_generare_next_question)
    builder.add_node("node_generate_output", node_generate_output)


     # Edges definitions 
    builder.add_edge(START, "node_entrypoint")
    builder.add_edge("node_entrypoint", "node_context_rag")
    builder.add_conditional_edges("node_context_rag", question_8a0, ["node_generare_next_question", END])
    builder.add_conditional_edges("node_generare_next_question", question_8a1, ["node_generare_next_question", END])
    builder.add_conditional_edges("node_generare_next_question", question_8a2, ["node_generare_next_question", END])
    builder.add_conditional_edges("node_generare_next_question", END)