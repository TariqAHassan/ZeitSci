"""

    Formal Python Analyses of the Data
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Python 3.5

"""
import pandas as pd

from tqdm import tqdm
from pprint import pprint
from funding_database_tools import MAIN_FOLDER
from easymoney.easy_pandas import pandas_print_full

# ------------------------------------------------------------------------------------------------
# Read in Data
# ------------------------------------------------------------------------------------------------

funding = pd.read_pickle(MAIN_FOLDER + "/Data/MasterDatabase/" + "MasterDatabaseRC8.p")
tqdm("status")

# ------------------------------------------------------------------------------------------------
# Most by Funding Year
# ------------------------------------------------------------------------------------------------

funding['StartYear'] = funding['StartYear'].astype(float)

range_funding = funding[(funding['StartYear'] >= 2005) & (funding['StartYear'] <= 2015)]

db_total = range_funding['NormalizedAmount'].sum()
d = {c: range_funding[range_funding['FunderBlock'].str.upper() == c.upper()]['NormalizedAmount']\
        .sum()/db_total for c in funding['FunderBlock'].unique()}

block_dict = {k: round(float(v)*100, 1) for k, v in d.items()}

# ------------------------------------------------------------------------------------------------
# Highest-Funded Organizations
# ------------------------------------------------------------------------------------------------

top = 250

top_orgs = funding[(funding['StartYear'].astype(float) >= 2010) & (funding['StartYear'].astype(float) < 2016)].groupby(
    ['OrganizationName', 'OrganizationBlock', 'StartYear'])['NormalizedAmount'].sum().reset_index()

# Get the Top Funded Orgs for Each Year

# Sort by Year and Amount
top_orgs_sorted = top_orgs.sort_values(['StartYear', 'NormalizedAmount'], ascending=[False, False]).reset_index(drop=True)

# Get the top x per year
by_year = top_orgs_sorted.sort_values('NormalizedAmount', ascending=False).groupby('StartYear', as_index=False).head(top)

# Sort
by_year_sorted = by_year.sort_values(['StartYear', 'NormalizedAmount'], ascending=[False, False]).reset_index(drop=True)

# Add Ranking (will only work for certian values of top)
by_year_sorted['Ranking'] = list(range(1, top+1)) * int(round(by_year_sorted.shape[0]/top))

# Rename
by_year_sorted.columns = ['Name', 'Country', 'Start Year', 'Total Grants (USD)', 'Ranking']

# Format Money (see http://stackoverflow.com/a/3393776/4898004)
by_year_sorted['Total Grants (USD)'] = by_year_sorted['Total Grants (USD)'].map(lambda x: '{:20,.2f}'.format(x).strip())

# Reorder
by_year_sorted = by_year_sorted[['Ranking', 'Name', 'Country', 'Start Year', 'Total Grants (USD)']]

by_year_sorted.to_csv(MAIN_FOLDER + "analysis/resources/" + '2010_2015_rankings_detailed.csv', index=False)





























