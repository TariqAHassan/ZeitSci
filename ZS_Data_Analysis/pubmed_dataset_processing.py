"""

    Process the Pubmed Data set
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Python 3.5

"""
import pubmed_parser_master.pubmed_parser as pp

xml_file = '/Users/tariq/Desktop/SampleMedline/medline16n0365.xml'

# Need:
# Funding

data = pp.parse_medline_xml(xml_file, year_info_only=False)

# parse_grant_id
for k, v in data[0].items():
    print(k, " ", (v if len(str(v)) else None))

data[0]['journal_iso']


























































