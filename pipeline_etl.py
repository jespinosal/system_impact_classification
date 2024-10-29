import os
from data_loader import DataMerger
from data_parser import estimate_equipment_group_names
from config import config


def main():
    # Load and merge data sources from different sites
    print(f"Loading and mergering data sources cross all the sites from {config['folder_data_raw']}")
    data_path = config['folder_data_raw']
    data_merger = DataMerger(data_path)
    df_merged = data_merger.merge_folder_files()
    print(df_merged)

    # Generate equipment names group
    print('Computing group names based on equipment names')
    equipment_names = data_merger.get_equipment_names(df_merged)
    print("equipment names:", equipment_names)
    df_group_names = estimate_equipment_group_names(equipment_names)
    print(df_group_names)

    # Estimate equipement probabilities
    print('Calculating equipment criteria scores')
    df_names_exploded = df_group_names.explode('equipments')
    df_merged_renamed = df_merged.merge(df_names_exploded, left_on='Equipment Group', right_on='equipments', how='left')
    df_merged_renamed = df_merged_renamed.replace()
    cols_bool = ['Criteria 1', 'Criteria 2', 'Criteria 3', 'Criteria 4', 'Criteria 5', 'Criteria 6', 'Criteria 7', 'Criteria 8a', 'Criteria 8b']
    map_answers = {'Yes':1, 'No': 0}
    df_merged_renamed[cols_bool] = df_merged_renamed[cols_bool].replace(map_answers).astype(int)
    df_agg_scores = df_merged_renamed[cols_bool+['equipment_group_name']].groupby(['equipment_group_name']).mean()
    df_agg_scores = df_agg_scores.reset_index()
    print(df_agg_scores)

    # Save artifacts:
    if not os.path.isdir(config['folder_data_processed']):
        print(f"Creating {config['folder_data_processed']} directory")
        os.makedirs(config['folder_data_processed'])
    print('Saving artifacts')
    df_merged_renamed.to_csv(os.path.join(config['folder_data_processed'], config['filename_merged_historical_records']), index=False)
    df_group_names.to_csv(os.path.join(config['folder_data_processed'], config['filename_map_equipment_groups']), index=False)
    df_agg_scores.to_csv(os.path.join(config['folder_data_processed'], config["filename_equipment_group_probs"]), index=False)


if __name__=="__main__":
    main()