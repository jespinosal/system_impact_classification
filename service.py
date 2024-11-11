from pydantic import BaseModel
import uvicorn
from fastapi import FastAPI
from bot_as import main_call # , graph as bot_graph


class UserInput(BaseModel):
  human_answer: str

# @todo add parser for return output as well
class GeneratedOutput(BaseModel):     
    text: str 
    topic: str

app = FastAPI()
app.counter = 0
app.event_output = {}
#app.bot_graph = bot_graph


# To interact with bot
@app.post('/process_input_message')
async def process_input_message(data:UserInput):
   human_answer = data.human_answer
   event_output = await main_call(user_input=human_answer, event=app.event_output)
   app.event_output = event_output
   app.counter+=1
   ai_message = event_output['ai_message']
   return {'ai_message': f'system answer:  {ai_message}', 'counter':app.counter}


# To interact with button 'get output', user can press button in between (get 1 to 7 criteria) or at the end  (get 1 to 8 criteria)
@app.get('/get_output')
def process_output_message():
  app.counter+=1
  df_output = app.event_output.get('df_output', 'output is not done')
  return {'output_table': df_output}


@app.get('/reset')
async def reset_graph():
  app.counter = 0
  event_output = await main_call(user_input='None', event={}, reset_agent=True)
  ai_message = event_output['ai_message']
  return {'ai_message': ai_message}
  
  # Ideas more get/button functions --> Get requirment group name, get group sysnonims, 
  # @todo add reset option to restar graph (for POC)
  
if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000) # uvicorn service:app --reload    ---> http://127.0.0.1:8000/docs



