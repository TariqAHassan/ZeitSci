"""

    Keyword Visualization Data Processing
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Python 3.5

"""
import pandas as pd

from pprint import pprint
from funding_database_tools import MAIN_FOLDER

# ------------------------------------------------------------------------------------------------
# Read in Data
# ------------------------------------------------------------------------------------------------

funding = pd.read_pickle(MAIN_FOLDER + "/Data/MasterDatabase/" + "MasterDatabaseRC8.p")

# ------------------------------------------------------------------------------------------------
# Descriptive Stats
# ------------------------------------------------------------------------------------------------

funding['StartYear'] = funding['StartYear'].astype(float)

range_funding = funding[(funding['StartYear'] >= 2005) & (funding['StartYear'] <= 2015)]


db_total = range_funding['NormalizedAmount'].sum()
d = {c: range_funding[range_funding['FunderBlock'].str.upper() == c.upper()]['NormalizedAmount']\
        .sum()/db_total for c in funding['FunderBlock'].unique()}

block_dict = {k: round(float(v)*100, 1) for k, v in d.items()}

























































