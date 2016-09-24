"""

    Clean the Pubmed Dump
    ~~~~~~~~~~~~~~~~~~~~~

    Dump obtained on: July 11, 2016 (double check).

    Python 3.5

"""


# Modules
import re
import os
import blaze
import numpy as np
import pandas as pd
from blaze import *
from copy import deepcopy
# from odo import odo
# from pandas import DataFre, read_csv
# from abstract_analysis import *



# Goal:
# A dataframe with the following columns:

#   Researcher
#   Fields                        X  -- use journal ranking dataframe
#   ResearcherSubfields           X  -- use journal ranking dataframe
#   ResearchAreas (sub-subfield)  X  -- use journal ranking dataframe
#   Amount
#   NormalizedAmount                 -- the grant in 2015 USD (2016 not handled properly...fix)
#   Currency
#   YearOfGrant
#   FundingSource
#   Collaborators                 X  -- based on pubmed 2000-2016 download
#   keywords
#   Institution
#   Endowment                        -- use wikipedia universties database
#   InstitutionType                  -- use wikipedia universties database (i.e., public or private)
#   InstitutionRanking            X  -- Ranking of the institution (read: uni). QS Data avaliable; usage rights unkown.
#   InstutionCountry
#   City/NearestCity
#   lng
#   lat

# X = to do (when all country's data are assembled)
# Also: Run an abstract analysis on each keyword/term this will standardize the terms


# ------------------------------------------------------------------------- #
#                        General Tools & Information                        #
# ------------------------------------------------------------------------- #

MAIN_FOLDER = "/Users/tariq/Google Drive/Programming Projects/ZeitSci/"


# Move to AUX_NCBI_DATA Folder
os.chdir(MAIN_FOLDER + "/Data/NCBI_DATA")

ncbi_journals_df = pd.read_csv('jlist.csv')

journal_abrev_full_dict = dict(zip(ncbi_journals_df['NLM TA'], ncbi_journals_df['Journal title']))

# pubmed.to_csv("pubmed_download_partial_clean.csv", index = False)

# ------------------------------------------------------------------------- #
#                                 Processing                                #
# ------------------------------------------------------------------------- #

# Move to MetaData Folder
os.chdir(MAIN_FOLDER + "/Data/NCBI_DATA/JounralMetadata")

# Tell pandas how many columns there are and what they're called
names = ["Title", "URL", "Description", "Details", "ShortDetails", "Resource", "Type", "Identifiers", "Db", "EntrezUID", "Properties"]

columns_to_use = ['Title', 'Description', 'ShortDetails', 'Properties']

# Import with (1) a manual override of column header information and (2) only reading in columns in columns_to_use
pubmed = pd.io.parsers.read_csv("pubmed_result_2000_jul_2016.csv"
                                , usecols=columns_to_use
                                , names=names
                                , error_bad_lines=False
                                , nrows=100000)[1:]

# Remove row with columns_to_use as values
for col in columns_to_use:
    pubmed[col] = pubmed[col].astype(str)
    pubmed = pubmed[pubmed[col] != col]

# Refresh Index
pubmed.index = range(pubmed.shape[0])

# Rename columns
pubmed.columns = ["title", "authors", "short_details", "properties"]

# Fix author column
pubmed['authors'] = pubmed['authors'].str.split(", ")

# Split short_details column
short_details = pubmed['short_details'].str.split('.  ')

# Make new Journal and year Columns
pubmed["journal"] = short_details.str[0]
pubmed["year"] = short_details.str[1]

# Drop short_details
# usig del to release memory
del pubmed["short_details"]

# Only those "strings" with length 4; Remove NaN years
pubmed = pubmed[(pubmed['year'].str.len() == 4) & (pd.notnull(pubmed["year"]))]  # 17,925 rows removed

# convert year to an int.
pubmed['year'] = pubmed['year'].astype(int)

# Remove those entries prior to 2000
pubmed = pubmed[pubmed['year'] >= 2000]
# 3335 rows removed; they shouldn't have been there in the first place.

# Split Properties on pipe
properties = pubmed['properties'].str.split('|')

pubmed['date_created'] = properties.str[0].str.replace("create date:", "").str.strip()
pubmed['first_author'] = properties.str[1].str.replace("first author:", "").str.strip()

# Drop properties column
del pubmed['properties']





























































# Refresh index
pubmed.index = range(pubmed.shape[0])















































































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














































