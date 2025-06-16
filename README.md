# SEC data keyword-analysis
TODO: allow for year selection beyond 2024, check why nvidia is included in the analysis regardless of the specified CIKs. Provide short explanation (just copy pasted from the README).
The knowledge hidden in financial reports without the hassle. We provide an interface for the easy extraction of keywords from SEC forms. You provide the relevant keywords, companies and time range and we deliver insights. 

Through `EDGAR-CRAWLER` we crawl and download financial reports and extract relevant items in a conveninent format. We then identify whether the indicated keywords can be found in the form and in which section, extracting relevant sentences. An Excel sheet is provided for convenient and systematic analysis of relevant statements. 

### `EDGAR-CRAWLER` core modules:
📥🕷️ Business Documents Crawling: Utilize the power of the `edgar_crawler.py` module to effortlessly crawl and download financial reports for every publicly-traded company within your specified years.

🔍📑 Item Extraction: Extract and clean specific text sections such as Risk Factors or Management's Discussion & Analysis from 10-K documents (annual reports) using the `extract_items.py` module. Get straight to the heart of the information that matters most.

### Added module
📚🔬 Keyword Extraction: Use keywords and regular expressions to identify relevant statements in financial reports. Harnessing the output of `edgar-cralwer`'s module we offer a seamless method for identifying relevant keywords at scale. 

## Who Can Benefit from `EDGAR-CRAWLER`?
📚 Academics: Enhance your NLP research in economics & finance or business management by accessing and analyzing financial data efficiently.

💼 Professionals: Strengthen financial analysis, strategic planning, and decision-making with comprehensive, easy-to-interpret financial reports.

🛠 Developers: Seamlessly integrate financial data into your models, applications, and experiments using our open-source toolkit.

