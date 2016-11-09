"""

    EU Funding
    ~~~~~~~~~~

    Python 3.5
        ...contains starred expression

"""
# Import Modules
import os
import glob2
import datetime
import pycountry
import numpy as np
import pandas as pd
from tqdm import tqdm
from fuzzywuzzy import process
from abstract_analysis import *
from supplementary_fns import cln
from supplementary_fns import multi_replace
from easymoney.money import EasyPeasy
from aggregated_geo_info import master_geo_lookup

from funding_database_tools import MAIN_FOLDER
from funding_database_tools import order_cols
from funding_database_tools import titler
from funding_database_tools import col_cln
from funding_database_tools import fdb_common_words
from funding_database_tools import df_combine
from funding_database_tools import column_drop
from funding_database_tools import first_name_clean
from funding_database_tools import string_match_list

ep = EasyPeasy()

# Data Pipline Checklist:
#     Researcher                    X - (o) contactfirstnames + contactlastnames
#     Funder                        X - OK
#     StartDate                     X - (p) startdate
#     GrantYear                     X - (p) call
#     Amount                        X - (p) ecmaxcontribution
#     FundCurrency                  X - OK
#     ProjectTitle                  X - (p) title
#     FunderBlock                   X - OK
#     OrganizationName              X - (p) coordinator
#     OrganizationCity              X - (o) city
#     OrganizationState             X - (p) coordinatorcountry
#     OrganizationBlock             X - OK
#     lat                           X
#     lng                           X
#     Keywords                      X - (p) objectives


# Legend:
#     X = Complete
#     V = Currently Void
#     P = Partially Stabalized
#     o = EC organization files
#     p = EC program files
#     OK = Generated manually

# Start tqdm
tqdm.pandas(desc="status")

from easymoney.easy_pandas import pandas_print_full

# ------------------------------------------------------------------------------------------------------------ #
# European Union
# ------------------------------------------------------------------------------------------------------------ #

os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/EU")

# 1998-2002 dataset has been excluded because only project
# funding information is provided -- individual institution grants are not.
# Thus, this project includes data from 2002 onward.

# Get file names
eu_data_file_names = list(set([i.replace("~$", "") for i in glob2.glob('**/*.xlsx')]))
eu_data_file_names.sort(key=lambda x: x.split("-")[0])

# -------------------------------------------------------
# Read in Project Data (2002-2006, 2007-2013, 2014-2020)
# -------------------------------------------------------
eu_dfp = df_combine(string_match_list(eu_data_file_names, "proj"), file_name_add=True)
eu_dfp.file_name = eu_dfp.file_name.str.split("/").str.get(0)

# Clean the columns
eu_dfp = col_cln(eu_dfp)

# Remove Project duplicates
eu_dfp = eu_dfp.drop_duplicates(subset=['rcn', 'reference'])

# Convert ECmaxcontribution to float
eu_dfp['ecmaxcontribution'] = eu_dfp['ecmaxcontribution'].astype(str).map(lambda x: cln(re.sub("[^0-9.]", "", x), 2))
eu_dfp['ecmaxcontribution'] = eu_dfp['ecmaxcontribution'].progress_map(lambda x: np.NaN if x.strip() == "" else x).astype(float)

# Drop unneed columns
eu_dfp = eu_dfp.drop(['acronym',
                      'status',
                      'programme',
                      'topics',
                      'frameworkprogramme',
                      'enddate',
                      'projecturl',
                      'totalcost',
                      'fundingscheme',
                      'participants',
                      'participantcountries',
                      'subjects'], axis=1)

# -------------------------------------------------------
# Read in Org. Data (2002-2006, 2007-2013, 2014-2020)
# -------------------------------------------------------

eu_dfo = df_combine(string_match_list(eu_data_file_names, "organ"), file_name_add=True)
eu_dfo['file_name'] = eu_dfo['file_name'].str.split("/").str.get(0)

# Clean the columns
eu_dfo = col_cln(eu_dfo)

# eu_dfo = eu_dfo[~eu_dfo['role'].str.lower().isin(['participant', 'beneficiary'])].reset_index(drop=True)

