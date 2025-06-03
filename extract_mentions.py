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


def extract_keywords(file:dict, sections:list=["1", "1A", "3", "7"], search_terms:list=[]):
  search_terms = ["Artificial Intelligence","A\.I", "Machine Learning","Deep Learning","NLP",
    "Natural Language Processing", "Computer Vision", "Chatbot","Recommendation System", "Recommender System", "Image Recognition", "Speech Recognition", "Voice Assistant",
    "Artificial General Intelligence","AGI", "generative", "deepfake"]
  search_pattern = re.compile(r'\b(' + '|'.join(search_terms) + r')\b', re.IGNORECASE)
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

def mention_extraction(files:list, file_name:str, sections:list=["1", "1A", "3", "7"], search_terms:list=[]):
    ## Matches extraction and saving to files 
    # Took ~35m for 5 years of data, may take less if files not saved considering everything fit in memory.
    processed_mentions = pd.read_csv(f"datasets/{file_name}.csv").drop(columns=['Unnamed: 0']).set_index('file_name')
    existing = processed_mentions.index.tolist()
    to_process = [file for file in files if file not in existing]
    json_files = {}
    # processed_mentions = pd.read_csv(r"C:\Users\P70088982\Documents\edgar-crawler\datasets\processed_mentions.csv").set_index('file_name')
    # to_process = [file for file in files if file not in processed_mentions['file_name'].values]
    for i, file in enumerate(to_process):
        example_file = read_file(file)
        keywords = extract_keywords(example_file)
        processed_mentions.loc[file] = pd.Series([None, pd.to_datetime('now', utc=True).date()], index=processed_mentions.columns)
        if keywords:
            json_files[file] = keywords
            # Save the results to a JSON file
            mentions_file = file.replace('.json', '_matches.json').replace('extracted_filings', 'ai_mentions')


            with open(mentions_file, 'w') as f:
                json.dump(keywords, f, indent=4)
            processed_mentions.loc[file, 'mentions'] = mentions_file

        if i % 100 == 0:
            print(f"{i} files processed, {len(json_files)} files with keywords found, {len(to_process)-i} files remaining")
            # Take out of loop if you don't want to save every 100 files
            processed_mentions.to_csv(f"datasets/{file_name}.csv")

    json_files = {}
    files_paths = glob.glob(r"C:\Users\P70088982\Documents\edgar-crawler\datasets\ai_mentions\*")
    for i, file in enumerate(files_paths):
        with open(file, 'r') as handle:
            content = json.load(handle)
        json_files[file] = content
        if i % 100 == 0:
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
    matches_df.to_csv(r'C:\Users\P70088982\Documents\edgar-crawler\datasets\ai_mentions.csv', index=False)
    matches_df.to_excel(r'C:\Users\P70088982\Documents\edgar-crawler\datasets\ai_mentions.xlsx', index=False)

def extract_mentions(config_path:str="config.json"): 
    with open(config_path, "r") as f:
        config = json.load(f)
    print(config)

    files_dir = 'datasets/extracted_filings'
    files = glob.glob(files_dir+r'\*')
    relevant_filings = pd.read_csv(f'datasets/{config['extract_items']['filings_metadata_file']}')
    relevant_files = [file for file in files if f'{os.path.basename(file).split('.')[0]}.htm' in relevant_filings['file_name'].values]
    assert len(relevant_files) == len(relevant_filings), "Not all relevant filings found in extracted files directory"
    file_name = config['extract_keywords']['extract_keywords_file_name']
    # mention_extraction(relevant_files, file_name, search_terms=config['extract_keywords']['search_terms'])


def main(config_path:str="config.json"):

    edgar_crawler.main(config_path)
    extract_items.main(config_path)
    extract_mentions(config_path)

    