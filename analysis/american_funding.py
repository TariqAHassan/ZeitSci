"""

    US Funding
    ~~~~~~~~~~

    Python 3.5

"""
# Import Modules
import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from abstract_analysis import *
from region_abbrevs import US_states, Canada_prov_terr, European_Countries

from aggregated_geo_info import uni_dict, uni_geo_locator, us_geo_locator, master_geo_lookup

from funding_database_tools import MAIN_FOLDER
from funding_database_tools import order_cols
from funding_database_tools import titler
from funding_database_tools import comma_reverse
from funding_database_tools import column_drop
from funding_database_tools import multi_readin

# ------------------------------------------------------------------------------------------------------------ #
#                                            United States of America                                          #
# ------------------------------------------------------------------------------------------------------------ #

# NOTEs:
#   1. this code will merge fy_total_cost and fy_total_cost_sub_projects
#   2. AE is in the OrganizationState column (not a US State). Correct.

os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/USA")
us_files = [i for i in os.listdir() if i.endswith(".csv")]

us_df = multi_readin(us_files, encoding="ISO-8859-1", dtypes={"Organization_Zip": 'str'})
tqdm.pandas(desc="status")

def total_merge(fy_total, fy_total_sub):
    if str(fy_total) != 'nan':
        return fy_total
    elif str(fy_total_sub) != 'nan':
        return fy_total_sub
    else:
        return np.nan

us_df['fy_merged'] = us_df.apply(lambda x: total_merge(x['fy_total_cost'], x['fy_total_cost_sub_projects']), axis=1)

# Drop Unneeded Columns
to_drop = [  "congressional_district"
           , "cfda_code"
           , "sm_application_id"
           , "fy_total_cost"
           , "fy_total_cost_sub_projects"
           , "project_id"
           , "duns_number"
           , "project_end_date"
           , "budget_start_date"
           , "budget_end_date"
           , "project_number"
           , "ic_center"
           , "other_pis"]
us_df = column_drop(us_df, columns_to_drop = to_drop)

# Drop row if NA for certian columns
na_drop = [  "fy"
           , "contact_pi_project_leader"
           , "fy_merged"
           , "organization_city"
           , "organization_country"
           , "organization_name"
           , "organization_state"]
us_df = column_drop(us_df, columns_to_drop=na_drop, drop_type = "na")

# Merge agency and department; drop both after.
us_df["fundingsource"] = us_df['department'] + "_" + us_df['agency']
us_df.drop("agency", axis=1, inplace=True)
us_df.drop("department", axis=1, inplace=True)

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

# Clean Country Names (drop tabs, i.e., "\t")
us_df['organization_country'] = us_df['organization_country'].str.replace("\t", "")

# Clean City Names (remove extra white space).
us_df['organization_city'] = us_df.organization_city.apply(lambda v: v.strip())

# Drop duplicates.
us_df.drop_duplicates(keep="first", inplace=True)
us_df.reset_index(drop=True, inplace=True)

# Cean the Dataframe zip codes
us_df['organization_zip'] = us_df['organization_zip'].astype(str)
us_df['organization_zip'] = us_df['organization_zip'].apply(lambda v: v.strip().split("-")[0][:5])

def us_geo_lookup(geos, zipcode, uni, country):
    """

    :param geos:
    :param zipcode:
    :param uni:
    :param country: 
    :return: 
    """
    first_try = us_geo_locator(zipcode)
    if str(first_try[0]) != 'nan':
        return first_try
    elif country.upper() in uni_dict:
        return uni_geo_locator(uni, country)
    else:
        return master_geo_lookup(geos, zipcode, country, uni)
        # ^ Somewhat awkward, but this was added after the EU Script was finished.
        # Thus, it was simply appended, rather than substituted, to insure prior gains are conserved.

us_df_lat_lng = us_df.progress_apply(
    lambda x: us_geo_lookup(
        [np.NaN, np.NaN], x['organization_zip'], x['organization_name'], x['organization_country']),
    axis=1)
us_df_lat_lng_np = np.array(us_df_lat_lng.tolist())

us_df['lat'] = us_df_lat_lng_np[:,0]
us_df['lng'] = us_df_lat_lng_np[:,1]

# Many thanks to @miraculixx over on Stack Overflow.
# see: http://stackoverflow.com/questions/38284615/speed-up-pandas-dataframe-lookup/38284860#38284860

# Drop entries for which location information could not be obtained
us_df = us_df.dropna(subset=['lat', 'lng']).reset_index(drop=True)

# lower col names
us_df.columns = [c.lower() for c in us_df.columns]

# deploy comma_reverse()
us_df['contact_pi_project_leader'] = us_df['contact_pi_project_leader'].map(comma_reverse)

# Correct organization_city; not perfect, but close enough
us_df['organization_city'] = us_df['organization_city'].astype(str).str.lower().str.title()

# Correct Keywords
us_df['project_terms'] = us_df['project_terms'].progress_map(lambda x: x.strip().lower().split(";"), na_action='ignore')

# Correct the titles...will take a moment
us_df['project_title'] = us_df['project_title'].progress_map(titler, na_action='ignore')

# Correct the organization_name; not perfect, but close enough
us_df['organization_name'] = us_df['organization_name'].progress_map(titler, na_action='ignore')

del us_df["organization_zip"]

# Rename Columns
us_df.columns = ["Researcher"
                 , "GrantYear"
                 , "OrganizationCity"
                 , "OrganizationBlock"
                 , "OrganizationName"
                 , "OrganizationState"
                 , "StartDate"
                 , "Keywords"
                 , "ProjectTitle"
                 , "Amount"
                 , "Funder"
                 , "lat"
                 , "lng"
]

# Add Currency Column
us_df["FundCurrency"] = pd.Series("USD", index=us_df.index)

# Set Organization Block Name to 'United States'.
us_df['OrganizationBlock'] = pd.Series("United States", index=us_df.index)

# Correct OrganizationState: USA, Canada and Europe.
for d in [US_states, Canada_prov_terr, European_Countries]:
    us_df['OrganizationState'] = us_df['OrganizationState'].replace(d)

# Convert GrantYear and Amount to Floats
us_df['GrantYear'] = us_df['GrantYear'].astype(float)
us_df['Amount'] = us_df['Amount'].astype(float)

# Correct weird case of negative grants.
# us_df['Amount'] = us_df['Amount'].map(lambda x: x if str(x) == 'nan' or x >= 0 else x*-1)

# Refresh index
us_df = us_df.reset_index(drop=True)

# Order Columns
us_df = us_df[order_cols]


# US Data Stabilized #


# Save
us_df.to_pickle(MAIN_FOLDER + "/Data/Governmental_Science_Funding/CompleteRegionDatabases/" + "AmericanFundingDatabase.p")










































