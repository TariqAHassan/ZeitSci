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
from fuzzywuzzy import fuzz    # needed?
from fuzzywuzzy import process
from abstract_analysis import *
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
ep = EasyPeasy()


# Goal:
# A dataframe with the following
# columns:

#  Researcher
#       Fields                       X  -- use journal ranging dataframe
#       ResearcherSubfields          X  -- use journal ranging dataframe
#       ResearchAreas (sub-subfield) X  -- use journal ranging dataframe
#       GrantAmount
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

# ------------------------------------------------------------------------- #
#                        Commonly Used Data/Objects                         #
# ------------------------------------------------------------------------- #

MAIN_FOLDER = "/Users/tariq/Google Drive/Programming Projects/ZeitSci/"

# Reorder
order_cols = [
     "Researcher"
    ,"Funder"
    ,"GrantYear"
    ,"Amount"
    ,"FundCurrency"
    ,"ProjectTitle"
    ,"OrganizationName"
    ,"OrganizationCity"
    ,"OrganizationState"   # -> region
    ,"OrganizationBlock"
    ,"lat"
    ,"lng"
    ,"Keywords"
]

def titler(input_str):
    """

    # Doesn't handle ', e.g., l'University

    String titling function

    :param input_str:
    :return:
    """

    if not isinstance(input_str, str):
        return input_str

    # Define stop words
    esw = stopwords.words("english") + ["de", "la", "et", "di", "fur", "l'"]

    # Strip whitespace and split
    input_str = cln(input_str).lstrip().rstrip().split()

    for i in range(len(input_str)):
        if i == 0:
            input_str[i] = input_str[i].lower().capitalize()
        else:
            if input_str[i].lower() not in esw:
                input_str[i] = input_str[i].lower().capitalize()
            elif input_str[i].lower() in esw:
                input_str[i] = input_str[i].lower()

    return " ".join(input_str)

def df_combine(files, file_types = 'excel', skip = 0, file_name_add = False, encoding = "ISO-8859-1", lower_col = True):

    # If a string is provided, convert to a list
    if not isinstance(files, list) and isinstance(files, str):
        files = [files]

    # Read in data
    to_concat = list()
    for f in files:
        if file_types == 'excel':
            temp_df = pd.read_excel(f, skiprows = range(skip))
        elif file_types == 'csv':
            temp_df = pd.read_csv(f, encoding = encoding)
        if lower_col:
            temp_df.columns = [cln(i).lower().lstrip().rstrip() for i in temp_df.columns.tolist()]
        else:
            temp_df.columns = [cln(i).lstrip().rstrip() for i in temp_df.columns.tolist()]

        if file_name_add:
            temp_df['file_name' if lower_col else 'File_Name'] = f
        to_concat.append(temp_df)

    # Combine frames into a single data frame
    df = pd.concat(to_concat)

    # Reindex
    df.index = range(df.shape[0])

    return df

def comma_reverse(input_str):
    """

    :param input_str:
    :return:
    """

    if input_str.count(",") != 1:
        return input_str

    # should join on " ", not ", " -- could be useful though for handling middle names.
    return " ".join([cln(i).lstrip().rstrip().lower().title() for i in input_str.split(",")][::-1])

def column_drop(data_frame, columns_to_drop, drop_type = "complete"):
    """

    :param data_frame:
    :param columns_to_drop:
    :param drop_type: 'complete' or 'na'
    :return:
    """

    # Drop column or NAs in columns.
    for col in columns_to_drop:
        if drop_type == 'complete':
            data_frame.drop(col, axis = 1, inplace = True)
        elif drop_type == 'na':
            data_frame = data_frame[pd.notnull(data_frame[col])]

    # Refactor index
    data_frame.index = range(data_frame.shape[0])

    return data_frame

def string_match_list(input_list, string_to_match):
    """

    :param input_list:
    :param string_to_match:
    :return:
    """
    return [i for i in input_list if string_to_match in i]

def fdb_common_words(summary_series, n = 5, update_after = 5000):
    """

    :param summary_list:
    :return:
    """

    counter = 0
    words = [[]]*summary_series.shape[0]
    for sw in range(summary_series.shape[0]):
        words[sw] = common_words(summary_series[sw], n = n)[0]

        counter += 1
        if counter % update_after == 0:
            print("Strings Analyzed:", str(round(float(counter)/summary_series.shape[0]*100, 2)) + "%")

    return words

