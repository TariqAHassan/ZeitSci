'''

    Develop a Database of Science Funding
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


'''

# Modules
import re
import os
import time
import glob2
import string
import numpy as np
import pandas as pd

from abstract_analysis import *
from funding_database_tools import MAIN_FOLDER
from funding_database_tools import multi_readin


from easymoney.money import EasyPeasy
from easymoney.easy_pandas import strlist_to_list, twoD_nested_dict


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
#       Endowment                        -- use wikipedia universties database
#       InstitutionType                  -- use wikipedia universties database (i.e., public or private)
#       InstitutionRanking            V  -- Ranking of the institution (read: uni). QS Data avaliable; usage rights unkown.
#       InstutionCountry
#       City/NearestCity
#       lng
#       lat

# X = to do (when all country's data are assembled)

# Also: Run an abstract analysis on each keyword/term this will standardize the terms


# ------------------------------------------------------------------------- #
#                           General Tools & Information                     #
# ------------------------------------------------------------------------- #


# Special Characters.
chars = re.escape(string.punctuation)

# Create an instance of EasyPeasy
ep = EasyPeasy()

def alphanum(input_str, chars=chars):
    """
    Remove *all* non-alphanumeric characters
    see: http://stackoverflow.com/questions/23996118/replace-special-characters-in-a-string-python

    #return " ".join("".join(c for c in substring if c.isalnum()) for substring in input_str.split())

    :param input_str:
    :return:
    """
    return re.sub(r'[' + chars + ']', '', input_str)


os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/CompleteRegionDatabases")


# ------------------------------------------------------------------------- #
#               Integrate Funding Data from around the World                #
# ------------------------------------------------------------------------- #

# Read in Databases
us_df = pd.read_pickle('AmericanFundingDatabase.p')
eu_df = pd.read_pickle('EuropeanUnionFundingDatabase.p')
ca_df = pd.read_pickle('CanadianFundingDatabase.p')

# Merge the dataframes
df = us_df.append([eu_df, ca_df])
df.index = range(df.shape[0])

# ------------------------------------------------------------------------- #
#                           Normalize Grant Amount                          #
# ------------------------------------------------------------------------- #

def zeitsci_normalize(amount
                      , org_block
                      , org_state
                      , grant_year
                      , to_year=2015
                      , base_currency='USD'
                      , exchange_date = '2015-12-31'):
    """

    :param amount:
    :param org_block:
    :param org_state:
    :param grant_year:
    :param to_year:
    :param base_currency:
    :param exchange_date:
    :return:
    """
    # Set the Currency (and handle Europe properly).
    currency = org_state if org_block == 'Europe' else org_block

    # Return a NaN if any nans are passed
    if 'nan' in [str(i) for i in list(locals().values())]:
        return np.nan

    try:
        return ep.normalize(amount=amount
                             , currency=currency
                             , from_year=int(grant_year)
                             , to_year=to_year
                             , base_currency=base_currency
                             , exchange_date=exchange_date)
    except:
        return np.nan

c = 0
normalize_grant_list = list()
for grant in zip(*[df['Amount'], df['OrganizationBlock'], df['OrganizationState'], df['GrantYear']]):
    c += 1
    if c % 5000 == 0:
        print(round((float(c) / df.shape[0]) * 100, 2), "%")
    normalize_grant_list.append(zeitsci_normalize(grant[0], grant[1], grant[2], grant[3]))

# An .apply wasn't used because this is a lengthy operation, currently
# bottlednecked by easymoney. This way progress can be monitored.
df['NormalizedAmount'] = normalize_grant_list

# ------------------------------------------------------------------------- #
#                      Write Integrated Database to Disk                    #
# ------------------------------------------------------------------------- #

df.to_pickle("FundingDatabase.p")
# df.to_csv('FundingDatabase.csv', index=False)

# ------------------------------------------------------------------------- #
#                      Read In Cached Integrated Database                   #
# ------------------------------------------------------------------------- #

df = pd.read_pickle('FundingDatabase.p')

# Temporary until the above Integration code is rerun.
df['OrganizationBlock'] = df['OrganizationBlock'].astype(str).str.replace("Italy", "United States")

# ------------------------------------------------------------------------- #
#                          Post Integration Processing                      #
# ------------------------------------------------------------------------- #

# Peak at Keywords

# keyword_funding_dict = defaultdict(list)
# for i in range(df.shape[0]):
#     keywords = df['Keywords'][i]
#     amount = df['NormalizedAmount'][i]
#
#     if not str(keywords) == 'nan' and not str(amount) == 'nan':
#         for k in keywords:
#             keyword_funding_dict[k].append(amount)
#
#     if i % 10000 == 0:
#         print(round(i/float(df.shape[0])*100, 2), "%")
#
#
# sum_keywords = {k: sum(v) for k, v in keyword_funding_dict.items()}
#
# kdf = pd.DataFrame({
#     'amount': list(sum_keywords.values()),
#     'keywords' : list(sum_keywords.keys())})
#
#
# kdf = kdf.sort_values('amount', ascending=False)
# kdf.reset_index(drop=True, inplace=True)
#
#
# kdf[kdf.keywords == 'rat']
# df[df['Researcher'].map(lambda x: True if 'raymond klein' in str(x).lower() else False)]

# ------------------------------------------------------------------------- #
#                        Integrate University Endowment                     #
# ------------------------------------------------------------------------- #

os.chdir(MAIN_FOLDER + "/Data/WikiPull")

# Read in University Endowment and information if the uni is public or private.
univerties_dbs = list(set([i.replace("~$", "") for i in glob2.glob('*/*Complete.csv')]))
university_db = multi_readin(univerties_dbs, unnammed_drop=True)

# Endowment '['x', 'y', 'z']' --> ['x', 'y', 'z'].
university_db['endowment'] = university_db['endowment'].map(lambda x: x if str(x) == 'nan' else strlist_to_list(x))

def endowment_normalizer(endowment_list, country, base_currency='USD'):
    """

    :param endowment_list:
    :param block:
    :param state:
    :return:
    """
    if str(endowment_list) == 'nan':
        return np.NaN

    amount = float(endowment_list[0])
    from_year = int(float(endowment_list[2]))

    if len(str(from_year)) == 4:
        try:
            return ep.normalize(amount=amount, currency=country, from_year=from_year, base_currency=base_currency)
        except:
            return np.NaN

    return np.NaN

university_db['normalized_endowment'] = university_db.apply(
    lambda x: endowment_normalizer(x['endowment'], x['country']), axis=1)

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



# ------------------------------------------------------------------------- #
#                         Integrate University Ranking                      #
# ------------------------------------------------------------------------- #

# Have not found usable data source for this.
# QS does publish the data as a .xlsx, but usage rights are currently unknown.


# ------------------------------------------------------------------------- #
#                                    Save                                   #
# ------------------------------------------------------------------------- #

# Save
df.to_pickle(MAIN_FOLDER + "/Data/MasterDatabase/" + 'MasterDatabaseRC3.p')


# Fix quotes in Org. Name, e.g., "3s - Sensors, Signal Processing, Systems Gmbh".






































































































































































































































































































































































































































































































































































