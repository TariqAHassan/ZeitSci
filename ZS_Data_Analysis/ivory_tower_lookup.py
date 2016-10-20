'''

    This Script Structures the Data Following Extraction from Wikipedia
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Python 3.5

see :
  https://github.com/endSly/world-universities-csv
  https://en.wikipedia.org/wiki/List_of_colloquial_names_for_universities_and_colleges_in_the_United_States
  Kaggle Data


'''

# ---------------- #
#  Import Modules  #
# ---------------- #

import os
import time
import numpy as np
import pandas as pd
import datetime
from fuzzywuzzy import fuzz    # needed?
from fuzzywuzzy import process
from supplementary_fns import cln
from supplementary_fns import lprint
from supplementary_fns import insen_replace
from supplementary_fns import partial_match
from supplementary_fns import pandas_col_shift
from supplementary_fns import partial_list_match
from supplementary_fns import items_present_test

# ZeitSci Classes
from zeitsci_wiki_api import WikiUniversities
# from open_cage_functwionality import ZeitOpenCage

# TO DO: Remove website col.

from my_keys import OPENCAGE_KEY
MAIN_FOLDER = "/Users/tariq/Google Drive/Programming Projects/ZeitSci/"

# Note: fuzzywuzzy needs python-levenshtein
#       -- faster...though wdb is ~45000 rows, so search will be slow no matter what.


# -------------------- #
#     Import Data      #
# -------------------- #

# Import country db
cdb = pd.read_csv(MAIN_FOLDER + "Data/" + "countries_by_continents.csv", encoding = "ISO-8859-1")

# Import the iso country name database
# see: https://en.wikipedia.org/wiki/ISO_3166-1#Current_codes
isodb = pd.read_csv(MAIN_FOLDER + "Data/" + "iso_country_codes.csv")

# Import world city info
wldc = pd.read_csv("worldcities.csv")
wldc = wldc.rename(columns = {wldc.columns[0] : "CountryCode", wldc.columns[6]: "City"})

# Import the university database
wdb = pd.read_csv(MAIN_FOLDER + "Data/" + "world_universities.csv", keep_default_na=False) # prevent NA --> nan

# Import currency codes
# see wiki: https://en.wikipedia.org/wiki/Template:Most_traded_currencies
iso_currencies = pd.read_csv(MAIN_FOLDER + "Data/" + "popular_ISO_currencies.csv")

# -------------------------- #
#  Correct/Add Country Col.  #
# -------------------------- #

# Use of isodb #

def alpha2_lookup(alpha):
    """

    :param alpha: ISO Alpha2 Country Code
    :return: Country Name
    """

    # Input check
    if not isinstance(alpha, str):
        try:
            alpha = str(alpha)
        except:
            return ""
            # raise ValueError("alpha must be a string")

    # Special Case
    if alpha.lower() == "an":
        return "Netherlands Antilles" # this Country has been disolved and removed from the ISO data.

    # Return Country
    try:
        return np.array(isodb["Country"][isodb.Alpha2Code.str.lower() == alpha.lower()])[0]
    except:
        return ""


# Deploy alpha2_lookup() on wdb's country col.
wdb.rename(columns = {'Country': 'CountryCode'}, inplace = True)
wdb["Country"] = ""
for ac in wdb.CountryCode.unique().tolist():
    wdb.ix[wdb.CountryCode == str(ac).upper(), 'Country'] = alpha2_lookup(str(ac).upper())

# Shift Country Column
wdb = pandas_col_shift(wdb, "Country")

# Deploy alpha2_lookup() on wldc's country col.
wldc["Country"] = ""
for ac in wldc.CountryCode.unique().tolist():
    wldc.ix[wldc.CountryCode == str(ac).upper(), 'Country'] = alpha2_lookup(ac)

# Shift Country Column
wldc = pandas_col_shift(wldc, "Country")


# -------------------------- #
#          Clean cdb         #
# -------------------------- #


# Split into Country and Capital
cdb.CountryCapital = cdb.CountryCapital.apply(lambda i: [cln(j,1).lstrip().rstrip() for j in i.split("-")])

# Country alone
cdb["Country"] = cdb.CountryCapital.apply(lambda i: i[0])

# Capital alone
cdb["Capital"] = cdb.CountryCapital.apply(lambda i: i[1])


# -------------------------------- #
# Add Continent Information to wdb #
# -------------------------------- #

# Use of cdb #

def continent_lookup(country):
    """

    :param country: any country in the world
    :return: the continent of a country
    """

    # Special Case; the USA has many names
    if country.lower().rstrip().lstrip() in ["united states of america", "united states", "america", "usa"]:
        return "North America"

    try:
        return np.array(cdb["Continent"][cln(cdb.Country.str.lower(), 1) == cln(country.lower(), 1)])[0]
    except:
        return ""


