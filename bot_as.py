"""
Implement Nodes to build conversational grahp: based on langchain and langgraph libraries
"""
import os
from typing import List, Optional, Annotated
from typing_extensions import TypedDict
from operator import add
import pandas as pd
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import NodeInterrupt
from config import config
from custom_rag import get_equipment_scores
from utils import  df_string_encoder_decoder

class AgentState(TypedDict):
    stage: int
    equipment: str
    human_message: str
    ai_message: str
    criteria_8a_status: bool
    criteria_8b_status: bool = False # Default doens't work need to update value in Node @todo check how to do 
    df_output: str # # pandas is not compatible "DataFrame is not serializable"
    current_question_id: str

        

async def node_get_human_equipment(state: AgentState):
    """Get human equioment name
    """
    # @todo add regex for alphabetic - Camell case - Add Guardrails?? -
    print('-----------Node get human equipment-------------------')
    equipment = state['equipment'].strip()
    stage = state['stage'] + 1
    equipment =  state['equipment']
    return {'equipment': equipment, 'stage': stage, 'current_question_id':0, 'criteria_8b_status':False }# Default 8B false and current_question_id=0 as not possinle to setup default value 

async def node_rag(state:AgentState):
    """Given human equipment find the most similar equipment group and return probs row wih the highest similarity
    """
    # @todo add fallback case and actions to take in that situation. At the moment unknowk equipments will broke the code
    print('-----------Node RAG-------------------')
    user_equipment = state['equipment']
    stage = state['stage'] + 1
    print(f"RAG for input: {user_equipment}")
    df_equipment_score = await get_equipment_scores(user_equipment=user_equipment)
    print("RAG Output:")
    print(df_equipment_score)
    value_8a = True if df_equipment_score['Criteria 8a'].values[0]>0.5 else False
    print(f"According to historical data 'Criteria 8a' is : {value_8a}")
    df_equipment_score_str = df_string_encoder_decoder(df=df_equipment_score)
    ai_message = f'Your request for {user_equipment} is done'
    return {'df_output': df_equipment_score_str,  'criteria_8a_status': value_8a, 'stage': stage, 'ai_message': ai_message} 

def eval_criteria_8a(state:AgentState):
    """Rooting criteria de dermine if we need to proceed with questions or not.
    criteria_8a_is_true : Proceed with questions
    criteria_8a_is_false: Skip questions
    """
    print("---Step 3---")
    if state['criteria_8a_status']:
        return 'criteria_8a_is_true'
    else:
        return 'criteria_8a_is_false'
    
