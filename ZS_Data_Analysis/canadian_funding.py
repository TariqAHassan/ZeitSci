'''

    Canadian Funding
    ~~~~~~~~~~~~~~~~

    Python 3.5

'''

# ---------------- #
#  Import Modules  #
# ---------------- #

import os
import glob2
import unicodedata
import numpy as np
import pandas as pd
from abstract_analysis import *

from funding_database_tools import MAIN_FOLDER
from funding_database_tools import order_cols
from funding_database_tools import comma_reverse
from funding_database_tools import remove_accents
from funding_database_tools import try_dict_lookup
from funding_database_tools import fdb_common_words
from funding_database_tools import df_combine
from funding_database_tools import column_drop


# ------------------------------------------------------------------------------------------------------------ #
#                                                     Canada                                                   #
# ------------------------------------------------------------------------------------------------------------ #


# Will need to get geographic information from University
# University of Toronto was downloaded in two parts...Errors when attempting to download all grants at once from
# NSERC's generously-provided API.

os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/Canada/Funding_by_Region")

# Import
ca_data_file_names = list(set([i.replace("~$", "") for i in glob2.glob('*/*.xlsx')]))
ca_df = df_combine(ca_data_file_names, skip=3, file_types='excel', file_name_add = True)

# Get State (Province) and University Information
ca_df['state'] = ca_df.file_name.map(lambda x: x.split("/")[0].replace("_", " "))
ca_df['university'] = ca_df.file_name.map(lambda x: x.split("/")[1].split(".")[0])

# Remove _x if it exits
ca_df['university'] = ca_df['university'].map(lambda x: x.split("_")[0])

# Remove unneeded columns
ca_df = column_drop(ca_df, ["file_name", "award type", "program"])

# Rename columns
ca_df.columns = ['amount', 'year', 'researcher', 'title', 'state', 'university']

# Drop NaNs
ca_df = column_drop(ca_df, ["amount", "year", "researcher"], drop_type = "na")

# Drop Rows with No Title
ca_df = ca_df[~(ca_df.title.astype(str).str.contains("No title"))]
ca_df.index = range(ca_df.shape[0])

# Correct Year
ca_df.year = ca_df.year.map(lambda x: x.split("-")[0])

# Import
can_uni_geo = pd.read_csv(MAIN_FOLDER + "/Data/WikiPull/North_America/" + "NorthAmericaUniversitiesComplete.csv")
del can_uni_geo["Unnamed: 0"]

# Limit to canada
can_uni_geo = can_uni_geo[can_uni_geo.Country == "Canada"].reset_index(drop=True)
# can_uni_geo.index = range(can_uni_geo.shape[0])

# Get lat - lng info
can_city_lat = dict(zip([remove_accents(k) for k in can_uni_geo['University'].str.lower()], can_uni_geo['lat']))
can_city_lng = dict(zip([remove_accents(k) for k in can_uni_geo['University'].str.lower()], can_uni_geo['lng']))

# Determine what Unis are missing
# missing_can_unis = list(set(ca_df.university.unique().tolist()) - set(can_city_dict.keys()))

# Populate with lat-lng information
ca_df['lng'] = ca_df.university.str.lower().map(lambda x: try_dict_lookup(can_city_lng, x))
ca_df['lat'] = ca_df.university.str.lower().map(lambda x: try_dict_lookup(can_city_lat, x))

# -------------------- #
# Add city information #
# -------------------- #


os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/Canada")

# Import
can_uni_cities = pd.read_excel("Canadian_Universities_Wiki.xlsx")

# Limit to city
can_uni_cities['City'] = can_uni_cities['City'].map(lambda x: x.split(",")[0])

# Create a dict (preferable time complexity).
missing_can_cities_dict = dict(zip(can_uni_cities['Name'].str.lower(), can_uni_cities['City']))

# Populate the city Column
ca_df['city'] = ca_df['university'].str.lower().map(lambda x: try_dict_lookup(missing_can_cities_dict, x))

# Drop rows without geo information
ca_df = column_drop(ca_df, columns_to_drop=["lat", "city"], drop_type='na')

# Correct Researcher Name
ca_df.researcher = ca_df.researcher.map(lambda x: comma_reverse(x))

# Clean up title
ca_df['title'] = ca_df['title'].astype(str).map(lambda x: x.replace("\\\"", ""))

# Use the title for keywords...not ideal, but it's the only option.
ca_df['keywords'] = fdb_common_words(ca_df['title'], n=5, update_after=5000)

# Refactor index
ca_df.index = range(ca_df.shape[0])

# Add Curency Column
ca_df["FundCurrency"] = pd.Series("CAD", index=ca_df.index)

# Add Funder Column
ca_df["Funder"] = pd.Series("NSERC", index=ca_df.index)

# Add block
ca_df["OrganizationBlock"] = pd.Series("Canada", index=ca_df.index)

# Add Start Date
ca_df["StartDate"] = ca_df['year'].map(lambda x: "01/01/" + str(x))

# Rename Columns
new_col_names = [  "Amount"
                 , "GrantYear"
                 , "Researcher"
                 , "ProjectTitle"
                 , "OrganizationState"
                 , "OrganizationName"
                 , "lng"
                 , "lat"
                 , "OrganizationCity"
                 , "Keywords"
                 , "FundCurrency"
                 , "Funder"
                 , "OrganizationBlock"
                 , "StartDate"]

# Rename columns
ca_df.columns = new_col_names

# Convert GrantYear and Amount to Floats
ca_df['GrantYear'] = ca_df['GrantYear'].astype(float)
ca_df['Amount'] = ca_df['Amount'].map(lambda x: x if str(x) == 'nan' else str(x).replace(",", "")).astype(float)

# Reorder columns
ca_df = ca_df[order_cols]

# Canadian Data Stabalized #

# Save
os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/CompleteRegionDatabases")
ca_df.to_pickle("CanadianFundingDatabase.p")



















































