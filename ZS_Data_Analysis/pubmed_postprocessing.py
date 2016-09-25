"""

    Clean the Pubmed Post Processing
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
from collections import defaultdict
from easymoney.easy_pandas import strlist_to_list
from easymoney.easy_pandas import twoD_nested_dict
from abstract_analysis import common_words
# from odo import odo



# Goal:
# A dataframe with the following columns:

#   Researcher
#   Fields                           -- use journal ranking dataframe
#   ResearcherSubfields              -- use journal ranking dataframe
#   ResearchAreas (sub-subfield)     -- use journal ranking dataframe -- keywords
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
#   InstitutionRanking            V  -- Ranking of the institution (uni). Impact Factor usage rights are prohibitive.
#   InstutionCountry
#   City/NearestCity
#   lng
#   lat

# V = VOID, i.e., not possible
# X = to do (when all country's data are assembled)
# Also: Run an abstract analysis on each keyword/term this will standardize the terms


# ------------------------------------------------------------------------- #
#                         General Tools & Information                       #
# ------------------------------------------------------------------------- #


MAIN_FOLDER = "/Users/tariq/Google Drive/Programming Projects/ZeitSci/"


# Move to AUX_NCBI_DATA Folder
os.chdir(MAIN_FOLDER + "/Data/NCBI_DATA")

ncbi_journals_df = pd.read_csv('jlist.csv')

journal_abrev_full_dict = dict(zip(ncbi_journals_df['NLM TA'].astype(str).str.upper(), ncbi_journals_df['Journal title']))

# pubmed.to_csv("pubmed_download_partial_clean.csv", index = False)

# ------------------------------------------------------------------------- #
#                             Process NCBI Metadata                         #
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
                                , nrows=100000)

# Remove row with columns_to_use as values
for col in columns_to_use:
    pubmed[col] = pubmed[col].astype(str)
    pubmed = pubmed[pubmed[col] != col]

# Refresh Index
pubmed.index = range(pubmed.shape[0])

# Rename columns
pubmed.columns = ["title", "authors", "short_details", "properties"]

# Fix author column
pubmed['authors'] = pubmed['authors'].str.replace(".", "").str.replace("\' ", "\'").str.split(", ")

# Split short_details column
short_details = pubmed['short_details'].str.split('.  ')

# Make new Journal and year Columns
pubmed["journal"] = short_details.str[0]
pubmed["year"] = short_details.str[1]

# Drop short_details
# using del to release memory
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

# Try to add the Journal's Full Name -- upper case may not be the best solution (too computationally complex).
pubmed['journal_full'] = pubmed['journal'].str.upper().replace(journal_abrev_full_dict).str.lower().str.title()

# Refresh index
pubmed.index = range(pubmed.shape[0])

# ------------------------------------------------------------------------- #
#         Integrate NCBI Metadata with Journal Ranking Information          #
# ------------------------------------------------------------------------- #

os.chdir(MAIN_FOLDER + "/Data/WikiPull")

# Read in Journal Database
journal_db = pd.read_csv("wiki_journal_db.csv")

# Remove '.' from Journal_Abbrev
journal_db['Journal_Abbrev'] = journal_db['Journal_Abbrev'].map(lambda x: x if str(x) == 'nan' else x.replace(".", ""))

# Convert Field to list
journal_db['Field'] = journal_db['Field'].map(lambda x: x if str(x) == 'nan' else strlist_to_list(x))

# Convert Discipline to list.
# the first map converts "['item', 'item']" --> ['item', 'item']
# the second map replaces empty lists with nans
journal_db['Discipline'] = journal_db['Discipline'].map(
    lambda x: x if str(x) == 'nan' else strlist_to_list(x)).\
    map(lambda x: np.NaN if str(x) == 'nan' or len(x) == 1 and x[0] == '' else x)

# Merge Field and Discipline
field_and_discipline = journal_db.apply(lambda x: [x['Field'], x['Discipline']], axis=1)

# Dict with Journal's Full Name as the key
full_title_dict = dict(zip(journal_db['Title'].str.upper(), field_and_discipline))

# Dict with Journal's Abrev. as the key
abrev_title_dict = dict(zip(journal_db['Journal_Abbrev'].str.upper(), field_and_discipline))

# Remove NaN key
abrev_title_dict = {k: v for k, v in abrev_title_dict.items() if str(k) != 'nan'}

def journal_match(full_name, partial_name):
    """

    Fuction to match joural to its field and discipline
    using the full_title_dict and abrev_title_dict dictionaries.

    :param full_name: the full name of the journal.
    :type full_name: str
    :param partial_name: the abrev. of the journal.
    :type partial_name: str
    :return: [FIELD, DISCIPLINE]
    :rtype: ``nan`` or ``list``
    """

    if partial_name.upper() in abrev_title_dict:
        return abrev_title_dict[partial_name.upper()]
    elif partial_name.upper() != full_name.upper() and full_name.upper() in full_title_dict:
        return full_title_dict[full_name.upper()]
    else:
        return [np.NaN, np.NaN]

# Attempt to add field and discipline information using a journal's full name or abrev.
mapped_field_discipline = pubmed.apply(lambda x: journal_match(x['journal_full'], x['journal']), axis=1)

# Add journal field to the pubmed data frame
pubmed['field'] = mapped_field_discipline.map(lambda x: x[0])

# Add journal discipline to the pubmed data frame
pubmed['discipline'] = mapped_field_discipline.map(lambda x: x[1])

# ------------------------------------------------------------------------- #
#                                Add Keywords                               #
# ------------------------------------------------------------------------- #

# Faster -- 42588.45 ms on average (N=3)
# title_keywords = pubmed['title'].map(lambda x: common_words(x, n=5, return_rank=False, digit_check=False), na_action='ignore')

# Slower -- 47377.06 ms on average (N=3)...but easier to monitor.
title_keywords = [0]*pubmed.shape[0]
for t in range(len(pubmed['title'])):
    if t % 10000 == 0: print(round(float(t)/len(pubmed['title'])*100, 2), "%")
    title_keywords[t] = common_words(pubmed['title'][t], n=5, return_rank=False, digit_check=True, wrap_nans=False)

# Add Keywords based on the title
pubmed['keywords'] = title_keywords

# ------------------------------------------------------------------------- #
#                              Find Collaborations                          #
# ------------------------------------------------------------------------- #

# The most of the 'solutions' below are really just a series of hacks designed to
# drive down the run down because, frankly, this problem is a gemoetric nighmare when you have ~ 12 million rows.

# "...premature optimization is the root of all evil." ~ Donald Knuth
# So, you know, do as I say, not...

# ---------------------------------------------------------------------------------------- #

# Author + Index (to be used to locate field_discipline). This operation is vectorized (minus that map()...).
authors_field_discipline = pubmed['authors'] + pd.Series(mapped_field_discipline.index).map(lambda x: [x])

# Try to work out collaborators.
# Thanks to @zvone on stackoverflow.
# see: http://stackoverflow.com/questions/39677070/procedure-to-map-all-relationships-between-elements-in-a-list-of-lists
collaborators_dict = defaultdict(set)
for paper in authors_field_discipline:
    for author in paper:
        collaborators_dict[author].update(paper)

for author, collaborators in collaborators_dict.items():
    collaborators.remove(author)

# dict of fields with keys corresponding to the pubmed df
field_nan_drop = pubmed['field'].dropna().reset_index()
index_field_dict = dict(zip(field_nan_drop['index'], field_nan_drop['field']))

# dict of disciplines with keys corresponding to the pubmed df
discipline_nan_drop = pubmed['discipline'].dropna().reset_index()
discipline_field_dict = dict(zip(discipline_nan_drop['index'], discipline_nan_drop['discipline']))

# collab_domain = collaborators_dict[pubmed['authors'][32786][0]]

def collaborators_domain_seperator(collab_domain):
    """

    Separates a list of authors and pubmed indexes into a list of lists of the form: [[AUTHORS], [FIELD], [DISCIPLINE]].
    Please see: http://stackoverflow.com/questions/14776980/python-splitting-list-that-contains-strings-and-integers

    Notes:
        1. necessary to set(collab_domain)? Unclear.
        2. add year information?

    :param collab_domain:
    :return:
    :rtype: dict
    """

    collab_dict = defaultdict(list)
    for i in collab_domain:
        collab_dict[type(i)].append(i)

    fields = list()
    disciplines = list()
    for i in collab_dict[int]:
        if i in index_field_dict:
            fields += index_field_dict[i]
        if i in discipline_field_dict:
            disciplines += discipline_field_dict[i]

    # note: len is --obviously -- O(1)...so the
    # time cost of adding this information here should be minimal.
    info = {"index_of_papers": collab_dict[int]
            , "num_authored": len(collab_dict[int])
            , "collaborators": collab_dict[str]
            , "num_collaborators": len(collab_dict[str])
            , "fields": set(fields)
            , "disciplines": set(disciplines)}

    return info

# import cProfile
# cProfile.runctx("for i in range(10000): "
#                 "   collaborators_domain_seperator({'Yum SK', 'Youn YA', 55558, 'Lee IG', 55597, 'Kim JH', 'Moon CJ'})"
#                 , None, locals())

def collaborator_analysis(single_author):
    return collaborators_domain_seperator(collaborators_dict[single_author])

def mutli_collaborators_analysis(authors):
    return [collaborator_analysis(a) for a in authors]

# cProfile.runctx("for i in range(10000): "
#                 "   mutli_collaborators_analysis(authors)"
#                 , None, locals())

c = 0
relationships = list()
len_authors = len(pubmed['authors'])
for authors in pubmed['authors']:
    c += 1
    if c % 1000 == 0:
        print(round(float(c)/len_authors * 100, 2), "%")
    relationships.append(mutli_collaborators_analysis(authors))


# NOTE:
# Problem: Authors Sharing Name.
len(set([i for s in pubmed['authors'] for i in s]))
# !=
len([i for s in pubmed['authors'] for i in s])

# This can be solved by switching to a more complete database.














































































