import streamlit as st
from client import get_ai_output, post_human_message, reset_agent, get_group_names


st.title("System Impact classification agent")
st.write("This is an AI assistant that drives the user to identify system impact criteria on manufacturing use cases based on historical records and human feedback")
st.write("Start the conversation by indicating the equipment name and replying to the questions with 'yes' or 'not' if the system formulates any question.")

button_3 = st.button("Show all equipment groups")
if button_3:
    df_group_names = get_group_names()
    st.table(df_group_names)


button_0 = st.button("Send message")
text_input = st.text_input("Please, write your answer here") # Be carfuly every changes on the UI will be taked into consideration 

if text_input and button_0 : # if text is empty or has default values do not call the method 
    ai_message_output = post_human_message(text_input)   
    st.write(f"You've entered {text_input}")
    st.write("AI message : ")
    st.write(ai_message_output)
elif text_input and not button_0:
    st.write("Press the button 'Send message' to process your request ")
else:
    st.write("Write your message and press the button 'Send message' to continue")


button_1 = st.button("Get criteria table")

if button_1:
    df_output = get_ai_output() 
    st.dataframe(df_output)

button_2 = st.button("Start new analysis")

if button_2:
    # st.empty() ---> text is restarded using last text
    ai_message_reset = reset_agent() 
else:
    ai_message_reset = 'Agente is ready'

st.write(ai_message_reset)





#  streamlit run front_end_st.py

