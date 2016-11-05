"""

    Tools for Manipulating the Databases for Geo-Mapping
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# Imports
import re
import os
import time
import numpy as np
import pandas as pd
from tqdm import tqdm
from pprint import pprint
from copy import deepcopy
from statistics import mean, median
from haversine import haversine
from calendar import monthrange
from collections import Counter
from supplementary_fns import cln
from graphs.graphing_data import funders_dict
from itertools import combinations, permutations
from funding_database_tools import MAIN_FOLDER
from funding_database_tools import unique_order_preseve
from easymoney.easy_pandas import pandas_print_full
from graphs.graphing_tools import money_printer, org_group

# To Do:
# Add EU to EC in legend

# ------------------------------------------------------------------------------------------------ #
# Read in Data
# ------------------------------------------------------------------------------------------------ #

funding = pd.read_pickle(MAIN_FOLDER + "/Data/MasterDatabase/" + 'MasterDatabaseRC6.p')
tqdm.pandas(desc="status")

# ------------------------------------------------------------------------------------------------ #
# Add Funder Information
# ------------------------------------------------------------------------------------------------ #

# Used an jupyter notebook to choose the colors (simulation_color_palette.ipynb).

funding['FunderNameFull'] = funding['Funder'].progress_map(lambda x: funders_dict[x][0])
funding['FunderNameAbbrev'] = funding['Funder'].progress_map(lambda x: re.findall('\((.*?)\)', funders_dict[x][0])[0])
funding['latFunder'] = funding['Funder'].progress_map(lambda x: funders_dict[x][1][0])
funding['lngFunder'] = funding['Funder'].progress_map(lambda x: funders_dict[x][1][1])

# ------------------------------------------------------------------------------------------------ #
# Export to .csv for analyses and graphing in R
# ------------------------------------------------------------------------------------------------ #

save_to = MAIN_FOLDER + "/analysis/R/funding_data.csv"
exclude_from_r_export = ['lat', 'lng', 'Keywords', 'Amount', 'FunderNameFull', 'latFunder', 'lngFunder']
funding.drop(exclude_from_r_export, axis=1).fillna("").to_csv(save_to, index=False)

# ------------------------------------------------------------------------------------------------ #
# Remove Organization that are outside of the scope.
# ------------------------------------------------------------------------------------------------ #

# Note: these terms may be resulting in false positives with non-English names.
# Use NLP to guess language first?

# Define Terms that are banned under what conditions
as_is_terms = ['Inc ', 'Inc.', "Dept ", "Dept.", "Serv ", "Servs", "Srvs"]

to_lower_terms = ["Inc.", "LLC", "Incorporated", "Company", "Corporation", "Radio",
                  "Academy", "Television", "Service", "Servs", "Srvs", "Department",
                  "Mr." "Mrs.", "Dr.", " PhD "]

ends_with_terms = list(map(lambda x: x.rstrip().lower(), as_is_terms + ["PhD",  "LLC", "Incorporated", "Company"]))

for at in as_is_terms:
    funding = funding[~(funding['OrganizationName'].astype(str).str.strip().str.contains(at))]

for lt in to_lower_terms:
    funding = funding[~(funding['OrganizationName'].astype(str).str.lower().str.strip().str.contains(lt))]

# Block ends_with_terms
def ends_with_checker(x, ends_with_terms=ends_with_terms, override_terms=['university']):
    if str(x) == 'nan':
        return False

    if any(x.lower().rstrip().endswith(i) for i in ends_with_terms) and not any(i in x.lower() for i in override_terms):
        return True
    else:
        return False

# Ablate
funding = funding[~(funding['OrganizationName'].progress_map(ends_with_checker))].reset_index(drop=True)

# ------------------------------------------------------------------------------------------------ #
# Homogenize Lng-Lat by OrganizationName (exact match)
# ------------------------------------------------------------------------------------------------ #

org_geos_groupby = funding.groupby(['OrganizationName']).apply(
                                                lambda x: list(zip(x['lat'].tolist(), x['lng'].tolist()))).reset_index()

org_geos_groupby = org_geos_groupby[org_geos_groupby[0].map(lambda x: len(set(x)) > 1)].reset_index(drop=True)

def most_central_point(geos_array, valid_medoid=30):
    """
    Algorithm to find the point that is most central (i.e., medoid)
    using the haversine formula. Distances are weighted by the number
    of observations (increases sucessful selection of a medoid from the pool by 50%).

    :param geos_array:
    :param valid_medoid: min for mean distance to all other points / number of observations.
                         Defaults to 30. If the value is still over 30 after computing the above
                         weighting metric, it is almost certainly worth removing.
    :return:
    """
    geos_array_count = dict(Counter(geos_array))
    uniuqe_geos = list(set(geos_array))

    coord_dict = dict()
    for i in uniuqe_geos:
        coord_dict[i] = [haversine(i, j) for j in uniuqe_geos if j != i]

    # Compute the mean for each and divide by the number of times it occured in geos_array
    coord_dict_mean = {k: mean(v)/float(geos_array_count[k]) for k, v in coord_dict.items()}

    # Use the most central point as the medoid
    medoid_mean_coord = min(coord_dict_mean, key=coord_dict_mean.get)

    if coord_dict_mean[medoid_mean_coord] <= valid_medoid:
        return medoid_mean_coord
    else:
        return np.NaN

# Work out the medoid for each duplicate location
org_geos_groupby['medoid'] = org_geos_groupby[0].progress_map(most_central_point)

# Save in a dict of the form {OrganizationName: medoid}
multi_geo_dict = dict(zip(org_geos_groupby['OrganizationName'], org_geos_groupby['medoid']))

# Swap out duplicates
def geo_swap(org_name, current_geo, lat_or_lng):
    """

    :param org_name:
    :param current_geo:
    :param lat_or_lng:
    :return:
    """
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
funding = funding.dropna(subset = ['lat', 'lng']).reset_index(drop=True)

# ------------------------------------------------------------------------------------------------ #
# Remove Organization Collisions for Geo Mapping (Multiple Orgs at the same lat/lng).
# ------------------------------------------------------------------------------------------------ #

funding['UniqueGeo'] = funding['lng'].astype(str) + funding['lat'].astype(str) + funding['OrganizationName']

def sclwr(input_list):
    """Set, Clean, Lower input list."""
    return set(map(lambda x: cln(str(x), 2).lower(), input_list))

unique_geo_names = funding.groupby('UniqueGeo').apply(lambda x: x['OrganizationName'].tolist()).reset_index()
unique_geo_names_duplicates = unique_geo_names[unique_geo_names[0].map(lambda x: len(sclwr(x))) > 1]

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
# Time Series animation
# ------------------------------------------------------------------------------------------------ #

top_x_orgs = 100
min_start_date = "01/01/2010"
max_start_date = time.strftime("%d/%m/%Y")
required_terms = []
# required_terms = ['unive', 'ecole', 'polytechnique', 'school', 'acad', 'hospit', 'medical', 'istit', 'labra', 'obser',
# 'clinic', 'centre', 'center', 'college']

def contains_required_term(x, required_terms=required_terms):
    if not len(required_terms): return True
    return True if any(i in str(x).lower() for i in required_terms) else False

# Limit to org's that contain required terms (above).
to_export = funding[funding['OrganizationName'].map(contains_required_term)].reset_index(drop=True)

# Drop invalid start dates
to_export = to_export[to_export['StartDate'].astype(str).str.count("/") == 2].reset_index(drop=True)

# Drop rows without a start date.
to_export = to_export[pd.notnull(to_export['StartDate'])].reset_index(drop=True)

# --- Spread Canadian Data over the whole year --- #
def random_day_month_swap(input_date, block, looking_for='Canada'):
    """
    Random Day Generator
    """
    if block != looking_for or input_date[0:5] != "01/01":
        return input_date
    dsplit = input_date.split("/")

    # Pick a random month
    random_month = np.random.randint(1, high=12, size=1)[0]
    max_day = monthrange(int(dsplit[2]), random_month)[1]

    random_day = np.random.randint(1, high=max_day, size=1)[0]
    day_to_add = "0" + str(random_day) if random_day < 10 else str(random_day)
    month_to_add = "0" + str(random_month) if random_month < 10 else str(random_month)
    return "/".join([day_to_add, month_to_add, dsplit[2]])

to_export['StartDate'] = to_export.apply(lambda x: random_day_month_swap(x['StartDate'], x['OrganizationBlock']), axis=1)

# ---------------------------------------------------------- #
# Drop StartDate to month temporal resolution
# ---------------------------------------------------------- #

date_format = "%m/%Y"
to_export['StartDate'] = to_export['StartDate'].map(lambda x: x[3:])

# ---------------------------------------------------------- #
# Restrict
# ---------------------------------------------------------- #

# Restrict to a date range
to_export['StartDateDTime'] = pd.to_datetime(to_export['StartDate'], format=date_format).sort_values()
to_export = to_export[(to_export['StartDateDTime'] >= min_start_date) &
                      (to_export['StartDateDTime'] <= max_start_date)].reset_index(drop=True)

# Remove Rows without Normalized Grant
to_export = to_export.dropna(subset=['NormalizedAmount']).reset_index(drop=True)

# Find orgs with the most grants (dollar amount).
orgs_by_grants = to_export.groupby('OrganizationName').apply(lambda x: sum(x['NormalizedAmount'].tolist())).reset_index()
orgs_by_grants = orgs_by_grants.sort_values(0, ascending=False).reset_index(drop=True)[0:top_x_orgs]

# 100 /19938 * 100
# orgs_by_grants[0].sum()/funding['NormalizedAmount'].sum() * 100

#Filter to the top x orgs by funding
to_export = to_export[to_export['OrganizationName'].isin(orgs_by_grants['OrganizationName'].tolist())].reset_index(drop=True)

# too long for the legend...come back and fix later.
# to_export = to_export[~(to_export['FunderNameFull'].str.contains("NIDILRR"))]

# ---------------------------------------------------------- #
# Agg by FunderNameFull by year
# ---------------------------------------------------------- #

funder_year_groupby = deepcopy(to_export)
funder_year_groupby['StartYear'] = funder_year_groupby['StartDate'].map(lambda x: x.split("/")[1]).astype(int)

funder_year_groupby = funder_year_groupby.groupby(['FunderNameFull', 'StartYear']).apply(
                                                            lambda x: sum(x['NormalizedAmount'].tolist())).reset_index()

funder_year_groupby = funder_year_groupby.rename(columns={0:'TotalGrants'})

# Work out proportion of grants given by Org
org_year_byyear = funder_year_groupby.groupby('StartYear').apply(lambda x: sum(x['TotalGrants'])).to_dict()
funder_year_groupby['PercentTotalGrants'] = funder_year_groupby.apply(lambda x: x['TotalGrants']/org_year_byyear[x['StartYear']], axis=1)

# Convert Proportion to Percent and round to value to one decimal place of precision.
funder_year_groupby['PercentTotalGrants'] = funder_year_groupby['PercentTotalGrants'].map(lambda x: x * 100).round(2).astype(float)

# Drop Rows for funders with ~zero grants awarded in a given year.
funder_year_groupby = funder_year_groupby[funder_year_groupby['PercentTotalGrants'] > 0].reset_index(drop=True)

# Format as str.
funder_year_groupby['PercentTotalGrants'] = funder_year_groupby['PercentTotalGrants'].astype(str).map(
                                                                lambda x: x + "0" if len(x.split(".")[1]) != 2 else x)

# Rename StartYear
funder_year_groupby = funder_year_groupby.rename(columns={"StartYear":"Year"}).sort_values('Year').reset_index(drop=True)

# Check
# funder_year_groupby.groupby('StartYear')['PercentTotalGrants'].sum()

# ------------------------------------------------------------------------------------------------ #

def to_export_col_summary(x):
    return [sum(x['NormalizedAmount'].tolist()), x['lng'].tolist()[0], x['lat'].tolist()[0], len(x['lat'].tolist())]

# Grouby by OrganizationName, StartDate, OrganizationName
to_export = to_export.groupby(['OrganizationName', 'StartDate', 'StartDateDTime', 'FunderNameFull']).apply(
    lambda x: to_export_col_summary(x)).reset_index()
to_export_groupbycol = np.array(to_export[0].tolist())
to_export['NormalizedAmount'] = to_export_groupbycol[:,0]
to_export['lng'] = to_export_groupbycol[:,1]
to_export['lat'] = to_export_groupbycol[:,2]
to_export['NumberOfGrants'] = [int(i) for i in to_export_groupbycol[:,3]]
del to_export[0]

# Shuffle
to_export = to_export.reindex(np.random.permutation(to_export.index))

# Sort by date
to_export = to_export.sort_values(by='StartDateDTime').reset_index(drop=True)
del to_export['StartDateDTime']

# Add an ID Column
to_export["uID"] = pd.Series(to_export.index, index=to_export.index)

# Restrict columns to those that are needed and Set Column Order
allowed_columns = ["OrganizationName", "FunderNameFull", "NormalizedAmount", "StartDate", "NumberOfGrants", "lng", "lat"]
column_order = ['uID'] + allowed_columns

#Order Columns
to_export = to_export[column_order]

print("# rows:", to_export.shape[0])
print("# Organizations:", len(to_export.OrganizationName.unique()))

#round(to_export.NormalizedAmount.sum()) --> ~ 65 Billion.

# ------------------------------------------------------------------------------------------------ #
# Create a Summary of Science Funding Orgs. in the Database.
# ------------------------------------------------------------------------------------------------ #

funders_info = pd.DataFrame(list(funders_dict.values()))
funders_info.rename(columns={2: "colour"}, inplace=True)
funders_info['lat'] = list(map(lambda x: x[0], funders_info[1]))
funders_info['lng'] = list(map(lambda x: x[1], funders_info[1]))
del funders_info[1]
funders_info.rename(columns={0:'funder'}, inplace=True)

funders_info = funders_info.sort_values("funder").drop_duplicates('funder')
funders_info = funders_info[funders_info['funder'].isin(to_export['FunderNameFull'].tolist())].reset_index(drop=True)

funders_info = funders_info[['funder', 'lat', 'lng', 'colour']]

# ------------------------------------------------------------------------------------------------ #
# Exports
# ------------------------------------------------------------------------------------------------ #

export_dir = MAIN_FOLDER + "/visualizations/data/"
to_export_name = "funding_simulation_data" + ".csv"

# 1.
to_export.to_csv(export_dir + to_export_name, index=False)

# 2.
funder_year_groupby.to_csv(export_dir + "funding_yearby_summary.csv", index=False)

# 3.
orgs_by_grants = orgs_by_grants['OrganizationName'].reset_index().rename(columns={'index':'OrganizationRank'})
orgs_by_grants['OrganizationRank'] += 1
orgs_by_grants.to_csv(export_dir + "organization_rankings.csv", index=False)

# 4.
funders_info.to_csv(export_dir + "funder_db.csv", index=False)







































































