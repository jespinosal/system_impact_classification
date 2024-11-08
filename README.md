# System impact calssification 

- Introduction:
This GEN ai solution is based in langchain and langgraph to support SME's in manufactiring to get summaries from historical data of equipments. 
The user need to provide equipment and answer questions from system to get a report (table) with results about historical records.


-Devs info config:
* Intalls requirements (if you want to run notebooks in playground need to "pip instal notebook" manually)
* Create .env file with OpenAI Azure variables as .env_example describes

- Devs info execution: main files are pipeline_etl.py and bot.py that should be executed as follows:
* pipeline_etl.py: If folder "data_processed" is empty, or historical recorsd (excel files) has changed. This script should be executed to updated records.
The Scrip will provide 3 main outputs:
- *  data_processed\merged_historical_records.csv: Merge all the excel files available on data_raw
- *  data_processed\map_equipment_groups.csv: Using data_parser.py generate groups of similar equipments based on merged_historical_records.csv
- *  data_processed\equipment_group_probs.csv: Compute aggregation (mean) on equipment groups (considering 'yes' as 1 and 'no' as 0)
* bot.py: Once "data_processed" folder has the 3 above files you can run it on the terminal. To check the bot paths take a look to the file \playground\bot_flows_experiments_hitl_tree_default.ipynb that describe the graph work flow.

