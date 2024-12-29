# NRSR Scraper

This is a minimal scraper for data related to **National Council of the Slovak Republic** (NRSR).

The scraper currently allows to get:

- Votings in the NRSR (a.k.a 'Parlament')
- Documenat page related to each voting (a.k.a. 'Parlamentna tlac')
- NRSR Members bio
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

> No selenium needed - just bs4 :)

## Run scraper

### Scrape individual subsets

```bash
# Scrape votings - passing the starting and end ID of the session
python src/main.py --type voting \
                   --start-id 55837 \
                   --end-id 55841

# Scrape votings - passing the starting and end ID of the session and specifying the save file and log file
python src/main.py --type voting \
                   --start-id 55837 \
                   --end-id 55902 \
                   --log-file data/raw/voting_data_55837-55902.log \
                   --save-to data/raw/voting_data_55837-55902.json

# Scrape member info using the voting to get all member IDs
python src/main.py --type member \
                   --input-file data/raw/voting_data.json \
                   --save-to data/raw/members_data.json

# Scrape election results for members
python src/main.py --type election \
                    --input-file https://volby.statistics.sk/nrsr/nrsr2023/files/xlsx/NRSR2023_SK_tab07a.xlsx \
                    --save-to data/interim/member_elections.xlsx

# Scrape documents related to voting
python src/main.py --type document \
                    --input-file data/raw/voting_data.json \
                    --save-to data/raw/document_data.xlsx
```

The IDs can be obtianed by visiting the [Voting by session](https://www.nrsr.sk/web/?sid=schodze/hlasovanie/schodze) then selecting the session and the voting - the ID is in the URL, e.g. 55635 `https://www.nrsr.sk/web/Default.aspx?sid=schodze/hlasovanie/hlasklub&ID=55635`

> the script was tested using voting IDs starting at 51426, i.e. starting 9th election cycle (from 2023)

#### Combine the scraped subsets - convert to excel

```bash
python src/convert/convert_to_excel.py --input-voting data/raw/voting_data.json \
                                       --input-member data/raw/members_data.json \
                                       --input-election data/interim/member_elections.xlsx \
                                       --input-document data/raw/document_data.xlsx \
                                       --output-file data/interim/voting_member_election.xlsx
```


### Scrape voting + member bio + voting document info

Use this option to get full info for voting and member in one output file.

```bash
python src/main.py --type voting+member+document \
                   --start-id 55837 \
                   --end-id 55841 \
                   --save-to data/raw/voting_and_member.json
```

## Related/similar projects

* [Rozuzli.to](rozuzli.to) - direct download a CSV with all votings (no election and member bio)
