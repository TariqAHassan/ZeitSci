"""

    Australia
    ~~~~~~~~~

"""
import os
import numpy as np
import pandas as pd
from analysis.supplementary_fns import cln
from analysis.funding_database_tools import titler, year_columns
from analysis.funding_database_tools import MAIN_FOLDER
from analysis.funding_database_tools import column_drop
from analysis.region_abbrevs import Australia_Inist_Cities
from analysis.zeitsci_wiki_api import WikiUniversities, wiki_complete_get
from analysis.funding_database_tools import order_cols
from analysis.open_cage_functionality import ZeitOpenCage

from analysis.my_keys import OPENCAGE_KEY


# ------------------------------------------------------------- #
# Australia's National Health and Medical Research Council Data #
# ------------------------------------------------------------- #

# COLLAPSING ACCROSS YEAR. THIS NEEDS TO BE REVERSED AS IT IS NOT CONSISTENT WITH THE OTHER DATASETS.


os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/Australia")

# import Aussie Data
aus_df = pd.read_excel("AUS_GRants_2000_2015.xlsx", sheetname="2000 TO 2015 DATA")

# fix column names
aus_df.columns = ["_".join(cln(i).split(" ")).lower() if " " in i else cln(i).lower() for i in aus_df.columns.tolist()]

# Remove all non university or research funding
aus_df.sector = [s.lower().capitalize() for s in aus_df.sector.tolist()]
aus_df = aus_df[aus_df.sector.isin(["University"])]
aus_df.index = range(0, aus_df.shape[0])

# fix n-a
for column in aus_df.columns.tolist():
    aus_df[column][aus_df[column].astype(str).str.lower() == "n-a"] = np.NaN
aus_df.index = range(aus_df.shape[0])

# Remove Researcher name Information
for to_replace in ['Prof', 'Dr', 'A/Pr', 'Mr', 'Ms']:
    aus_df['pi_name'] = aus_df['pi_name'].str.replace(to_replace, '')

# Clean pi_name column
aus_df['pi_name'] = [cln(c).rstrip().lstrip() for c in aus_df['pi_name'].tolist()]

# Clean keywords

# replace "," with "|", which they should be
aus_df.keywords = aus_df.keywords.str.replace(",", "|")

# Split on pipe
aus_df.keywords = aus_df.keywords.str.split("|")

cleaned_keywords = list()
for k in aus_df.keywords.tolist():
    cleaned_keywords.append([cln(str(kw)).lstrip().rstrip() for kw in k if cln(kw, 2) not in ['', ' ']])

# add back to df
aus_df.keywords = cleaned_keywords

# Remove any rows without keywords
aus_df = aus_df[aus_df.astype(str)['keywords'] != '[]']
aus_df.index = range(aus_df.shape[0])

# Drop Unneeded Columns
to_drop = ["application_year"
    , "grant_sub_type"
    , "sector"
    , "status"
    , "end_yr"
    , "grant_id"
    , "field_of_research"
    , "broad_research_area"]

aus_df = column_drop(aus_df, to_drop)
# for td in to_drop:
#     aus_df.drop(td, axis = 1, inplace = True)
# aus_df.index = range(aus_df.shape[0])

# Add Curency Column
aus_df["FundCurrency"] = "AUD"

# Add Funder Column
aus_df["Funder"] = "NHMRC"

# Add blcok
aus_df["OrganizationBlock"] = "Australia"

# Get Geographical location information
os.chdir(MAIN_FOLDER + "/Data/WikiPull/Oceania")

# Import and remove nulls
oc_unis = pd.read_csv("OceaniaUniversities.csv")
oc_unis = oc_unis[pd.notnull(oc_unis["lat"])]

# Add Geo Columns
aus_df["lng"] = ""
aus_df["lat"] = ""

aus_df = aus_df[pd.notnull(aus_df["administering_institution"])]
oc_unis.index = range(oc_unis.shape[0])

oc_uni_names_before = oc_unis.University
oc_unis.University = oc_unis.University.astype(str).str.lower()


def aus_loc_lookup(university):
    """

    :param university:
    :return:
    """

    try:
        # this will slow it down
        df_slice = oc_unis[oc_unis.University == cln(university.lower())]

        if df_slice.shape[0] == 1:
            return df_slice.lat.iloc[0], df_slice.lng.iloc[0]
        else:
            return (None, None)
    except:
        return (None, None)