def year_columns(columns):

    def is_float(input_str):
        try:
            float(input_str)
            return True
        except:
            return False

    return [x.strip() for x in columns if is_float(x.strip()) and len(x.strip()) == 4]

# Create ISO country Dict.
two_iso_country_dict = dict()
for country in list(pycountry.countries):
    two_iso_country_dict[country.alpha2] = country.name

# ------------------------------------------------------------------------- #
#               Integrate Funding Data from around the World                #
# ------------------------------------------------------------------------- #

# Data sets to integrate #
# United States, Europe, Australia and Canada.

# ------------------------------------------------------------------------------------------------------------ #
#                                            United States of America                                          #
# ------------------------------------------------------------------------------------------------------------ #


# Notes: this take a little time to run...
# it's pushing around over half a million entries after all.

# os.getcwd()
os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/USA")

us_files = [i for i in os.listdir() if i != ".DS_Store"][0:]

to_concat = []
for f in us_files:
    temp_df = pd.read_csv(f, encoding = "ISO-8859-1")
    temp_df.columns = [cln(c.lower(), 2) for c in temp_df.columns.tolist()]
    to_concat.append(temp_df)

us_df = pd.concat(to_concat)
us_df.index = range(us_df.shape[0])

# Drop Unneeded Columns
to_drop = [  "congressional_district"
           , "cfda_code"
           , "sm_application_id"
           , "fy_total_cost_sub_projects"
           , "project_id"
           , "duns_number"
           , "project_start_date"
           , "project_end_date"
           , "budget_start_date"
           , "budget_end_date"
           , "project_number"
           , "ic_center"
           , "other_pis"]
us_df = column_drop(us_df, columns_to_drop = to_drop)
# for td in to_drop:
#     us_df.drop(td, axis = 1, inplace = True)
# us_df.index = range(us_df.shape[0])

# Drop row if NA for certian columns
na_drop = [  "fy"
           , "contact_pi_project_leader"
           , "fy_total_cost"
           , "organization_city"
           , "organization_country"
           , "organization_name"
           , "organization_state"
]
us_df = column_drop(us_df, columns_to_drop = na_drop, drop_type = "na")
# for n in na_drop:
#     us_df = us_df[pd.notnull(us_df[n])]
# us_df.index = range(us_df.shape[0])

# Merge agency and department; drop both after.
us_df["fundingsource"] = us_df.agency + "_" + us_df.department
us_df.drop("agency", axis = 1, inplace = True)
us_df.drop("department", axis = 1, inplace = True)

# Clean up fundingsource
def funding_sources(fs):
    """

    :param fs:
    :return:
    """

    new_fs = list()
    for f in fs:
        if f.split("_")[0] == f.split("_")[1]:
            if [f, f.split("_")[0]] not in new_fs:
                new_fs.append([f, f.split("_")[0]])
        else:
            if [f, f] not in new_fs:
                new_fs.append([f, f])

    return new_fs

new_fs = funding_sources(fs = us_df.fundingsource.unique())

# Remove rows like NASA_NASA; they're redundant.
new_fs = [i for i in new_fs if i[0] != i[1]]
for f in new_fs:
    us_df.loc[us_df.fundingsource == f[0], 'fundingsource'] = f[1]

# Drop duplicates; less rows = less computation time.
us_df.drop_duplicates(keep = "first", inplace = True)
us_df.index = range(us_df.shape[0])

# Get lng/lat from zip
os.chdir(MAIN_FOLDER + "/Data")

# Get Zip code data
zipdb = pd.read_csv("free-zipcode-database.csv")

# Cean the us_df Dataframe
us_df['organization_zip'] = us_df.organization_zip.astype(str)
us_df['organization_zip'] = us_df.organization_zip.apply(lambda v: v.strip().split("-")[0])
us_df['organization_city'] = us_df.organization_city.apply(lambda v: v.strip())

# Convert Zipcode to a string
zipdb['Zipcode'] = zipdb.Zipcode.astype(str)

# Correct zipdb column names
zipdb.rename(columns = dict(  Zipcode = 'organization_zip'
                            , City = 'organization_city'
                            , Country = 'organization_country'
                            , State = 'organization_state')
                            , inplace = True)

# Specify join on
cols = ['organization_zip', 'organization_city', 'Lat', 'Long']

# Merage
us_df = us_df.merge(zipdb[cols], how = 'left')

