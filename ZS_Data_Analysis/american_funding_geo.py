"""

    US Funding GIS
    ~~~~~~~~~~~~~~

    Python 3.5
        ...i.e., beware of starred expression.

"""

# ---------------- #
#  Import Modules  #
# ---------------- #
import os
import numpy as np
import pandas as pd
from abstract_analysis import *
from supplementary_fns import cln
from easymoney.easy_pandas import twoD_nested_dict

from funding_database_tools import MAIN_FOLDER


from funding_database_tools import wiki_pull_geo_parser
from funding_database_tools import partial_key_check
from funding_database_tools import remove_accents


# --------------------------------------------------------------------------------------- #
# Zip / Postal Code to Geo Location
# --------------------------------------------------------------------------------------- #

# Geocode by zipcode #

# Need to Process:
# - United States    D
# - Canada           D
# - South Korea      H
# - Europe (Italy)   D
# - United Kingdom   D
# - Australia        D
# - Chile            H
# - Bermuda          H
#
# H = Half Done
# D = Done

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

us_uni_geo = pd.read_csv(MAIN_FOLDER + "/Data/WikiPull/North_America/" + "NorthAmericaUniversitiesComplete.csv")
us_uni_geo = us_uni_geo[us_uni_geo['Country'] == "United States of America"]
us_uni_geo = us_uni_geo.dropna(subset=['lat', 'lng']).reset_index(drop=True)
us_uni_geo['lat_long'] = us_uni_geo.apply(lambda x: [round(x['lat'], 6), round(x['lng'], 6)], axis=1)

us_uni_geo_dict = dict(zip(us_uni_geo['University'].str.lower(), us_uni_geo['lat_long']))

# --------- Canada --------- #

can_uni_geo = pd.read_csv(MAIN_FOLDER + "/Data/WikiPull/North_America/" + "NorthAmericaUniversitiesComplete.csv")
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
korea_repub_uni_geo_dict = {"KOREA REP OF": {"korea university": [37.589167, 127.032222]}}

# --------- Europe --------- #

# Make this more robust -- use capability in euopean_union_funding.py

# Missing
# us_df[us_df['organization_country'].str.lower().str.contains("italy")]['organization_name'].unique()

eu_uni_geo_dict = wiki_pull_geo_parser(db_path=MAIN_FOLDER + "/Data/WikiPull/Europe/" + "EuropeUnivertiesComplete.csv")

# Manually add Universita Degli Studi di Trento to the Italy key
eu_uni_geo_dict['ITALY'] = {**eu_uni_geo_dict['ITALY'], **{'universita degli studi di trento': [46.069426, 11.121117]}}

# --------- United Kingdom --------- #

# us_df[us_df['organization_country'].str.lower().str.contains("united kingdom")]['organization_name'].unique()
# -- eu_uni_geo_dict should suffice


# --------- Australia --------- #

# us_df[us_df['organization_country'].str.lower().str.contains("australia")]['organization_name'].unique()
australia_uni_geo = wiki_pull_geo_parser(db_path=MAIN_FOLDER + "/Data/WikiPull/Oceania/" + "OceaniaUniversities.csv")

# --------- Chile --------- #

# Manually Account for this -- Make more robust.
# us_df[us_df['organization_country'].str.lower().str.contains("chile")]['organization_name'].unique()
chile_uni_geo = {"CHILE": {'pontificia universidad catolica de chile': [-33.4411, -70.6408]}}

# --------- Bermuda --------- #

# us_df[us_df['organization_country'].str.lower().str.contains("bermuda")]['organization_name'].unique()
bermuda_uni_geo = {"BERMUDA": {"bermuda institute of ocean sciences inc": [32.37, -64.69]}}

# ---------------------------------- Combine ---------------------------------- #

# print(us_df['organization_country'].unique().tolist())

uni_dict = {
    'UNITED STATES': us_uni_geo_dict,
    'CANADA': canada_uni_geo_dict,
    'KOREA REP OF': korea_repub_uni_geo_dict,
    'EUROPE': eu_uni_geo_dict,  # Italy & the United Kingdom
    'AUSTRALIA': australia_uni_geo,
    'CHILE': chile_uni_geo,
    'BERMUDA': bermuda_uni_geo
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


def master_geo_locator(zipcode, uni, country):
    first_try = us_geo_locator(zipcode)
    if str(first_try[0]) != 'nan':
        return first_try
    elif country.upper() in uni_dict:
        return uni_geo_locator(uni, country)
    else:
        return [np.NaN, np.NaN]

















