"""
Implement Nodes to build conversational grahp: based on langchain and langgraph libraries
"""
import os
from io import StringIO
from typing import List, Optional, Annotated
from typing_extensions import TypedDict
from operator import add
import pandas as pd
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import NodeInterrupt
from config import config
from custom_rag import get_equipment_scores
from config import config
from custom_rag import get_equipment_scores

class AgentState(TypedDict):
    stage: int
    equipment: str
    human_message: str
    ai_message: str
    criteria_8a_status: bool
    criteria_8b_status: bool = False # Default doens't work need to update value in Node @todo check how to do 
    df_output: str # # pandas is not compatible "DataFrame is not serializable"
    current_question_id: str


# Note: we can manage all the 8a question flow in one node. But having indivial flows will be benefitial for demo purposes and debugging.
def df_string_encoder_decoder(df=None, df_str= None):
    # Step required to des-serialzie str DF. Cols should avoid whitespaces
    if df is None and isinstance(df_str, str):
        print('decoding str to pandas')
        df = pd.read_csv(StringIO(df_str), sep='\s+')
        df['equipment_group_name'] = df['equipment_group_name'].apply(lambda x: x.replace("_", " "))
        df.columns = [col.replace("_", " ") for col in df.columns]
        return df
    elif isinstance(df, pd.DataFrame) and df_str is None:
        print('encoding str to pandas')
        df.columns = [col.replace(" ", "_") for col in df.columns]
        df['equipment_group_name'] = df['equipment_group_name'].apply(lambda x: x.replace(" ", '_'))
        df_str = df.to_string(index=False)
        return df_str
    else:
        raise(TypeError, "provide a valid pandas data frame or string parsed version")
        

def node_get_human_equipment(state: AgentState):
    # @todo add regex for alphabetic - Camell case - Add Guardrails?? -
    print('-----------Node get human equipment-------------------')
    equipment = state['equipment'].strip()
    stage = state['stage'] + 1
    equipment =  state['equipment']
    return {'equipment': equipment, 'stage': stage, 'current_question_id':0, 'criteria_8b_status':False }# Default 8B false and current_question_id=0 as not possinle to setup default value 

def node_rag(state:AgentState):
    # @todo add fallback case and actions to take in that situation. At the moment unknowk equipments will broke the code
    print('-----------Node RAG-------------------')
    user_equipment = state['equipment']
    stage = state['stage'] + 1
    print(f"RAG for input: {user_equipment}")
    df_equipment_score = get_equipment_scores(user_equipment=user_equipment)
    print("RAG Output:")
    print(df_equipment_score)
    value_8a = True if df_equipment_score['Criteria 8a'].values[0]>0.5 else False
    print(f"According to historical data 'Criteria 8a' is : {value_8a}")
    df_equipment_score_str = df_string_encoder_decoder(df=df_equipment_score)
    return {'df_output': df_equipment_score_str,  'criteria_8a_status': value_8a, 'stage': stage, } 

def eval_criteria_8a(state:AgentState):
    print("---Step 3---")
    if state['criteria_8a_status']:
        return 'criteria_8a_is_true'
    else:
        return 'criteria_8a_is_false'
    
def get_next_question(question_id:str, human_answer:str) -> dict:
    """This allowxs yy the method managed 3 uses cases:
    1- Start
    2- Intermediate
    3- End

    Args:
        question_id (str): _description_
        human_answer (str): _description_

    Returns:
        dict: _description_
    """

    questions = {'question_1': "1. The issue is related to IT protocol 00x1?", 
                'question_2': "2. The system reported temperature over 15 Celcius degree?", 
                'question_3': "3. The system error was reported less than 24 hours ago??", 
                'question_4': "4. The system error affects equipment XXY"}

    question_id_edges = { # Also , as output a need next node and final answe (it is already on the key)
            'question_1': {'yes': 'question_3',  'no': 'question_2'},
            'question_2': {'yes': 'question_3',  'no': 'END'},
            'question_3': {'yes': 'question_4',  'no': 'question_4'},
            'question_4': {'yes': 'END',  'no': 'END'}}
        
    if question_id == 'None' and human_answer == 'None':
        question_id_next = 'question_1' 
        question_str_next = questions['question_1']
    else:
        question_id_next = question_id_edges[question_id][human_answer]
        if question_id_next != 'END':
            question_str_next = questions[question_id_next]
        else:
            question_id_next = 'question_end'
            question_str_next = 'Questionary is done'
    return  question_id_next , question_str_next
    