# Many thanks to @miraculixx over on Stack Overflow.
# see: http://stackoverflow.com/questions/38284615/speed-up-pandas-dataframe-lookup/38284860#38284860

# Drop entries for which location information could not be obtained
us_df = us_df[pd.notnull(us_df["Lat"])]

# lower col names
us_df.columns = [c.lower() for c in us_df.columns]
us_df.index = range(us_df.shape[0])

# deploy comma_reverse()
us_df.contact_pi_project_leader = [comma_reverse(i) for i in us_df.contact_pi_project_leader.tolist()]

# Correct organization_city; not perfect, but close enough
us_df.organization_city = [i.lower().title() for i in us_df.organization_city.tolist()]

# Correct Keywords
keywords = us_df.project_terms.tolist()
us_df.project_terms = [i.lstrip().rstrip().lower().split(";") if isinstance(i, str) else np.NaN for i in keywords]

# Correct the titles...will take a moment
us_df.project_title = [titler(i) for i in us_df.project_title.tolist()]

# Correct the organization_name; not perfect, but close enough
us_df.organization_name = [titler(i) for i in us_df.organization_name.tolist()]

del us_df["organization_zip"]

# DOUPLE CHECK ZIPCODE COLUMN DROP IS WORKING CORRECTLY #

# Rename Columns
new_col_names = [  "Researcher"
                 , "GrantYear"
                 , "Amount"
                 , "OrganizationCity"
                 , "OrganizationBlock"
                 , "OrganizationName"
                 , "OrganizationState"
                 , "Keywords"
                 , "ProjectTitle"
                 , "Funder"
                 , "lat"
                 , "lng"
]
us_df.columns = new_col_names

# Remove individual reserchers
us_df = us_df[~us_df.OrganizationName.map(lambda x: "".join(x.lower().split())).str.contains(",phd")]
us_df = us_df[~us_df.OrganizationName.map(lambda x: "".join(x.lower().split())).str.contains(",md")]

# Add Currency Column
us_df["FundCurrency"] = "USD"

# Correct Block Name
us_df.OrganizationBlock = us_df.OrganizationBlock.str.title()

# Order Columns
us_df = us_df[order_cols]


# US Data Stabilized #


# ------------------------------------------------------------------------------------------------------------ #
#                                                European Union                                                #
# ------------------------------------------------------------------------------------------------------------ #


# Need to merge 2007-2013 with: 2002-2006, and 2014-2020 (truncate projections) data.
# File structures are similair.

os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/EU")

# 1998-2002 excluded because only project funding information
# is provided -- individual uni. grants are not.
# Have data from 2002 - 2016.

# Get file names
eu_data_file_names = list(set([i.replace("~$", "") for i in glob2.glob('**/*.xlsx')]))
eu_data_file_names.sort(key = lambda x: x.split("-")[0])

# Read in Project Data (2002-2006, 2007-2013, 2014-2020)
eu_dfp = df_combine(string_match_list(eu_data_file_names, "proj"), file_name_add = True)
eu_dfp.file_name = eu_dfp.file_name.str.split("/").str.get(0)

# Convert ECmaxcontribution to float
eu_dfp.ecmaxcontribution = eu_dfp.ecmaxcontribution.astype(str).map(lambda x: re.sub("[^0-9]", "", x))
eu_dfp.ecmaxcontribution = eu_dfp.ecmaxcontribution.map(lambda x: [np.NaN if x.strip() == "" else x.strip()][0]).astype(float)

# Read in Org. Data (2002-2006, 2007-2013, 2014-2020)
eu_dfo = df_combine(string_match_list(eu_data_file_names, "organ"), file_name_add = True)
eu_dfo.file_name = eu_dfo.file_name.str.split("/").str.get(0)

# Get Grant Year and Project Summary from EU_Funding_Projects
eu_dfo["grant_year"] =  pd.Series("", index = eu_dfo.index)
eu_dfo["summary"]    =  pd.Series("", index = eu_dfo.index)
eu_dfo["title"]      =  pd.Series("", index = eu_dfo.index)

