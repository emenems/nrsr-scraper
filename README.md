# NRSR Scraper

This is a minimal scraper for data related to **National Council of the Slovak Republic** (NRSR).

The scraper currently allows to get:

- Votings in the NRSR (a.k.a Parliament)
- NRSR Members info
- Election results for all members

## Setup

1. Create a virtual environment:
    ```bash
    python -m venv venv
    ```

2. Activate the virtual environment:
    ```bash
    source venv/bin/activate
    ```

3. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Run scraper

```bash
# Scrape votings - passing the starting and end ID of the session
python src/main.py --type voting \
                   --start-id 51426 \
                   --end-id 55841

# Scrape votings - passing the starting and end ID of the session and specifying the save file
python src/main.py --type voting \
                   --start-id 51426 \
                   --end-id 52921 \
                   --save-to data/raw/voting_2023.json

# Scrape member info using the voting to get all member IDs
python src/main.py --type member \
                   --input-file data/raw/voting_2023.json \
                   --save-to data/raw/members_2023.json

# Scrape election results for members
python src/main.py --type election \
                    --input-file https://volby.statistics.sk/nrsr/nrsr2023/files/xlsx/NRSR2023_SK_tab07a.xlsx \
                    --save-to data/interim/member_elections.xlsx
```

The IDs can be obtianed by visiting the [Voting by session](https://www.nrsr.sk/web/?sid=schodze/hlasovanie/schodze) then selecting the session and the voting - the ID is in the URL, e.g. 55635 `https://www.nrsr.sk/web/Default.aspx?sid=schodze/hlasovanie/hlasklub&ID=55635`

> the script was tested using voting IDs starting at 51426, i.e. starting 9th election cycle (from 2023)


## Use data

Convert data to excel for easier use

```bash
python src/convert/convert_to_excel.py --input-voting data/raw/voting_51426-55841.json \
                                       --input-member data/raw/members_51426-55841.json \
                                       --input-election data/interim/member_elections.xlsx \
                                       --output-file data/interim/voting_51426-55841.xlsx
```

When using individual files, esure correct encoding when loading the results

```python
import json

with open('data/raw/votings.json', 'r', encoding='utf-8') as f:
    votings = json.load(f)

votings
```