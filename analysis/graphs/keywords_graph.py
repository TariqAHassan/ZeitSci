"""

    Keyword Visualization Data Processing
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Python 3.5

"""
# Imports
import re
import numpy as np
import pandas as pd

import decimal
import babel.numbers
from tqdm import tqdm
from itertools import chain
from unidecode import unidecode
from collections import defaultdict
from graphs.graphing_db_data import funders_dict
from graphs.graphing_tools import funder_info_db
from abstract_analysis import word_vector_clean
from funding_database_tools import MAIN_FOLDER

# babel.numbers.format_currency(decimal.Decimal("102327300000.0"), "USD")

# ------------------------------------------------------------------------------------------------
# Read in Data
# ------------------------------------------------------------------------------------------------

funding = pd.read_pickle(MAIN_FOLDER + "/Data/MasterDatabase/" + "MasterDatabaseRC7.p")
tqdm.pandas(desc="status")

# Convert keywords into a list
funding['Keywords'] = funding['Keywords'].str.split("; ")

# ------------------------------------------------------------------------------------------------
# Goal
# ------------------------------------------------------------------------------------------------

# Keyword by [StartDate] By [Funder] by [Org] by [State] By [Block] by sum(NormalizedAmount)

# ------------------------------------------------------------------------------------------------

# Columns to Use
keyword_df_columns = [ "Keywords",
                       "Funder",
                       "StartDate",
                       "OrganizationName",
                       "OrganizationCity",
                       "OrganizationState",
                       "OrganizationBlock",
                       "NormalizedAmount"
]

# Set the Keywords
funding["Keywords"] = funding["Keywords"].progress_map(lambda x: list(set(x)), na_action="ignore")

# Create a dataframe of only those rows with keywords and normalized funding amounts
zip_df = funding[(funding['Keywords'].astype(str) != 'nan') & (funding['NormalizedAmount'].astype(str) != 'nan')]

# Create a dict to populate
# keywords_dict = defaultdict(float)
keywords_dict = []
for i in tqdm(zip(*[zip_df[c] for c in keyword_df_columns])):
    data = list(i[1:-1])
    for k in i[0]:
        row = [k] + data + [i[-1]]
        keywords_dict.append(row)

# Convet to df
keyword_df = pd.DataFrame(keywords_dict, columns=keyword_df_columns)

# Remove Digits -- To Do: Allow for terms like 5HT (serotonin)
# keyword_df_r = keyword_df[~(keyword_df["Keywords"].progress_map(lambda x: x[0].isdigit() or x[-1].isdigit()))]

# Groupby and Sum
group_by_columns = [c for c in keyword_df_columns[:-1] if str(c) not in ['OrganizationState', 'OrganizationCity']]
keyword_df_sum = keyword_df.groupby(group_by_columns)['NormalizedAmount'].sum().reset_index()

def keyword_remove(s):
    if str(s) == 'nan':
        return True

    if len(s) == 0:
        return True
    elif any(c.isdigit() for c in s):
        return True
    else:
        return False

keyword_df_sum = keyword_df_sum[~keyword_df_sum['Keywords'].progress_map(keyword_remove)].reset_index(drop=True)

# Sort by NormalizedAmount
keyword_df_sum = keyword_df_sum.sort_values(by=["NormalizedAmount"], ascending=False).reset_index(drop=True)

# ------------------------------------------------------------------------------------------------
# Save to Disk
# ------------------------------------------------------------------------------------------------

export_path = MAIN_FOLDER + "/Data/keyword_databases/"
keyword_df_sum.to_csv(export_path + "keywords_db2.csv", index=False, chunksize=500000)

# ------------------------------------------------------------------------------------------------
# Analytic Groupbys
# ------------------------------------------------------------------------------------------------

# Unidecode Org Names
keyword_df_sum["OrganizationName"] = keyword_df_sum["OrganizationName"].progress_map(unidecode, na_action="ignore")

# Add Year Column
keyword_df_sum["Year"] = keyword_df_sum["StartDate"].progress_map(lambda x: x.split("/")[2], na_action="ignore")

def amount_groupby(groupby, df=None):
    data_frame = keyword_df_sum if df is None else df
    gb = data_frame.groupby(groupby)["NormalizedAmount"].sum().reset_index()
    by = ["NormalizedAmount"] if groupby == ["Keywords"] else [i for i in groupby if i != "Keywords"] + ["NormalizedAmount"]
    return gb.sort_values(by=by, ascending=False).reset_index(drop=True)

# ------------------------------------------------------------------------------------
# Most Funded Terms by Funder
# ------------------------------------------------------------------------------------

top = 3

top_funder_df = keyword_df_sum[(keyword_df_sum["Year"].astype(float) >= 2008) &
                               (keyword_df_sum["Year"].astype(float) <= 2015)]

top_funded_funder = amount_groupby(groupby=["Keywords", "Funder", "Year"], df=top_funder_df)

xs = top_funded_funder["Funder"].unique()

