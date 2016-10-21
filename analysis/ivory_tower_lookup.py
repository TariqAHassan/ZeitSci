"""

    This Extracts Information about Universties from Wikipedia
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Python 3.5

    see :
        https://github.com/endSly/world-universities-csv
        https://en.wikipedia.org/wiki/List_of_colloquial_names_for_universities_and_colleges_in_the_United_States
        --> Kaggle Data

"""
# Import Modules
import os
import time
import numpy as np
import pandas as pd
import datetime
from supplementary_fns import cln
from supplementary_fns import lprint
from supplementary_fns import insen_replace
from supplementary_fns import partial_match
from supplementary_fns import pandas_col_shift
from supplementary_fns import partial_list_match
from supplementary_fns import items_present_test

# ZeitSci Classes
from zeitsci_wiki_api import WikiUniversities
from my_keys import OPENCAGE_KEY, MAIN_FOLDER

# ---------------------------------------------------------------- #
# Import Data   
# ---------------------------------------------------------------- #

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

# ---------------------------------------------------------------- #
# Correct/Add Country Col.  
# ---------------------------------------------------------------- #

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

# ---------------------------------------------------------------- #
# Clean cdb         
# ---------------------------------------------------------------- #

# Split into Country and Capital
cdb.CountryCapital = cdb.CountryCapital.apply(lambda i: [cln(j,1).lstrip().rstrip() for j in i.split("-")])

# Country alone
cdb["Country"] = cdb.CountryCapital.apply(lambda i: i[0])

# Capital alone
cdb["Capital"] = cdb.CountryCapital.apply(lambda i: i[1])

# ---------------------------------------------------------------- #
# Add Continent Information to wdb 
# ---------------------------------------------------------------- #

# Use of cdb
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

# ---------------------------------------------------------------- #
# Reorder and Add Columns                                             
# ---------------------------------------------------------------- #

# Reorder
pref_col_order = ["University", "Country", "Continent", "Website"]
wdb = wdb.reindex_axis(pref_col_order, axis = 1)

# Institution Properties
wdb['Endowment'] = ""
wdb['InstitutionType'] = ""
wdb['lng'] = ""
wdb['lat'] = ""
wdb['DataSource'] = ""

# ---------------------------------------------------------------- #
# Wikipedia Geoinformation                                          
# ---------------------------------------------------------------- #

# Create an instance of the WikiUniversities class
wikiuni = WikiUniversities(iso_currencies=iso_currencies)


def wiki_uni_extractor(df, save_to, file_name, start=0, continent=None, semi_complete=50, partial_saves=True, verbose=True):
    """

    Very messy code...but it works.

    :param df:
    :param save_to:
    :param file_name:
    :param start:
    :param continent:
    :param semi_complete:
    :param partial_saves:
    :return:
    """
    # Counter
    fail_count = list()

    # Limit by continent on request
    if isinstance(continent, str):
        df = df[df['Continent'].map(lambda x: continent in x)].reset_index(drop=True)

    for row in range(start, df.shape[0]):
        # Breaks
        if start != 0 and row % 500 == 0:
            if verbose: print("Breaking for 3 mins")
            time.sleep(60 * 3)  # break for 3 mins
            if verbose: print(datetime.datetime.now())
        if verbose: print("Processing Row", row, "of", df.shape[0], "| University:", df['University'][row])

        # Look up info on wikipedia
        try:
            lookup_rslt = None
            lookup_rslt = wikiuni.university_information(wiki_page_title=df['University'][row], region=df['Country'][row])

            # Check that processing is going as desired
            if lookup_rslt == None:
                if verbose: print("No data extracted for this row.")
                fail_count.append(1)
                if fail_count[-60:] == [1] * 90:
                    if verbose: print("Consistent Failure to extract data. Breaking...", "fail count: ", fail_count)
                    break

            # Add information to df
            if lookup_rslt != None:
                if len(fail_count) > 0: fail_count = list()

                df.loc[row, "Endowment"] = lookup_rslt["endowment"]
                df.loc[row, "InstitutionType"] = lookup_rslt["institution_type"]
                df.loc[row, "lng"] = lookup_rslt["lng"]
                df.loc[row, "lat"] = lookup_rslt["lat"]
                df.loc[row, "DataSource"] = "Wikipedia"
        except:
            pass

        # Save to disk every x rows
        if partial_saves and row != 0 and row % semi_complete == 0:
            if verbose: print(" ------------ Saving ------------ ")
            csv_name = save_to + "/" + file_name + str(time.time()).replace(".", "_") + ".csv"
            df.to_csv(csv_name, sep=",", index=False)

    return df

# Extract
file_name = "EuropeanUniversities"
directory = MAIN_FOLDER + "/Data/WikiPull/Europe/semi_complete"

# Run Extractor
final_db = wiki_uni_extractor(wdb, save_to=directory, start=550, file_name=file_name, continent='Europe')

# Save result
final_db.to_csv(directory +  "/" + file_name + "Complete.csv", sep = ",", index=False)













































































































































































