def node_question(state: AgentState):
    print('-----------Node question-------------------')
    stage = state['stage'] + 1
    if stage ==3 : #first iteration
        current_question_id, ai_message = get_next_question(question_id='None', human_answer='None')
    else:
        current_question_id = state['current_question_id']
        human_answer = state['human_message']
        current_question_id_, ai_message = get_next_question(question_id=current_question_id, human_answer=human_answer)
        current_question_id = current_question_id_
    print(f"Question {current_question_id}: {ai_message}")
    return {'ai_message': ai_message, 'current_question_id':current_question_id, 'stage': stage}

def continue_questions(state: AgentState):
    last_question_id = state['current_question_id']
    if last_question_id == 'question_end':
        return 'skip_questions'
    else:
        return 'go_to_next_question'

def node_update_8b(state:AgentState):
    if state['criteria_8a_status']: # If questions has made
        last_human_message = state['human_message']
        criteria_8b_status = True if last_human_message=='yes' else False
    else:
        criteria_8b_status = False
 
    return {'criteria_8b_status': criteria_8b_status}

def node_human_feedback(state):
    stage = state['stage'] + 1
    current_question_id = state['current_question_id']
    print("---node human_feedback---") 
    print("Please answer the quesiton with yes/no answer")
    if state['current_question_id']!='question_end': # That means after the last question is answered we are going to skip human answer 
        raise NodeInterrupt(f"Thanks for answering the question {current_question_id}")
    else:
        return {'stage': stage}
        

def node_parse_output(state:AgentState)-> dict:
    """Parse de output table by modifiying the 8b based on human feedback.
    8a is updated as well based on the values in the state.

    Args:
        state (AgentState): _description_

    Returns:
        dict: _description_
    """
    print("---Step 6---")
    stage = state['stage'] + 1
    df_output_str = state['df_output']
    df_output = df_string_encoder_decoder(df_str=df_output_str)
    df_output['Criteria 8a'] = [state['criteria_8a_status']]
    df_output['Criteria 8b'] =  [state['criteria_8b_status']]
    print('-----------Node output-------------------')
    df_output_str = df_string_encoder_decoder(df=df_output)
    print(df_output)
    return {'df_output': df_output_str, 'stage': stage} 

def build_graph():
    # Node definitions
    builder = StateGraph(AgentState)
    builder.add_node("node_get_human_equipment", node_get_human_equipment)
    builder.add_node("node_rag", node_rag)
    builder.add_node("node_human_feedback", node_human_feedback)
    builder.add_node("node_question", node_question)
    builder.add_node("node_update_8b", node_update_8b)
    builder.add_node("node_parse_output", node_parse_output)

    # Node edges:
    builder.add_edge(START, "node_get_human_equipment")
    builder.add_edge("node_get_human_equipment", "node_rag")
    builder.add_conditional_edges("node_rag", eval_criteria_8a, {'criteria_8a_is_true': "node_question",  "criteria_8a_is_false": 'node_update_8b'})
    builder.add_edge("node_question", "node_human_feedback")
    builder.add_conditional_edges("node_human_feedback", continue_questions, {'skip_questions': "node_update_8b",  "go_to_next_question": "node_question"})
    builder.add_edge("node_update_8b", "node_parse_output")
    builder.add_edge("node_parse_output", END)
    return builder

if __name__ == "__main__":
    print('------------------------start-----------------------------')
    builder = build_graph()
    # You MUST use a checkpoiner when using breakpoints. This is because your graph needs to be able to resume execution. (https://langchain-ai.github.io/langgraph/concepts/low_level/#configuration)
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory) 

    stop_flag = True
    equipment = input('Hi! Please indicate the equipment to check:  ')
    config = {"configurable": {"thread_id": "1"}}
    initial_input = {"stage":0, "equipment":equipment}
    for event in graph.stream(initial_input, config, stream_mode="values"):
        print('------------------------step-----------------------------')
    while stop_flag:

        for event in graph.stream(None, config, stream_mode="values"):
            print(event)
        
        if len(graph.get_state(config).next)==0: # if there are not more next steps to execute
            print('------------------------end----------------------------')
            print(df_string_encoder_decoder(df_str =event['df_output']))
            stop_flag = False
            break

        if graph.get_state(config).next[0] == 'node_human_feedback':
            human_answer = input("Please answer the question with 'yes' or 'no':  ") 
            graph.update_state(config, {"human_message": human_answer}, as_node="node_human_feedback")


        """"
        for event in graph.stream(None, config, stream_mode="values"):
            print(event)

        if event['current_question_id'] == 'question_end' or event['criteria_8a_status'] is False:
            strop_flag = False
            print('-----------------------Analysis is done ------------------------------')
            print(event['df_output'])
            break
        else:
            human_answer = input("Please answer the question with 'yes' or 'no':  ") 
            graph.update_state(config, {"human_message": human_answer}, as_node="node_human_feedback")
        """

