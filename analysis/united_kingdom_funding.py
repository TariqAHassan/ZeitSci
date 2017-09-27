"""

    UK Funding
    ~~~~~~~~~~

    Python 3.5

"""
import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from unidecode import unidecode
from analysis.abstract_analysis import *

from analysis.supplementary_fns import cln
from analysis.funding_database_tools import titler
from analysis.funding_database_tools import order_cols
from analysis.funding_database_tools import MAIN_FOLDER
from analysis.funding_database_tools import first_name_clean
from analysis.aggregated_geo_info import master_geo_lookup
from analysis.funding_database_tools import fdb_common_words

# Data Pipline Checklist:
#     Researcher                    X
#     Funder                        X
#     StartDate                     X
#     GrantYear                  -- V --
#     Amount                        X
#     FundCurrency                  X
#     ProjectTitle                  X
#     FunderBlock                   X
#     OrganizationName              X
#     OrganizationCity           -- V --
#     OrganizationState             X
#     OrganizationBlock          -- P --
#     lat                           X
#     lng                           X
#     Keywords                      X

# Legend:
#     X = Complete
#     V = Currently Void
#     P = Partially Stabalized

# ------------------------------------------------------------------------------------------------------------
# United Kingdom
# ------------------------------------------------------------------------------------------------------------

os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/UK")
uk_df = pd.read_csv("uk_funding_data.csv")

# Start tqdm
tqdm.pandas(desc="status")

# Limit to Research Grants
uk_df = uk_df[uk_df['ProjectCategory'] == 'Research Grant'].reset_index(drop=True)

# Drop unneeded columns
to_drop = ['ProjectReference',
           'EndDate',
           'Status',
           'PIOtherNames',
           'PI ORCID iD',
           'StudentSurname',
           'StudentFirstName',
           'StudentOtherNames',
           'Student ORCID iD',
           'GTRProjectUrl',
           'ProjectCategory',
           'ProjectId',
           'FundingOrgId',
           'Department',
           'ExpenditurePounds',
           'LeadROId',
           'PIId']
uk_df = uk_df.drop(to_drop, axis=1)

# Lower names
uk_df.columns = [i.lower() for i in uk_df.columns]

# Replace 'Unknown' with NaN
for c in ['Unknown', 'UNLISTED']:
    uk_df = uk_df.replace(c, np.NaN)

# Remove AHRC and ESRC Funding
for a in ['AHRC', 'ESRC']:
    uk_df = uk_df[uk_df['fundingorgname'] != a].reset_index(drop=True)

for c in [i for i in uk_df.columns if i != 'awardpounds']:
    uk_df[c] = uk_df[c].astype(str).progress_map(lambda x: unidecode(cln(x))).str.strip().progress_map(
        lambda x: np.NaN if x == 'nan' else x
    )

# ------------------------------------------------------------------------------------------------------------ #
# Construct Required Columns
# ------------------------------------------------------------------------------------------------------------ #

# Researcher
uk_df['pifirstname'] = uk_df['pifirstname'].str.replace(",", "").str.replace(")", "").str.replace("(", "").replace(
    "Dr.", "")

# Clean first names
uk_df['pifirstname'] = uk_df['pifirstname'].map(first_name_clean, na_action='ignore')

# Combine
uk_df['Researcher'] = uk_df['pifirstname'] + " " + uk_df['pisurname']
del uk_df['pisurname']
del uk_df['pifirstname']

# Funder
uk_df['fundingorgname'] = "UK_" + uk_df['fundingorgname']
uk_df = uk_df.rename(columns={"fundingorgname": "Funder"})

# Start Date
uk_df = uk_df.rename(columns={"startdate": "StartDate"})

# Grant Year
uk_df['GrantYear'] = np.NaN

# Amount
uk_df = uk_df.rename(columns={"awardpounds": "Amount"})

# FundCurrency
uk_df['FundCurrency'] = "GBP"


# ProjectTitle
def uk_title_cln(input_str):
    clean = input_str.replace("\'", "").replace(" : ", ": ")
    return clean[0].upper() + clean[1:]


uk_df['title'] = uk_df['title'].map(titler, na_action='ignore').map(uk_title_cln)
uk_df = uk_df.rename(columns={"title": "ProjectTitle"})

# FunderBlock
uk_df['FunderBlock'] = "United Kingdom"

# OrganizationName
uk_df = uk_df.rename(columns={"leadroname": "OrganizationName"})

# OrganizationCity; TO DO: use the main database to populate this.
uk_df['OrganizationCity'] = np.NaN

# OrganizationState; TO DO: handle 'Outside UK'.
uk_df = uk_df.rename(columns={"region": "OrganizationState"})

# Fix state for Oxford
uk_df['OrganizationState'] = uk_df.apply(
    lambda x: "South East" if "of Oxford".upper() in str(x['OrganizationName']).upper() else x['OrganizationState'],
    axis=1
)

# OrganizationBlock
uk_df['OrganizationBlock'] = uk_df['OrganizationState'].map(
    lambda x: "United Kingdom" if str(x) != 'Outside UK' else np.NaN, na_action='ignore'
)

# Replace Outside UK with NaN (for now)
uk_df['OrganizationState'] = uk_df['OrganizationState'].replace("Outside UK", np.NaN)

# Keywords
# As with the Candadian dataset, analyze the title for keywords.
uk_df['Keywords'] = fdb_common_words(uk_df['ProjectTitle'], n=5, update_after=2500)

# Lat/Lng

# Special Cases
special_cases_geo = {
    "University of Oxford": [51.7611, -1.2534]
}


def uk_geo_lookup(organization, block):
    if organization in special_cases_geo:
        return special_cases_geo[organization]
    if any(pd.isnull(i) for i in [organization, block]):
        return [np.NaN, np.NaN]
    return master_geo_lookup([np.NaN], None, block, organization)


lat_lng = uk_df.progress_apply(
    lambda x: uk_geo_lookup(x['OrganizationName'], x['OrganizationBlock']), axis=1
)

uk_df['lat'] = [i[0] for i in lat_lng]
uk_df['lng'] = [i[1] for i in lat_lng]

# Reorder and reset index
uk_df = uk_df[order_cols].reset_index(drop=True)

# UK Data Partially Stabilized #

# Save
uk_df.to_pickle(
    MAIN_FOLDER + "/Data/Governmental_Science_Funding/CompleteRegionDatabases/" + "UnitedKingdomFundingDatabase.p")


# Fix location for imperial (science and tech) -- also in EU script
