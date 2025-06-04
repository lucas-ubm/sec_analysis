import edgar_crawler
import extract_items
import json
import pandas as pd
import os
import glob
import re 

def read_file(file_name:str) -> dict:
    with open(file_name, 'r') as handle:
      content = json.load(handle)
    return content


def search_file(file:dict, search_terms:list, sections:list=["1", "1A", "3", "7"], ignore_case:bool=True, regex_search:bool=True):
  flags = re.IGNORECASE if ignore_case else 0
  if regex_search:
    search_pattern = re.compile(r'\b(' + '|'.join(search_terms) + r')\b', flags)
  else:
    search_pattern = re.compile(r'\b(' + '|'.join(re.escape(term) for term in search_terms) + r')\b', flags)
  document_results = {}
  document_results['company'] = file['company']
  document_results['cik'] = file['cik']
  document_results['filing_date'] = file['filing_date']
  document_results['period_of_report'] = file['period_of_report']
  document_results['filename'] = file['filename']

  filled=False

  for section in sections:
      if f'item_{section}' in file:
            content = file[f'item_{section}']
            matches = list(search_pattern.finditer(content))
            for match in matches:
                keyword = match.group(0)

                # Extract the surrounding sentence
                start_index = content.rfind('.', 0, match.start()) + 1
                end_index = content.find('.', match.end())
                if end_index == -1:  # If no period found, go to the end of the string
                    end_index = len(content)
                sentence = content[start_index:end_index].strip()

                # Extract the paragraph containing the keyword (starting and ending with a newline)
                paragraph_start = content.rfind("\n", 0, match.start()) + 1  # Start of paragraph
                paragraph_end = content.find("\n", match.end())  # End of paragraph
                if paragraph_end == -1:  # If no newline is found after the match, go to the end of the string
                    paragraph_end = len(content)
                paragraph = content[paragraph_start:paragraph_end].strip()

                # Append match details
                if f'{section}_matches' not in document_results:
                    document_results[f'{section}_matches'] = []
                    filled=True
                document_results[f'{section}_matches'].append({
                    "keyword": keyword,
                    "sentence": sentence,
                    "paragraph": paragraph, 
                    "match_id": f'{file["cik"]}_{section}_{keyword}_{start_index}_{end_index}'})
  if not filled:
    document_results = None
  return document_results   

def load_config(config_path:str="config.json"):
    with open(config_path, "r") as f:
        config = json.load(f)
    if 'topic' in config:
        topic = config["topic"]
    if 'raw_filings_folder' not in config['edgar_crawler']:
        config['edgar_crawler']['raw_filings_folder'] = f'{topic}_raw_filings'
    if 'raw_filings_folder' not in config['extract_items']:
        config['extract_items']['raw_filings_folder'] = f'{topic}_raw_filings'

    if 'filings_metadata_file' not in config['extract_items']:
        config['extract_items']['filings_metadata_file'] = f'{topic}_filings_metadata.csv'
    if 'filings_metadata_file' not in config['edgar_crawler']:
        config['edgar_crawler']['filings_metadata_file'] =f'{topic}_filings_metadata.csv'

    if 'filing_types' not in config['extract_items']:
        config['extract_items']['filing_types'] = config['filing_types']
    if 'filing_types' not in config['edgar_crawler']:
        config['edgar_crawler']['filing_types'] = config['filing_types']
    

    if 'indices_folder' not in config['edgar_crawler']:
        config['edgar_crawler']['indices_folder'] = f'{topic}_indices'
    if 'extracted_filings_folder' not in config['extract_items']:
        config['extract_items']['extracted_filings_folder'] = f'{topic}_extracted_filings'

    if 'mentions_name' not in config['extract_keywords']:
        config['extract_keywords']['mentions_name'] = f'{topic}_mentions'
    
    return config

