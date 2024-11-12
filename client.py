import requests
import pandas as pd
from utils import df_string_encoder_decoder
from custom_rag import get_map_equipment_groups


def get_ai_output() -> pd.DataFrame:
    req = requests.get("http://127.0.0.1:8000/get_output")
    output = req.json()
    df_output_str = output['output_table']
    if df_output_str == 'output is not done':
        df_output = pd.DataFrame([{df_output_str: "Please, provide an equipment on the chat window"}])
    else:
        df_output = df_string_encoder_decoder(df_str=df_output_str)
    return df_output

def post_human_message(human_answer:str) ->str:
    params = {
    "human_answer":human_answer,
         }
    req = requests.post("http://127.0.0.1:8000/process_input_message", params=params, json=params)
    output = req.json()
    ai_message = output['ai_message']
    return ai_message

def reset_agent() -> pd.DataFrame:
    req = requests.get("http://127.0.0.1:8000/reset")
    output = req.json()
    ai_message = output['ai_message']
    return ai_message

def get_group_names()->str:
    #todo add request and put it into state on the graph to make dara accesible through the API (this is temp workaroound)
    _, _, df_group_names = get_map_equipment_groups()
    return df_group_names
