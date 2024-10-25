"""
Load and parse data source.

Notes:
- Good to keep original names in summary table in order to maximze 
- Use partial promp with Langchain to answer  querries from summary table  -- if amount of equiments increases use proper RAG solution.
"""


class DataLoader:
    """Load all available data sourcers in PDF and Excel format and merge sources in one table
    """
    def __init__(self, path_folder:str) -> None:
        self.path_folder = path_folder

    def load_excel_files():
        pass

    def load_pdf_files():
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