def agency_name_simplify(x):
    #return re.findall(r"\(([A-Za-z0-9_]+)\)", x)[0]
    return re.search('\((.*?)\)', funders_dict[x][0]).group(1)

top_funded_funder["FunderFull"] = top_funded_funder["Funder"]
top_funded_funder["Funder"] = top_funded_funder["Funder"].progress_map(agency_name_simplify, na_action="ignore")

# Limit to top 250 keywords for each agency for each year between 2000 and 2015
top_funded_funder = top_funded_funder.groupby(["Funder", "Year"]).head(top)\
                                        .sort_values(["Year", "Funder"], ascending=[True, False]).reset_index(drop=True)

# ---------------------------
# Aggregate by Year
# ---------------------------

top_funded_funder_year = top_funded_funder.groupby(["Keywords", "Year"])["NormalizedAmount"].sum()\
             .reset_index().sort_values(["Year", "NormalizedAmount"], ascending=[True, False]).reset_index(drop=True)

# Normalize between 0 and 1
year_min_max = [top_funded_funder_year["NormalizedAmount"].min(), top_funded_funder_year["NormalizedAmount"].max()]

def normalize(x_i, min_max):
    return (x_i - min_max[0]) / (min_max[1] - min_max[0])

# Normalize top_funded_funder_year -- between 0 and 1
top_funded_funder_year["ScaledAmount"] = top_funded_funder_year["NormalizedAmount"].map(
                                                    lambda x: normalize(x, year_min_max), na_action="ignore")

top_funded_futop_funded_funder_year = top_funded_funder.groupby(["Keywords", "Year"])["NormalizedAmount"].sum()\
             .reset_index().sort_values(["Year", "NormalizedAmount"], ascending=[True, False]).reset_index(drop=True)

# ---------------------------
# Normalize
# ---------------------------

year_min_max = [top_funded_funder_year["NormalizedAmount"].min(), top_funded_funder_year["NormalizedAmount"].max()]

def normalize(x_i, min_max):
    return (x_i - min_max[0]) / (min_max[1] - min_max[0])

# Normalize top_funded_funder_year -- between 0 and 1
top_funded_funder_year["ScaledAmount"] = top_funded_funder_year["NormalizedAmount"].map(
                                                    lambda x: normalize(x, year_min_max), na_action="ignore")

# Compute the proprtion each agency is driving funding for each keyword (considering only the top 3)
def keyword_yearly_proportion(x):
    total = top_funded_funder_year['NormalizedAmount'][(top_funded_funder_year['Keywords'] == x['Keywords']) &
                                                       (top_funded_funder_year["Year"] == x["Year"])]

    return x['NormalizedAmount'] / float(total)

top_funded_funder['ProportionTotal'] = top_funded_funder.apply(lambda x: keyword_yearly_proportion(x), axis=1)

# Compute the proportion for each keyword for each agency for each year.
def keyword_agency_proportion(x):
    total = top_funded_funder['NormalizedAmount'][(top_funded_funder["Funder"] == x["Funder"]) &
                                                  (top_funded_funder["Year"] == x["Year"])]

    return x['NormalizedAmount'] / total.sum()

top_funded_funder['ProportionYearlyTop'] = top_funded_funder.apply(keyword_agency_proportion, axis=1)

# ------------------------------------------------------------------------------------------------
# Additional Groupby
# ------------------------------------------------------------------------------------------------

# ------------------------------------------
# Most Funded Terms
# ------------------------------------------

top_funded = amount_groupby(["Keywords"])

# ------------------------------------------
# Most Funded Terms by Country
# ------------------------------------------

# top_funded_country = amount_groupby(["Keywords", "OrganizationState"])
# top_funded_country = top_funded_country[top_funded_country["OrganizationState"].map(lambda x: len(x) > 2, na_action="ignore")]

# ------------------------------------------
# Most Funded Terms by Org, State and Block
# ------------------------------------------

# top_funded_org = amount_groupby(["Keywords", "OrganizationName", "OrganizationState", "OrganizationBlock"])

# ------------------------------------------------------------------------------------------------
# Exports
# ------------------------------------------------------------------------------------------------


# General
top_funded.to_csv(export_path + "general_keywords.csv", index=False)

# Organizations
org_terms = ["university", "ecole", "institute"]
org_search_term = "|".join(org_terms)

# orgs = top_funded_org[top_funded_org["OrganizationName"].str.lower().str.contains(org_search_term)].reset_index(drop=True)
# orgs.to_csv(export_path + "organizations_keywords.csv", index=False, chunksize=100000)

# Funders#
top_funded_funder.to_csv(export_path + "funders_keywords.csv", index=False)
top_funded_funder_year.to_csv(export_path + "funders_keywords_by_year.csv", index=False)

# Save a funder_db
funder_info_db(df=top_funded_funder, col="FunderFull").to_csv(export_path + "funder_db_keywords.csv", index=False)


# Countries
# top_funded_country.to_csv(export_path + "countries_keywords.csv", index=False)



















