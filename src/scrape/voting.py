import requests
from bs4 import BeautifulSoup
import json
import time
import logging

def fetch_voting_content(voting_id, logger):
    url = f"https://www.nrsr.sk/web/Default.aspx?sid=schodze/hlasovanie/hlasklub&ID={voting_id}"
    response = requests.get(url)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch content for voting ID {voting_id}")
        return None
    if "unexpected error" in response.text:
        logger.info(f"Skipping {voting_id} - no such page")
        return None
  
    return response.content

def parse_voting_summary(content, logger):
    soup = BeautifulSoup(content, 'html.parser')
    summary_div = soup.find('div', class_='voting_stats_summary_panel')
    
    if not summary_div:
        logger.error("Failed to find voting summary panel")
        return None
    
    summary = {}
    
    try:
        summary['schodza'] = summary_div.find('a', id=lambda x: x and x.endswith('__schodzaLink')).text.strip()
        summary['datum_cas'] = summary_div.find('div', class_='grid_4').find_next_sibling('div').find('span').text.strip()
        summary['cislo_hlasovania'] = summary_div.find('div', class_='grid_4 omega').find('span').text.strip()
        summary['nazov_hlasovania'] = summary_div.find('div', class_='grid_12 alpha omega').find('span').text.strip()
        summary['vysledok_hlasovania'] = summary_div.find('div', id=lambda x: x and x.endswith('__votingResultCell')).find('span').text.strip()
    except AttributeError:
        logger.error("Error parsing voting summary")
        return None
    
    return summary

def parse_voting_stats(content, logger):
    soup = BeautifulSoup(content, 'html.parser')
    stats_div = soup.find('div', id="_sectionLayoutContainer_ctl01_ctl00__resultsTablePanel")
    
    if not stats_div:
        logger.error("Failed to find voting stats panel")
        return None
    
    stats = {}
    
    try:
        stats['pritomni'] = stats_div.find('strong', text='Prítomní').find_next('span').text.strip()
        stats['hlasujucich'] = stats_div.find('strong', text='Hlasujúcich').find_next('span').text.strip()
        stats['za_hlasovalo'] = stats_div.find('strong', text='[Z] Za hlasovalo').find_next('span').text.strip()
        stats['proti_hlasovalo'] = stats_div.find('strong', text='[P] Proti hlasovalo').find_next('span').text.strip()
        stats['zdrzalo_sa'] = stats_div.find('strong', text='[?] Zdržalo sa hlasovania').find_next('span').text.strip()
        stats['nehlasovalo'] = stats_div.find('strong', text='[N] Nehlasovalo').find_next('span').text.strip()
        stats['nepritomni'] = stats_div.find('strong', text='[0] Neprítomní').find_next('span').text.strip()
        try:
            stats['neplatne'] = stats_div.find('strong', text='[X] Neplatných hlasov').find_next('span').text.strip()
        except AttributeError:
            stats['neplatne'] = "0"
    except AttributeError:
        logger.error("Error parsing voting stats")
        return None
    
    return stats

def parse_voting_results(content, logger):
    soup = BeautifulSoup(content, 'html.parser')
    results_table = soup.find('table', id="_sectionLayoutContainer_ctl01__resultsTable")
    
    if not results_table:
        logger.error("Failed to find voting results table")
        return None
    
    results = []
    
    try:
        rows = results_table.find_all('tr')
        current_party = None
        for nr, row in enumerate(rows):
            td = row.find('td', class_='hpo_result_block_title')
            if td:
                current_party = td.text.strip()
            else:
                cells = row.find_all('td')
                for cell in cells:
                    vote = cell.text.strip().split(' ')[0]
                    if vote == "Poslanci," or "[" not in vote or "]" not in vote:
                        break
                    mep_name = cell.find('a').text.strip()
                    mep_id = cell.find('a')['href'].split('PoslanecID=')[1].split('&')[0]
                    results.append({
                        'hlas_id': vote,
                        'poslanec_id': mep_id,
                        'poslanec_meno': mep_name,
                        'hlasovanie_klub': current_party,
                        
                    })
    except AttributeError:
        logger.error(f"Error parsing voting results. Row: {nr} - {row}")
        return None
    
    return results

def scrape_voting_data(id_start: int, id_end: int, save_to_file: str | None, logger = None):
    logger = logger or logging.getLogger(__name__)
    data = {}
    for voting_id in range(id_start, id_end + 1):
        logger.info(f"Scraping data for voting ID {voting_id}")
        content = fetch_voting_content(voting_id, logger)
        if content:
            summary = parse_voting_summary(content, logger)
            stats = parse_voting_stats(content, logger)
            results = parse_voting_results(content, logger)
            
            if summary and stats and results:
                data[voting_id] = {
                    'cas_hlasovania': summary.get('datum_cas'),
                    'schodza': summary.get('schodza'),
                    'cislo_schodze': summary.get('schodza').split()[-1],
                    'cislo_hlasovania': summary.get('cislo_hlasovania'),
                    'nazov_hlasovania': summary.get('nazov_hlasovania'),
                    'vysledok_hlasovania': summary.get('vysledok_hlasovania'),
                    'url_hlasovania': f"https://www.nrsr.sk/web/Default.aspx?sid=schodze/hlasovanie/hlasklub&ID={voting_id}",
                    'pritomni': stats.get('pritomni'),
                    'hlasujucich': stats.get('hlasujucich'),
                    'za_hlasovalo': stats.get('za_hlasovalo'),
                    'proti_hlasovalo': stats.get('proti_hlasovalo'),
                    'zdrzalo_sa': stats.get('zdrzalo_sa'),
                    'nehlasovalo': stats.get('nehlasovalo'),
                    'nepritomni': stats.get('nepritomni'),
                    'neplatne': stats.get('neplatne'),
                    'hlasovanie': results
                }
                time.sleep(0.1)  # Pause for 0.1 second between each successful request
    
    with open(save_to_file, 'w') as f:
        json.dump(data, f, indent=4)
    
    logger.info(f"Scraping completed. Data saved to {save_to_file}")
    return data