import streamlit as st
from client import get_ai_output, post_human_message, reset_agent, get_group_names


st.title("System Impact classification agent")
st.write("AI assistant that drives user to manage system criteria on manufacturing based on historical records and human feedback")

example_text_start =  "i.e Cooler"
example_text_re_start = "i.e Generator"

st.write("Start the conversation indicanting equipment name and replying the questions with yes or not")

button_3 = st.button("Show all equipment groups")
if button_3:
    df_group_names = get_group_names()
    st.table(df_group_names)


button_0 = st.button("send message")
text_input = st.text_input("write your answer here") # Be carfuly every changes on the UI will be taked into consideration 

if text_input and button_0 : # if text is empty or has default values do not call the method 
    ai_message_output = post_human_message(text_input)   
    st.write(f"You've entered {text_input}")
    st.write("AI message : ")
    st.write(ai_message_output)
elif text_input and not button_0:
    st.write("Press the button 'send message' ")
else:
    st.write("Write a message and press the button 'send message' ")


button_1 = st.button("Click here to get the output")

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

