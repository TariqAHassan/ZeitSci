"""

    Tools for Manipulating the Databases for Graphing
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# Imports
import re
import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from pprint import pprint
from copy import deepcopy
from statistics import mean
from haversine import haversine
from supplementary_fns import cln
from itertools import combinations, permutations
from funding_database_tools import MAIN_FOLDER
from graphs.graphing_tools import money_printer, org_group

# To Do:
# - add year-by-year funding info for each org -- make proportional to all the money moving around that year.
# - remove funders from OrgName column.

# ------------------------------------------------------------------------------------------------ #
# Read in Data
# ------------------------------------------------------------------------------------------------ #

funding = pd.read_pickle(MAIN_FOLDER + "/Data/MasterDatabase/" + 'MasterDatabaseRC3.p')
tqdm.pandas(desc="status")

# ------------------------------------------------------------------------------------------------ #
# Add Funder Information
# ------------------------------------------------------------------------------------------------ #

funders_dict = {
       'DOD_CDMRP'      : ['US Department of Defence (DOD)',                                      [38.870833, -77.055833]]
     , 'DOD_CNRM'       : ['US Department of Defence (DOD)',                                      [38.870833, -77.055833]]
     , 'DoD_CDMRP'      : ['US Department of Defence (DOD)',                                      [38.870833, -77.055833]]
     , 'DoD_CNRM'       : ['US Department of Defence (DOD)',                                      [38.870833, -77.055833]]
     , 'European Union' : ['European Commission (EC)',                                            [50.843611, 4.382777]]
     , 'HHS_ACF'        : ['US Administration for Children & Families (ARS)',                     [38.886666, -77.014444]]
     , 'HHS_CDC'        : ['US Centers for Disease Control and Prevention (CDC)',                 [33.798817, -84.325598]]
     , 'HHS_FDA'        : ['US Food and Drug Administration (FDA)',                               [39.03556, -76.98271]]
     , 'HHS_NIDILRR'    : ['US National Institute on Disability, Independent Living, and Rehabilitation Research (NIDILRR)',
                                                                                                  [38.885939, -77.016469]]
     , 'HHS_NIH'        : ['US National Institutes of Health (NIH)',                              [39.000443, -77.102394]]
     , 'NASA'           : ['US National Aeronautics and Space Administration (NASA)',             [38.883, -77.0163]]
     , 'NSERC'          : ['Natural Sciences and Engineering Research Council of Canada (NSERC)', [45.418267, -75.703119]]
     , 'NSF'            : ['US National Science Foundation (NSF)',                                [38.88054, -77.110962]]
     , 'USDA_ARS'       : ['US Department of Agriculture: Agricultural Research Service (ARS)',   [38.886767, -77.030001]]
     , 'USDA_FS'        : ['US Forest Service (FS)',                                              [38.886767, -77.030001]]
     , 'USDA_NIFA'      : ['US National Institute of Food and Agriculture (NIFA)',                [38.886767, -77.030001]]
}

# Use an jupyter notebook to choose the colors (simulation_color_palette.ipynb).
color_palette = ['#db5f57', '#db9057', '#dbc257', '#c3db57', '#91db57', '#5fdb57', '#57db80', '#57dbb2',
                 '#57d3db', '#57a2db', '#5770db', '#6f57db', '#a157db', '#d357db', '#db57b2', '#db5780']

c = 0 # Add color for each Funder.
for k, v in funders_dict.items():
    funders_dict[k] += [color_palette[c]]
    c += 1

funding['FunderNameFull'] = funding['Funder'].progress_map(lambda x: funders_dict[x][0])
funding['latFunder'] = funding['Funder'].progress_map(lambda x: funders_dict[x][1][0])
funding['lngFunder'] = funding['Funder'].progress_map(lambda x: funders_dict[x][1][1])

# ------------------------------------------------------------------------------------------------ #
# Remove Organization that are outside of the scope. **Move this to funding_database_merge.py**
# ------------------------------------------------------------------------------------------------ #

# Note: these terms may be resulting in false positives with non-English names.
# Use NLP to guess language first?

# Define Terms that are banned under what conditions
as_is_terms = ['Inc ', "Dept ", "Serv ", "Servs", "Srvs"]

to_lower_terms = ["Inc.", "LLC", "Incorporated", "Company", "Corporation", "Radio",
                  "Academy", "Television", "Service", "Servs", "Srvs", "Department",
                  "Mr." "Mrs.", "Dr.", " PhD "]

ends_with_terms = list(map(lambda x: x.rstrip().lower(), as_is_terms + ["PhD",  "LLC", "Incorporated", "Company"]))

# Construct a search term based on as_is_terms & to_lower_terms.
to_lower_terms_lowered = list(map(lambda x: x.lower(), to_lower_terms))
search_term_lower = '|'.join(map(re.escape, to_lower_terms_lowered))
search_term_any = '|'.join(as_is_terms)
search_term = search_term_any + search_term_lower

# Block as_is_terms & to_lower_terms.
funding = funding[~(funding['OrganizationName'].astype(str).str.lower().str.strip().str.contains(search_term))]\
                                                                                        .reset_index(drop=True)
# Block ends_with_terms
def ends_with_checker(x, ends_with_terms=ends_with_terms, override_terms=['university']):
    if str(x) == 'nan':
        return False

    if any(x.lower().rstrip().endswith(i) for i in ends_with_terms) and not any(i in x.lower() for i in override_terms):
        return True
    else:
        return False

# Ablate
funding = funding[~(funding['OrganizationName'].map(ends_with_checker))].reset_index(drop=True)

# ------------------------------------------------------------------------------------------------ #
# Homogenize Lng-Lat by OrganizationName (exact match) **Move this to funding_database_merge.py**
# ------------------------------------------------------------------------------------------------ #

org_geos_groupby = funding.groupby(['OrganizationName']).apply(lambda x: list(zip(x['lat'].tolist(), x['lng'].tolist()))).reset_index()

org_geos_groupby = org_geos_groupby[org_geos_groupby[0].map(lambda x: len(set(x)) > 1)].reset_index(drop=True)

def most_central_point(geos_array, valid_centroid=10):
    """
    Algorithm to find the point that is most central.
    Using the haversine formula.

    Would be slow at scale...What is this? >O(n^4)...yikes.
    Thankfully, it only needs to churn though ~750 rows.
    :param geos_array:
    :param geos_array: valid_centroid (in KM). Defaults to 10.
    :return:
    """
    distance_dict = dict.fromkeys(set(geos_array), list())
    for i in set(geos_array):
        other_geos = [j for j in geos_array if j != i]
        distance_dict[i] = [haversine(i, k) for k in other_geos]

    distance_dict_mean = {k: mean(v) for k, v in distance_dict.items()}
    min_coord = min(distance_dict_mean, key=distance_dict_mean.get)

    if distance_dict_mean[min_coord] <= valid_centroid:
        return min_coord
    else:
        return np.NaN

# Work out the centroid for each duplicate location
org_geos_groupby['centroid'] = org_geos_groupby[0].map(most_central_point)

# Save in a dict of the form {OrganizationName: centroid}
multi_geo_dict = dict(zip(org_geos_groupby['OrganizationName'], org_geos_groupby['centroid']))

# Swap out duplicates
def geo_swap(org_name, current_geo, lat_or_lng):
    if str(org_name) == 'nan' or str(current_geo) == 'nan':
        return np.NaN
    elif org_name in multi_geo_dict:
        lookup = multi_geo_dict[org_name]
        if str(lookup) != 'nan':
            return lookup[lat_or_lng]
        else:
            return lookup
    else:
        return current_geo

funding['lat'] = funding.apply(lambda x: geo_swap(x['OrganizationName'], x['lat'], 0), axis=1)
funding['lng'] = funding.apply(lambda x: geo_swap(x['OrganizationName'], x['lng'], 1), axis=1)

# Remove rows with nans in their lat or lng columns
funding.dropna(subset = ['lat', 'lng'], inplace=True)

# ------------------------------------------------------------------------------------------------ #
# Remove Organization Collisions for Geo Mapping (Multiple Orgs at the same lat/lng).
# ------------------------------------------------------------------------------------------------ #

funding['UniqueGeo'] = funding['lng'].astype(str) + funding['lat'].astype(str)

def sclwr(input_list):
    """Set, Clean, Lower input list."""
    return set(map(lambda x: cln(str(x), 2).lower(), input_list))

unique_geo_names = funding.groupby('UniqueGeo').apply(lambda x: x['OrganizationName'].tolist()).reset_index()
unique_geo_names_duplicates = unique_geo_names[unique_geo_names[0].map(lambda x: len(sclwr(x))) > 1]

def unique_order_preseve(input_list):
    input_no_dup = list()
    for i in input_list:
        if i not in input_no_dup:
            input_no_dup.append(i)
    return input_no_dup

# Set and each list and preseve order
unique_geo_names_duplicates[0] = unique_geo_names[0].map(unique_order_preseve)

# Keep the first item in each list
to_keep = unique_geo_names_duplicates[0].map(lambda x: x[0]).tolist()

# Get Org Names that are to be tossed
to_remove = unique_geo_names_duplicates[0].map(lambda x: [i for i in x if i not in to_keep]).tolist()

# Flatten the result
to_remove_flat = [i for s in to_remove for i in s]

# Filter the funding df and drop duplicates
funding = funding[~(funding['OrganizationName'].isin(to_remove_flat))].reset_index(drop=True)

# ------------------------------------------------------------------------------------------------ #
# Create a Summary of Science Funding Orgs. in the Database.
# ------------------------------------------------------------------------------------------------ #

funders_info = pd.DataFrame(list(funders_dict.values()))
funders_info.rename(columns={2: "colour"}, inplace=True)
funders_info['lat'] = list(map(lambda x: x[0], funders_info[1]))
funders_info['lng'] = list(map(lambda x: x[1], funders_info[1]))
del funders_info[1]
funders_info.rename(columns={0:'funder'}, inplace=True)

funders_info = funders_info.sort_values("funder").drop_duplicates('funder').reset_index(drop=True)
funders_info = funders_info[['funder', 'lat', 'lng', 'colour']]

funders_info.to_csv(MAIN_FOLDER + "JavaScript/JavaScriptVisualizations/data/" + "funder_db.csv", index=False)

# ------------------------------------------------------------------------------------------------ #
# Group by Organization
# ------------------------------------------------------------------------------------------------ #

funding_gb = funding.reset_index(drop=True)
funding_gb.drop(["Keywords"], inplace=True, axis=1)

funding_gb_org = org_group(funding_gb, additiona_cols=['FunderNameFull', 'latFunder', 'lngFunder'])

funding_gb_org['OrganizationName'] = funding_gb_org['OrganizationName'].str.replace("\"", "")

funding_gb_org = funding_gb_org[~funding_gb_org['OrganizationName'].map(
    lambda x: any(i in str(x) for i in ['Inc', 'Llc', "Company", "Corporation"]))].reset_index(drop=True)

os.chdir(MAIN_FOLDER+"/JavaScript/JavaScriptVisualizations/data")

# Limit to $20,000,000 (2015 USD) and up
funding_gb_org_cln = funding_gb_org[(funding_gb_org['NormalizedAmount'].astype(float) > 50000000)].drop(
                                    ['Researcher', 'GrantYear'], axis=1)

funding_gb_org_cln['NormalizedAmount'] = funding_gb_org_cln['NormalizedAmount'].progress_map(
                                            lambda x: money_printer(x, "USD", 2015))
funding_gb_org_cln.to_csv("science_funding.csv", index=False)

# ------------------------------------------------------------------------------------------------ #
# Time Series animation
# ------------------------------------------------------------------------------------------------ #

min_grant_size = 750000

# Require a grant be > min_grant_size in its own currency
to_export = funding[(funding['Amount'].astype(float) >= min_grant_size) &\
                    (pd.notnull(funding['NormalizedAmount']))]

def date_zero_correct(input_str):
    if input_str[0] != "0" and float(input_str) < 10:
        return "0" + input_str
    else:
        return input_str

def date_correct(input_date):
    """
    Formats input to DD/MM/YYYY
    """
    input_split = input_date.split("/")
    if len(input_split) == 0 or len(input_split[-1]) != 4:
        return np.NaN

    if len(input_split) == 1 and len(input_split[0]) == 4 and input_split[0].isdigit():
        return "01/01/" + input_split[0]
    elif len(input_split) == 2 and float(input_split[0]) <= 12:
        month = date_zero_correct(input_split[0])
        year = input_split[1]
        return "/".join(("01", month, year))
    elif len(input_split) == 3:
        if float(input_split[0]) > 12 and float(input_split[1]) <= 12:
            day = date_zero_correct(input_split[0])
            month = date_zero_correct(input_split[1])
        elif float(input_split[0]) <= 12:
            month = date_zero_correct(input_split[0])
            day = date_zero_correct(input_split[1])
        else:
            return np.NaN
        year = input_split[2]
        return "/".join([day, month, year])
    else:
        return np.NaN

to_export['StartDate'] = to_export['StartDate'].astype(str).map(date_correct)

# Drop
to_export = to_export[pd.notnull(to_export['StartDate'])].reset_index(drop=True)

to_export = to_export[pd.to_datetime(to_export['StartDate']) > "01/01/2007"].reset_index(drop=True)

# Restrict columns to those that are needed
allowed_columns = ["OrganizationName", "FunderNameFull", "NormalizedAmount", "StartDate", "lng", "lat"]
to_export = to_export[allowed_columns]

# Sort
to_export = to_export.ix[pd.to_datetime(to_export['StartDate']).sort_values().index].reset_index(drop=True)

# Add an ID Column
to_export["uID"] = pd.Series(to_export.index, index=to_export.index)
column_order = ['uID'] + allowed_columns

# Export
to_export[column_order].to_csv(MAIN_FOLDER + "/JavaScript/JavaScriptVisualizations/data/" + "funding_sample.csv", index=False)

# ------------------------------------------------------------------------------------------------ #

# ------------
# Scratch Work
# ------------

print(len(to_export.OrganizationName.unique())) # high -- Improve filtering.

tester = deepcopy(funding[funding['OrganizationBlock'] == 'Europe'])

n_amount_groupby = tester.groupby('OrganizationName').apply(lambda x: sum(x['NormalizedAmount'].tolist())).reset_index()
print(round(float(n_amount_groupby[0].max()), 1))

# Groupby       Normal        Real USD
# Name:      3161183583.1 | $3789172600.4
# UniqueGeo: 3258690632.6 | $3904925835.0




























































