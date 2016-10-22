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
from easymoney.money import EasyPeasy
from aggregated_geo_info import master_geo_lookup

from funding_database_tools import MAIN_FOLDER
from funding_database_tools import order_cols
from funding_database_tools import titler
from funding_database_tools import fdb_common_words
from funding_database_tools import df_combine
from funding_database_tools import column_drop
from funding_database_tools import string_match_list

ep = EasyPeasy()

# ------------------------------------------------------------------------------------------------------------ #
# European Union
# ------------------------------------------------------------------------------------------------------------ #


os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/EU")


# 1998-2002 dataset has been excluded because only project
# funding information is provided -- individual uni. grants are not.
# Thus, this project includes data from 2002 - 2016.

# Get file names
eu_data_file_names = list(set([i.replace("~$", "") for i in glob2.glob('**/*.xlsx')]))
eu_data_file_names.sort(key=lambda x: x.split("-")[0])

# Read in Project Data (2002-2006, 2007-2013, 2014-2020)
eu_dfp = df_combine(string_match_list(eu_data_file_names, "proj"), file_name_add=True)
eu_dfp.file_name = eu_dfp.file_name.str.split("/").str.get(0)

# Convert ECmaxcontribution to float
eu_dfp['ecmaxcontribution'] = eu_dfp['ecmaxcontribution'].astype(str).map(lambda x: re.sub("[^0-9]", "", x))
eu_dfp['ecmaxcontribution'] = eu_dfp['ecmaxcontribution'].map(lambda x: [np.NaN if x.strip() == "" else x.strip()][0]).astype(float)

# Read in Org. Data (2002-2006, 2007-2013, 2014-2020)
eu_dfo = df_combine(string_match_list(eu_data_file_names, "organ"), file_name_add=True)
eu_dfo.file_name = eu_dfo.file_name.str.split("/").str.get(0)

# Get Grant Year and Project Summary from EU_Funding_Projects
eu_dfo["start_date"] =  pd.Series("", index=eu_dfo.index)
eu_dfo["summary"]    =  pd.Series("", index=eu_dfo.index)
eu_dfo["title"]      =  pd.Series("", index=eu_dfo.index)

def proj_to_org_extractor(project_data_frame, organization_data_frame):
    """

    :param project_data_frame:
    :param organization_data_frame:
    :return:
    """
    c = 0 # ugly counter variable...
    # Faster solutions are possible but this naive approach leaves little room for error.
    unique_rnc = organization_data_frame['projectrcn'].unique()
    for r in unique_rnc:
        c += 1
        if c % 1000 == 0: print(round((float(c)/len(organization_data_frame['projectrcn'].unique()))*100, 2), "%")

        df_slice = project_data_frame[project_data_frame.rcn == r]
        indices = organization_data_frame[organization_data_frame['projectrcn'] == r].index
        for i in indices:
            organization_data_frame.set_value(i, 'summary', df_slice["objective"].iloc[0])
            organization_data_frame.set_value(i, 'start_date', df_slice["startdate"].iloc[0])
            organization_data_frame.set_value(i, 'title', df_slice["title"].iloc[0])

            # for 2002-2006, the ECcontribution was in the projects file...
            if "2002-2006" in set(df_slice.file_name.tolist()):
                organization_data_frame.set_value(i, 'eccontribution', df_slice["ecmaxcontribution"].iloc[0])

    return organization_data_frame

# Rename org.df to EU df.
eu_df = proj_to_org_extractor(project_data_frame=eu_dfp, organization_data_frame=eu_dfo)

# Start tqdm
tqdm.pandas(desc="status")

# Add grant_year
eu_df['grant_year'] = eu_df['start_date'].map(lambda x: x.year)

# Reformat start_date as MM/DD/YYYY
eu_df['start_date'] = eu_df['start_date'].map(lambda x: str(x.month) + "/" + str(x.day) + "/" + str(x.year))

# Limit to the current year
eu_df = eu_df[eu_df['grant_year'].astype(float) <= datetime.datetime.now().year]

# Remove rows without either city or postal code information
eu_df = eu_df[(~eu_df.city.astype(str).isin(["nan", "NaN"])) | (~eu_df.postcode.astype(str).isin(["nan", "NaN"]))]

# Drop row if NA for certian columns
# eccontribution = European Commission Contribution
eu_df = column_drop(eu_df, columns_to_drop=["eccontribution", "country"], drop_type="na")

# Drop Unneeded Columns
to_drop = ["organizationurl"
           , "id"
           , "projectrcn"
           , "projectacronym"
           , "projectreference"
           , "contacttitle"]
eu_df = column_drop(eu_df, columns_to_drop=to_drop)

# ------------------------------------------------------------------#
# Import EU GeoLocation Data
# ------------------------------------------------------------------#

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
eu_cloc['city'] = eu_cloc.city.str.upper()
city_dict = eu_cloc.groupby('iso').apply(lambda x: x.set_index('city')['zipped'].to_dict()).to_dict()

def eu_loc_lookup(city, postal_code, alpha2country, postal_dict, city_dict):
    """

    :param city:
    :param postal_code:
    :param alpha2country:
    :return: lat, lng
    """
    value = None

    try:
        city = cln(city, 1).strip().upper()
        postal_code = cln(str(postal_code), 1).strip().upper()
        alpha2country = cln(str(alpha2country), 2)

        # Restrict to the given country #
        postal_dict = postal_dict[alpha2country.upper()]
    except:
        return None

    # Try Postal Code #

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
    try:
        return city_dict[alpha2country.upper()][city][0], city_dict[alpha2country.upper()][city][1], "city"
    except:
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

        if i % 25000 == 0: print(" -------- Lat/Long: %s of %s -------- " % (i, str(nrow)))

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