def extract_mentions(config_path:str=None, config:dict=None): 
    assert config_path is not None or config is not None, "config_path or config must be provided"
    if config is None:
        with open(config_path) as fin:
            config = json.load(fin)
    
    mentions_name = config['extract_keywords']['mentions_name']

    files_dir = fr"datasets\{config['extract_items']['extracted_filings_folder']}"
    files = glob.glob(files_dir+r'\*')
    relevant_filings = pd.read_csv(f"datasets/{config['extract_items']['filings_metadata_file']}")

    relevant_files = [file for file in files if f"{os.path.basename(file).split('.')[0]}.htm" in relevant_filings['filename'].values]

    assert len(relevant_files) == len(relevant_filings), "Not all relevant filings found in extracted files directory"
    
    if not os.path.exists(f"datasets/{mentions_name}_processed.csv"):
        # Create a new DataFrame with the specified columns
        processed_mentions = pd.DataFrame(columns=['file_name', 'mentions', 'processing_date']).set_index('file_name')
        processed_mentions.to_csv(f"datasets/{mentions_name}_processed.csv")
    else:
        processed_mentions = pd.read_csv(f"datasets/{mentions_name}_processed.csv").set_index('file_name')
    existing = processed_mentions.index.tolist()
    to_process = [file for file in relevant_files if file not in existing]
    json_files = {}

    for i, file in enumerate(to_process):
        example_file = read_file(file)
        keywords = search_file(example_file, config['extract_keywords']['search_terms'], ignore_case=config['extract_keywords']['ignore_case'], regex_search=config['extract_keywords']['regex_search'])
        processed_mentions.loc[file] = pd.Series([None, pd.to_datetime('now', utc=True).date()], index=processed_mentions.columns)
        if keywords:
            json_files[file] = keywords
            # Save the results to a JSON file
            mentions_file = file.replace('.json', '_matches.json').replace(config['extract_items']['extracted_filings_folder'], mentions_name)
            if not os.path.exists(os.path.dirname(mentions_file)):
                os.makedirs(os.path.dirname(mentions_file))
            with open(mentions_file, 'w') as f:
                json.dump(keywords, f, indent=4)
            processed_mentions.loc[file, 'mentions'] = mentions_file

        if i % 100 == 0 and i > 0:
            print(f"{i} files processed, {len(json_files)} files with keywords found, {len(to_process)-i} files remaining")
            # Take out of loop if you don't want to save every 100 files
            processed_mentions.to_csv(f"datasets/{mentions_name}_processed.csv")
    processed_mentions.to_csv(f"datasets/{mentions_name}_processed.csv")

    json_files = {}
    files_paths = glob.glob(f"datasets/{mentions_name}/*")
    for i, file in enumerate(files_paths):
        with open(file, 'r') as handle:
            content = json.load(handle)
        json_files[file] = content
        if i % 100 == 0 and i > 0:
            print(f"{i} files loaded, {len(files_paths)-i} files remaining")
    df_rows = []
    for file in json_files:
        match_fields = [match for match in json_files[file].keys() if match.endswith('_matches')]
        non_match_fields = [match for match in json_files[file].keys() if not match.endswith('_matches')]
        for match_field in match_fields:
            for match in json_files[file][match_field]:
                row = {}
                row.update({field: json_files[file][field] for field in non_match_fields})
                row['keyword'] = match['keyword']
                row['sentence'] = match['sentence']
                row['match_id'] = match['match_id']
                row['match_field'] = match_field
                df_rows.append(row)

    matches_df = pd.DataFrame(df_rows)
    matches_df['filing_year'] = pd.to_datetime(matches_df['filing_date']).dt.year 
    matches_df['reporting_year'] = pd.to_datetime(matches_df['period_of_report']).dt.year
    matches_df.to_csv(f'datasets/{mentions_name}.csv', index=False)
    matches_df.to_excel(f'datasets/{mentions_name}.xlsx', index=False)


def main(config_path:str="config.json"):
    config = load_config(config_path)
    edgar_crawler.main(config=config)
    extract_items.main(config=config)
    extract_mentions(config=config)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract mentions of AI-related keywords from SEC filings.")
    parser.add_argument('--config', type=str, default='config.json', help='Path to the configuration file.')
    args = parser.parse_args()
    
    main(args.config)