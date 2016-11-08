"""

    Tools to Look for GIS Information Accross a Large number of Databases
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Python 3.5
        ...i.e., beware of starred expression.

"""
# Import Modules
import os
import numpy as np
import pandas as pd
from fuzzywuzzy import process
from abstract_analysis import *
from supplementary_fns import cln

from funding_database_tools import MAIN_FOLDER
from funding_database_tools import wiki_pull_geo_parser
from funding_database_tools import partial_key_check, fuzzy_key_match
from funding_database_tools import remove_accents

# --------------------------------------------------------------------------------------- #
# Zip / Postal Code to Geo Location
# --------------------------------------------------------------------------------------- #

# Geocode by zipcode #

# Need to Process:
# - United States    D
# - Canada           D
# - South Korea      P
# - Europe (Italy)   D
# - United Kingdom   D
# - Australia        D
# - Chile            P
# - Bermuda          P
#
# D = Done
# P = Partial

# --------- United States --------- #

# --- Zip --- #

# Get lng/lat from zip
os.chdir(MAIN_FOLDER + "/Data/ZipPostalCodes/USA")

# Get Zip code data from the 2016 US Census.
zipdb = pd.read_table("2016_Gaz_zcta_national.txt", dtype={'GEOID': 'str'})
zipdb.columns = [i.lower().strip() for i in zipdb.columns]
zipdb = zipdb[['geoid', 'intptlat', 'intptlong']]
zipdb['lat_long'] = zipdb.apply(lambda x: [round(x['intptlat'], 6), round(x['intptlong'], 6)], axis=1)

# Create a dictionary of US zipcodes
us_zipcode_geo_dict = dict(zip(zipdb['geoid'], zipdb['lat_long']))

# --- Unis --- #

us_uni_geo = pd.read_csv(MAIN_FOLDER + "/Data/WikiPull/North_America/UnitedStates/" + "UnitedStatesUniversitiesComplete.csv")
us_uni_geo = us_uni_geo[us_uni_geo['Country'] == "United States of America"]
us_uni_geo = us_uni_geo.dropna(subset=['lat', 'lng']).reset_index(drop=True)
us_uni_geo['lat_long'] = us_uni_geo.apply(lambda x: [round(x['lat'], 6), round(x['lng'], 6)], axis=1)

us_uni_geo_dict = dict(zip(us_uni_geo['University'].str.lower(), us_uni_geo['lat_long']))

# --------- Canada --------- #

can_uni_geo = pd.read_csv(MAIN_FOLDER + "/Data/WikiPull/North_America/Canada/" + "CanadianUniversitiesComplete.csv")
can_uni_geo = can_uni_geo[can_uni_geo['Country'] == "Canada"]
can_uni_geo = can_uni_geo.dropna(subset=['lat', 'lng']).reset_index(drop=True)
can_uni_geo['lat_long'] = can_uni_geo.apply(lambda x: [round(x['lat'], 6), round(x['lng'], 6)], axis=1)

# Get lat - lng info
canada_uni_geo_dict = dict(
    zip([remove_accents(k) for k in can_uni_geo['University'].str.lower()], can_uni_geo['lat_long']))

# --------- South Korea --------- #

# Should Come from a wiki pull in the future
# us_df[us_df['organization_country'].str.lower().str.contains("korea")]

# from https://en.wikipedia.org/wiki/Korea_University
korea_repub_uni_geo_dict = {"korea university": [37.589167, 127.032222]}

# --------- Europe --------- #

# Make this more robust -- use capability in euopean_union_funding.py

# Missing
# us_df[us_df['organization_country'].str.lower().str.contains("italy")]['organization_name'].unique()

eu_uni_geo_dict = wiki_pull_geo_parser(db_path=MAIN_FOLDER + "/Data/WikiPull/Europe/" + "EuropeanUniversitiesComplete.csv")

# Manually add Universita Degli Studi di Trento to the Italy key
eu_uni_geo_dict['ITALY'] = {**eu_uni_geo_dict['ITALY'], **{'universita degli studi di trento': [46.069426, 11.121117]}}

# --------- United Kingdom --------- #

# us_df[us_df['organization_country'].str.lower().str.contains("united kingdom")]['organization_name'].unique()
# -- eu_uni_geo_dict should suffice


