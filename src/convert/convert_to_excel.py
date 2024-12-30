import json
import pandas as pd
import argparse

def voting_to_dataframe(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = []
    for voting_id, details in data.items():
        base_info = {
            'voting_id': voting_id,
            'cas_hlasovania': details.get('cas_hlasovania'),
            'schodza': details.get('schodza'),
            'cislo_schodze': details.get('cislo_schodze'),
            'cislo_hlasovania': details.get('cislo_hlasovania'),
            'nazov_hlasovania': details.get('nazov_hlasovania'),
            'vysledok_hlasovania': details.get('vysledok_hlasovania'),
            'schvalene': _map_result(details.get('vysledok_hlasovania')),
            'pritomni': details.get('pritomni'),
            'hlasujucich': details.get('hlasujucich'),
            'za_hlasovalo': details.get('za_hlasovalo'),
            'proti_hlasovalo': details.get('proti_hlasovalo'),
            'zdrzalo_sa': details.get('zdrzalo_sa'),
            'nehlasovalo': details.get('nehlasovalo'),
            'nepritomni': details.get('nepritomni')
        }
        
        for vote in details.get('hlasovanie', []):
            record = base_info.copy()
            record.update({
                'poslanec_klub': vote.get('hlasovanie_klub'),
                'poslanec_priezvisko_meno': vote.get('poslanec_meno'),
                'poslanec_id': vote.get('poslanec_id'),
                'hlas_id': vote.get('hlas_id'),
                'hlas': _map_voting(vote.get('hlas_id'))
            })
            records.append(record)
    
    df = pd.DataFrame(records)
    return df

def member_to_dataframe(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = []
    for member_id, details in data.items():
        base_info = {
            'poslanec_id': member_id,
            'poslanec_meno': details['info'].get('meno'),
            'poslanec_priezvisko': details['info'].get('priezvisko'),
            'poslanec_titul': details['info'].get('titul'),
            'kandidoval_za': str(details['info'].get('kandidoval_za')).replace(' – ', ' - '),
            'poslanec_narodeny': details['info'].get('narodeny'),
            'poslanec_narodnost': details['info'].get('narodnost'),
            'poslanec_bydlisko': details['info'].get('bydlisko'),
            'poslanec_kraj': details['info'].get('kraj'),
            'poslanec_email': details['info'].get('email'),
            'poslanec_www': details['info'].get('www'),
            'poslanec_photo': details['info'].get('photo'),
            'poslanec_clenstvo': ';'.join(details.get('clenstvo', []))
        }
        records.append(base_info)
    
    df = pd.DataFrame(records)
    df = df.drop_duplicates()
    return df

def _count_academic_titles(title_string):
    if not title_string:
        return 0
    elif len(title_string) < 2:
        return 0

    # List of academic titles used in Slovakia
    academic_titles = [
        'Bc.', 'Mgr.', 'Ing.', 'MUDr.', 'MVDr.', 'JUDr.', 'PhDr.', 'Ph.D', 'RNDr.', 'RSDr.', 'ThDr.', 'PharmDr.', 'PaedDr.', 'Dr.', 'PhD.', 'D.Phil.', 'ThLic.', 'ThDr.', 'DrSc.', 'doc.', 'prof.', 'Dr. med.', 'MBA', 'MSc', 'M.A.', 'MIM', 'Dis.art.', 'ArtD.', 'Mgr. art.'
    ]

    # Fix incorrect inputs
    titles_prep = title_string.replace('M. A.', 'M.A.').replace('MSc.','MSc').replace('Ph.D.','Ph.D').replace('Dis. art','Dis.art')

    # Split the input string by commas and spaces
    titles = [title.strip() for title in titles_prep.replace(',', ' ').split()]

    # Count the number of academic titles in the input string
    count = sum(1 for title in titles if title in academic_titles)

    return count

def _map_voting(hlas_id):
    if hlas_id is None:
        return None
    elif hlas_id == '[Z]':
        return 'za'
    elif hlas_id == '[P]':
        return 'proti'
    elif hlas_id == '[?]':
        return 'zdrzal' # tlacidlo "Zdrzal sa"
    elif hlas_id == '[N]':
        return 'nehlasoval' # rozdiel od "zdrzal" je ze nestlacil(a) tlacidlo
    elif hlas_id == '[0]':
        return 'nepritomny' # neprezentu
    elif hlas_id == '[X]':
        return 'neplatny'
    else:
        return None

def _map_result(result_str):
    if result_str is None:
        return None
    elif "neprešiel" in result_str.lower():
        return "nie"
    elif "prešiel" in result_str.lower():
        return "ano"
    elif "nebol" in result_str.lower(): # uznasaniaschopny
        return "nie"
    else:
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert JSON data to Excel format.')
    parser.add_argument('--input-voting', type=str, help='The JSON file to convert to Excel')
    parser.add_argument('--input-member', type=str, help='The JSON file to join with voting')
    parser.add_argument('--input-election', type=str, help='The excel containing election data and join with voting')
    parser.add_argument('--input-document', type=str, help='The XLSX file to join with voting')
    parser.add_argument('--output-file', type=str, help='The Excel file to save the converted data')

    args = parser.parse_args()

    if args.input_voting is None or args.output_file is None:
        print("Please provide the input and output file paths.")
        exit(1)
    else:
        voting = voting_to_dataframe(args.input_voting)
        nr_check = voting.shape[0]
        if args.input_member:
            member = member_to_dataframe(args.input_member)
            member['poslanec_titul_pocet'] = member['poslanec_titul'].apply(_count_academic_titles)
            if args.input_election:
                election = pd.read_excel(args.input_election)
                member = pd.merge(
                    member.assign(temp_priezvisko=member.poslanec_priezvisko.str.split().str[-1]),
                    election.assign(temp_priezvisko=election.poslanec_priezvisko.str.split().str[-1]).drop(columns=['poslanec_priezvisko']),
                    on=['kandidoval_za', 'poslanec_meno', 'temp_priezvisko'],
                    how='left',
                    validate='m:1',
                    suffixes=('', '_y')
                ).drop(columns=['temp_priezvisko', 'poslanec_priezvisko_y'], errors='ignore')
            voting = pd.merge(
                voting,
                member, 
                on='poslanec_id',
                how='left',
                validate='m:1',
                suffixes=('', '_y')
            ).drop(columns=['poslanec_priezvisko_meno_y'], errors='ignore')
        if args.input_document:
            document = pd.read_excel(args.input_document)
            voting = pd.merge(
                voting.astype({'cislo_schodze': 'int', 'cislo_hlasovania': 'int'}),
                document.drop(columns=['cas_hlasovania']),
                on=['cislo_schodze', 'cislo_hlasovania'],
                how='left',
                validate='m:1',
                suffixes=('', '_y')
            )
        if voting.shape[0] != nr_check:
            print(f"Error: The number of rows in the voting data has changed from {nr_check} to {voting.shape[0]} after joining with member data.")
            exit(1)
        else:
            voting.to_excel(args.output_file, index=False)
            print(f"Data saved to {args.output_file}")
