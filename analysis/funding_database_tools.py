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
from easymoney.easy_pandas import twoD_nested_dict

from unidecode import unidecode
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
    ,"FunderBlock"
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

def try_dict_lookup(input_dict, key):
    """

    :param input_dict:
    :param key:
    :return:
    """
    if key in input_dict.keys():
        return input_dict[key]
    if remove_accents(key) in input_dict.keys():
        return input_dict[remove_accents(key)]
    else:
        return np.NaN

def multi_readin(files_to_readin, lower_cols=True, unnammed_drop=False, encoding = None, dtypes=None):
    """

    Read in multiple csv files.

    :param files_to_readin:
    :param lower_cols:
    :return:
    """
    to_concat = list()
    for f in files_to_readin:
        if encoding != None:
            temp_df = pd.read_csv(f, encoding=encoding, dtype=dtypes)
        else:
            temp_df = pd.read_csv(f, dtype=dtypes)
        if lower_cols:
            temp_df.columns = [cln(c.lower(), 2) for c in temp_df.columns.tolist()]
        to_concat.append(temp_df)

    df = pd.concat(to_concat)

    to_drop = [i for i in df.columns if 'unnamed' in str(i).lower()]
    if unnammed_drop and len(to_drop) > 0:
        for td in to_drop:
            df.drop(td, axis=1, inplace=True)

    return df.reset_index(drop=True, inplace=False)

def wiki_pull_geo_parser(db_path):
    """
    Nested Dict from WikiPull {Country {UNI: GEO}}
    """
    df = pd.read_csv(db_path)
    df = df.dropna(subset=['lat', 'lng']).reset_index(drop=True)
    df['University'] = df['University'].str.lower()
    df['lat_long'] = df.apply(lambda x: [round(x['lat'], 6), round(x['lng'], 6)], axis=1)
    return  twoD_nested_dict(df, 'Country', 'University', 'lat_long')

def partial_key_check(partial_key, dictionary):
    """
    Checks for a partial key match in a dict.
    Returns the corresponding key if one (and only one) was found.
    Otherwise, returns nan.
    """
    keys = list(dictionary.keys())
    key_matches = [i for i in keys if partial_key.lower() in i.lower()]
    return key_matches[0] if len(key_matches) == 1 else np.NaN

def fuzzy_key_match(key, dictionary, quality_floor=90):
    """

    :param key:
    :param dictionary:
    :param quality_floor:
    :return:
    """
    match = process.extractOne(key, list(dictionary.keys()))
    return match[0] if match[1] >= quality_floor else np.NaN

# Create ISO country Dict.
two_iso_country_dict = dict()
for country in list(pycountry.countries):
    two_iso_country_dict[country.alpha2] = country.name

def unique_order_preseve(input_list):
    """
    Get unique items in a list and
    preserve their order.
    """
    input_no_dup = list()
    for i in input_list:
        if i not in input_no_dup:
            input_no_dup.append(i)
    return input_no_dup

def greatest_number_of_matches(word_a, candidate_matches):
    """

    Returns the candidate which contains the greatest number of words also in word_a.

    :param word_a:
    :param candidate_matches:
    :return:
    """
    word_a_upper = cln(word_a).upper().strip()
    candidate_matches_split = [[i, cln(i).upper().strip().split(" ")] for i in candidate_matches]

    match_dict = dict()
    for s in candidate_matches_split:
        match_dict[s[0]] = len([c for c in s[1] if c in word_a_upper])

    best_match = max(match_dict.keys(), key=lambda k: match_dict[k])

    return best_match

def first_name_clean(input_name):
    """

    :param input_name:
    :return:
    """
    if str(input_name).lower() == 'nan':
        return np.NaN
    input_name_split = input_name.split(" ")
    if len(input_name_split) == 3 and all(len(i.replace(".", "")) == 1 for i in input_name_split[1:]):
        return input_name_split[0] + " " + "".join([i.replace(".", "") for i in input_name_split[1:]])
    elif len(input_name_split) >= 3:
        return input_name_split[0] + " " + "".join([i[0] for i in input_name_split[1:]])
    elif len(input_name_split) == 2:
        return input_name_split[0].replace(".", "") + " " + input_name_split[1][0]
    else:
        return input_name.lower().title()

def col_cln(data_frame, update=True):
    """

    :param data_frame:
    :return:
    """
    for i, c in enumerate(data_frame.columns):
        if update:
            print(str(i) + ": ", c)
        data_frame[c] = data_frame[c].astype(str).map(lambda x: unidecode(cln(x).strip()), na_action='ignore')
    return data_frame

def researcher_cln(first, last):
    """

    :param first:
    :param last:
    :return:
    """
    if str(last) != 'nan':
        last_name = " ".join([i.lower().title() if i.isupper() else i for i in last.split()]).strip()
        if str(first) != 'nan':
            return (first.strip() + " " + last_name).strip()
        else:
            return last_name.strip()
    else:
        return np.NaN



















































