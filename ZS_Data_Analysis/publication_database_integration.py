"""

    Integrate Databases with Journal Publication Information
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Python 3.5

"""

# Modules
import os
import glob2
import string
import numpy as np
import pandas as pd
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

os.chdir(MAIN_FOLDER + "/Data/MasterDatabase")

# Read in
df = pd.read_pickle('MasterDatabaseRC1.p')

# ------------------------------------------------------------------------- #
#               Integrate Funding Data from around the World                #
# ------------------------------------------------------------------------- #











































































































































































































































































































































