def proj_to_org_extractor(project_data_frame, organization_data_frame):

    c = 0
    # Faster solutions are possible but this naive approach leaves little room for error.
    unique_rnc = organization_data_frame.projectrcn.unique()
    for r in unique_rnc:
        c += 1
        if c % 1000 == 0: print(round((float(c)/len(organization_data_frame.projectrcn.unique()))*100, 2), "%")

        df_slice = project_data_frame[project_data_frame.rcn == r]
        indices = organization_data_frame[organization_data_frame.projectrcn == r].index
        for i in indices:
            organization_data_frame.set_value(i, 'summary', df_slice["objective"].iloc[0])
            organization_data_frame.set_value(i, 'grant_year', df_slice["startdate"].iloc[0].year)
            organization_data_frame.set_value(i, 'title', df_slice["title"].iloc[0])

            # for 2002-2006, the ECcontribution was in the projects file...
            if "2002-2006" in set(df_slice.file_name.tolist()):
                organization_data_frame.set_value(i, 'eccontribution', df_slice["ecmaxcontribution"].iloc[0])

    return organization_data_frame

# Rename org.df to EU df.
eu_df = proj_to_org_extractor(eu_dfp, eu_dfo)

#[eu_df.grant_year.astype("float").min(), eu_df.grant_year.astype("float").max()]

# Limit to 2016 (the year of this analysis.
eu_df = eu_df[eu_df.grant_year.astype("float") <= 2016]
eu_df.grant_year = eu_df.grant_year.astype("float")

# Remove rows without either city or postal code information
eu_df = eu_df[(~eu_df.city.astype(str).isin(["nan", "NaN"])) | (~eu_df.postcode.astype(str).isin(["nan", "NaN"]))]

# Drop row if NA for certian columns
na_drop = [  "eccontribution"   # European Commission Contribution
           , "country"
           , "title"
]
eu_df = column_drop(eu_df, columns_to_drop = na_drop, drop_type = "na")
# for n in na_drop:
#     eu_df = eu_df[pd.notnull(eu_df[n])]
# eu_df.index = range(eu_df.shape[0])

# Drop Unneeded Columns
to_drop = [  "organizationurl"
           , "id"
           , "projectrcn"
           , "projectacronym"
           , "projectreference"
           , "contacttitle"]
eu_df = column_drop(eu_df, to_drop)
# for td in to_drop:
#     eu_df.drop(td, axis = 1, inplace = True)
# eu_df.index = range(eu_df.shape[0])

# Import EU GeoLocation Data #
eu_ploc = pd.read_csv("european_postcodes_us_standard.csv")
eu_cloc = pd.read_csv("european_cities_us_standard.csv")

# Rename their Columns
eu_ploc.columns = ["postal", "iso", "lat", "lng"]
eu_cloc.columns = ["city",   "iso", "lat", "lng"]

# Perform needed transformations to dtype str
eu_ploc["postal"] = eu_ploc["postal"].astype(str).str.strip()
eu_cloc["city"] = eu_cloc["city"].astype(str).str.strip()


# Use a hash table (dict) for geo-ifno look up; O(1) or O(n).
# See: http://stackoverflow.com/questions/38307855/nested-dictionary-from-pandas-data-frame/38309528#38309528

# Postal dict
eu_ploc["zipped"] = list(zip(eu_ploc.lat, eu_ploc.lng))
postal_dict = eu_ploc.groupby('iso').apply(lambda x: x.set_index('postal')['zipped'].to_dict()).to_dict()

# City Dict
eu_cloc["zipped"] = list(zip(eu_cloc.lat, eu_cloc.lng))
eu_cloc['city'] = eu_cloc.city.str.upper()
city_dict = eu_cloc.groupby('iso').apply(lambda x: x.set_index('city')['zipped'].to_dict()).to_dict()

def eu_loc_lookup(city, postal_code, alpha2country, postal_dict, city_dict):
    """

    :param city:
    :param postal_code:
    :param alpha2country:
    :return: lat, lng
    """

    try:
        city = cln(city, 1).lstrip().rstrip().upper()
        postal_code = cln(str(postal_code), 1).lstrip().rstrip().upper()
        alpha2country = cln(str(alpha2country), 2)

        # Restrict to the given country #
        postal_dict = postal_dict[alpha2country.upper()]
    except:
        return None

    # Try Postal Code #

    # Try as is
    if postal_code in postal_dict.keys():
        return postal_dict[postal_code][0], postal_dict[postal_code][1], "postal"

    # Try Clearing the space
    if cln(postal_code, 2) in postal_dict.keys():
        return postal_dict[cln(postal_code, 2)][0], postal_dict[cln(postal_code, 2)][1], "postal"

    # Try splitting on " "
    if postal_code.count(" ") == 1 and postal_code.split(" ")[0] in postal_dict.keys():
        if list(postal_dict.keys()).count(postal_code.split(" ")[0]) == 1:
            return postal_dict[postal_code.split(" ")[0]][0], postal_dict[postal_code.split(" ")[0]][1], "postal"

    # Try splitting on "-"
    if postal_code.count("-") == 1 and postal_code.split("-")[0] in postal_dict.keys():
        if list(postal_dict.keys()).count(postal_code.split("-")[0]) == 1:
            return postal_dict[postal_code.split("-")[0]][0], postal_dict[postal_code.split("-")[0]][1], "postal"

    # Try City #
    try:
        return city_dict[alpha2country.upper()][city][0], city_dict[alpha2country.upper()][city][1], "city"
    except:
        return None

