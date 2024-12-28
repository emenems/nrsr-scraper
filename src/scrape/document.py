import requests
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime, timedelta
# import pandas as pd
# import re

def _generate_datetime_string(dt):
    """Generate NRSR page specific type string with %20 between date and time.
    """
    date_str = dt.strftime('%Y-%m-%d')
    time_str = dt.strftime('%H:%M:%S')
    datetime_str = f"{date_str}%20{time_str}"
    return datetime_str

def fetch_voting_document_table(meeting_id, voting_time, logger):
    """Aux function to fetch the html content of the voting table for a specific meeting and time.

    Args:
        meeting_id (int): The ID of the meeting = 'Schôdza č {meeting_id}'.
        voting_time (datetime): The time of the voting
        logger (Logger): The logger object.
    """
    datetime_start = _generate_datetime_string(voting_time - timedelta(minutes=1))
    datetime_end = _generate_datetime_string(voting_time + timedelta(minutes=1))
    url = f"https://www.nrsr.sk/web/Default.aspx?sid=schodze/hlasovanie/vyhladavanie_vysledok&Text=&CPT=&CisSchodze={meeting_id}&DatumOd={datetime_start}&DatumDo={datetime_end}"

    response = requests.get(url)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch content for voting table for meeting {meeting_id} and time {voting_time}")
        return None
    if "unexpected error" in response.text:
        logger.info(f"Skipping {meeting_id} - no such page")
        return None
  
    return response.content

def parse_voting_document_id(content, logger):
    """Aux function to parse the voting table content and return the data in a structured way.

    Args:
        content (bytes): The html content of the voting table.
        logger (Logger): The logger object.
    """
    soup = BeautifulSoup(content, 'html.parser')
    table = soup.find('table', class_='tab_zoznam')
    
    if not table:
        logger.error("Failed to find the document table")
        return None
    
    rows = table.find_all('tr', class_=['tab_zoznam_nonalt', 'tab_zoznam_alt'])
    data = []
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 6:
            continue
        
        record = {
            'cislo_schodze': cols[0].get_text(strip=True),
            'cislo_hlasovania': cols[2].get_text(strip=True),
            'cislo_parlamentna_tlac': cols[3].get_text(strip=True),
        }
        data.append(record)
    
    return data

def fetch_document_details(url, logger):
    """Fetch the html content of the document details.

    Args:
        url (str): The URL of the document details.
        logger (Logger): The logger object.
    """
    response = requests.get(url)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch content for document details")
        return None
    if "unexpected error" in response.text:
        logger.info(f"Skipping document details - no such page")
        return None
  
    return response.content

def parse_document_details(content, logger):
    """Parse the document details content and return the data in a structured way.

    Args:
        content (bytes): The html content of the document details.
        logger (Logger): The logger object.
    """
    soup = BeautifulSoup(content, 'html.parser')
    details_div = soup.find('div', class_='parliamentary_press_details')
    
    if not details_div:
        logger.error("Failed to find the document details")
        return None
    
    details = {}
    
    try:
        details['cislo_parlamentna_tlac'] = details_div.find('strong', text='Číslo').find_next('span').text.strip()
        details['parlamentna_tlac_typ'] = details_div.find('strong', text='Typ').find_next('span').text.strip()
        details['parlamentna_tlac_datum'] = details_div.find('strong', text='Dátum doručenia').find_next('span').text.strip()
        details['parlamentna_tlac_nazov'] = details_div.find('strong', text='Názov').find_next('span').text.strip()

        documents = []
        documents_div = details_div.find('strong', text='Dokumenty').find_next('span')
        for a in documents_div.find_all('a', href=True):
            doc = {
                'link': a['href'],
                'description': a.get_text(strip=True)
            }
            documents.append(doc)
        details['parlamentna_tlac_dokumenty'] = documents

    except AttributeError as e:
        logger.error(f"Error parsing document details: {e}")
        return None
    
    return details

def add_documents_to_voting_data(voting_data, logger = None, save_to_file = None):
    logger = logger or logging.getLogger()
    document_cache = {}
    
    for _, details in voting_data.items():
        cislo_schodze = details.get('cislo_schodze')
        cislo_hlasovania = details.get('cislo_hlasovania')
        cas_hlasovania = datetime.strptime(details.get('cas_hlasovania'), '%d. %m. %Y %H:%M')

        cache_key = (cislo_schodze, cislo_hlasovania)

        details['parlamentna_tlac'] = []

        if cache_key in document_cache:
            details['parlamentna_tlac'] = document_cache[cache_key]
        else:
            content = fetch_voting_document_table(cislo_schodze, cas_hlasovania, logger)
            if content:
                document_ids = parse_voting_document_id(content, logger)
                if document_ids:
                    matching_document = next((doc for doc in document_ids if doc['cislo_schodze'] == cislo_schodze and doc['cislo_hlasovania'] == cislo_hlasovania), None)
                    if matching_document:
                        url_parlamentna_tlac = f"https://www.nrsr.sk/web/Default.aspx?sid=zakony/cpt&ID={matching_document['cislo_parlamentna_tlac']}"
                        document_content = fetch_document_details(url_parlamentna_tlac, logger)
                        if document_content:
                            document_details = parse_document_details(document_content, logger)
                            if document_details:
                                all_info = {
                                    'cislo_parlamentna_tlac': matching_document['cislo_parlamentna_tlac'],
                                    'url_parlamentna_tlac': url_parlamentna_tlac,
                                    'typ_parlamentna_tlac': document_details['parlamentna_tlac_typ'],
                                    'cas_parlamentna_tlac': document_details['parlamentna_tlac_datum'],
                                    'nazov_parlamentna_tlac': document_details['parlamentna_tlac_nazov'],
                                    'dokumenty_parlamentna_tlac': document_details['parlamentna_tlac_dokumenty']
                                }
                                document_cache[cache_key] = all_info
                                details['parlamentna_tlac'] = all_info
    if save_to_file:
        with open(save_to_file, 'w', encoding='utf-8') as f:
            json.dump(voting_data, f, ensure_ascii=False, indent=4)

    return voting_data

