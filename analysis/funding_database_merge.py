"""

    Merge the Various Funding Databases into One
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""
# Modules
import re
import os
import time
import glob2
import string
import numpy as np
import pandas as pd
from tqdm import tqdm

import dask.dataframe as dd
from unidecode import unidecode
from abstract_analysis import *
from currency_converter import CurrencyConverter

from funding_database_tools import titler
from funding_database_tools import MAIN_FOLDER
from funding_database_tools import multi_readin

from easymoney.money import EasyPeasy
from easymoney.easy_pandas import strlist_to_list, twoD_nested_dict, pandas_print_full
from sources.world_bank_interface import _world_bank_pull_wrapper as wbpw

# Release Candidate
RC = 6

# Goal:
# A dataframe with the following columns:

#   Researcher
#       Fields                        X  -- use journal ranking dataframe
#       ResearcherSubfields           X  -- use journal ranking dataframe
#       ResearchAreas (sub-subfield)  X  -- use journal ranking dataframe
#       Amount
#       NormalizedAmount                 -- the grant in 2015 USD (2016 not handled properly...fix)
#       Currency
#       YearOfGrant
#       FundingSource
#       Collaborators                 X  -- based on pubmed 2000-2016 download
#       keywords
#       Institution
#       Endowment                        -- use wikipedia universities database
#       InstitutionType                  -- use wikipedia universities database (i.e., public or private)
#       InstitutionRanking            V  -- Ranking of the institution (read: uni). QS Data available; usage Prohibitive.
#       InstutionCountry
#       City/NearestCity
#       lng
#       lat

# X = to do (when all country's data are assembled)

# To do: Run an abstract analysis on each keyword/term. This will standardize the terms


# ------------------------------------------------------------------------- #
#                           General Tools & Information                     #
# ------------------------------------------------------------------------- #


# Special Characters.
chars = re.escape(string.punctuation)

# Create an instance of EasyPeasy

def alphanum(input_str, chars=chars):
    """
    Remove *all* non-alphanumeric characters
    see: http://stackoverflow.com/questions/23996118/replace-special-characters-in-a-string-python

    return " ".join("".join(c for c in substring if c.isalnum()) for substring in input_str.split())

    :param input_str:
    :return:
    """
    return re.sub(r'[' + chars + ']', '', input_str)

os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/CompleteRegionDatabases")

# ------------------------------------------------------------------------- #
# Integrate Funding Data from around the World
# ------------------------------------------------------------------------- #

# Read in Databases
us_df = pd.read_pickle('AmericanFundingDatabase.p')
eu_df = pd.read_pickle('EuropeanUnionFundingDatabase.p')
ca_df = pd.read_pickle('CanadianFundingDatabase.p')

# Merge the dataframes
df = us_df.append([eu_df, ca_df])
df = df.reset_index(drop=True)
tqdm.pandas(desc="status")

# ------------------------------------------------------------------------- #
# Normalize Grant Amount
# ------------------------------------------------------------------------- #

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
            c1 = float(cpi_dict[year_a_str][region]) # start
            c2 = float(cpi_dict[year_b_str][region]) # end
            rate = (c2 - c1)/c1 + 1

    return rate

def zeitsci_normalize(amount, amount_state, amount_cur, from_year, amount_block = None, base_year=2015, base_currency='USD'):
    """

    :param amount:
    :param amount_block:
    :param amount_state:
    :param amount_cur:
    :param from_year:
    :param base_year:
    :param base_currency:
    :return:
    """
    region = amount_block if amount_block in ['United States', 'Canada'] else amount_state

    # Handle regions not in the DB
    if region not in cpi_dict_max:
        return np.NaN

    # Set the inflation rate
    if from_year <= cpi_dict_max[region]:
        inflation_rate = zeitsci_cpi(region, from_year, base_year)
    else:
        inflation_rate = 1

    if pd.isnull(inflation_rate):
        return np.NaN

    # Adjust for inflation
    real_amount = amount * inflation_rate

    # Convert to base currency
    return c.convert(real_amount, amount_cur, base_currency)

def zeitsci_grant_normalize_wrapper(x):

    if pd.isnull(x['GrantYear']): return np.NaN
    input_dict = {
        'state' : x['OrganizationState'],
        'amount' : x['Amount'],
        'from_year' : int(x['GrantYear']),
        'amount_cur' : x['FundCurrency'],
        'block': x['OrganizationBlock']
    }
    if any(pd.isnull(i) for i in input_dict.values()): return np.NaN

    return zeitsci_normalize(input_dict['amount']
                             , input_dict['state']
                             , input_dict['amount_cur']
                             , input_dict['from_year']
                             , input_dict['block'])

df['NormalizedAmount'] = df.progress_apply(lambda x: zeitsci_grant_normalize_wrapper(x), axis=1)

# Temporary until the above Integration code is rerun.
# df['OrganizationBlock'] = df['OrganizationBlock'].astype(str).str.replace("Italy", "United States")

# ------------------------------------------------------------------------- #
# Clean OrganizationName
# ------------------------------------------------------------------------- #

# To fix: The Medical University of South Carolina =/= University of South Carolina.

# Clean the OrganizationName
df['OrganizationName'] = df['OrganizationName'].map(cln).str.replace("\"","").str.strip().progress_apply(titler)

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

subsidiaries_dict = subsidiary_checker(unique_orgs, possible_subsidiaries_cln )

# Subsidiaries
df['OrganizationSubsidiary'] = df['OrganizationName'].map(
                                                lambda x: x if x in subsidiaries_dict else np.NaN, na_action='ignore')

# Principal Orgs
df['OrganizationName'] = df['OrganizationName'].replace(subsidiaries_dict)

# pandas_print_full(pd.DataFrame(list(subsidiaries_dict.items())))

# Reorder
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
df['OrganizationSubsidiary'] = df['OrganizationSubsidiary'].progress_map(lambda x: tails_cln(x, punc_rmv), na_action="ignore")
df['OrganizationName'] = df['OrganizationName'].progress_map(lambda x: tails_cln(x, punc_rmv), na_action="ignore")

# Fix Md --> MD (Medical Doctor).
df['OrganizationName'] = df['OrganizationName'].astype(str).str.replace(" Md ", " MD ").str.replace(" Md,", " MD,")

# ------------------------------------------------------------------------- #
# Integrate University Endowment
# ------------------------------------------------------------------------- #

os.chdir(MAIN_FOLDER + "/Data/WikiPull")

# Read in University Endowment and information if the uni is public or private.
univerties_dbs = list(set([i.replace("~$", "") for i in glob2.glob('*/*Complete.csv')]))
university_db = multi_readin(univerties_dbs, unnammed_drop=True)

# Endowment '['x', 'y', 'z']' --> ['x', 'y', 'z'].
university_db['endowment'] = university_db['endowment'].map(lambda x: strlist_to_list(x), na_action='ignore')

def endowment_normalizer(x, base_currency='USD'):
    """

    :param x: passed from the university_db dataframe
    :param base_currency:
    :return:
    """
    endowment_list = x['endowment']
    if str(endowment_list) == 'nan':
        return np.NaN

    amount = float(endowment_list[0])
    amount_currency = endowment_list[1]
    from_year = int(float(endowment_list[2]))

    if len(str(from_year)) == 4:
        try:
            return zeitsci_normalize(amount, x['country'], amount_currency, from_year)
        except:
            return np.NaN

    return np.NaN

university_db['normalized_endowment'] = university_db.apply(lambda x: endowment_normalizer(x), axis=1)

# Upper university names and remove special chars
university_db['university'] = university_db['university'].astype(str).str.upper().map(lambda x: alphanum(x))

# Rename United States of America to United States
university_db['country'] = university_db['country'].str.upper().str.replace("UNITED STATES OF AMERICA", "UNITED STATES")

# Create a dictionary of normalized (2015 USD) university endowments
endowment_dict = twoD_nested_dict(university_db, 'country', 'university', 'normalized_endowment')

# Create a dictionary of whether or not the institution is public or private
institution_type_dict = twoD_nested_dict(university_db, 'country', 'university', 'institutiontype')

def institution_information_lookup(institution, block, state):
    """

    :param institution:
    :param region:
    :return:
    """
    # Initialize
    insts_map = list()

    # Check inputs
    if str(institution) == 'nan' or str(block) == 'nan' or str(state) == 'nan':
        return np.NaN, np.NaN

    # Set Region
    region = (state if block == 'Europe' else block).upper()

    # Look up in the dict
    if region in endowment_dict:
        insts_map = [i for i in endowment_dict[region] if institution in i]
        if len(insts_map) == 1:
            return endowment_dict[region][insts_map[0]], institution_type_dict[region][insts_map[0]]

    return np.NaN, np.NaN

# Create a list of lists of the form [[OrganizationName, OrganizationBlock, OrganizationState]]
institutions = list(zip(*[df['OrganizationName'].str.upper(), df['OrganizationBlock'], df['OrganizationState']]))

# Run institution_information_lookup on all dataframe entries
endowment_type = np.array([institution_information_lookup(i[0], i[1], i[2]) for i in institutions])

# Add Endowment information to the DF
df['Endowment'] = endowment_type[:,0]

# Add InstitutionType information to the DF
df['InstitutionType'] = endowment_type[:,1]

df['OrganizationName'] = df['OrganizationName'].map(lambda x: x.replace("\"", ""), na_action='ignore')

# ------------------------------------------------------------------------- #
# Clean the Keywords (will take a while).
# ------------------------------------------------------------------------- #

def keyword_cln(x):
    if str(x) == 'nan':
        return np.NaN
    joined_x = unidecode(" ".join(x))
    return word_vector_clean(joined_x)

# df['Keywords'] = df['Keywords'].progress_map(lambda x: keyword_cln(x), na_action='ignore')

# Use Dask to Execute this in Parallel
dd_df = dd.from_pandas(df[['Keywords']], npartitions=4)
df['Keywords'] = dd_df.apply(lambda x: keyword_cln(x['Keywords']), axis=1).compute()

# ------------------------------------------------------------------------- #
# Date Correct
# ------------------------------------------------------------------------- #

def date_zero_correct(input_str):
    """
    Add a Zero to days and months less than 10.
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

# ------------------------------------------------------------------------- #
# Save
# ------------------------------------------------------------------------- #

print("Saving...")
df.to_pickle(MAIN_FOLDER + "/Data/MasterDatabase/" + "MasterDatabaseRC" + str(RC) + ".p")











