def _lat_lng_add(data_frame):

    lat_lng = list()
    quality = list()
    nrow = data_frame.shape[0]
    for i in range(0, nrow):

        if i % 25000 == 0: print(" -------- %s of %s -------- " % (i, str(nrow)))

        rslt = eu_loc_lookup(   city = data_frame["city"][i]
                              , postal_code = data_frame["postcode"][i]
                              , alpha2country = data_frame["country"][i]
                              , postal_dict = postal_dict
                              , city_dict = city_dict)

        if rslt == None:
            lat_lng.append([None, None])
            quality.append(None)
        elif rslt != None:
            lat_lng.append([rslt[0], rslt[1]])
            quality.append(rslt[2])

    data_frame.index = range(data_frame.shape[0])
    data_frame["lat"] = np.array(lat_lng)[:,0].tolist()
    data_frame["lng"] = np.array(lat_lng)[:,1].tolist()
    data_frame["CoordRes"] = quality

    return data_frame

eu_df = _lat_lng_add(eu_df)

# Remove any entries without lat/lng info
eu_df = eu_df[pd.notnull(eu_df["lat"])]
eu_df.index = range(eu_df.shape[0])

# Run an abstract analysis on the summaries
eu_df.summary = eu_df.summary.str.replace(r"\s\s+", " ").str.replace(r'[^0-9a-zA-Z\s]', "")

# Only interested in the keywords, for now
eu_df["Keywords"] = fdb_common_words(eu_df.summary)

# Merge Author Names
eu_df = eu_df[pd.notnull(eu_df["contactfirstnames"])]
eu_df["contactfirstnames"] = eu_df["contactfirstnames"].astype(str)
eu_df = eu_df[pd.notnull(eu_df["contactlastnames"])]
eu_df["contactlastnames"] = eu_df["contactlastnames"].astype(str)
eu_df.index = range(eu_df.shape[0])

# Create a Researcher Column
eu_df["Researcher"] = eu_df.contactfirstnames + " " + eu_df.contactlastnames

# Title the Columns
eu_df.city = eu_df.city.str.lower()
eu_df.city = eu_df.city.str.title()

# Correct the title the organisation.
eu_df.name = eu_df.name.map(lambda x: titler(x))

# Correct the title of the project.
eu_df.title = eu_df.title.str.replace("\"", "").str.replace("\'", "").map(lambda x: titler(x))

# Add Curency Column
eu_df["FundCurrency"] = "EUR"

# Add Funder Column
eu_df["Funder"] = "European Union"

# Add blcok
eu_df["OrganizationBlock"] = "Europe"

# Delete Columns
to_drop2 = ["street", "CoordRes", "summary", "contactfirstnames", "contactlastnames",
            "contacttype", "endofparticipation", "activitytype", "role", "shortname",
            "postcode", "contactemail", "contacttelephonenumber", "contactfaxnumber",
            "contactfunction", "file_name"]
eu_df = column_drop(eu_df, columns_to_drop = to_drop2)

# Rename Columns
new_col_names = [ "OrganizationName"
                , "Amount"
                , "OrganizationState"
                , "OrganizationCity"
                , "GrantYear"
                , "ProjectTitle"
                , "lat"
                , "lng"
                , "Keywords"
                , "Researcher"
                , "FundCurrency"
                , "Funder"
                , "OrganizationBlock"
]

# Rename Columns
eu_df.columns = new_col_names

# Order new Columns
eu_df = eu_df[order_cols]

# Save
# eu_df.to_pickle("EU_Science_with_GeoData_complete")

# EU Data Stabalized #


# ------------------------------------------------------------------------------------------------------------ #
#                                                    Australia                                                 #
# ------------------------------------------------------------------------------------------------------------ #