# def _extract_unique_ids(json_file: str | None = None, data: dict | None = None):
#     if json_file is not None and data is None:
#         with open(json_file, 'r', encoding='utf-8') as f:
#             voting_data = json.load(f)
    
#     records = []
#     for _, details in data.items():
#         schodza = re.search(r'\d+', details.get('schodza'))
#         record = {
#             'datum_cas': datetime.strptime(details.get('datum_cas'), '%d. %m. %Y %H:%M'),
#             'cislo_schodze': int(schodza.group(0)),
#             'cislo_hlasovania': int(details.get('cislo_hlasovania'))
#         }
#         records.append(record)
    
#     df = pd.DataFrame(records)
#     df = df.drop_duplicates()
#     return df

# def scrape_voting_table(voting_file: str | dict, save_to_file, logger = None):
#     logger = logger or logging.getLogger()
#     # get all meetings in order to get unique meeting and voting IDs needet to find the CPT (document id)
#     meetings = _extract_unique_ids(json_file=voting_file if isinstance(voting_file, str) else None, data=voting_file if isinstance(voting_file, dict) else None)

#     # run a loop over all unique ID combination and fetch all possible document CPT IDs
#     df = pd.DataFrame()
#     for _, meeting in meetings.iterrows():
#         meeting_id = meeting['cislo_schodze']
#         voting_time = meeting['datum_cas']
        
#         logger.info(f"Scraping voting table for meeting {meeting_id} and time {voting_time}...")
#         content = fetch_voting_document_table(meeting_id, voting_time, logger)

#         if content:
#             df = pd.concat([df,pd.DataFrame(parse_voting_document_table(content, logger))], ignore_index=True)
    
#     df = df.drop_duplicates().dropna().astype({'cislo_schodze': int, 'cislo_hlasovania': int})

#     # having the CPT ID related to voting, now get the data related to the CPT
#     meetings = pd.merge(meetings, df, on=['cislo_schodze', 'cislo_hlasovania'])
#     meetings = meetings[meetings['parlamentna_tlac_cislo'] != ''].drop_duplicates()
#     meetings["cpt_url"] = meetings['parlamentna_tlac_cislo'].apply(lambda x: f"https://www.nrsr.sk/web/Default.aspx?sid=zakony/cpt&ID={x}")

#     # run a loop over all unique CPT IDs and fetch all possible document details
#     df = pd.DataFrame()
#     for _, meeting in meetings.iterrows():
#         url = meeting['cpt_url']
        
#         logger.info(f"Scraping document details for CPT {url}...")
#         content = fetch_document_details(url, logger)

#         if content:
#             df = pd.concat([df,pd.DataFrame([parse_document_details(content, logger)])], ignore_index=True)

# def extend_voting_data(data: dict, logger = None):
#     """Extend the voting data with the document details.

#     Args:
#         data (dict): The voting data.
#         logger (Logger): The logger object.
#     """
#     logger = logger or logging.getLogger()
#     meetings = _extract_unique_ids(data=data)

#     # run a loop over all unique ID combination and fetch all possible document CPT IDs
#     df = pd.DataFrame()
#     for _, meeting in meetings.iterrows():
#         meeting_id = meeting['cislo_schodze']
#         voting_time = meeting['datum_cas']
        
#         logger.info(f"Scraping voting table for meeting {meeting_id} and time {voting_time}...")
#         content = fetch_voting_document_table(meeting_id, voting_time, logger)

#         if content:
#             df = pd.concat([df,pd.DataFrame(parse_voting_document_table(content, logger))], ignore_index=True)
    
#     df = df.drop_duplicates().dropna().astype({'cislo_schodze': int, 'cislo_hlasovania': int})

#     # having the CPT ID related to voting, now get the data related to the CPT
#     meetings = pd.merge(meetings, df, on=['cislo_schodze', 'cislo_hlasovania'])
#     meetings = meetings[meetings['parlamentna_tlac_cislo'] != ''].drop_duplicates()
#     meetings["cpt_url"] = meetings['parlamentna_tlac_cislo'].apply(lambda x: f"https://www.nrsr.sk/web/Default.aspx?sid=zakony/cpt&ID={x}")

#     # run a loop over all unique CPT IDs and fetch all possible document details
#     df = pd.DataFrame()
#     for _, meeting in meetings.iterrows():
#         url = meeting['cpt_url']
        
#         logger.info(f"Scraping document details for CPT {url}...")
#         content = fetch_document_details(url, logger)

#         if content:
#             df = pd.concat([df,pd.DataFrame([parse_document_details(content, logger)])], ignore_index=True)

#     return df