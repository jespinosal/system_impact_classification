from io import StringIO
import pandas as pd

# Note: we can manage all the 8a question flow in one node. But having indivial flows will be benefitial for demo purposes and debugging.
def df_string_encoder_decoder(df=None, df_str= None):
    """As states are not seriallizable, we need to transform pandas to str to keed values in state and str to pandas to compute calculations
    """
    # Step required to des-serialzie str DF. Cols should avoid whitespaces
    if df is None and isinstance(df_str, str):
        print('decoding str to pandas')
        df = pd.read_csv(StringIO(df_str), sep='\s+')
        df['equipment_group_name'] = df['equipment_group_name'].apply(lambda x: x.replace("_", " "))
        df.columns = [col.replace("_", " ") for col in df.columns]
        return df
    elif isinstance(df, pd.DataFrame) and df_str is None:
        print('encoding str to pandas')
        df.columns = [col.replace(" ", "_") for col in df.columns]
        df['equipment_group_name'] = df['equipment_group_name'].apply(lambda x: x.replace(" ", '_'))
        df_str = df.to_string(index=False)
        return df_str
    else:
        raise(TypeError, "provide a valid pandas data frame or string parsed version")