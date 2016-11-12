"""

    Record of Resources Used
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Python 3.5

"""
# Imports
import pandas as pd
from funding_database_tools import MAIN_FOLDER


# ------------------------------------------------------------------------------------------------
# Read in Data
# ------------------------------------------------------------------------------------------------

df = pd.read_pickle(MAIN_FOLDER + "/Data/MasterDatabase/" + "MasterDatabaseRC7.p")

# Project Titles, Authors and Organizations for Canadian Data
canada_data_source = df[df['FunderBlock'] == 'Canada'][['ProjectTitle', 'Researcher', 'OrganizationName', 'GrantYear', 'Amount']]

canada_data_source.to_csv(MAIN_FOLDER + "analysis/resources/" + "CanadianDataSource.csv", index=False)

















































