'''

Develop a Database of Science Funding
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 3.5

'''

# ---------------- #
#  Import Modules  #
# ---------------- #

import os
import sys
import time
import glob2
import datetime
import pycountry
import unicodedata
import numpy as np
import pandas as pd
from copy import deepcopy
from fuzzywuzzy import fuzz    # needed?
from fuzzywuzzy import process

from abstract_analysis import *

from region_abbrevs import US_states, European_Countries

from supplementary_fns import cln
from supplementary_fns import lprint
from supplementary_fns import insen_replace
from supplementary_fns import partial_match
from supplementary_fns import pandas_col_shift
from supplementary_fns import partial_list_match
from supplementary_fns import items_present_test

# ZeitSci Classes
from zeitsci_wiki_api import WikiUniversities, wiki_complete_get
from open_cage_functionality import ZeitOpenCage

from nltk.corpus import stopwords

from region_abbrevs import Australian_states
from region_abbrevs import Australia_Inist_Cities
from open_cage_functionality import ZeitOpenCage
from my_keys import OPENCAGE_KEY

from easymoney.money import EasyPeasy
ep = EasyPeasy()

# Goal:
# A dataframe with the following columns:

#  Researcher
#       Fields                       X  -- use journal ranging dataframe
#       ResearcherSubfields          X  -- use journal ranging dataframe
#       ResearchAreas (sub-subfield) X  -- use journal ranging dataframe
#       Amount
#       NormalizedAmount             X  -- the grant in 2015 USD (or 2016...fix)
#       Currency
#       YearOfGrant
#       FundingSource
#       Colaberators                 X -- based on pubmed 2000-2016 download
#       keywords
#       Instution
#       Endowment                    X -- use wikipedia universties database
#       InstutionCountry
#       City/NearestCity
#       lng
#       lat

# X = do when all country's data are assembled

# TO DO: Run a abstract analysis on each keyword/term.
# this will standardize the terms

# ------------------------------------------------------------------------- #
#                        Commonly Used Data/Objects                         #
# ------------------------------------------------------------------------- #

MAIN_FOLDER = "/Users/tariq/Google Drive/Programming Projects/ZeitSci/"

# Reorder
order_cols = [
     "Researcher"
    ,"Funder"
    ,"GrantYear"
    ,"Amount"
    ,"FundCurrency"
    ,"ProjectTitle"
    ,"OrganizationName"
    ,"OrganizationCity"
    ,"OrganizationState"   # -> region
    ,"OrganizationBlock"
    ,"lat"
    ,"lng"
    ,"Keywords"
]

def titler(input_str):
    """

    # Doesn't handle ', e.g., l'University

    String titling function

    :param input_str:
    :return:
    """

    if not isinstance(input_str, str):
        return input_str

    # Define stop words
    esw = stopwords.words("english") + ["de", "la", "et", "di", "fur", "l'"]

    # Strip whitespace and split
    input_str = cln(input_str).lstrip().rstrip().split()

    for i in range(len(input_str)):
        if i == 0:
            input_str[i] = input_str[i].lower().capitalize()
        else:
            if input_str[i].lower() not in esw:
                input_str[i] = input_str[i].lower().capitalize()
            elif input_str[i].lower() in esw:
                input_str[i] = input_str[i].lower()

    return " ".join(input_str)

def df_combine(files, file_types = 'excel', skip = 0, file_name_add = False, encoding = "ISO-8859-1", lower_col = True):
    """

    :param files:
    :param file_types:
    :param skip:
    :param file_name_add:
    :param encoding:
    :param lower_col:
    :return:
    """
    # If a string is provided, convert to a list
    if not isinstance(files, list) and isinstance(files, str):
        files = [files]

    # Read in data
    to_concat = list()
    for f in files:
        if file_types == 'excel':
            temp_df = pd.read_excel(f, skiprows = range(skip))
        elif file_types == 'csv':
            temp_df = pd.read_csv(f, encoding = encoding)
        if lower_col:
            temp_df.columns = [cln(i).lower().lstrip().rstrip() for i in temp_df.columns.tolist()]
        else:
            temp_df.columns = [cln(i).lstrip().rstrip() for i in temp_df.columns.tolist()]

        if file_name_add:
            temp_df['file_name' if lower_col else 'File_Name'] = f
        to_concat.append(temp_df)

    # Combine frames into a single data frame
    df = pd.concat(to_concat)

    # Reindex
    df.index = range(df.shape[0])

    return df

def comma_reverse(input_str):
    """

    :param input_str:
    :return:
    """

    if input_str.count(",") != 1:
        return input_str

    # should join on " ", not ", " -- could be useful though for handling middle names.
    return " ".join([cln(i).lstrip().rstrip().lower().title() for i in input_str.split(",")][::-1])