# Process Researcher
def researcher(first, last):
    if str(last) != 'nan':
        last_name = " ".join([i.lower().title() if i.isupper() else i for i in last.split()]).strip()
        if str(first) != 'nan':
            return (first.strip() + " " + last_name).strip()
        else:
            return last_name.strip()
    else:
        return np.NaN

eu_dfo['contactfirstnames'] = eu_dfo['contactfirstnames'].progress_map(first_name_clean)
eu_dfo['Researcher'] = eu_dfo.progress_apply(lambda x: researcher(x['contactfirstnames'], x['contactlastnames']), axis=1)
del eu_dfo['contactfirstnames']
del eu_dfo['contactlastnames']

# -------------------------------------------------------
# Pull Select eu_dfo Infoformation into eu_dfp
# -------------------------------------------------------

# From Org: Researcher, City, Postal Code
org_coordinator = eu_dfo[eu_dfo['role'] == 'coordinator']

# Upper names for matching
org_coordinator['name'] = org_coordinator['name'].str.upper()
eu_dfp['coordinator'] = eu_dfp['coordinator'].str.upper()

# Zip select eu_dfo information
select_org_info = zip(*[org_coordinator[i] for i in ['projectrcn', 'name', 'city', 'postcode', 'Researcher']])

# Convert eu_dfo infoformation into a dict
org_dict = {(project, name): [c, p, r] for project, name, c, p, r in select_org_info}

def org_extractor(x):
    """
    Wrapper Function for org_dict.

    :param x: row with 'rcn' and 'coordinator'.
    :return: [City, Postal Code, Researcher]
    """
    return org_dict.get((x['rcn'], x['coordinator']), [np.NaN]*3)

# Look up coordinator in Org
org_info = eu_dfp.progress_apply(org_extractor, axis=1)

# Add Researcher Info
eu_dfp['city'] = [c[0] for c in org_info]

# Add Researcher Info
eu_dfp['postcode'] = [p[1] for p in org_info]

# Add Researcher Info
eu_dfp['Researcher'] = [r[2] for r in org_info]

# Remove the 'rcn' and 'reference' columns
eu_dfp = eu_dfp.drop(['rcn', 'reference'], axis=1)

# ------------------------------------------------------------------
# Correct Date Information
# ------------------------------------------------------------------

def call_year_extract(c, ignore="H2020"):
    """

    Use a statemachine-esk approach to harvest the year

    :param c:
    :return:
    """
    year = ""
    for l in c.replace(ignore, ""):
        if l.isdigit() and len(year) < 4:
            year += l
        elif not l.isdigit() and len(year) < 4:
            year = ""
            
    return year if len(year) == 4 else np.NaN

eu_dfp['grant_year'] = eu_dfp['call'].map(call_year_extract, na_action='ignore')

# Drop call
eu_dfp = eu_dfp.drop(['call'], axis=1)

# Reformat startdate as MM/DD/YYYY
eu_dfp['startdate'] = pd.to_datetime(eu_dfp['startdate']).map(lambda x: "/".join(map(str, [x.month, x.day, x.year])))

# ------------------------------------------------------------------
# Define eu_df
# ------------------------------------------------------------------

# Drop row if NaN for certian columns
# ecmaxcontribution = European Commission Contribution
eu_dfp = eu_dfp.rename(columns={"coordinatorcountry":"country"})
eu_df = column_drop(eu_dfp, columns_to_drop=["ecmaxcontribution"], drop_type="na")

# ------------------------------------------------------------------
# Import EU GeoLocation Data
# ------------------------------------------------------------------

eu_ploc = pd.read_csv("../european_postcodes_us_standard.csv")
eu_cloc = pd.read_csv("../european_cities_us_standard.csv")

# Rename their Columns
eu_ploc.columns = ["postal", "iso", "lat", "lng"]
eu_cloc.columns = ["city",   "iso", "lat", "lng"]

# Perform needed transformations to dtype str
eu_ploc["postal"] = eu_ploc["postal"].astype(str).str.strip()
eu_cloc["city"] = eu_cloc["city"].astype(str).str.strip()

