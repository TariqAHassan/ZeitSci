"""

    Data Visualizations Built using Bokeh
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Python 3.5

"""
# Imports
import numpy as np
import pandas as pd
from tqdm import tqdm
from copy import deepcopy
from itertools import chain
from abstract_analysis import word_vector_clean
from funding_database_tools import MAIN_FOLDER
from funding_database_tools import unique_order_preseve


# ------------------------------------------------------------------------------------------------ #
# Read in Data
# ------------------------------------------------------------------------------------------------ #

funding = pd.read_pickle(MAIN_FOLDER + "/Data/MasterDatabase/" + 'MasterDatabaseRC6.p')
tqdm.pandas(desc="status")

# Funder, Org, State, Block, Keyword, NormalizedAmount

# Keyword by [StartDate] By [Funder] by [Org] by [State] By [Block] by sum(NormalizedAmount)

def keyword_mapper(c):
    """

    """
    d = list(c[1:])
    unpack = list()
    for k in c[0]:
        unpack += [[k] + d]
    return unpack

# Columns to Use
keyword_df_columns = ['Funder',
                       'StartDate',
                       'NormalizedAmount',
                       'OrganizationName',
                       'OrganizationCity',
                       'OrganizationState',
                       'OrganizationBlock'
]

cols = list(zip(*[funding[c] for c in ['Keywords'] + keyword_df_columns]))

# Writen in this verbose way because it's the form that makes tqdm the most stable...
keywords = list()
for c in tqdm(cols):
    if not any(str(i) == 'nan' for i in [c[0], c[3]]):
        keywords += keyword_mapper(c)

# Convert to DataFrame
columns = ['Keywords'] + keyword_df_columns
keyword_df = pd.DataFrame(keywords, columns=columns)

# Collapse on NormalizedAmount
group_by = [c for c in ['Keywords'] + keyword_df_columns if c != 'NormalizedAmount']
keyword_df_sum = keyword_df.groupby(group_by)['NormalizedAmount'].sum().reset_index()

keyword_df_sum = keyword_df_sum[keyword_df_sum['Keywords'].str.strip() != ""].reset_index(drop=True)

keyword_df_sum.to_csv(MAIN_FOLDER + "/Data/" + "keywords.csv")