def column_drop(data_frame, columns_to_drop, drop_type = "complete"):
    """

    :param data_frame:
    :param columns_to_drop:
    :param drop_type: 'complete' or 'na'
    :return:
    """

    # Drop column or NAs in columns.
    for col in columns_to_drop:
        if col in data_frame.columns:
            if drop_type == 'complete':
                data_frame.drop(col, axis = 1, inplace = True)
            elif drop_type == 'na':
                data_frame = data_frame[pd.notnull(data_frame[col])]

    # Refactor index
    data_frame.index = range(data_frame.shape[0])

    return data_frame

def string_match_list(input_list, string_to_match):
    """

    :param input_list:
    :param string_to_match:
    :return:
    """
    return [i for i in input_list if string_to_match in i]

def fdb_common_words(summary_series, n = 5, update_after = 5000):
    """

    :param summary_list:
    :return:
    """

    counter = 0
    words = [[]]*summary_series.shape[0]
    for sw in range(summary_series.shape[0]):
        words[sw] = common_words(summary_series[sw], n = n)[0]

        counter += 1
        if counter % update_after == 0:
            print("Strings Analyzed:", str(round(float(counter)/summary_series.shape[0]*100, 2)) + "%")

    return words

def year_columns(columns):

    def is_float(input_str):
        try:
            float(input_str)
            return True
        except:
            return False

    return [x.strip() for x in columns if is_float(x.strip()) and len(x.strip()) == 4]

# Create ISO country Dict.
two_iso_country_dict = dict()
for country in list(pycountry.countries):
    two_iso_country_dict[country.alpha2] = country.name


# ------------------------------------------------------------------------------------------------------------ #
#                                            United States of America                                          #
# ------------------------------------------------------------------------------------------------------------ #



os.chdir(MAIN_FOLDER + "/Data/Governmental_Science_Funding/USA/US_Funding")


us_df = pd.read_csv("2016_All_Grants_Full_20160915.csv")
#Fernandez

to_drop = [
      'fyq'
    , 'unique_transaction_id'
    , 'federal_award_id'
    , 'transaction_status'
    , 'federal_award_mod'
    , 'cfda_program_num'
    , 'sai_number'
    , 'recipient_city_code'
    , 'recipient_type'
    , 'action_type'
    , 'non_fed_funding_amount'
    , 'total_funding_amount'
    , 'obligation_action_date'
    , 'ending_date'
    , 'assistance_type'
    , 'correction_late_ind'
    , 'fyq_correction'
    , 'principal_place_code'
    , 'principal_place_state'
    , 'principal_place_cc'
    , 'principal_place_country_code'
    , 'principal_place_zip'
    , 'principal_place_cd'
    , 'cfda_program_title'
    , 'duns_no'
    , 'uri'
    , 'duns_conf_code'
    , 'progsrc_agen_code'
    , 'progsrc_acnt_code'
    , 'progsrc_subacnt_code'
    , 'face_loan_guran'
    , 'recip_cat_type'
    , 'asst_cat_type'
    , 'orig_sub_guran'
    , 'recipient_cd'
    , 'agency_code'
    , 'record_type'
    , 'recipient_county_code'
    , 'maj_agency_cat'
    , 'rec_flag'
    , 'recipient_county_name'
    , 'last_modified_date'
]

us_df = column_drop(us_df, to_drop)

# us_df[us_df['exec1_fullname'].astype(str) != 'nan']

# Drop rows where US Federal Spending was zero
us_df = us_df[us_df['fed_funding_amount'].astype(float) > 0]

# Clean Agency Names
us_df['agency_name'] = us_df['agency_name'].astype(str).map(lambda x: re.sub("\(.*\)", "", x).strip())

# add?
# NATIONAL ENDOWMENT FOR THE ARTS
# NATIONAL ENDOWMENT FOR THE HUMANITIES
# ECONOMIC RESEARCH SERVICE

us_science_agencies = [
     'DEPARTMENT OF HEALTH AND HUMAN SERVICES'
    ,'ENVIRONMENTAL PROTECTION AGENCY'
    ,'ENERGY, DEPARTMENT OF'
    ,'NATIONAL AERONAUTICS AND SPACE ADMINISTRATION'
    ,'NATIONAL SCIENCE FOUNDATION'
    ,'GEOLOGICAL SURVEY'
]

# Limit to funding from the above sectors of the federal government
us_df = us_df[us_df['agency_name'].astype(str).isin(us_science_agencies)]


# Refresh index
us_df.reset_index(drop = True, inplace = True)

us_df[(us_df['recipient_name'].astype(str).str.lower().str.contains('university'))]

us_df['project_description'][426]























































































