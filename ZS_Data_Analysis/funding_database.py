'''

Develop a Database of Science Funding
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 3.5

'''

# ---------------- #
#  Import Modules  #
# ---------------- #

import os
import sys
import time
import glob2
import datetime
import pycountry
import unicodedata
import numpy as np
import pandas as pd
from copy import deepcopy
from collections import defaultdict

from abstract_analysis import *
from funding_database_tools import MAIN_FOLDER

from region_abbrevs import US_states, European_Countries

from supplementary_fns import cln
from supplementary_fns import lprint
from supplementary_fns import insen_replace
from supplementary_fns import partial_match
from supplementary_fns import pandas_col_shift
from supplementary_fns import partial_list_match
from supplementary_fns import items_present_test

# ZeitSci Classes
from zeitsci_wiki_api import WikiUniversities, wiki_complete_get
from open_cage_functionality import ZeitOpenCage

from nltk.corpus import stopwords

from region_abbrevs import Australian_states
from region_abbrevs import Australia_Inist_Cities
from open_cage_functionality import ZeitOpenCage
from my_keys import OPENCAGE_KEY

from easymoney.money import EasyPeasy
# ep = EasyPeasy()


# Goal:
# A dataframe with the following columns:

#  Researcher
#       Fields                       X  -- use journal ranging dataframe
#       ResearcherSubfields          X  -- use journal ranging dataframe
#       ResearchAreas (sub-subfield) X  -- use journal ranging dataframe
#       Amount
#       NormalizedAmount             X  -- the grant in 2015 USD (or 2016...fix)
#       Currency
#       YearOfGrant
#       FundingSource
#       Colaberators                 X -- based on pubmed 2000-2016 download
#       keywords
#       Instution
#       Endowment                    X -- use wikipedia universties database
#       InstutionCountry
#       City/NearestCity
#       lng
#       lat

# X = do when all country's data are assembled

# TO DO: Run a abstract analysis on each keyword/term.
# this will standardize the terms

os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/CompleteRegionDatabases")


# ------------------------------------------------------------------------- #
#               Integrate Funding Data from around the World                #
# ------------------------------------------------------------------------- #


us_df = pd.read_pickle('AmericanFundingDatabase.p')
eu_df = pd.read_pickle('EuropeanUnionFundingDatabase.p')
ca_df = pd.read_pickle('CanadianFundingDatabase.p')


# Merge the dataframes
df = us_df.append([eu_df, ca_df])
df.index = range(df.shape[0])

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

# Didn't use an .apply because this is a lengthy operation, currently
# bottlednecked by easymoney. This way progress can be monitored
df['NormalizedAmount'] = normalize_grant_list

# df.to_pickle("FundingDatabase.p")
# df.to_csv('FundingDatabase.csv', index=False)


# ------------------------------------------------------------------------- #
#                          Post Integration Processing                      #
# ------------------------------------------------------------------------- #

df = pd.read_pickle('FundingDatabase.p')


df[df['NormalizedAmount'] < 0]



keyword_funding_dict = defaultdict(list)
for i in range(df.shape[0]):
    keywords = df['Keywords'][i]
    amount = df['NormalizedAmount'][i]

    if not str(keywords) == 'nan' and not str(amount) == 'nan':
        for k in keywords:
            keyword_funding_dict[k].append(amount)

    if i % 10000 == 0:
        print(round(i/float(df.shape[0])*100, 2), "%")


sum_keywords = {k: sum(v) for k, v in keyword_funding_dict.items()}

kdf = pd.DataFrame({
    'amount': list(sum_keywords.values()),
    'keywords' : list(sum_keywords.keys())
})


kdf = kdf.sort_values('amount', ascending=False)
kdf.reset_index(drop=True, inplace=True)


kdf[kdf.keywords == 'rat']




























































































































































































































































































































































































































































































































































































































