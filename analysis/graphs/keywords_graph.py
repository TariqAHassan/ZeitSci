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
from graphs.graphing_data import funders_dict
from abstract_analysis import word_vector_clean
from funding_database_tools import MAIN_FOLDER

# babel.numbers.format_currency(decimal.Decimal("102327300000.0"), "USD")

# ------------------------------------------------------------------------------------------------ #
# Read in Data
# ------------------------------------------------------------------------------------------------ #

funding = pd.read_pickle(MAIN_FOLDER + "/Data/MasterDatabase/" + "MasterDatabaseRC6.p")
tqdm.pandas(desc="status")

# ------------------------------------------------------------------------------------------------ #
# Goal
# ------------------------------------------------------------------------------------------------ #

# Keyword by [StartDate] By [Funder] by [Org] by [State] By [Block] by sum(NormalizedAmount)

# ------------------------------------------------------------------------------------------------ #

# Columns to Use
keyword_df_columns = ["Funder",
                       "StartDate",
                       "NormalizedAmount",
                       "OrganizationName",
                       "OrganizationCity",
                       "OrganizationState",
                       "OrganizationBlock"
]

# Set the Keywords
funding["Keywords"] = funding["Keywords"].progress_map(lambda x: list(set(x)), na_action="ignore")

def fast_flatten(input_list):
    return list(chain.from_iterable(input_list))

def keyword_mapper(x):
    """

    """
    keywords = x["Keywords"]
    if pd.isnull(x["NormalizedAmount"]) or not isinstance(keywords, list):
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
keyword_df = pd.DataFrame(keywords_flatten, columns=["Keywords"] + keyword_df_columns)

# Correct for weird negative grants
keyword_df["NormalizedAmount"] = keyword_df["NormalizedAmount"].progress_map(lambda x: -1*x if x < 0 else x, na_action="ignore")

# Collapse on NormalizedAmount (yeilds ~30% Reduction in the number of rows)
group_by = [c for c in ["Keywords"] + keyword_df_columns if c != "NormalizedAmount"]
keyword_df_sum = keyword_df.groupby(group_by)["NormalizedAmount"].sum().reset_index()

# Remove Digits -- Allow for terms like 5HT (serotonin)
keyword_df_sum = keyword_df_sum[~(keyword_df_sum["Keywords"].map(lambda x: x[0].isdigit() or x[-1].isdigit()))]

# Sort by NormalizedAmount
keyword_df_sum = keyword_df_sum.sort_values(by=["NormalizedAmount"], ascending=False).reset_index(drop=True)

# ------------------------------------------------------------------------------------------------ #
# Save to Disk
# ------------------------------------------------------------------------------------------------ #

export_path = MAIN_FOLDER + "/Data/keyword_databases/"

# keyword_df_sum.to_csv(export_path + "keywords_db.csv", index=False, chunksize=500000)

keyword_df_sum = pd.read_csv(export_path + "keywords_db.csv")

# ------------------------------------------------------------------------------------------------ #
# Analytic Groupbys
# ------------------------------------------------------------------------------------------------ #

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

def agency_name_simplify(x):
    return re.findall(r"\(([A-Za-z0-9_]+)\)", x)[0]

top_funded_funder["Funder"] = top_funded_funder["Funder"].map(
                                                lambda x: agency_name_simplify(funders_dict[x][0]), na_action="ignore")

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

# Scale and add a floor, precisely: f(x) = x * 2250 + 23.
# top_funded_funder_year["ScaledAmount"] = top_funded_funder_year["ScaledAmount"] * 2250 + 23

# Compute the proprtion each agency is driving funding for each keyword
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

# ------------------------------------------------------------------------------------------------ #
# Additional Groupby
# ------------------------------------------------------------------------------------------------ #

# ------------------------------------------
# Most Funded Terms
# ------------------------------------------

top_funded = amount_groupby(["Keywords"])

# ------------------------------------------
# Most Funded Terms by Country
# ------------------------------------------

top_funded_country = amount_groupby(["Keywords", "OrganizationState"])
top_funded_country = top_funded_country[top_funded_country["OrganizationState"].map(lambda x: len(x) > 2, na_action="ignore")]

# ------------------------------------------
# Most Funded Terms by Org, State and Block
# ------------------------------------------

top_funded_org = amount_groupby(["Keywords", "OrganizationName", "OrganizationState", "OrganizationBlock"])

# ------------------------------------------------------------------------------------------------ #
# Exports
# ------------------------------------------------------------------------------------------------ #

# General
top_funded.to_csv(export_path + "general_keywords.csv", index=False)

# Organizations
org_terms = ["university", "ecole", "institute"]
org_search_term = "|".join(org_terms)

orgs = top_funded_org[top_funded_org["OrganizationName"].str.lower().str.contains(org_search_term)].reset_index(drop=True)
orgs.to_csv(export_path + "organizations_keywords.csv", index=False, chunksize=100000)

# Funders
top_funded_funder.to_csv(export_path + "funders_keywords.csv", index=False)
top_funded_funder_year.to_csv(export_path + "funders_keywords_by_year.csv", index=False)

# Countries
top_funded_country.to_csv(export_path + "countries_keywords.csv", index=False)



