# use an apply?
for row in range(aus_df.shape[0]):
    if row % 500 == 0: print(row, "of", aus_df.shape[0])

    uni_loc = aus_loc_lookup(aus_df.administering_institution[row])
    aus_df.set_value(row, 'lat', uni_loc[0])
    aus_df.set_value(row, 'lng', uni_loc[1])

# Drop those rows for which geo info was
# not obtained
aus_df = aus_df[pd.notnull(aus_df["lat"])]
aus_df = aus_df[aus_df["lat"] != None]
aus_df.index = range(aus_df.shape[0])

aus_df.start_yr = aus_df.start_yr.astype(int)

# Limit to 2000 onward
aus_df = aus_df[aus_df.start_yr >= 2000]
aus_df.index = range(aus_df.shape[0])

# Create Cities column based on the University
aus_df["city"] = ""
aus_df["city"] = aus_df.administering_institution.replace(Australia_Inist_Cities).tolist()

# Clean up grant_title
aus_df["grant_title"] = [titler(i) for i in aus_df.grant_title.tolist()]

# Rename columns
new_col_names = ["Researcher"
    , "ProjectTitle"
    , "OrganizationName"
    , "OrganizationState"
    , "GrantYear"
    , "Amount"
    , "Keywords"
    , "FundCurrency"
    , "Funder"
    , "OrganizationBlock"
    , "lng"
    , "lat"
    , "OrganizationCity"
                 ]

# Rename columns
aus_df.columns = new_col_names

# Reorder columns
aus_df = aus_df[order_cols]

# ---------------------------------- #
#  Australian Research Council Data  #
# ---------------------------------- #

os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/Australia")

ausf_df = pd.read_excel("ARC_NCGP_Projects_and_fellowships_completed_Nov2015.xlsx", sheetname="Projects")
ausf_df.columns = [cln(str(i)).lstrip().rstrip() for i in ausf_df.columns.tolist()]

to_drop = ["Scheme Code",
           "Submission Year",
           "Summary/National Benefit",
           "Primary FoR/RFCD",
           "Primary FoR/RFCD Description"]\
          + year_columns(columns=aus_df.columns)  # [str(i) for i in range(2002, 2016, 1)]
ausf_df = column_drop(ausf_df, to_drop)
ausf_df.columns = ["title", "year", "organisation_name", "state", "researcher", "keywords", "amount"]

na_drop = [
    "year"
    , "organisation_name"
    , "state"
    , "researcher"
    , "keywords"
    , "amount"
]
ausf_df = column_drop(ausf_df, na_drop, drop_type="na")

# Clean researcher column
for to_replace in ['Prof ', 'Dr ', 'A/Pr ', 'A/Prof ', 'Mr ', 'Ms ']:
    ausf_df['researcher'] = ausf_df['researcher'].map(lambda x: cln(x, 1)).str.replace(to_replace, '')

ausf_df['researcher'] = ausf_df['researcher'].str.replace("A/", '')

# Split
ausf_df['researcher'] = ausf_df['researcher'].str.strip().map(
    lambda x: cln(x, 1).replace(";", ',')).str.title().str.split(";  ")

# Clean keywords
ausf_df['keywords'] = ausf_df['keywords'].str.lower().str.split("; ")

# Add City information
ausf_df["organisation_city"] = ""

# Try without 'The' in front
regex = r'({})'.format('|'.join(list(Australia_Inist_Cities.keys())))
ausf_df.organisation_city = ausf_df.organisation_name.str.extract(regex, expand=False).map(Australia_Inist_Cities)

# Manually account for CSIRO
ausf_df["organisation_city"][ausf_df["organisation_name"].astype(str).str.contains("CSIRO")] = "Canberra"

# ausf_df["organisation_name"][ausf_df["organisation_city"].isnull()].unique()
# Charles Sturt University is multi-campus and not enouch information is given in the dataset
# to determine which campus is being refered to. Thus, it will be excluded.

# Drop NaN Cities
ausf_df = ausf_df[pd.notnull(ausf_df["organisation_city"])]
ausf_df.index = range(ausf_df.shape[0])

# Add Curency Column
ausf_df["FundCurrency"] = pd.Series("AUD", index=ausf_df.index)

# Add Funder Column
ausf_df["Funder"] = pd.Series("ARC", index=ausf_df.index)

# Add blcok
ausf_df["OrganizationBlock"] = pd.Series("Australia", index=ausf_df.index)

