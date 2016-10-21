"""

    Integrate Funding with Pubmed Data
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Python 3.5

"""

import os
import glob2
import string
import numpy as np
import pandas as pd
from tqdm import tqdm
from supplementary_fns import cln, fast_flatten
from easymoney.money import EasyPeasy
from funding_database_tools import MAIN_FOLDER

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
#                           Read In Cached Database                         #
# ------------------------------------------------------------------------- #

# Read in Pubmed Data
os.chdir(MAIN_FOLDER + "/Data/NCBI_DATA")
pubmed = pd.read_csv("Pubmed2000_to_2015.csv"
                          , dtype={'author': np.str, 'grants': np.str, 'keywords': np.str, 'journal': np.str,
                                   'pmid': np.str, 'title': np.str, 'mesh_terms': np.str, 'pubdate': np.str,
                                   'affiliation': np.str, 'journal_iso': np.str}
                          , error_bad_lines=False
                          , nrows=10000000)

# Read in Funding Data
funding = pd.read_pickle(MAIN_FOLDER + "/Data/MasterDatabase/" + 'MasterDatabaseRC2.p')

# Start tqdm
tqdm.pandas(desc="status")

# ------------------------------------------------------------------------- #
#                  Group by Researcher and OrganizationName                 #
# ------------------------------------------------------------------------- #

def researcher_name_cln(researcher):
    cleaned_name = cln(researcher.strip())
    split_name = cleaned_name.split(" ")

    if len(split_name) == 2:
        return split_name[0][0] + " " + split_name[-1]
    elif len(split_name) == 3:
        return split_name[0][0] + split_name[1][0] + " " + split_name[2]
    else:
        return cleaned_name if cleaned_name != '' else np.NaN

funding['ResearcherAbrev'] = funding['Researcher'].progress_map(researcher_name_cln, na_action='ignore')

# ------------------------------------------------------------------------- #
#                  Group by Researcher and OrganizationName                 #
# ------------------------------------------------------------------------- #





































