import logging
import argparse
from scrape.voting import scrape_voting_data
from scrape.member import scrape_member_data_all, add_member_info_to_voting_data
from scrape.election import get_election_member_votes
from scrape.document import add_documents_to_voting_data, scrape_voting_documents

def setup_logging(log_file):
    """
    Set up logging to log both to console and a file.
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # File handler
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Scrape voting data from the Slovak National Council website.')
    parser.add_argument('--start-id', type=int, default=51426, help='The starting ID for scraping')
    parser.add_argument('--end-id', type=int, default=51427, help='The ending ID for scraping')
    parser.add_argument('--save-to', type=str, default='', help='The file path to save the scraped data')
    parser.add_argument('--log-file', type=str, default='scraper.log', help='The file path to save the logs')
    parser.add_argument('--type', type=str, default='voting', help='The type of data to scrape')
    parser.add_argument('--input-file', type=str, default='data/raw/voting.json', help='The file path to load the input data')

    # Parse arguments
    args = parser.parse_args()
    
    start_id = args.start_id
    end_id = args.end_id
    save_to = args.save_to if args.save_to != '' else f'data/raw/voting_{start_id}-{end_id}.json'
    log_file = args.log_file

    # Configure logging
    setup_logging(log_file)

    # Perform the scraping
    try:
        if args.type == 'voting':
            logging.info(f"Scraping data for IDs {start_id} to {end_id} and saving to {save_to}...")
            data = scrape_voting_data(start_id, end_id, save_to)
            logging.info(f"Scraped data for {len(data)} votings.")
        elif args.type == 'member':
            logging.info(f"Scraping member info...")
            data = scrape_member_data_all(args.input_file, save_to_file=save_to)
            logging.info(f"Scraped data for {len(data)} members.")
        elif args.type == 'election':
            logging.info(f"Scraping election member votes...")
            data = get_election_member_votes(input_xlsx=args.input_file, output_xlsx=save_to)
            logging.info(f"Scraped data for {len(data)} members.")
        elif args.type == 'document':
            logging.info(f"Sraping documents for votings in {args.input_file}...")
            data = scrape_voting_documents(args.input_file, save_to_file=save_to)
            logging.info(f"Scraped data for {len(data)} votings.")
        elif 'voting+' in args.type:
            logging.info(f"Scraping data for IDs {start_id} to {end_id} and saving to {save_to}...")
            data = scrape_voting_data(start_id, end_id, save_to)
            logging.info(f"Scraped data for {len(data)} votings.")
            if 'document' in args.type:
                logging.info(f"Adding documents to votings...")
                data = add_documents_to_voting_data(data, save_to_file=save_to)
                logging.info(f"Added documents to {len(data)} votings.")
            if 'member' in args.type:
                logging.info(f"Adding member info to votings...")
                data = add_member_info_to_voting_data(data, save_to_file=save_to)
                logging.info(f"Added member info to {len(data)} votings.")
        else:
            logging.error(f"Invalid type: {args.type}")
    except Exception as e:
        logging.error(f"An error occurred during scraping: {e}", exc_info=True)

if __name__ == "__main__":
    main()