# Make required columns
ausf_df["lng"] = pd.Series("", index=ausf_df.index)
ausf_df["lat"] = pd.Series("", index=ausf_df.index)

# lng dict
aus_uni_lng_dict = dict(zip(oc_unis.University.tolist(), oc_unis.lng.tolist()))
regex = r'({})'.format('|'.join(aus_uni_lng_dict.keys()))
ausf_df["lng"] = ausf_df.organisation_name.str.lower().str.extract(regex, expand=False).map(aus_uni_lng_dict)

# lat dict
aus_uni_lat_dict = dict(zip(oc_unis.University.tolist(), oc_unis.lat.tolist()))
regex = r'({})'.format('|'.join(aus_uni_lat_dict.keys()))
ausf_df["lat"] = ausf_df.organisation_name.str.lower().str.extract(regex, expand=False).map(aus_uni_lat_dict)

# ----------------------- #
#  Fill missing Geo Info  #
# ----------------------- #

# Fill in CSIRO's location (Canberra) #

# Create an instance of the WikiUniversities Class
wiki_info_get = WikiUniversities()

# Find the CSIRO CSIRO is located in (...granted, it doesn't need to be this complex)...
CSIRO_CITY = ausf_df.organisation_city[ausf_df.organisation_name.str.upper().str.contains("CSIRO")].unique().tolist()[0]

# Populate the ausf_df with info extract from wikipedia
selector = ausf_df.organisation_name.str.upper().str.contains("CSIRO")
ausf_df.lng[selector], ausf_df.lat[selector] = wiki_info_get.wiki_coords_extractor(wiki_complete_get(CSIRO_CITY))

# Fill in the Unis with missing Geo Info #
replacement_dict = {"University of Technology, Sydney": "University of Technology Sydney"
    , "Victoria University of Technology": "Victoria University, Australia"
    , "Victoria University": "Victoria University, Australia"
    , "Northern Territory University": "Charles Darwin University"}


def _missing_geo_name_corrector(institution):
    if institution in list(replacement_dict.keys()):
        return replacement_dict[institution]
    else:
        return institution


def missing_geo_populate(data_frame, unis_missing_geo_info):
    for u in unis_missing_geo_info:
        sel = data_frame["organisation_name"] == u
        coords = wiki_info_get.wiki_coords_extractor(wiki_complete_get(_missing_geo_name_corrector(u)))
        data_frame.lng[sel], data_frame.lat[sel] = coords if coords != None else [np.NaN, np.NaN]

    return data_frame


# Fill in via wikipedia
ausf_df = missing_geo_populate(ausf_df, ausf_df.organisation_name[ausf_df["lat"].isnull()].unique().tolist())


# Define a function to fill in via OPENCAGE
def specific_uni_fill(data_frame, uni, name_to_lookup=None):
    """

    :param data_frame:
    :param uni: in data frame
    :return: what to query OPENCAGE with/for
    """

    if name_to_lookup == None:
        name_to_lookup = uni

    ocage = ZeitOpenCage(api_key=OPENCAGE_KEY)
    sel = data_frame["organisation_name"] == uni
    data_frame.lng[sel], data_frame.lat[sel] = ocage.lookup(name_to_lookup, request="geo")

    return data_frame


# Fill in via OpenCage
ausf_df = specific_uni_fill(ausf_df, uni="Deakin University", name_to_lookup="Deakin University, Australia")

# To be sure, drop any rows with missing lat information (should yeild no change)
ausf_df = column_drop(ausf_df, columns_to_drop=["lat"], drop_type="na")

# Rename Columns
new_col_names = ["ProjectTitle"
    , "GrantYear"
    , "OrganizationName"
    , "OrganizationState"
    , "Researcher"
    , "Keywords"
    , "Amount"
    , "OrganizationCity"
    , "FundCurrency"
    , "Funder"
    , "OrganizationBlock"
    , "lng"
    , "lat"
                 ]

# Rename columns
ausf_df.columns = new_col_names

# Reorder columns
ausf_df = ausf_df[order_cols]

# Only use first author
ausf_df.Researcher = ausf_df.Researcher.map(lambda x: x[0].split(",")[0])

# ---------------------------------- #
#     Combine aus_df and ausf_df     #
# ---------------------------------- #

au_df = aus_df.append(ausf_df)
au_df.index = range(au_df.shape[0])

# ***UNCOLLAPSE FUNDING ACCROSS YEAR.***