def get_next_question(question_id:str, human_answer:str) -> dict:
    """This method compute the next question shopuld be asked based on current question/answer the method managed 3 uses cases:

    1- First step: For the first question is goint to ommit inputs, will return question 1 info ('question_1', "Content of question 1")
    2- Intermediate step: we'll return the next question data (question_id,  question_str_next) 
    3- Last step: Once last question is asked and answered this method will send ('question_end', 'Questionary is done') to indicate when to skip question loop

    The dictionary 'questions' maps question_id with corresponding text.  
    The question_id_edges describe the future step, given curren question and human answer which question should be asked?

    Args:
        question_id (str): id to identify question 
        human_answer (str): yes/no answer of question in question_id

    Returns:
        dict: question_id_next: id of next question will be asked to human 
              question_str_next: text of question that correspont to question_id_next
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
    

async def node_question(state: AgentState):
    """Get next question should be asked to human user
    """
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
    """Routing to determine if questionary loop is done
    skip_questions : questionary is done proceed with next step
    go_to_next_question: questionary need to be completed, iterate again on question loop
    """
    last_question_id = state['current_question_id']
    if last_question_id == 'question_end':
        return 'skip_questions'
    else:
        return 'go_to_next_question'

async def node_update_8b(state:AgentState):
    """Logic to determine how to update criteria_8b_status. Bools answer based on last question and human answers on questionary loop
    """
    # @todo add real logic. 
    if state['criteria_8a_status']: # If questions has made
        last_human_message = state['human_message']
        criteria_8b_status = True if last_human_message=='yes' else False
    else:
        criteria_8b_status = False
 
    return {'criteria_8b_status': criteria_8b_status}

async def node_human_feedback(state):
    """Interrupt graph execution if human feedback is needed. If questionary loop is done we can skip it.
    """
    stage = state['stage'] + 1
    current_question_id = state['current_question_id']
    print("---node human_feedback---") 
    print("Please answer the quesiton with yes/no answer")
    if state['current_question_id']!='question_end': # That means after the last question is answered we are going to skip human answer 
        raise NodeInterrupt(f"Thanks for answering the question {current_question_id}")
    else:
        return {'stage': stage}
        

async def node_parse_output(state:AgentState)-> dict:
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
    """Describe graph nodes and conextions (edges)
    """
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

async def main_call_bucle(): # todo add human_input as parameter and use it instead keyboard 'input' in lines 229 and 250
    
    while True: # todo, delete loop for steamlit app call. As graph will know next step which each invoke, is not mandatory async call.
                
        if len(graph.get_state(config).values)==0: # First iteration
            print('------------------------start-----------------------------')
            ai_message = 'Hi! Please indicate the equipment to check:  '
            equipment = input(ai_message)
            initial_input = {"stage":0, "equipment":equipment}
            input_data = initial_input
            # Todo --> return ai_message 
        else:
            input_data = None
            if len(graph.get_state(config).next)==0: # Last iteration: if there are not more next steps to execute (check it first as graph.get_state(config).next[0] throw error in last iter)
                print('------------------------end----------------------------')
                ai_message = "Analysis is done!"
                print(ai_message)
                print(df_string_encoder_decoder(df_str =event['df_output']))
                break # no needed to call graph again
                # Todo --> return df_str 
            elif graph.get_state(config).next[0] == 'node_human_feedback': # Intermediate execution: the ones that require human feedback
                print('--------------------user feedback-------------------------')
                ai_message =  event['ai_message']
                print("system question:", ai_message)
                human_answer = input("Please answer the question with 'yes' or 'no':  ") 
                graph.update_state(config, {"human_message": human_answer}, as_node="node_human_feedback")
                # Todo --> return ai_message  
            else:
                print("---------------------Unknown state---------------------")

        event = await graph.ainvoke(input_data, config)


async def main_call(user_input: str, event:dict, reset_agent:bool=False): # todo add human_input as parameter and use it instead keyboard 'input' in lines 229 and 250
    
    if reset_agent:
        global builder
        global memory
        global graph
        global config
        builder, memory, graph, config = reset_graph()
        print('------------------------restart-----------------------------')
        return {'ai_message': 'The agent has  been restarted, please write the new equipment to check'}

    if len(graph.get_state(config).values)==0: # First iteration
        print('------------------------start-----------------------------')
        ai_message = f'Hi! we will check your equipment {user_input}:  '
        print(ai_message)
        initial_input = {"stage":0, "equipment":user_input}
        input_data = initial_input

    else:
        input_data = None
        if len(graph.get_state(config).next)==0: # Last iteration: if there are not more next steps to execute (check it first as graph.get_state(config).next[0] throw error in last iter)
            print('------------------------end----------------------------')
            ai_message = "Analysis is done!"
            print(ai_message)
            print(df_string_encoder_decoder(df_str =event['df_output']))

        elif graph.get_state(config).next[0] == 'node_human_feedback': # Intermediate execution: the ones that require human feedback
            print('--------------------user feedback-------------------------')
            ai_message =  event['ai_message']
            print("system question:", ai_message)
            #human_answer = input("Please answer the question with 'yes' or 'no':  ") 
            graph.update_state(config, {"human_message": user_input}, as_node="node_human_feedback")
            # Todo --> return ai_message  
        else:
            print("---------------------Unknown state---------------------")

    event = await graph.ainvoke(input_data, config) # Will be executed till next interuption
    return event

# Need to be executed just once on the API life. @todo add reset function to process more than one after MVE
def reset_graph():
    builder = build_graph()
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory) 
    config = {"configurable": {"thread_id": "1"}}
    return builder, memory, graph, config

builder, memory, graph, config = reset_graph()

if __name__ == "__main__":
    
    import asyncio

    # Run all bucle
    # asyncio.run(main_call_bucle())


    # Run step by step: Firs step require human equipment name, the next 'no'/'yes' if criteria_8a=True
    event_output = asyncio.run(main_call(user_input="Cooler", event={})) # 
    print('output done 1st step', event_output)
    event_output = asyncio.run(main_call(user_input="no", event=event_output)) # need previous even result, i.e to show next question (calculated preious call) 
    print('output done 2nd step', event_output)
    event_output = asyncio.run(main_call(user_input="no", event=event_output)) # need previous even result, i.e to show next question (calculated preious call) 
    print('output done 3nd step', event_output)

    event_output = asyncio.run(main_call(user_input='None', event={}, reset_agent=True)) # need previous even result, i.e to show next question (calculated preious call) 
    print('output done 3nd step', event_output)
    event_output = asyncio.run(main_call(user_input="Generator", event={})) # continue next use case....
    