# Use a dict for geo-info look up; O(1).
# See: http://stackoverflow.com/questions/38307855/nested-dictionary-from-pandas-data-frame/38309528#38309528

# Postal dict
eu_ploc["zipped"] = list(zip(eu_ploc.lat, eu_ploc.lng))
postal_dict = eu_ploc.groupby('iso').apply(lambda x: x.set_index('postal')['zipped'].to_dict()).to_dict()

# Postal dict with ISO country code
eu_ploc["zip_and_iso"] = eu_ploc['postal'] + " " + eu_ploc['iso']
postal_and_iso_dict = eu_ploc.groupby('iso').apply(lambda x: x.set_index('zip_and_iso')['zipped'].to_dict()).to_dict()

# City Dict
eu_cloc["zipped"] = list(zip(eu_cloc.lat, eu_cloc.lng))
eu_cloc['city'] = eu_cloc['city'].str.upper()
city_dict = eu_cloc.groupby('iso').apply(lambda x: x.set_index('city')['zipped'].to_dict()).to_dict()

def eu_loc_lookup(city, postal_code, alpha2country, postal_dict, city_dict):
    """

    :param city:
    :param postal_code:
    :param alpha2country:
    :return: lat, lng
    """
    # Init
    value = None

    if all(pd.isnull(i) for i in [city, postal_code]):
        return None

    try:
        city = cln(city, 1).strip().upper()
        postal_code = cln(str(postal_code), 1).strip().upper()
        alpha2country = cln(str(alpha2country), 2)

        # Restrict to the given country #
        postal_dict = postal_dict[alpha2country.upper()]
    except:
        return None

    # Try Postal Code #
    if pd.notnull(postal_code):
        # Try as is
        if postal_code in postal_dict.keys():
            value = postal_dict[postal_code]
            return value[0], value[1], "postal"

        # Try Clearing the space
        if cln(postal_code, 2) in postal_dict.keys():
            value = postal_dict[cln(postal_code, 2)]
            return value[0], value[1], "postal"

        # Try Zip + " " + ISO Country Code
        if cln(postal_code, 1).strip() in postal_and_iso_dict.keys():
            value = postal_and_iso_dict[cln(postal_code, 1).strip()]
            return value[0], value[1], "postal"

        # Try splitting on " "
        if postal_code.count(" ") == 1 and postal_code.split(" ")[0] in postal_dict.keys():
            if list(postal_dict.keys()).count(postal_code.split(" ")[0]) == 1:
                value = postal_dict[postal_code.split(" ")[0]]
                return value[0], value[1], "postal"

        # Try splitting on "-"
        if postal_code.count("-") == 1 and postal_code.split("-")[0] in postal_dict.keys():
            if list(postal_dict.keys()).count(postal_code.split("-")[0]) == 1:
                value = postal_dict[postal_code.split("-")[0]]
                return value[0], value[1], "postal"

    # Try City #
    if pd.notnull(city):
        try:
            return city_dict[alpha2country.upper()][city][0], city_dict[alpha2country.upper()][city][1], "city"
        except:
            return None
    else:
        return None # give up

def lat_lng_add(data_frame):
    """

    :param data_frame:
    :return:
    """
    lat_lng = list()
    quality = list()
    nrow = data_frame.shape[0]
    for i in range(0, nrow):

        if i % 5000 == 0: print(" -------- Lat/Long: %s of %s -------- " % (i, str(nrow)))

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

eu_df = lat_lng_add(eu_df)

# ------------------------------------------------------------------
# Expand Country Names to Full from Alpha2 Codes
# ------------------------------------------------------------------

# Correct Alpha2 Codes in the country column

# Get Data from the EasyMoney module
em_options = ep.options('all', pretty_print=False).dropna(subset=['Region', 'Alpha2'])
easymoney_alpha2_dict = dict(zip(em_options['Alpha2'], em_options['Region']))

# Get Data from the pycountry module
pycountry_alpha2_dict = {i.alpha2: i.name for i in pycountry.countries}

# Special Cases found in the dataset
eu_country_special_dict = {'AN': 'Netherlands Antilles', 'CS': 'Serbia and Montenegro',
                           'EL': 'United Kingdom','UK': 'United Kingdom', 'YU': 'Yugoslavia'}

