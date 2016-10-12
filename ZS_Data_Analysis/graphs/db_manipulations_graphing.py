"""

    Tools for Manipulating the Databases for Graphing
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# Imports
import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from pprint import pprint
from funding_database_tools import MAIN_FOLDER
from graphs.graphing_tools import money_printer, org_group

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
# Create a list of Science Funding Orgs. in the Database.
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

# Limit to 20,000,000 and up
funding_gb_org_cln = funding_gb_org[(funding_gb_org['NormalizedAmount'].astype(float) > 50000000)].drop(
                                    ['Researcher', 'GrantYear'], axis=1)

funding_gb_org_cln['NormalizedAmount'] = funding_gb_org_cln['NormalizedAmount'].progress_map(
    lambda x: money_printer(x, "USD", 2015))
#[funding_gb_org_cln.OrganizationBlock.isin(["United States", "Canada"])].
funding_gb_org_cln.to_csv("science_funding.csv", index=False)

# ------------------------------------------------------------------------------------------------ #
# Time Series animation
# ------------------------------------------------------------------------------------------------ #

to_export = funding[(funding['NormalizedAmount'].astype(float) > 2500000)]

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

to_export = to_export[pd.to_datetime(to_export['StartDate']) > "01/01/2010"]

# Export
to_export.ix[pd.to_datetime(to_export['StartDate']).sort_values().index].reset_index(drop=True)\
    .to_csv(MAIN_FOLDER+"/JavaScript/JavaScriptVisualizations/data/"+"funding_sample.csv", index=False)


import math
x = 2500000
maxAmount = to_export['NormalizedAmount'].max()

def logistic_fn(x, minValue, maxValue, curveSteepness):

    # maxAmount (Order of Magitude) / 10
    maxOrderOfMag = 10 ** (int(math.log10(maxAmount)) - 1)

    L = maxValue/maxOrderOfMag
    k = curveSteepness
    denominator = 1 + math.e**(-k*(x/maxOrderOfMag))

    return L/denominator - L/2 + minValue

logistic_fn(x*3, 1.5, maxAmount, curveSteepness=1)
















































