# ------------------------------------------------------------------#
# Expand Country Names to Full from Alpha2 Codes
# ------------------------------------------------------------------#

# Correct Alpha2 Codes in the country column

# Get Data from the EasyMoney module
em_options = ep.options('all', pretty_print=False).dropna(subset=['Region', 'Alpha2'])
easymoney_alpha2_dict = dict(zip(em_options['Alpha2'], em_options['Region']))

# Get Data from the pycountry module
pycountry_alpha2_dict = {i.alpha2: i.name for i in pycountry.countries}

# Special Cases found in the dataset
eu_country_special_dict = {'AN': 'Netherlands Antilles', 'CS': 'Serbia and Montenegro',
                           'EL': 'United Kingdom','UK': 'United Kingdom', 'YU': 'Yugoslavia'}

# Merge the above Dictionaries (I believe this requires python >= 3.5).
merged_alpha2_dict = {**pycountry_alpha2_dict, **easymoney_alpha2_dict, **eu_country_special_dict}

eu_df['country'] = eu_df['country'].map(lambda x: merged_alpha2_dict.get(x.upper(), np.NaN), na_action='ignore')

# ------------------------------------------------------------------#
# Try american_funding_geo.py for GIS
# ------------------------------------------------------------------#

# Consider rows with missing lat/lng data

# Check lat and lng are paired
len(eu_df[(pd.notnull(eu_df['lat'])) & ~(pd.notnull(eu_df['lng']))]) == 0

# Clean needed str columns
for c in ['shortname', 'name', 'postcode']:
    eu_df[c] = eu_df[c].astype(str).str.strip()

eu_df['name'] = eu_df['name'].str.lower().str.title().str.replace(",", "").str.strip()
eu_df['shortname'] = eu_df['shortname'].str.lower().str.title()

# a = eu_df[pd.isnull(eu_df['lat'])].groupby('country').apply(lambda x: list(set(x['name'].tolist())))['United States']

# Add temp marker
eu_df['u_id'] = range(eu_df.shape[0])

lat_lngs2 = eu_df.apply(lambda x: master_geo_lookup(geos=[x['lat'], x['lng']],
                                                    zipcode=x['postcode'],
                                                    country=x['country'],
                                                    u_id=x['u_id'],
                                                    uni=x['name']), axis=1)

# Put Back in lat/lng columns
lat_lngs_np = np.array(lat_lngs2.tolist())
eu_df['lat'] = lat_lngs_np[:,0]
eu_df['lng'] = lat_lngs_np[:,1]

# Delete marker
del eu_df['u_id']

# ------------------------------------------------------------------#
# Clean
# ------------------------------------------------------------------#

# Remove any entries without lat/lng info
eu_df = eu_df[pd.notnull(eu_df["lat"])].reset_index(drop=True)

# Run an abstract analysis on the summaries
eu_df.summary = eu_df['summary'].str.replace(r"\s\s+", " ").str.replace(r'[^0-9a-zA-Z\s]', "")

# Only interested in the keywords, for now
eu_df["Keywords"] = fdb_common_words(summary_series=eu_df['summary'], update_after=1000)

# Merge Author Names
eu_df["contactfirstnames"] = eu_df["contactfirstnames"].astype(str)
eu_df["contactlastnames"] = eu_df["contactlastnames"].astype(str)
eu_df.index = range(eu_df.shape[0])

def researcher(first, last):
    if str(first) != 'nan' and str(last) != 'nan':
        return first.strip() + " " + last.strip()
    elif str(last).strip() != 'nan':
        return last.strip()
    else:
        return np.NaN

# Create a Researcher Column
eu_df["Researcher"] = eu_df.apply(lambda x: researcher(x['contactfirstnames'], x['contactlastnames']), axis = 1)

# Title the Columns
eu_df['city'] = eu_df['city'].str.lower().str.title()

# Correct the title the organisation.
eu_df['name'] = eu_df['name'].map(lambda x: titler(x))

# Correct the title of the project.
eu_df['title'] = eu_df['title'].str.replace("\"", "").str.replace("\'", "").map(lambda x: titler(x))

# Add Curency Column
eu_df["FundCurrency"] = "EUR"

# Add Funder Column
eu_df["Funder"] = "European Commission"

# Add block
eu_df["OrganizationBlock"] = "Europe"

# Delete Columns
to_drop2 = ["street", "CoordRes", "summary", "contactfirstnames", "contactlastnames",
            "contacttype", "endofparticipation", "activitytype", "role", "shortname",
            "postcode", "contactemail", "contacttelephonenumber", "contactfaxnumber",
            "contactfunction", "file_name"]
eu_df = column_drop(eu_df, columns_to_drop=to_drop2)

# Rename Columns
new_col_names = [ "OrganizationName"
                , "Amount"
                , "OrganizationState"
                , "OrganizationCity"
                , "StartDate"
                , "ProjectTitle"
                , "GrantYear"
                , "lat"
                , "lng"
                , "Keywords"
                , "Researcher"
                , "FundCurrency"
                , "Funder"
                , "OrganizationBlock"]

# Rename Columns
eu_df.columns = new_col_names

# Convert GrantYear and Amount to Floats
eu_df['GrantYear'] = eu_df['GrantYear'].astype(float)
eu_df['Amount'] = eu_df['Amount'].astype(float)

# Order new Columns
eu_df = eu_df[order_cols]

# EU Data Stabilized #

# Save
eu_df.to_pickle(MAIN_FOLDER + "/Data/Governmental_Science_Funding/CompleteRegionDatabases/" + "EuropeanUnionFundingDatabase.p")





















































