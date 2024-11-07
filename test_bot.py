import unittest 
import pandas as pd
from langgraph.checkpoint.memory import MemorySaver
from bot import build_graph, df_string_encoder_decoder


def bot_loop(user_input_equipment, user_input_answer, builder, run_question_loop):
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory) 
    config = {"configurable": {"thread_id": "1"}}
    initial_input = {"stage":0, "equipment":user_input_equipment}

    for event in graph.stream(initial_input, config, stream_mode="values"):
        print('------------------------step-----------------------------')
  
    while run_question_loop:

        for event in graph.stream(None, config, stream_mode="values"):
            print(event)
        
        if len(graph.get_state(config).next)==0: # if there are not more next steps to execute
            print('------------------------end----------------------------')
            run_question_loop = False
            break

        if graph.get_state(config).next[0] == 'node_human_feedback':
            human_answer = user_input_answer
            graph.update_state(config, {"human_message": human_answer}, as_node="node_human_feedback")
    return event




class TestGraphQuestions(unittest.TestCase):

    def test_all_no(self):
        run_question_loop = True
        user_input_equipment = 'Cooler'
        user_input_answer = 'no'
        builder = build_graph()
        event = bot_loop(user_input_equipment, user_input_answer, builder, run_question_loop)
        # Test Criteria 8B is FALSE
        df_output = df_string_encoder_decoder(df_str =event['df_output'])
        self.assertEqual(df_output['Criteria 8b'].values[0], False)

        
    def test_all_yes(self):
        run_question_loop = True
        user_input_equipment = 'Cooler'
        user_input_answer = 'yes'
        builder = build_graph()
        event = bot_loop(user_input_equipment, user_input_answer, builder, run_question_loop)
        # Test Criteria 8B is True
        df_output = df_string_encoder_decoder(df_str =event['df_output'])
        self.assertEqual(df_output['Criteria 8b'].values[0], True)




class TestGraphRag(unittest.TestCase): # Test Main node
    def test_rag_direct_match(self):
        run_question_loop = False
        user_input_equipment = 'Cooler'
        user_input_answer = 'yes'
        builder = build_graph()
        event = bot_loop(user_input_equipment, user_input_answer, builder, run_question_loop)
        # Test return expected value
        self.assertIn('Cooling', event['df_output'])
        self.assertI(user_input_equipment, event['df_output'])

    def test_rag_indirect_match(self):
        run_question_loop = False
        user_input_equipment = 'Freezer'
        user_input_answer = 'yes'
        builder = build_graph()
        event = bot_loop(user_input_equipment, user_input_answer, builder, run_question_loop)
        self.assertIn('Cooling', event['df_output'])
        self.assertIn(user_input_equipment, event['df_output'])

    def test_rag_fallback():
        pass


class TestGraphRouting(unittest.TestCase):

    def test_skip_questions(self):
        run_question_loop = False
        user_input_equipment = 'Generator'
        user_input_answer = 'yes'
        builder = build_graph()
        event = bot_loop(user_input_equipment, user_input_answer, builder, run_question_loop)
        # Test Criteria_8a False
        df_output = df_string_encoder_decoder(df_str =event['df_output'])
        self.assertEqual(df_output['Criteria 8a'].values[0], False)

    def test_go_to_questions(self):
        run_question_loop = False
        user_input_equipment = 'Cooler'
        user_input_answer = 'yes'
        builder = build_graph()
        event = bot_loop(user_input_equipment, user_input_answer, builder, run_question_loop)
        # Test Criteria_8a False
        df_output = df_string_encoder_decoder(df_str =event['df_output'])
        self.assertEqual(df_output['Criteria 8a'].values[0], True)



class TestGraphOutput(unittest.TestCase):

    def test_output_structure(self):
        run_question_loop = True
        user_input_equipment = 'Cooler'
        user_input_answer = 'yes'
        builder = build_graph()
        event = bot_loop(user_input_equipment, user_input_answer, builder, run_question_loop)
        # Test pandas structure, implemente inverse conversion str to pd
        df_output_str = event['df_output']
        df_output = df_string_encoder_decoder(df_str=df_output_str)
        

        data_format = {'event': dict, 'df_output_str': str, 'df_output': pd.DataFrame, 
                'df_cols': ['equipment group name', 'Criteria 1', 'Criteria 2', 'Criteria 3',
                            'Criteria 4', 'Criteria 5', 'Criteria 6', 'Criteria 7', 'Criteria 8a',
                            'Criteria 8b', 'equipment name']}
        
        self.assertIsInstance(event, data_format['event'])
        self.assertIsInstance(event['df_output'], data_format['df_output_str'])
        self.assertIsInstance(df_output, data_format['df_output'])
        
        for col in data_format['df_cols']:
            self.assertIn(col, df_output_str)



if __name__=="__main__":
    pass
    