# --------- Australia --------- #

# us_df[us_df['organization_country'].str.lower().str.contains("australia")]['organization_name'].unique()
australia_uni_geo_dict = wiki_pull_geo_parser(
    db_path=MAIN_FOLDER + "/Data/WikiPull/Oceania/" + "OceaniaUniversitiesComplete.csv")['AUSTRALIA']

# --------- Chile --------- #

# Manually Account for this -- Make more robust.
# us_df[us_df['organization_country'].str.lower().str.contains("chile")]['organization_name'].unique()
chile_uni_geo_dict = {'pontificia universidad catolica de chile': [-33.4411, -70.6408]}

# --------- Bermuda --------- #

# us_df[us_df['organization_country'].str.lower().str.contains("bermuda")]['organization_name'].unique()
bermuda_uni_geo_dict = {"bermuda institute of ocean sciences inc": [32.37, -64.69]}

# ---------------------------------- Combine ---------------------------------- #

# print(us_df['organization_country'].unique().tolist())

uni_dict = {
    'UNITED STATES': us_uni_geo_dict,
    'CANADA': canada_uni_geo_dict,
    'KOREA REP OF': korea_repub_uni_geo_dict,
    'EUROPE': eu_uni_geo_dict,                  # Italy & the United Kingdom
    'AUSTRALIA': australia_uni_geo_dict,
    'CHILE': chile_uni_geo_dict,
    'BERMUDA': bermuda_uni_geo_dict
}


def uni_geo_locator(uni, country):
    if str(uni) == 'nan' or str(country) == 'nan':
        return [np.NaN, np.NaN]

    cleaned_uni = cln(uni).strip().lower()
    lookup_dict = uni_dict[country.upper()]

    if cleaned_uni in lookup_dict:
        return lookup_dict[cleaned_uni]

    partial_key_attempt = partial_key_check(uni, lookup_dict)
    if str(partial_key_attempt) != 'nan':
        return lookup_dict[partial_key_attempt]
    else:
        return [np.NaN, np.NaN]


# For US entries, use their zipcode
def us_geo_locator(zipcode):
    if str(zipcode) == 'nan':
        return [np.NaN, np.NaN]
    if cln(zipcode, 2) in us_zipcode_geo_dict:
        return us_zipcode_geo_dict[cln(zipcode, 2)]
    else:
        return [np.NaN, np.NaN]


def master_geo_lookup(geos, zipcode, country, uni, u_id=0, quality_floor=85, update_after=1000):
    """

    This adds ~27, 000 lat/lngs for the EU Dataset.

    :param geos:
    :param zipcode:
    :param country:
    :param uni:
    :param u_id:
    :param quality_floor: match threshold for `fuzzywuzzy`.
    :param update_after:
    :return:
    """

    if u_id != 0 and u_id is not None and u_id % update_after == 0:
        print("row: ", u_id)

    if all(pd.notnull(i) for i in geos):
        return geos

    # Init
    d = dict()
    country_upper = country.upper()
    uni_lower = cln(uni).lower().strip()

    # Check US Postal Code
    if zipcode is not None:
        zipcode = cln(zipcode, 2)[:5]
        if country == 'United States' and str(zipcode) != 'nan' and zipcode in us_zipcode_geo_dict:
            return us_zipcode_geo_dict[zipcode]

    # Check by Uni
    country_l = [i for i in uni_dict.keys() if country_upper in i]
    if len(country_l) == 1:
        d = uni_dict[country_l[0]]
    elif country_upper in uni_dict['EUROPE']:
        d = uni_dict['EUROPE'][country_upper]

    if d != {}:
        if uni_lower in d:
            return d[uni_lower]

        partial_normal_forward = [i for i in d if uni_lower in i]
        if len(partial_normal_forward) == 1:
            return d[partial_normal_forward[0]]

        partial_normal_backward = [j for j in d if j in uni_lower]
        if len(partial_normal_backward) == 1:
            return d[partial_normal_backward[0]]

        partial_fuzzy = process.extractOne(uni_lower, list(d.keys()))
        if partial_fuzzy[1] >= quality_floor:
            return d[partial_fuzzy[0]]

    return [np.NaN, np.NaN]
















