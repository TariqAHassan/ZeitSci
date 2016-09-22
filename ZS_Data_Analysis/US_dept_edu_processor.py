
'''

This Script Structures the Data post Extraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 3.5

'''


# ---------------- #
#  Import Modules  #
# ---------------- #

import geocoder
import numpy as np
import pandas as pd
from itertools import compress

# ------------- #
#  Import Data  #
# ------------- #

# Import abbreviations for US states
from region_abbrevs import US_states


# A record of all accredited US universities.
# Data avaliable from the US Dept. of Education: http://ope.ed.gov/accreditation/GetDownLoadFile.aspx
us_unis = pd.read_csv('../data/accreditation_2016_03.csv')

# Now Read in the data obtained by crawing Pubmed
# (place holder .csv for now)
df = pd.read_csv('../data/sample_data.csv')

'''
# ---------------------------------------------------- #
# Goal: Get the log. and lat. for each University here #
# ---------------------------------------------------- #
'''


# ------------------------------------------------------------------------- #
#                               Clean the main DF                           #
# ------------------------------------------------------------------------- #

# see :
#   https://github.com/endSly/world-universities-csv
#   https://en.wikipedia.org/wiki/List_of_colloquial_names_for_universities_and_colleges_in_the_United_States
#   Kaggle Data

# ------------------------------------------------------------------------- #
#                               Clean the Uni DF                            #
# ------------------------------------------------------------------------- #

### 1. Add Country Column ###
us_unis["Country"] = "USA"

### 2. Delete unneeded columns ###
us_unis_cols = us_unis.columns.values.tolist()
cols_to_keep = [
        "Institution_Name"
      , "Institution_State"
      , "Institution_Address"
      , "Institution_City"
      , "Institution_Zip"
]
cols_to_drop = [i for i in us_unis_cols if i not in cols_to_keep]
us_unis.drop(cols_to_drop, axis = 1, inplace = True)


### 3. Next, do a rough clean of "duplicate" rows ###
# Remove Duplicates from the us_unis df
dup_rows = us_unis["Institution_Name"].duplicated().tolist()

# Pretty 'Find Trues in list' Solution from @AshwiniChaudhary:
# see: http://stackoverflow.com/questions/21448225/getting-indices-of-true-values-in-a-boolean-list
to_drop = list(compress(range(len(dup_rows)), dup_rows))
us_unis.drop(us_unis.index[to_drop], inplace = True)


### 4. Replace Institution_State abbreviations with full name #
us_unis.replace({"Institution_State": US_states}, inplace = True)


### 5. Correct Str. Type for zip information ##
us_unis["Institution_Zip"] = us_unis["Institution_Zip"].str.replace('"', '')

# ------------------------------------------------------------------------- #
#                Obtain Address of Uni from us_unis for df                  #
# ------------------------------------------------------------------------- #

def uni_address_get(uni):

    if not isinstance(uni, str):
        return np.nan

    # This DOES NOT handle cases where there are two unis with *similar* names, e.g.,
    # Cornell College and  Cornell University.
    # The fix to this depends on what pubmed crawers provides -- does it include a uni's full name?

    # Should make this make robust either way.

    try:
        # a bit dense, but this just tries to map an university name to a name in the the us_uni data frame
        address = np.array(us_unis[us_unis['Institution_Name'].str.contains(uni, case = False)]).tolist()[0]
    except:
        return np.nan

    return ', '.join(map(str, address))

# Add Complete Address to df
df["Full_Address"] = [uni_address_get(uni) for uni in df["University"].tolist()]


# Finally, add the lat_lng to the df for each university
lat_lng = []
for addr in df["Full_Address"].tolist():
    if addr == np.nan:
        lat_lng.append(addr)
    else:
        loc = geocoder.google(addr)
        lat_lng.append(loc.latlng)

df["lat_lng"] = lat_lng

# ------------------------------------------------------------------------- #
#                   Save the `df` dataframe as a .json                      #
# ------------------------------------------------------------------------- #

