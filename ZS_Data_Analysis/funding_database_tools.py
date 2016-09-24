'''

    Tools for evolving the Region Specific Databases
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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


# ------------------------------------------------------------------------- #
#                        Commonly Used Data/Objects                         #
# ------------------------------------------------------------------------- #

MAIN_FOLDER = "/Users/tariq/Google Drive/Programming Projects/ZeitSci/"

# Reorder
order_cols = [
     "Researcher"
    ,"Funder"
    ,"StartDate"
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

    Currently can't handle ', e.g., l'University

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
    return " ".join([cln(i).strip().lower().title() for i in input_str.split(",")][::-1])

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

def fdb_common_words(summary_series, n = 5, update_after = 1000):
    """

    :param summary_list:
    :param n: number of most common words
    :param update_after: print update of analysis progress after x strings
    :return:
    """
    counter = 0
    words = [[]]*summary_series.shape[0]
    for sw in range(summary_series.shape[0]):
        words[sw] = common_words(input_str=summary_series[sw], n=n)[0]

        counter += 1
        if counter % update_after == 0 or counter == 1:
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

def remove_accents(input_str):
    """
    http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
    :param input_str:
    :return:
    """
    nkfd_form = unicodedata.normalize('NFKD', input_str)
    return ("".join([c for c in nkfd_form if not unicodedata.combining(c)]))

def multi_readin(files_to_readin, lower_cols=True, unnammed_drop=False, encoding = None):
    """

    Read in multiple csv files.

    :param files_to_readin:
    :param lower_cols:
    :return:
    """
    to_concat = list()
    for f in files_to_readin:
        if encoding != None:
            temp_df = pd.read_csv(f, encoding=encoding)
        else:
            temp_df = pd.read_csv(f)
        if lower_cols:
            temp_df.columns = [cln(c.lower(), 2) for c in temp_df.columns.tolist()]
        to_concat.append(temp_df)

    df = pd.concat(to_concat)

    to_drop = [i for i in df.columns if 'unnamed' in str(i).lower()]
    if unnammed_drop and len(to_drop) > 0:
        for td in to_drop:
            df.drop(td, axis=1, inplace=True)

    return df.reset_index(drop=True, inplace=False)

# Create ISO country Dict.
two_iso_country_dict = dict()
for country in list(pycountry.countries):
    two_iso_country_dict[country.alpha2] = country.name






























































