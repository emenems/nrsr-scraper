import requests
from bs4 import BeautifulSoup
import json
import logging

def fetch_mp_content(mp_id, logger):
    url = f"https://www.nrsr.sk/web/Default.aspx?sid=poslanci/poslanec&PoslanecID={mp_id}"
    
    response = requests.get(url)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch content for MP ID {mp_id}")
        return None
    if "unexpected error" in response.text:
        logger.info(f"Skipping {mp_id} - no such page")
        return None
  
    return response.content

def parse_member_info(content, logger):
    soup = BeautifulSoup(content, 'html.parser')
    personal_data_div = soup.find('div', class_='mp_personal_data')
    
    if not personal_data_div:
        logger.error("Failed to find personal data panel")
        return None
    
    member_info = {}
    
    try:
        member_info['meno'] = personal_data_div.find('strong', text='Meno').find_next('span').text.strip()
        member_info['titul'] = personal_data_div.find('strong', text='Titul').find_next('span').text.strip()
        member_info['priezvisko'] = personal_data_div.find('strong', text='Priezvisko').find_next('span').text.strip()
        member_info['kandidoval_za'] = personal_data_div.find('strong', text='Kandidoval(a) za').find_next('span').text.strip()
        member_info['narodeny'] = personal_data_div.find('strong', text='Narodený(á)').find_next('span').text.strip()
        member_info['narodnost'] = personal_data_div.find('strong', text='Národnosť').find_next('span').text.strip()
        member_info['bydlisko'] = personal_data_div.find('strong', text='Bydlisko').find_next('span').text.strip()
        member_info['kraj'] = personal_data_div.find('strong', text='Kraj').find_next('span').text.strip()
        member_info['email'] = personal_data_div.find('strong', text='E-mail').find_next('span').find('a').text.strip()
        member_info['www'] = personal_data_div.find('strong', text='WWW').find_next('span').text.strip()
    except AttributeError:
        logger.error("Error parsing member info")
        return None
    
    photo_div = soup.find('div', class_='mp_foto')
    if photo_div:
        member_info['photo'] = photo_div.find('img')['src']
    elif member_info != {}:
        member_info['foto'] = None

    return member_info

def parse_member_membership(content, logger):
    soup = BeautifulSoup(content, 'html.parser')
    memberships_div = soup.find('div', class_='box')
    
    if not memberships_div:
        logger.error("Failed to find memberships panel")
        return []
    
    memberships = []
    
    try:
        membership_items = memberships_div.find_all('li')
        for item in membership_items:
            memberships.append(item.text.strip())
    except AttributeError as e:
        logger.error(f"Error parsing memberships: {e}")
        return []
    
    return memberships

def scrape_member_data(mp_id, save_to_file="data/raw/member.json", logger=None):
    logger = logger or logging.getLogger(__name__)
    data = {}
    
    logger.info(f"Scraping data for MP ID {mp_id}")
    content = fetch_mp_content(mp_id, logger)
    if content:
        info = parse_member_info(content, logger)
        memberships = parse_member_membership(content, logger)
        
        if info:
            data[mp_id] = {
                'info': info,
                'clenstvo': memberships
            }
            if save_to_file:
                with open(save_to_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            return data
        else:
            return None
        
    return None

def scrape_member_data_all(voting_file, save_to_file="data/raw/members.json", logger=None):
    logger = logger or logging.getLogger(__name__)
    with open(voting_file, 'r', encoding='utf-8') as f:
        votings = json.load(f)
    
    members = set()
    for voting in votings.values():
        for result in voting['hlasovanie']:
            members.add(result['poslanec_id'])
    
    data = {}
    for member in members:
        member_data = scrape_member_data(member, save_to_file=None, logger=logger)
        if member_data:
            data.update(member_data)

    if data != {}:
        with open(save_to_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    return data

def add_member_info_to_voting_data(voting_data, logger=None, save_to_file=None):
    logger = logger or logging.getLogger(__name__)
    member_cache = {}

    for _, voting in voting_data.items():
        for member in voting['hlasovanie']:
            member_id = member['poslanec_id']
            member['poslanec_bio'] = {}
            member['poslanec_clenstvo'] = []
            if member_id in member_cache:
                member["poslanec_bio"] = member_cache[member_id]["info"]
                member["poslanec_clenstvo"] = member_cache[member_id]["clenstvo"]
            else:
                member_data = scrape_member_data(member_id, save_to_file=None, logger=logger)
                if member_data:
                    member_cache[member_id] = member_data[member_id]
                    member["poslanec_bio"] = member_data[member_id]["info"]
                    member["poslanec_clenstvo"] = member_data[member_id]["clenstvo"]

    if save_to_file:
        with open(save_to_file, 'w', encoding='utf-8') as f:
            json.dump(voting_data, f, ensure_ascii=False, indent=4)

    return voting_data