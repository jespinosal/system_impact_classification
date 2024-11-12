import streamlit as st
import pandas as pd
from bot import df_string_encoder_decoder, build_graph, MemorySaver
from custom_rag import get_map_equipment_groups




def main_call(user_input: str, event:dict, reset_agent:bool=False): # todo add human_input as parameter and use it instead keyboard 'input' in lines 229 and 250
    
    if reset_agent:
        reset_graph()
        print('------------------------restart-----------------------------')
        return {'ai_message': 'The agent has  been restarted, please write the new equipment to check'}

    if len(st.session_state['graph'].get_state(st.session_state['config']).values)==0: # First iteration
        print('------------------------start-----------------------------')
        ai_message = f'Hi! we will check your equipment {user_input}:  '
        print(ai_message)
        initial_input = {"stage":0, "equipment":user_input}
        input_data = initial_input
    else:
        input_data = None
        if len(st.session_state['graph'].get_state(st.session_state['config']).next)==0: # Last iteration: if there are not more next steps to execute (check it first as graph.get_state(config).next[0] throw error in last iter)
            print('------------------------end----------------------------')
            ai_message = "Analysis is done!"
            print(ai_message)
            print(df_string_encoder_decoder(df_str =event['df_output']))

        elif st.session_state['graph'].get_state(st.session_state['config']).next[0] == 'node_human_feedback': # Intermediate execution: the ones that require human feedback
            print('--------------------user feedback-------------------------')
            ai_message =  event['ai_message']
            print("system question:", ai_message)
            #human_answer = input("Please answer the question with 'yes' or 'no':  ") 
            st.session_state['graph'].update_state(st.session_state['config'], {"human_message": user_input}, as_node="node_human_feedback")
            # Todo --> return ai_message  
        else:
            print("---------------------Unknown state---------------------")

    event = st.session_state['graph'].invoke(input_data, st.session_state['config']) # Will be executed till next interuption
    return event

# Need to be executed just once on the API life. @todo add reset function to process more than one after MVE
def reset_graph():
    builder = build_graph()
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory) 
    config = {"configurable": {"thread_id": "1"}}
        
    st.session_state['builder'] = builder
    st.session_state['memory'] = memory
    st.session_state['event'] = {}
    st.session_state['graph'] = graph
    st.session_state['config'] = config

st.title("System Impact classification agent")
st.write("This is an AI assistant that drives the user to identify system impact criteria on manufacturing use cases based on historical records and human feedback")
st.write("Start the conversation by indicating the equipment name and replying to the questions with 'yes' or 'not' if the system formulates any question.")

# Create global variables first code invation
try:
    state = st.session_state['event']
    print('Agent already initialized')
    print(state)
except:
    reset_graph()
    print("Initializing the agent")

button_show_equipment_gropus = st.button('Show equipment groups')
if button_show_equipment_gropus:
    _, _, df_group_names = get_map_equipment_groups()
    st.dataframe(df_group_names)

button_send_message = st.button('send message')
input_text = st.text_input('Write here')

if input_text and button_send_message:
    try:
        st.session_state['event'] = main_call(user_input=input_text, event=st.session_state['event'], reset_agent=False)
        ai_message = st.session_state['event']['ai_message']
        st.text(ai_message)
    except: # If graph fail, we'll restart the agent to start from scratch
        st.session_state['event'] = main_call(user_input='None', event={}, reset_agent=True)
        ai_message = st.session_state['event']['ai_message']
        st.text(ai_message)


button_show_table = st.button("Show impact table")
if button_show_table:
    df_output_str = st.session_state['event'].get('df_output', 'output is not done')
    if df_output_str == 'output is not done':
        df_output = pd.DataFrame([{df_output_str: "Please, provide an equipment on the chat window"}])
    else:
        df_output = df_string_encoder_decoder(df_str=df_output_str)
    st.dataframe(df_output)


button_reset = st.button('Press here to re start the agent')

if button_reset:
    st.session_state['event'] = main_call(user_input='None', event={}, reset_agent=True)
    ai_message = st.session_state['event']['ai_message']
    st.text(ai_message)
