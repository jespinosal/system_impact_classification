"""
Load and parse data source.

Notes:
- Good to keep original names in summary table in order to maximze 
- Use partial promp with Langchain to answer  querries from summary table  -- if amount of equiments increases use proper RAG solution.
- The equiment name groups could be generated using GenAi or by hand, or both by modifying the file data/data_groups.xlsx

"""
import os
import pandas as pd
from pydantic import BaseModel, ValidationError, field_validator

class DataFrameSchema(BaseModel):
    # @todo add field and methods for relevant validations (Yes/No field), check nulls, filenames etc
    col_1 : str


class DataMerger:
    """Load all available data sourcers in PDF and Excel format from different sites and merge sources in one table
    """
    def __init__(self, path_folder:str) -> None:
        self.path_folder = path_folder
        self.data_merged_file =  os.path.join(self.path_folder,'merged_sites_table.xlsx')
        
    def table_sanity_check(self):
        NotImplemented
   
    def merge_folder_files(self:str)-> pd.DataFrame: 
        """Build one table taking into consideration valid files in path_folder

        Args:
            self (str): _description_

        Returns:
            pd.Dataframe: _description_
        """
        files = os.listdir(self.path_folder) 
        table_accumulator = []
        for file in files:
            _, file_extension = os.path.splitext(file)
            if file_extension == '.xlsx' and '~$' not in file and file != os.path.basename(self.data_merged_file):
                print(f"Mergering file {file}")
                df = self.load_excel_file(file)
                table_accumulator.append(df)
            else:
                pass #raise(TypeError, "System only support xlsx files")
        df_consilidated = pd.concat(table_accumulator, axis=0)
        return df_consilidated
    
    def load_excel_file(self:str, file_path:str)->pd.DataFrame:
        # @todo implement basic data validation/imputation/parse if needed
        return pd.read_excel(os.path.join(self.path_folder, file_path))

    @staticmethod
    def get_equipment_names(df:pd.DataFrame) ->str:
        return df['Equipment Group'].values
    
    @staticmethod
    def load_pdf_files(self):
        pass


class EquipmentNameMatcher:    
    """Load table and generate group id based on text similarity of given column
    """
    def parse():
        pass


class DataAggregator:
    """Generate a summary table taking into given an aggreation column and agg operation
    """
    def parse():
        pass


if "__main__" == __name__:
    pass