## Table of Contents
- [Install](#install)
- [Usage](#usage)
- [Citation](#citation)
- [License](#license)

## Install
- Before starting, it's recommended to create a new virtual environment using Python 3.8. We recommend [installing](https://docs.anaconda.com/anaconda/install/index.html) and [using Anaconda](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands) for this.
- Install dependencies via `pip install -r requirements.txt`

## Usage
You can test out the tool in https://web-production-3838.up.railway.app. 

We provide two different interfaces for the module through config files: one follows the `edgar-crawler` format for compatibility, the other one provides a simplified interface. Both produce the same behavior and there is no need to specify which kind of config you are using. We provide four example config files: `climate_simplified_config.json`, `climate_config.json`, `ai_simplified_config.json`, `ai_config.json`

### `edgar-crawler` style config
Before running any script, you should edit the `config.json` file, which configures the behavior of the 3 modules. The first two modules follow the format specified in `edgar-crawler`'s documentation, find them below for convenience.
  - Arguments for `edgar_crawler.py`, the module to download financial reports:
      - `start_year XXXX`: the year range to start from (default is 2021).
      - `end_year YYYY`: the year range to end to (default is 2021).
      - `quarters`: the quarters that you want to download filings from (List).<br> Default value is: `[1, 2, 3, 4]`.
      - `filing_types`: list of filing types to download.<br> Default value is: `['10-K', '10-K405', '10-KT']`.
      - `cik_tickers`: list or path of file containing CIKs or Tickers. e.g. `[789019, "1018724", "AAPL", "TWTR"]` <br>
        In case of file, provide each CIK or Ticker in a different line.  <br>
      If this argument is not provided, then the toolkit will download annual reports for all the U.S. publicly traded companies.
      - `user_agent`: the User-agent (name/email) that will be declared to SEC EDGAR.
      - `raw_filings_folder`: the name of the folder where downloaded filings will be stored.<br> Default value is `'RAW_FILINGS'`.
      - `indices_folder`: the name of the folder where EDGAR TSV files will be stored. These are used to locate the annual reports. Default value is `'INDICES'`.
      - `filings_metadata_file`: CSV filename to save metadata from the reports.
      - `skip_present_indices`: Whether to skip already downloaded EDGAR indices or download them nonetheless.<br> Default value is `True`.
  - Arguments for `extract_items.py`, the module to clean and extract textual data from already-downloaded 10-K reports:
    - `raw_filings_folder`: the name of the folder where the downloaded documents are stored.<br> Default value s `'RAW_FILINGS'`.
    - `extracted_filings_folder`: the name of the folder where extracted documents will be stored.<br> Default value is `'EXTRACTED_FILINGS'`.<br> For each downloaded report, a corresponding JSON file will be created containing the item sections as key-pair values.
    - `filings_metadata_file`: CSV filename to load reports metadata (Provide the same csv file as in `edgar_crawler.py`).
    - `items_to_extract`: a list with the certain item sections to extract. <br>
      e.g. `['7','8']` to extract 'Management’s Discussion and Analysis' and 'Financial Statements' section items.<br>
      The default list contains all item sections.
    - `remove_tables`: Whether to remove tables containing mostly numerical (financial) data. This work is mostly to facilitate NLP research where, often, numerical tables are not useful.
    - `skip_extracted_filings`: Whether to skip already extracted filings or extract them nonetheless.<br> Default value is `True`.
  - Arguments for `extract_keywords`: 
    - `search_terms`: a list with the terms to be searched, the terms can be regular expressions or strings. e.g. ["Artificial Intelligence","A.I", "AI"]
    - `ignore_case`: whether the search for terms should be case insensitive. Default value is True. 
    - `regex_search`: whether the terms should be compiled as regular expressions or not. Default value is True.
    - `mentions_name`: the name that the output files should have. 

### Simplified config
This simplified config resolves redundancies in the `edgar-crawler` config, ensuring consistency across the pipeline steps and ease of use. The config is transformed to `edgar-crwaler` style automatically, ensuring maximum compatibility.
In the config file you can specify:
  - `topic`: string representings the name of the topic your keywords relate to, all directories and files will be of the form `<topic>_<directory>` e.g. if the topic was climate, filings would be stored under `climate_raw_filings` and `climate_extracted_filings`
  - `filing_types`: list of filing types to download.<br> Default value is: `['10-K', '10-K405', '10-KT']`.
  - Arguments for `edgar_crawler.py`, the module to download financial reports:
      - `start_year XXXX`: the year range to start from (default is 2021).
      - `end_year YYYY`: the year range to end to (default is 2021).
      - `quarters`: the quarters that you want to download filings from (List).<br> Default value is: `[1, 2, 3, 4]`.
      - `cik_tickers`: list or path of file containing CIKs or Tickers. e.g. `[789019, "1018724", "AAPL", "TWTR"]` <br>
        In case of file, provide each CIK or Ticker in a different line.  <br>
      If this argument is not provided, then the toolkit will download annual reports for all the U.S. publicly traded companies.
      - `user_agent`: the User-agent (name/email) that will be declared to SEC EDGAR.
      - `skip_present_indices`: Whether to skip already downloaded EDGAR indices or download them nonetheless.<br> Default value is `True`.
  - Arguments for `extract_items.py`, the module to clean and extract textual data from already-downloaded 10-K reports:
    - `items_to_extract`: a list with the certain item sections to extract. <br>
      e.g. `['7','8']` to extract 'Management’s Discussion and Analysis' and 'Financial Statements' section items.<br>
      The default list contains all item sections.
    - `remove_tables`: Whether to remove tables containing mostly numerical (financial) data. This work is mostly to facilitate NLP research where, often, numerical tables are not useful.
    - `skip_extracted_filings`: Whether to skip already extracted filings or extract them nonetheless.<br> Default value is `True`.
  - Arguments for `extract_keywords`: 
    - `search_terms`: a list with the terms to be searched, the terms can be regular expressions or strings. e.g. ["Artificial Intelligence","A.I", "AI"]
    - `ignore_case`: whether the search for terms should be case insensitive. Default value is True. 
    - `regex_search`: whether the terms should be compiled as regular expressions or not. Default value is True.
    - `mentions_name`: the name that the output files should have. 

- To execute the full pipeline, run `python extract_mentions.py --config=<config>`. This will automatically run each of the three modules consecutively. If the download or extraction is interrupted, re-running the pipeline will only execute the remaining tasks instead of starting from scratch. For example, to use one of the provided configs: `python extract_mentions.py --config=configs/simplified_ai_config.json`
## Citation
A paper is on its way. Until then, please cite the relevant EDGAR-CORPUS paper published at the [3rd Economics and Natural Language Processing (ECONLP) workshop](https://lt3.ugent.be/econlp/) at EMNLP 2021 (Punta Cana, Dominican Republic):
```
@inproceedings{loukas-etal-2021-edgar,
    title = "{EDGAR}-{CORPUS}: Billions of Tokens Make The World Go Round",
    author = "Loukas, Lefteris  and
      Fergadiotis, Manos  and
      Androutsopoulos, Ion  and
      Malakasiotis, Prodromos",
    booktitle = "Proceedings of the Third Workshop on Economics and Natural Language Processing",
    month = nov,
    year = "2021",
    address = "Punta Cana, Dominican Republic",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2021.econlp-1.2",
    pages = "13--18",
}
```
## License
Please see the [GNU General Public License v3.0](). TODO: add link to our license.