# Deploy continent_lookup ---> good, but not perfect
wdb["Continent"] = wdb.Country.apply(continent_lookup)

# Split by comma, for countries that are in more than one continent
wdb["Continent"] = wdb["Continent"].apply(lambda i: [cln(j, 1).lstrip().rstrip() for j in i.split(",")])

# -------------------------------- #
#           Clean up wdb           #
# -------------------------------- #

pref_col_order = ["University", "Country", "Continent", "Website"]

wdb = wdb.reindex_axis(pref_col_order, axis = 1)

# -------------------------------------------------------------------------------------------------------------------- #
#                                                        Restrict DB                                                   #
# -------------------------------------------------------------------------------------------------------------------- #


# # # Limit to North America for now
# allowed_continents = ["North America"]
# wdb = wdb[wdb.Continent.apply(items_present_test, args = [allowed_continents,])]
#
# # Further limit to a few Universties for now
# select_unis = [
#     "Harvard"
#     ,"University of Toronto"
#     ,"Dalhousie University"
#     ,"McGill University"
#     ,"Northwestern University"
#     ,"University of British Columbia"
#     ,"University of California, San Francisco"
# ]
#
# select_unis = [i.lower() for i in select_unis]
#
# # rewrite with fuzzywuzzy partial
# wdb = wdb[wdb.University.apply(partial_list_match, args = (select_unis,))]
# wdb.index = range(wdb.shape[0])

# --------------------------------------------------------------------------------------------- #

# Limit to North America
# wdb = wdb[wdb['Country'].apply(items_present_test, args = [allowed_continents,])].reset_index(drop=True)
# set([i for s in wdb['Continent'].tolist() for i in s])
wdb = wdb[wdb['Continent'].map(lambda x: 'Oceania' in x)].reset_index(drop=True)

# Move to Correct folder
os.chdir(MAIN_FOLDER + "/Data/WikiPull/Oceania/semi_complete")

# ---------------------------------------------------------------- #
#                                                                  #
#                     Geoinformation Extraction                    #
#                                                                  #
# ---------------------------------------------------------------- #


# Pass 1: Crawl wikipedia
# Pass 2: fill remaining log/lat holes with online API

# Construct needed columns #

# Institution Properties
wdb['Endowment'] = ""
wdb['InstitutionType'] = ""

# Geo Information
wdb['Address'] = ""  # will have to use reverse lookup for this

wdb['lng'] = ""
wdb['lat'] = ""
# These should be flipped...

wdb['DataSource'] = ""

file_name = "OceaniaUniversities"

# ---------------------------------------------------------------- #
#                    1.  Wikipedia Geoinformation                  #
# ---------------------------------------------------------------- #

# Create an instance of the class
wikiuni = WikiUniversities(iso_currencies=iso_currencies)

# Get the current dir
current_dir = os.getcwd()

start = 0
fail_count = []

for row in range(start, wdb.shape[0]):
    # Breaks
    if start != 0 and row % 500 == 0:
        print("Breaking for 3 mins")
        time.sleep(60*3)  # break for 3 mins
        print(datetime.datetime.now())

    # Update
    print("Processing Row", row, "of", wdb.shape[0], "| University:", wdb['University'][row])

    # Look up info on wikipedia
    # try:
    lookup_rslt = None
    lookup_rslt = wikiuni.university_information(wiki_page_title=wdb['University'][row], region=wdb['Country'][row])

    # Check that processing is going as desired
    if lookup_rslt == None:
        print("No data extracted for this row")
        fail_count.append(1)
        if fail_count[-60:] == [1]*90:
            print("Consistent Failure to extract data. Breaking...")
            print(fail_count)
            # break

    # Add information to wdb
    if lookup_rslt != None:
        if len(fail_count) > 0: fail_count = []

        wdb.loc[row, "Endowment"]       = lookup_rslt["endowment"]
        wdb.loc[row, "InstitutionType"] = lookup_rslt["institution_type"]
        wdb.loc[row, "lng"]             = lookup_rslt["lng"]
        wdb.loc[row, "lat"]             = lookup_rslt["lat"]
        wdb.loc[row, "DataSource"]      = "Wikipedia"

    # except:
    #     print("problem here:", row)

    # Save to disk every 100 rows
    if row != 0 and row % 50 == 0:
        print(" ------------ Saving ------------ ")
        csv_name = file_name + str(time.time()).replace(".", "_") + ".csv"
        wdb.to_csv(csv_name, sep = ",")
    if row == (wdb.shape[0]-1):
        wdb.to_csv(file_name+"_pcomplete_raw.csv", sep = ",")




















































































































































































