df.to_json("../data/to_vis_data.json")
df.to_csv("../data/to_vis_data.csv")





'''

This Script Structures the Data post Extraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 3.5

# see :
#   https://github.com/endSly/world-universities-csv
#   https://en.wikipedia.org/wiki/List_of_colloquial_names_for_universities_and_colleges_in_the_United_States
#   Kaggle Data


'''


# ---------------- #
#  Import Modules  #
# ---------------- #

import geocoder
import numpy as np
import pandas as pd
from itertools import compress

# ------------- #
#  Import Data  #
# ------------- #

# Import abbreviations for US states
from region_abbrevs import US_states


# A record of all accredited US universities.
# Data avaliable from the US Dept. of Education: http://ope.ed.gov/accreditation/GetDownLoadFile.aspx
us_unis = pd.read_csv('../data/accreditation_2016_03.csv')


# Now Read in the data obtained by crawing Pubmed
# (place holder .csv for now)
df = pd.read_csv('../data/sample_data.csv')


'''
# ---------------------------------------------------- #
# Goal: Get the log. and lat. for each University here #
# ---------------------------------------------------- #
'''


# ------------------------------------------------------------------------- #
#                               Clean the main DF                           #
# ------------------------------------------------------------------------- #


# ------------------------------------------------------------------------- #
#                               Clean the Uni DF                            #
# ------------------------------------------------------------------------- #

### 1. Add Country Column ###
us_unis["Country"] = "USA"

### 2. Delete unneeded columns ###
us_unis_cols = us_unis.columns.values.tolist()
cols_to_keep = [
        "Institution_Name"
      , "Institution_State"
      , "Institution_Address"
      , "Institution_City"
      , "Institution_Zip"
]
cols_to_drop = [i for i in us_unis_cols if i not in cols_to_keep]
us_unis.drop(cols_to_drop, axis = 1, inplace = True)


### 3. Next, do a rough clean of "duplicate" rows ###
# Remove Duplicates from the us_unis df
dup_rows = us_unis["Institution_Name"].duplicated().tolist()

# Pretty 'Find Trues in list' Solution from @AshwiniChaudhary:
# see: http://stackoverflow.com/questions/21448225/getting-indices-of-true-values-in-a-boolean-list
to_drop = list(compress(range(len(dup_rows)), dup_rows))
us_unis.drop(us_unis.index[to_drop], inplace = True)


### 4. Replace Institution_State abbreviations with full name #
us_unis.replace({"Institution_State": US_states}, inplace = True)


### 5. Correct Str. Type for zip information ##
us_unis["Institution_Zip"] = us_unis["Institution_Zip"].str.replace('"', '')

# ------------------------------------------------------------------------- #
#                Obtain Address of Uni from us_unis for df                  #
# ------------------------------------------------------------------------- #

def uni_address_get(uni):

    if not isinstance(uni, str):
        return np.nan

    # This DOES NOT handle cases where there are two unis with *similar* names, e.g.,
    # Cornell College and  Cornell University.
    # The fix to this depends on what pubmed crawers provides -- does it include a uni's full name?

    # Should make this make robust either way.

    try:
        # a bit dense, but this just tries to map an university name to a name in the the us_uni data frame
        address = np.array(us_unis[us_unis['Institution_Name'].str.contains(uni, case = False)]).tolist()[0]
    except:
        return np.nan

    return ', '.join(map(str, address))

# Add Complete Address to df
df["Full_Address"] = [uni_address_get(uni) for uni in df["University"].tolist()]


# Finally, add the lat_lng to the df for each university
lat_lng = []
for addr in df["Full_Address"].tolist():
    if addr == np.nan:
        lat_lng.append(addr)
    else:
        loc = geocoder.google(addr)
        lat_lng.append(loc.latlng)

df["lat_lng"] = lat_lng

# ------------------------------------------------------------------------- #
#                   Save the `df` dataframe as a .json                      #
# ------------------------------------------------------------------------- #

df.to_json("../data/to_vis_data.json")
df.to_csv("../data/to_vis_data.csv")




































































