# Merge the above Dictionaries (this technique requires python > 3.4).
merged_alpha2_dict = {**pycountry_alpha2_dict, **easymoney_alpha2_dict, **eu_country_special_dict}

eu_df['country'] = eu_df['country'].map(lambda x: merged_alpha2_dict.get(x.upper(), np.NaN), na_action='ignore')

# ------------------------------------------------------------------#
# Try american_funding_geo.py for GIS
# ------------------------------------------------------------------#

# Consider rows with missing lat/lng data

# Check lat and lng are paired
len(eu_df[(pd.notnull(eu_df['lat'])) & ~(pd.notnull(eu_df['lng']))]) == 0

# Clean up the coordinator column
eu_df['coordinator'] = eu_df['coordinator'].map(
    lambda x: " ".join([i.lower().title() if "." not in i else i for i in x.split()])
)

# a = eu_df[pd.isnull(eu_df['lat'])].groupby('country').apply(lambda x: list(set(x['name'].tolist())))['United States']

eu_df['u_id'] = range(eu_df.shape[0])
lat_lngs2 = eu_df.apply(lambda x: master_geo_lookup(geos=[x['lat'], x['lng']],
                                                    zipcode=x['postcode'],
                                                    country=x['country'],
                                                    u_id=x['u_id'],
                                                    uni=x['coordinator']), axis=1)

# Delete marker
del eu_df['u_id']

# Put Back in lat/lng columns
lat_lngs_np = np.array(lat_lngs2.tolist())
eu_df['lat'] = lat_lngs_np[:,0]
eu_df['lng'] = lat_lngs_np[:,1]

# ------------------------------------------------------------------
# Clean City
# ------------------------------------------------------------------

city_info_remove = ["NO - 5020"]
eu_df['city'] = eu_df['city'].map(
    lambda x: "".join([c for c in multi_replace(x, city_info_remove) if not c.isdigit()]).strip(), na_action='ignore'
)

# ------------------------------------------------------------------
# Keywords
# ------------------------------------------------------------------

# Run an abstract analysis on the summaries
eu_df['objective'] = eu_df['objective'].str.replace(r"\s\s+", " ").str.replace(r'[^0-9a-zA-Z\s]', "").str.strip()

# Harvest Keywords
eu_df["Keywords"] = fdb_common_words(summary_series=eu_df['objective'], update_after=1000)

# ------------------------------------------------------------------
# Additional String Cleaning
# ------------------------------------------------------------------

# Title the Columns
eu_df['city'] = eu_df['city'].progress_map(titler)

# Correct the title of the project.
eu_df['title'] = eu_df['title'].str.replace("\"", "").str.replace("\'", "").progress_map(lambda x: titler(x))

# ------------------------------------------------------------------
# Add Required Columns
# ------------------------------------------------------------------

# Add Curency Column
eu_df["FundCurrency"] = "EUR"

# Add Funder Column
eu_df["Funder"] = "European Commission"

# Add block
eu_df['OrganizationState'] = np.NaN
eu_df["FunderBlock"] = "Europe"

# Delete Columns
eu_df = eu_df.drop(['file_name', 'postcode', 'CoordRes', 'objective'], axis=1)


# Rename Columns
new_col_names = ["ProjectTitle"
                 , "StartDate"
                 , "Amount"
                 , "OrganizationName"
                 , "OrganizationBlock"
                 , "OrganizationCity"
                 , "Researcher"
                 , "GrantYear"
                 , "lat"
                 , "lng"
                 , "Keywords"
                 , "FundCurrency"
                 , "Funder"
                 , "OrganizationState"
                 , "FunderBlock"]

# Rename Columns
eu_df.columns = new_col_names

# Convert GrantYear and Amount to Floats
for c in ['Amount', 'GrantYear']:
    eu_df[c] = eu_df[c].astype(float)

# Order new Columns
eu_df = eu_df[order_cols]

# EU Data Stabilized #

# Save
eu_df.to_pickle(MAIN_FOLDER + "/Data/Governmental_Science_Funding/CompleteRegionDatabases/" + "EuropeanUnionFundingDatabase.p")

















































