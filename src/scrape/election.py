import pandas as pd

def get_election_member_votes(
        input_xlsx: str = 'https://volby.statistics.sk/nrsr/nrsr2023/files/xlsx/NRSR2023_SK_tab07a.xlsx',
        output_xlsx: str = 'data/interim/election_member_votes.xlsx',
        elected_only: bool = True
    ):
    """
    Get the election member votes from the given URL - should be the tab07a of the election results.
    """
    df = pd.read_excel(input_xlsx, skiprows=2)
    
    df = df.rename(
        columns={
            'Názov politického subjektu': 'kandidoval_za',
            'Meno':'poslanec_meno',
            'Priezvisko': 'poslanec_priezvisko',
            'Počet platných prednostných hlasov': 'poslanec_volby_hlasov',
            'Podiel platných prednostných hlasov v %': 'poslanec_volby_hlasov_podiel',
            'Poradie po zohľadnení prednostného hlasovania': 'poslanec_volby_poradie',
            'Poradie na hlasovacom lístku': 'poslanec_volby_poradie_listok'
        }
    )
    df = df[['kandidoval_za', 'poslanec_meno', 'poslanec_priezvisko', 'poslanec_volby_hlasov', 'poslanec_volby_hlasov_podiel', 'poslanec_volby_poradie', 'poslanec_volby_poradie_listok']]
    
    if elected_only:
        df = df[df.poslanec_volby_poradie.notna()]

    if output_xlsx:
        df.to_excel(output_xlsx, index=False)

    return df