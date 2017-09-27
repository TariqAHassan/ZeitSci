"""

    Merge the Various Funding Databases into One
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import re
import os
import time
import glob2
import string
import numpy as np
import pandas as pd
from tqdm import tqdm

from fuzzywuzzy import process
from unidecode import unidecode
from datetime import datetime
from analysis.abstract_analysis import *
from currency_converter import CurrencyConverter  # pip3 install CurrencyConverter

from datetime import date
from analysis.funding_database_tools import titler
from analysis.funding_database_tools import MAIN_FOLDER
from analysis.funding_database_tools import multi_readin

from easymoney.money import EasyPeasy
from analysis.organization_classification import organization_classifier
from easymoney.easy_pandas import strlist_to_list, twoD_nested_dict, pandas_print_full
from sources.world_bank_interface import _world_bank_pull_wrapper as wbpw

# Release Candidate
RC = 8

# Goal:
# A dataframe with the following columns:
#     Researcher
#     Fields                        A  -- use journal ranking dataframe
#     ResearcherSubfields           A  -- use journal ranking dataframe
#     ResearchAreas (sub-subfield)  A  -- use journal ranking dataframe
#     Amount
#     NormalizedAmount                 -- the grant in 2015 USD (2016 not handled properly...fix)
#     Currency
#     YearOfGrant
#     FundingSource
#     Collaborators                 A  -- based on pubmed 2000-2016 download
#     keywords
#     Institution
#     Endowment                        -- use wikipedia universities database
#     InstitutionType                  -- use wikipedia universities database (i.e., public or private)
#     InstitutionRanking            V  -- Ranking of the institution (read: uni). QS Data available; usage Prohibitive.
#     InstutionCountry
#     City/NearestCity
#     lng
#     lat

# A = to do when all country's data are assembled

# To do:
#   Handle RB country code in Block;
#   Country codes in OrgState should be moved to OrgBlock

# -------------------------------------------------------------------------
# General Tools & Information
# -------------------------------------------------------------------------

# Special Characters.
chars = re.escape(string.punctuation)


def alphanum(input_str, chars=chars):
    """
    Remove *all* non-alphanumeric characters
    see: http://stackoverflow.com/questions/23996118/replace-special-characters-in-a-string-python

    :param input_str:
    :return:
    """
    return re.sub(r'[' + chars + ']', '', input_str)


os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/CompleteRegionDatabases")

# -------------------------------------------------------------------------
# Integrate Funding Data from around the World
# -------------------------------------------------------------------------

# Read in Databases
us_df = pd.read_pickle('AmericanFundingDatabase.p')
uk_df = pd.read_pickle('UnitedKingdomFundingDatabase.p')
eu_df = pd.read_pickle('EuropeanUnionFundingDatabase.p')
ca_df = pd.read_pickle('CanadianFundingDatabase.p')

# Merge the dataframes
df = us_df.append([uk_df, eu_df, ca_df])
df = df.reset_index(drop=True)
tqdm.pandas(desc="status")

df['OrganizationBlock'] = df['OrganizationBlock'].str.lower().str.title()

# ------------------------------------------------------------------------------------------------
# Standardize Names of UK Unis
# ------------------------------------------------------------------------------------------------

# The EU and UK refer to this orgs with slightly different names

# To do: (should not be a nan here)
# df[df['OrganizationName'].str.contains("Imperial College of Science, Technology and Medicine")]['OrganizationBlock']

uk_uni_special_names = {'University of Oxford': 'University of Oxford',
                        "Imperial College": "Imperial College London",
                        'University of Cambridge': "University of Cambridge",
                        'University of Cambrige': "University of Cambridge",
                        "University of Edinburgh": "University of Edinburgh"
                        }


def uk_org_cln(x, uk_uni_special_names):
    """

    :param x:
    :return:
    """
    org_name = x['OrganizationName']
    if str(org_name) == 'nan':
        return org_name

    # Bit of a hack for now...
    if "imperial college" in org_name.lower() or \
                    str(x['FunderBlock']).lower() in ["united kingdom"] or \
                    str(x['OrganizationBlock']).lower() == "united kingdom":
        for k in uk_uni_special_names:
            if k.upper() in org_name.upper():
                return (uk_uni_special_names[k])

    return org_name


# Fix UK Uni(s)
df['OrganizationName'] = df.progress_apply(lambda x: uk_org_cln(x, uk_uni_special_names), axis=1)

# -------------------------------------------------------------------------
# Convert 'nan's to true NaNs
# -------------------------------------------------------------------------

for i, c in enumerate(df.columns):
    print(i + 1, "of", len(df.columns))
    df[c] = df[c].progress_map(lambda x: np.NaN if str(x) == 'nan' else x)

# -------------------------------------------------------------------------
# Normalize Grant Amount
# -------------------------------------------------------------------------

# Create an instance of CurrencyConverter
c = CurrencyConverter()

# Get Most Recent CPI Information from the IMF via. the world Bank
cpi = wbpw("CPI", "FP.CPI.TOTL")[0]

# Convert to CPI dataframe to a dict
cpi_dict = twoD_nested_dict(cpi, 'Year', 'Country', 'CPI', engine='fast')

# Max Years in CPI dataframe
cpi_dict_max = cpi.groupby('Country').apply(lambda x: int(max(x['Year']))).to_dict()


def zeitsci_cpi(region, year_a, year_b):
    rate = np.NaN
    year_a_str = str(year_a)
    year_b_str = str(year_b)

    if all(i in cpi_dict for i in [year_a_str, year_b_str]):
        if all(region in j for j in [cpi_dict[year_a_str], cpi_dict[year_b_str]]):
            c1 = float(cpi_dict[year_a_str][region])  # start
            c2 = float(cpi_dict[year_b_str][region])  # end
            rate = (c2 - c1) / c1 + 1

    return rate


def zeitsci_normalize(amount, amount_state, amount_cur, from_year, base_year=2015, base_currency='USD',
                      base_date=date(2015, 12, 31)):
    """

    :param amount:
    :param amount_state:
    :param amount_cur:
    :param from_year:
    :param base_year:
    :param base_currency:
    :return:
    """
    # Handle regions not in the DB
    if amount_state not in cpi_dict_max:
        return np.NaN

    # Set the inflation rate
    if from_year <= cpi_dict_max[amount_state]:
        inflation_rate = zeitsci_cpi(amount_state, from_year, base_year)
    else:
        inflation_rate = 1

    if pd.isnull(inflation_rate):
        return np.NaN

    # Adjust for inflation
    real_amount = amount * inflation_rate

    # Convert to base currency
    if base_date == None:
        return c.convert(real_amount, amount_cur, base_currency)
    else:
        return c.convert(real_amount, amount_cur, base_currency, date=base_date)


def zeitsci_grant_normalize_wrapper(x):
    from_year = np.NaN
    if pd.isnull(x['GrantYear']):
        if pd.isnull(x['StartDate']):
            return np.NaN
        else:
            if len([i for i in x['StartDate'].split("/") if len(i) == 4]) != 1:
                return np.NaN
            else:
                from_year = [i for i in x['StartDate'].split("/") if len(i) == 4][0]
    else:
        from_year = x['GrantYear']

    input_dict = {
        'amount': x['Amount'],
        'block': x['OrganizationBlock'],
        'amount_cur': x['FundCurrency'],
        'from_year': int(from_year)
    }
    if any(pd.isnull(i) for i in input_dict.values()):
        return np.NaN

    return zeitsci_normalize(input_dict['amount']
                             , input_dict['block']
                             , input_dict['amount_cur']
                             , input_dict['from_year'])


df['NormalizedAmount'] = df.progress_apply(lambda x: zeitsci_grant_normalize_wrapper(x), axis=1)
# This procedure worked on 99.9% of rows. Acceptable.

# -------------------------------------------------------------------------
# Clean OrganizationCity
# -------------------------------------------------------------------------

df['OrganizationCity'] = df['OrganizationCity'].map(
    lambda x: x if "," not in x else x.split(",")[0].strip(), na_action='ignore'
)

# -------------------------------------------------------------------------
# Clean OrganizationName
# -------------------------------------------------------------------------

# Clean the OrganizationName
df['OrganizationName'] = df['OrganizationName'].map(cln).str.replace("\"", "").str.strip().progress_apply(titler)

# Search and Block terms
to_block = ['centre', 'center', 'hospital']
search_terms = ['school of', 'medical', 'faculty', 'department']
query = "|".join(map(re.escape, search_terms))

# List subsidiaries
possible_subsidiaries = df['OrganizationName'][
    (df['OrganizationName'].astype(str).str.lower().str.contains(query))].unique().tolist()
possible_subsidiaries_cln = [i for i in possible_subsidiaries if not any(x in i.lower() for x in to_block)]


def subsidiary_checker(principals, subsidiaries):
    """
    Check for subsidiaries in principal Orgs.
    """
    subsidiaries_dict = dict()
    for k in tqdm(subsidiaries):
        matches = [j for j in principals if " " in j and j.lower().title() in k.lower().title()]
        if len(matches) == 1 and matches[0] != k:
            subsidiaries_dict[k] = matches[0]
    return subsidiaries_dict


unique_orgs = [i for i in df['OrganizationName'].unique().tolist() if i not in possible_subsidiaries]

subsidiaries_dict = subsidiary_checker(unique_orgs, possible_subsidiaries_cln)

# Define erroneous pairings
erronous_pair = {'Medical University of South Carolina': 'University of South Carolina'}

# Remove erroneous pairs from the subsidiaries dict
subsidiaries_dict = {k: v for k, v in subsidiaries_dict.items() if
                     k not in erronous_pair and v != erronous_pair.get(k, True)}

# Subsidiaries
df['OrganizationSubsidiary'] = df['OrganizationName'].map(lambda x: x if x in subsidiaries_dict else np.NaN,
                                                          na_action='ignore')

# Principal Orgs
df['OrganizationName'] = df['OrganizationName'].replace(subsidiaries_dict)

# Reorder Columns
df = df[list(df.columns)[:8] + ['OrganizationSubsidiary'] + list(df.columns[8:-1])]


# Remove unneeded punctuation
def starting_or_trailing_remove(input_str, to_remove, start_or_end):
    input_str_cln = input_str.strip()
    if start_or_end == 'start':
        if any(input_str_cln.startswith(i) for i in to_remove):
            return input_str_cln[1:]
    elif start_or_end == 'end':
        if any(input_str_cln.endswith(i) for i in to_remove):
            return input_str_cln[:-1]

    # Default
    return input_str


def tails_cln(input_str, to_remove):
    for tail in ['start', 'end']:
        input_str = starting_or_trailing_remove(input_str, to_remove, tail)
    return input_str


punc_rmv = [".", ",", ":", ";"]
df['OrganizationSubsidiary'] = df['OrganizationSubsidiary'].progress_map(lambda x: tails_cln(x, punc_rmv),
                                                                         na_action="ignore")
df['OrganizationName'] = df['OrganizationName'].progress_map(lambda x: tails_cln(x, punc_rmv), na_action="ignore")

# Fix Md --> MD (Medical Doctor).
df['OrganizationName'] = df['OrganizationName'].astype(str).str.replace(" Md ", " MD ").str.replace(" Md,", " MD,")

# -------------------------------------------------------------------------
# Integrate University Endowment
# -------------------------------------------------------------------------

os.chdir(MAIN_FOLDER + "/Data/WikiPull")

# Read in University Endowment and information if the uni is public or private.
univerties_dbs = list(set([i.replace("~$", "") for i in glob2.glob('*/*Complete.csv')]))
university_db = multi_readin(univerties_dbs, unnammed_drop=True)

# Endowment '['x', 'y', 'z']' --> ['x', 'y', 'z'].
university_db['endowment'] = university_db['endowment'].map(lambda x: strlist_to_list(x), na_action='ignore')

# Rename United States of America to United States
university_db['country'] = university_db['country'].str.upper().str.replace("UNITED STATES OF AMERICA", "UNITED STATES")


def endowment_normalizer(endowment_list, country, base_currency='USD', assume_recent=True):
    """

    :param x: passed from the university_db dataframe
    :param base_currency:
    :return:
    """
    if str(endowment_list) == 'nan':
        return np.NaN

    country = country.lower().title()
    amount = float(endowment_list[0])
    amount_currency = endowment_list[1]
    from_year = int(float(endowment_list[2]))

    if len(str(from_year)) != 4:
        if assume_recent:
            from_year = datetime.now().year  # assume most recent
        else:
            return np.NaN

    try:
        return zeitsci_normalize(amount, country, amount_currency, from_year)
    except:
        return np.NaN


university_db['normalized_endowment'] = university_db.apply(
    lambda x: endowment_normalizer(x['endowment'], x['country']), axis=1)

# Upper university names and remove special characters
university_db['university'] = university_db['university'].astype(str).str.upper().map(lambda x: alphanum(unidecode(x)))

# Create a dictionary of normalized (2015 USD) university endowments
university_db_endowment = university_db[university_db['normalized_endowment'].astype(str) != 'nan'].reset_index(
    drop=True)
endowment_dict = twoD_nested_dict(university_db_endowment, 'country', 'university', 'normalized_endowment')

# Create a dictionary of whether or not the institution is public or private
university_db_type = university_db[university_db['institutiontype'].astype(str) != 'nan'].reset_index(drop=True)
institution_type_dict = twoD_nested_dict(university_db_type, 'country', 'university', 'institutiontype')


def institution_to_skip(institution):
    if str(institution) == 'nan' or any(institution.endswith(i) for i in ['Inc', 'Llc', 'Ltd', 'Phd']):
        return True

    institution_lower = institution.lower()
    to_skip = ['council', 'management', 'company', 'foundation', 'software', 'limited', 'asociacion', 'associacion',
               'hospital', 'clinic', 'organisation']
    if any(i in institution_lower for i in to_skip):
        return True
    else:
        return False


def institution_information_lookup(institution, region, fuzzy_threshold=85):
    """
    Look up Endowment and Institution Type (i.e., public or private) Information.
    Note: consider costs of increasing fuzzy_threshold.
    """
    # Initialize
    info_not_found = [np.NaN, np.NaN]
    insts_map = list()

    # Check inputs
    if str(institution) == 'nan' or str(region) == 'nan':
        return institution, info_not_found

    region_upper = region.upper()
    institution_upper = institution.upper()

    # Look up in the dict
    if region_upper not in endowment_dict:
        return institution, info_not_found

    # Check Forwards and Backwards
    insts_map = [i for i in endowment_dict[region_upper] if (institution_upper in i) or (i in institution_upper)]

    if len(insts_map) > 1:
        insts_map = [max(insts_map, key=len)]  # look for counter examples to this heuristic

    # Check with fuzzy matching
    if len(insts_map) != 1:
        fuzzy_match = process.extractOne(institution_upper, endowment_dict[region_upper].keys())
        if fuzzy_match[1] >= fuzzy_threshold:
            insts_map = [fuzzy_match[0]]
        else:
            return institution, info_not_found

    # Look up the information
    endowment = endowment_dict[region_upper].get(insts_map[0], np.NaN)
    institution_type = institution_type_dict[region_upper].get(insts_map[0], np.NaN)

    return institution, [endowment, institution_type]


# Create dataframe of unique orgs
unique_org_df = df.drop_duplicates(subset=['OrganizationName']).reset_index(drop=True)
unique_org_df = unique_org_df[~unique_org_df['OrganizationName'].map(institution_to_skip)].reset_index(drop=True)

# Run -- Pretty quick (despite being a bit slow to start).
inst_info = unique_org_df.progress_apply(
    lambda x: institution_information_lookup(x['OrganizationName'], x['OrganizationBlock']), axis=1
)

# Convert to a dict
insitution_info_dict = {k: v for k, v in inst_info}

end_type = df['OrganizationName'].progress_map(
    lambda x: insitution_info_dict[x] if x in insitution_info_dict else [np.NaN] * 2)

# Add InstitutionType information to the DF
df['Endowment'] = [i[0] for i in end_type]
df['InstitutionType'] = [i[1] for i in end_type]

# -------------------------------------------------------------------------
# Additional Cleaning of String Columns (with Unidecode)
# -------------------------------------------------------------------------

df['OrganizationName'] = df['OrganizationName'].map(lambda x: x.replace("\"", ""), na_action='ignore')

cols_to_decode = ['OrganizationName', 'ProjectTitle', 'Researcher']

for c in cols_to_decode:
    df[c] = df[c].progress_map(unidecode, na_action='ignore')

# Handle keywords separately
df['Keywords'] = df['Keywords'].progress_map(lambda x: unidecode(" ".join(x)), na_action='ignore')

# -------------------------------------------------------------------------
# Guess the Category of Organizations
# -------------------------------------------------------------------------
# Levels: Educational, Governmental, Individual, Industry, Institute, Medical, NGO, NaN.

# Deploy
org_category = pd.Series(df['OrganizationName'].unique()).progress_map(lambda x: [x, organization_classifier(x)])
org_category_dict = {k: v for k, v in org_category}

# Pull org_category_dict mappings into the dataframe
df['OrganizationCategory'] = df['OrganizationName'].progress_map(lambda x: org_category_dict.get(x, np.NaN))


# -------------------------------------------------------------------------
# Clean the Keywords (will take a while).
# -------------------------------------------------------------------------

def keyword_cln(x):
    return [i for i in word_vector_clean(x) if len(i) > 1]


df['Keywords'] = df['Keywords'].progress_map(lambda x: "; ".join(keyword_cln(x)), na_action='ignore')


# -------------------------------------------------------------------------
# Date Correct
# -------------------------------------------------------------------------

def date_zero_correct(input_str):
    """
    Add a zero to days and months less than 10.
    """
    if input_str[0] != "0" and float(input_str) < 10:
        return "0" + input_str
    else:
        return input_str


def date_correct(input_date):
    """
    Formats input to DD/MM/YYYY
    """
    input_split = input_date.split("/")
    if len(input_split) == 0 or len(input_split[-1]) != 4:
        return np.NaN

    if len(input_split) == 1 and len(input_split[0]) == 4 and input_split[0].isdigit():
        return "01/01/" + input_split[0]
    elif len(input_split) == 2 and float(input_split[0]) <= 12:
        month = date_zero_correct(input_split[0])
        year = input_split[1]
        return "/".join(("01", month, year))
    elif len(input_split) == 3:
        if float(input_split[0]) > 12 and float(input_split[1]) <= 12:
            day = date_zero_correct(input_split[0])
            month = date_zero_correct(input_split[1])
        elif float(input_split[0]) <= 12:
            month = date_zero_correct(input_split[0])
            day = date_zero_correct(input_split[1])
        else:
            return np.NaN
        year = input_split[2]
        return "/".join([day, month, year])
    else:
        return np.NaN


df['StartDate'] = df['StartDate'].astype(str).progress_map(date_correct)


def year_extract(date):
    if str(date) == 'nan':
        return np.NaN
    else:
        date_split = str(date).split("/")
        if len(date_split) == 3 and len(date_split[2]) == 4:
            return date_split[2]
        else:
            return np.NaN


# Add a start Year
df['StartYear'] = df['StartDate'].progress_map(year_extract)

# Reorder
reorder = list(df.columns)[0:3] + ["StartYear"] + list(df.columns)[3:-1]
df = df[reorder]

# -------------------------------------------------------------------------
# Remove Invalid Values
# -------------------------------------------------------------------------

max_grant = 10 ** 9
max_endowment = 50 * 10 ** 9

df['NormalizedAmount'] = df['NormalizedAmount'].map(lambda x: x if x <= max_grant else np.NaN, na_action='ignore')
df['Endowment'] = df['Endowment'].map(lambda x: x if x <= max_endowment else np.NaN, na_action='ignore')

# Limit to Current Year
# df = df[df['StartYear'].astype(float) <= 2016].reset_index(drop=True)

# ------------------------------------------------------------------------------------------------
# Clean NaNs
# ------------------------------------------------------------------------------------------------

for i, c in enumerate(df.columns):
    print(str(i) + ": ", c)
    df[c] = df[c].progress_map(lambda x: np.NaN if str(x) == 'nan' else x)

# -------------------------------------------------------------------------
# Save
# -------------------------------------------------------------------------

df.to_pickle(MAIN_FOLDER + "/Data/MasterDatabase/" + "MasterDatabaseRC" + str(RC) + ".p")
