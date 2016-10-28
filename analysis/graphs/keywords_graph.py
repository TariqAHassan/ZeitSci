"""

    Data Visualizations Built using Bokeh
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Python 3.5

"""
# Imports
import numpy as np
import pandas as pd

import decimal
import babel.numbers
from tqdm import tqdm
from copy import deepcopy
from itertools import chain
from unidecode import unidecode
from abstract_analysis import word_vector_clean
from funding_database_tools import MAIN_FOLDER
from funding_database_tools import unique_order_preseve

# babel.numbers.format_currency(decimal.Decimal("102327300000.0"), "USD")

# ------------------------------------------------------------------------------------------------ #
# Read in Data
# ------------------------------------------------------------------------------------------------ #

funding = pd.read_pickle(MAIN_FOLDER + "/Data/MasterDatabase/" + 'MasterDatabaseRC6.p')
tqdm.pandas(desc="status")

# ------------------------------------------------------------------------------------------------ #
# Goal
# ------------------------------------------------------------------------------------------------ #

# Keyword by [StartDate] By [Funder] by [Org] by [State] By [Block] by sum(NormalizedAmount)

# ------------------------------------------------------------------------------------------------ #

# Columns to Use
keyword_df_columns = ['Funder',
                       'StartDate',
                       'NormalizedAmount',
                       'OrganizationName',
                       'OrganizationCity',
                       'OrganizationState',
                       'OrganizationBlock'
]

# Set the Keywords
funding['Keywords'] = funding['Keywords'].progress_map(lambda x: list(set(x)), na_action='ignore')

def fast_flatten(input_list):
    return list(chain.from_iterable(input_list))

def keyword_mapper(x):
    """

    """
    keywords = x['Keywords']
    if pd.isnull(x['NormalizedAmount']) or not isinstance(keywords, list):
        return np.NaN

    d = [x[c] for c in keyword_df_columns]

    unpack = [[]] * len(keywords)
    for i in range(len(keywords)):
        unpack[i] = [keywords[i]] + d
    return unpack

# Expand the funding dataframe on keywords
keywords = funding.progress_apply(lambda x: keyword_mapper(x), axis=1).dropna().tolist()

# Flatten the nested list by one degree
keywords_flatten = fast_flatten(keywords)

# Convert to DataFrame
keyword_df = pd.DataFrame(keywords_flatten, columns=['Keywords'] + keyword_df_columns)

# Correct for weird negative grants
keyword_df['NormalizedAmount'] = keyword_df['NormalizedAmount'].progress_map(lambda x: -1*x if x < 0 else x, na_action='ignore')

# Collapse on NormalizedAmount (yeilds ~30% Reduction in the number of rows)
group_by = [c for c in ['Keywords'] + keyword_df_columns if c != 'NormalizedAmount']
keyword_df_sum = keyword_df.groupby(group_by)['NormalizedAmount'].sum().reset_index()

# Remove Digits -- Allow for terms like 5HT (serotonin)
keyword_df_sum = keyword_df_sum[~(keyword_df_sum['Keywords'].map(lambda x: x[0].isdigit() or x[-1].isdigit()))]

# Sort by NormalizedAmount
keyword_df_sum = keyword_df_sum.sort_values(by=['NormalizedAmount'], ascending=False).reset_index(drop=True)

# ------------------------------------------------------------------------------------------------ #
# Save to Disk
# ------------------------------------------------------------------------------------------------ #

keyword_df_sum.to_csv(MAIN_FOLDER + "/Data/keyword_databases/" + "keywords_db.csv", index=False, chunksize=500000)

# ------------------------------------------------------------------------------------------------ #
# Analytic Groupbys
# ------------------------------------------------------------------------------------------------ #

keyword_df_sum['OrganizationName'] = keyword_df_sum['OrganizationName'].progress_map(unidecode, na_action='ignore')

def amount_groupby(groupby):
    gb = keyword_df_sum.groupby(groupby)['NormalizedAmount'].sum().reset_index()
    by = ['NormalizedAmount'] if groupby == ['Keywords'] else [i for i in groupby if i != 'Keywords'] + ['NormalizedAmount']
    return gb.sort_values(by=by, ascending=False).reset_index(drop=True)

# Most Funded Terms
top_funded = amount_groupby(['Keywords'])

# Most Funded Terms by Country
top_funded_country = amount_groupby(['Keywords', 'OrganizationState'])
top_funded_country = top_funded_country[top_funded_country['OrganizationState'].map(lambda x: len(x) > 2, na_action='ignore')]

# Most Funded Terms by Org
top_funded_org = amount_groupby(['Keywords', 'OrganizationName'])

# Most Funded Terms by Funder
top_funded_funder = amount_groupby(['Keywords', 'Funder'])































