import os
from typing import List
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser 


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


class EquipmentGroup(BaseModel):
    """
        This class is going to capture one group of equipments on the list 'equipments' under the groupd name 'equipment_group_name'.
    """
    equipment_group_name: str = Field(description="Group name of equipments")
    equipments: List[str] = Field(description="List of all the equipments that belong to group indicated in equipment_group_name. One or more elements from equipment_list fit here")


class EquipmentGroups(BaseModel):
    """
        This class is used to srore the collections/list of EquipmentGroup.
    """
    equipment_groups: List[EquipmentGroup]


def estimate_equipment_group_names(equipment_list: List[str]) -> pd.DataFrame:
    """
    LLM call to generate equimpment group names based on similar equipments on equipment_list
    # @todo modify prompt to focus on corner cases (like plural equipment names)
    # @todo add Guardrails to a) Check all names exists b) Group name meet business requirements
    """
    output_parser = PydanticOutputParser(pydantic_object = EquipmentGroups)

    output_format_instructions = output_parser.get_format_instructions()

    equipment_list = ", ".join(equipment_list)

    promt_template = """You are an assistant expert in manufactoring area, you need to group the following equipments in groups.

    Instructions:
    1. Generate groups based on similarity of words of equipment names in equipment_list. Some equipments has been named using synonims
    2. Generate a meaningful name for each group
    3. Generate the output as follows: 
    {output_format_instructions}

    equipment_list to process:
    {equipment_list}

    """

    system_promt = PromptTemplate(template=promt_template, input_variables=['equipment_list', 'output_format_instructions'])

    chain = system_promt | llm | output_parser


    results = chain.invoke({'equipment_list':equipment_list,
                            'output_format_instructions': output_format_instructions})
    
    return pd.DataFrame([dict(result) for result in results.equipment_groups])