# ------------------------------------------------------------- #
# Australia's National Health and Medical Research Council Data #
# ------------------------------------------------------------- #



# COLLAPSING ACCROSS YEAR. THIS NEEDS TO BE REVERSED AS IT IS NOT CONSISTENT WITH THE OTHER DATASETS.



os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/Australia")

# import Aussie Data
aus_df = pd.read_excel("AUS_GRants_2000_2015.xlsx", sheetname = "2000 TO 2015 DATA")

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
to_drop = [  "application_year"
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
new_col_names = [  "Researcher"
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

ausf_df = pd.read_excel("ARC_NCGP_Projects_and_fellowships_completed_Nov2015.xlsx", sheetname = "Projects")
ausf_df.columns = [cln(str(i)).lstrip().rstrip() for i in ausf_df.columns.tolist()]

to_drop = [
      "Scheme Code"
    , "Submission Year"
    , "Summary/National Benefit"
    , "Primary FoR/RFCD"
    , "Primary FoR/RFCD Description"
] + year_columns(columns = aus_df.columns) #[str(i) for i in range(2002, 2016, 1)]
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
ausf_df = column_drop(ausf_df, na_drop, drop_type = "na")

# Clean researcher column
for to_replace in ['Prof ', 'Dr ', 'A/Pr ', 'A/Prof ' , 'Mr ', 'Ms ']:
    ausf_df['researcher'] = ausf_df['researcher'].map(lambda x: cln(x, 1)).str.replace(to_replace, '')

ausf_df['researcher'] = ausf_df['researcher'].str.replace("A/", '')

# Split
ausf_df['researcher'] =  ausf_df['researcher'].str.strip().map(lambda x: cln(x, 1).replace(";", ',')).str.title().str.split(";  ")

# Clean keywords
ausf_df['keywords'] = ausf_df['keywords'].str.lower().str.split("; ")

# Add City information
ausf_df["organisation_city"] = ""

# Try without 'The' in front
regex = r'({})'.format('|'.join(list(Australia_Inist_Cities.keys())))
ausf_df.organisation_city = ausf_df.organisation_name.str.extract(regex, expand = False).map(Australia_Inist_Cities)

# Manually account for CSIRO
ausf_df["organisation_city"][ausf_df["organisation_name"].astype(str).str.contains("CSIRO")] = "Canberra"

# ausf_df["organisation_name"][ausf_df["organisation_city"].isnull()].unique()
# Charles Sturt University is multi-campus and not enouch information is given in the dataset
# to determine which campus is being refered to. Thus, it will be excluded.

# Drop NaN Cities
ausf_df = ausf_df[pd.notnull(ausf_df["organisation_city"])]
ausf_df.index = range(ausf_df.shape[0])

# Add Curency Column
ausf_df["FundCurrency"] = pd.Series("AUD", index = ausf_df.index)

# Add Funder Column
ausf_df["Funder"] = pd.Series("ARC", index = ausf_df.index)

# Add blcok
ausf_df["OrganizationBlock"] = pd.Series("Australia", index = ausf_df.index)

# Make required columns
ausf_df["lng"] = pd.Series("", index = ausf_df.index)
ausf_df["lat"] = pd.Series("", index = ausf_df.index)

# lng dict
aus_uni_lng_dict = dict(zip(oc_unis.University.tolist(), oc_unis.lng.tolist()))
regex = r'({})'.format('|'.join(aus_uni_lng_dict.keys()))
ausf_df["lng"] = ausf_df.organisation_name.str.lower().str.extract(regex, expand = False).map(aus_uni_lng_dict)

# lat dict
aus_uni_lat_dict = dict(zip(oc_unis.University.tolist(), oc_unis.lat.tolist()))
regex = r'({})'.format('|'.join(aus_uni_lat_dict.keys()))
ausf_df["lat"] = ausf_df.organisation_name.str.lower().str.extract(regex, expand = False).map(aus_uni_lat_dict)

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
replacement_dict = {  "University of Technology, Sydney"  :  "University of Technology Sydney"
                    , "Victoria University of Technology" :  "Victoria University, Australia"
                    , "Victoria University"               :  "Victoria University, Australia"
                    , "Northern Territory University"     :  "Charles Darwin University"}

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
def specific_uni_fill(data_frame, uni, name_to_lookup = None):
    """

    :param data_frame:
    :param uni: in data frame
    :return: what to query OPENCAGE with/for
    """

    if name_to_lookup == None:
        name_to_lookup = uni

    ocage = ZeitOpenCage(api_key=OPENCAGE_KEY)
    sel = data_frame["organisation_name"] == uni
    data_frame.lng[sel], data_frame.lat[sel] = ocage.lookup(name_to_lookup, request = "geo")

    return data_frame

# Fill in via OpenCage
ausf_df = specific_uni_fill(ausf_df, uni = "Deakin University", name_to_lookup = "Deakin University, Australia")

# To be sure, drop any rows with missing lat information (should yeild no change)
ausf_df = column_drop(ausf_df, columns_to_drop = ["lat"], drop_type = "na")

# Rename Columns
new_col_names = [  "ProjectTitle"
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

# ------------------------------------------------------------------------------------------------------------ #
#                                                     Canada                                                   #
# ------------------------------------------------------------------------------------------------------------ #


# Will need to get geographic information from University
# University of Toronto was downloaded in two parts...Errors when attempting to download all grants at once.

os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/Canada/Funding_by_Region")

# Import
ca_data_file_names = list(set([i.replace("~$", "") for i in glob2.glob('*/*.xlsx')]))
ca_df = df_combine(ca_data_file_names, skip = 3, file_types = 'excel', file_name_add = True)

# Get State (Provience) and University Information
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

# Move to get Canadian Uni Info.
os.chdir(MAIN_FOLDER + "/Data/WikiPull/North_America")

# Import
can_uni_geo = pd.read_csv("NorthAmericaUnis.csv")
del can_uni_geo["Unnamed: 0"]

# Limit to canada
can_uni_geo = can_uni_geo[can_uni_geo.Country == "Canada"]
can_uni_geo.index = range(can_uni_geo.shape[0])

def remove_accents(input_str):
    """
    http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
    :param input_str:
    :return:
    """
    nkfd_form = unicodedata.normalize('NFKD', input_str)
    return ("".join([c for c in nkfd_form if not unicodedata.combining(c)]))

# Get lat - lng info
can_city_lat = dict(zip([remove_accents(k) for k in can_uni_geo.University.str.lower()]
                        , can_uni_geo.lat))
can_city_lng = dict(zip([remove_accents(k) for k in can_uni_geo.University.str.lower()]
                        , can_uni_geo.lng))

# Dertermine what Unis are missing
# missing_can_unis = list(set(ca_df.university.unique().tolist()) - set(can_city_dict.keys()))

def try_dict_lookup(input_dict, key):

    if key in input_dict.keys():
        return input_dict[key]
    if remove_accents(key) in input_dict.keys():
        return input_dict[remove_accents(key)]
    else:
        return np.NaN

# Populate with lat-lng information
ca_df['lng'] = ca_df.university.str.lower().map(lambda x: try_dict_lookup(can_city_lng, x))
ca_df['lat'] = ca_df.university.str.lower().map(lambda x: try_dict_lookup(can_city_lat, x))


# -------------------- #
# Add city information #
# -------------------- #


os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/Canada")

# Import
can_uni_cities = pd.read_excel("Canadian_Universities_WIki.xlsx")

# Limit to city
can_uni_cities.City = can_uni_cities.City.map(lambda x: x.split(",")[0])

# Create a dict (preferable time complexity).
missing_can_cities_dict = dict(zip(can_uni_cities.Name.str.lower(), can_uni_cities.City))

# Populate the city Column
ca_df['city'] = ca_df.university.str.lower().map(lambda x: try_dict_lookup(missing_can_cities_dict, x))

# Drop rows without geo information
ca_df = column_drop(ca_df, columns_to_drop = ["lat", "city"], drop_type = 'na')

# Correct Researcher Name
ca_df.researcher = ca_df.researcher.map(lambda x: comma_reverse(x))

# Use the title for keywords...not ideal, but it's the only option.
ca_df['keywords'] = fdb_common_words(ca_df.title, n = 3, update_after = 5000)

# Refactor index
ca_df.index = range(ca_df.shape[0])

# Add Curency Column
ca_df["FundCurrency"] = pd.Series("CAD", index = ca_df.index)

# Add Funder Column
ca_df["Funder"] = pd.Series("NSERC", index = ca_df.index)

# Add blcok
ca_df["OrganizationBlock"] = pd.Series("Canada", index = ca_df.index)

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
]

# Rename columns
ca_df.columns = new_col_names

# Reorder columns
ca_df = ca_df[order_cols]

# Canadian Data Stabalized #

# ------------------------------------------------------------------------- #
#               Integrate Funding Data from around the World                #
# ------------------------------------------------------------------------- #


os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding")

# Merge the dataframes
df = us_df.append([eu_df, aus_df, ca_df])
df.index = range(df.shape[0])

# Save

# WAY TOO MUCH MISSING DATA. Reduce Attrition.
df.to_csv("EU_US_CAD_AUD_Science_Funding_DB.csv", index_label = False)
df.to_pickle("EU_US_CAD_AUD_Science_Funding_DB")

df = pd.read_csv("EU_US_CAD_AUD_Science_Funding_DB.csv")
df.GrantYear = df.GrantYear.astype(float)
df.Amount = df.Amount.astype(str).map(lambda x: re.sub(r'[^0-9.]', "", x)).convert_objects(convert_numeric = True)


# ------------------------------------------------------------------------- #
#                                   Analysis                                #
# ------------------------------------------------------------------------- #

######## RESTRICT TO YEAR <= 2016 ########


# Add Inflation information #
os.chdir(MAIN_FOLDER + "/Data")

df.OrganizationState = df.OrganizationState.astype(str)
df.OrganizationBlock = df.OrganizationBlock.astype(str)
df.index = range(df.shape[0])


from new_money.money import Currency
curr = Currency()

#two_iso_country_dict
def country_namer(state, block, iso_country_dict):
    """

    :param state:
    :param block:
    :param iso_country_dict:
    :return:
    """

    if any([not isinstance(state, str), not isinstance(block, str)]):
        return np.NaN

    if block.lower().title() != "Europe":
        return block

    elif block.lower().title() == "Europe":
        try:
            return iso_country_dict[state.upper()]
        except:
            return np.NaN

def country_namer_series(state, block, iso_country_dict):
    """

    :param state:
    :param block:
    :param iso_country_dict:
    :return:
    """

    return [country_namer(i[0], i[1], iso_country_dict) for i in zip(state.tolist(), block.tolist())]

def norm_wrapper(amount, nation, year_a, year_b):
    """

    :param amount:
    :param nation:
    :param year_a:
    :param year_b:
    :return:
    """

    if float(year_a) > float(year_b):
        return amount

    normed = curr.currency_normalizer(amount, nation, year_a, year_b)

    if np.isnan(np.array(normed)):
        return np.NaN

    return normed

def norm_array(data_frame, amount_series, nation_series, year_a_series, year_b_series):
    """

    :param amount_series:
    :param nation_series:
    :param year_a_series:
    :param year_b_series:
    :return:
    """

    if isinstance(year_b_series, str):
        year_b = [year_b_series]*data_frame[nation_series].shape[0]
    else:
        year_b = data_frame[year_b_series].tolist()

    to_iter = zip(data_frame[amount_series].tolist(), data_frame[nation_series].tolist(),
                  data_frame[year_a_series].tolist(), year_b)

    return [norm_wrapper(i[0], i[1], i[2], i[3]) for i in to_iter]


df['Nation'] = country_namer_series(df.OrganizationState, df.OrganizationBlock, two_iso_country_dict)
df['RealAmount'] = norm_array(df, 'Amount', 'Nation', 'GrantYear', '2015')


# df.to_csv("temp2.csv",  index_label = False)

df.groupby('Nation')['RealAmount'].min().map(lambda x: round(x, 1))

grouped = df[(df.OrganizationName.astype(str).str.contains("Uni")) & (df.OrganizationBlock.astype(str) != "shdhd")].\
            groupby('OrganizationName', as_index = False)['RealAmount'].mean()
#
grouped.sort_values('RealAmount', ascending = False)

grouped.size().reset_index(name='OrganizationName')

# import wbpy
# # from pprint import pprint
#
# api = wbpy.IndicatorAPI()
#
# iso_country_codes = ["GB", "FR", "JP"]
# total_population = "SP.POP.TOTL"
#
# def
# dataset = api.get_dataset(total_population, iso_country_codes, date="2010:2012")


df[df.OrganizationName.astype(str).str.contains("Harvard")].Amount.max()




lprint(df[df.Nation == 'Germany'].Amount.tolist())


df[df.Nation == 'Canada'].GrantYear[0:3]
df[df.Nation == 'Canada'].Amount[0:3]
df[df.Nation == 'Canada'].RealAmount[0:3]



















































































































































