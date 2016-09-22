
# Modules #

import re
import os
import numpy as np
import pandas as pd
import blaze
from copy import deepcopy
from odo import odo
from blaze import *
from pandas import DataFrame, read_csv
from abstract_analysis import *
from supplementary_fns import cln
from supplementary_fns import lprint
from supplementary_fns import insen_replace
from supplementary_fns import partial_match
from supplementary_fns import pandas_col_shift
from supplementary_fns import partial_list_match
from supplementary_fns import items_present_test


MAIN_FOLDER = "/Users/tariq/Google Drive/Programming Projects/ZeitSci/"

# Move to MetaData Folder
os.chdir(MAIN_FOLDER + "/Data/JounralMetadata")


# This thing is a beast

# Tell pandas how many columns there are and what they're called
names = ["Title", "URL", "Description", "Details", "ShortDetails", "Resource", "Type", "Identifiers", "Db", "EntrezUID", "Properties"]

# Import; manual override of column header information.
pubmed = pd.io.parsers.read_csv("pubmed_result_2000_jul_2016.csv", names = names, error_bad_lines = False)

backup_df1 = pubmed

# Make column names lower case now.
pubmed.columns = [i.lower() for i in pubmed.columns]

# Remove useless columns
pubmed = pubmed[["title", "description", "details", "shortdetails"]]

# Limit to rows with useful information
pubmed.shortdetails = pubmed.shortdetails.astype("str")
pubmed = pubmed[pubmed.shortdetails != "ShortDetails"]
pubmed.index = range(pubmed.shape[0])

#  Memory usage started at ~1.1 GB
#  These steps drive memory usagage down to ~400 mbs!
pubmed.info()

backup_df2 = pubmed

# rename columns
pubmed.columns = ["title", "authors", "long_details", "short_details"]

# fix author column
pubmed.authors = pubmed.authors.str.split(", ") # pubmed seems to add a space after their commas...

# Split short_details column
short_details = pubmed.short_details.str.split('.  ')

# Make new Journal and year Columns
pubmed["journal"] = short_details.str[0]
pubmed["year"] = short_details.str[1]
del pubmed["short_details"]

# Only those "strings" with length 4; Remove NaN years
pubmed = pubmed[(pubmed.year.str.len() == 4) & (pd.notnull(pubmed["year"]))]  # 17,925 rows removed

# convert year to an int.
pubmed.year = pubmed.year.astype(int)

# Remove those entries prior to 2000
pubmed = pubmed[pubmed.year >= 2000]   # 3335 rows removed; shouldn't have been there in the first place.
pubmed.index = range(pubmed.shape[0])

# Save to csv...slow
# pubmed.to_csv("pubmed_download_partial_clean.csv") # ,index = False


# Need to Create a PI Column.
# If no PI, remove row



from decorator import *


def double(f):
    def g(a ,b):
        return 100 * f(a, b)
    return g

@double
def sub(a, b):
    return b - a


sub(0.5, 1)
























































#
#
#
# # Move to blaze for fast querying
# pubmed2 = data(pubmed)
#
# # Remove unwanted columns
# pubmed2.fields
#
#
#














































