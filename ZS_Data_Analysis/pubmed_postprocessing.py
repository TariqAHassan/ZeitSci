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
from collections import OrderedDict
from easymoney.easy_pandas import strlist_to_list
from easymoney.easy_pandas import twoD_nested_dict
from abstract_analysis import common_words
from tqdm import tqdm
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

pubmed = pd.io.parsers.read_csv("Pubmed2000_to_2015.csv", nrows=100000, encoding='utf-8')

# Clean..for now
pubmed['title'] = pubmed['title'].str.replace("[", "").str.replace("]", "")
tqdm.pandas(desc="status")

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
mapped_field_discipline = pubmed.progress_apply(lambda x: journal_match(x['journal'], x['journal_iso']), axis=1)

# Add journal field to the pubmed data frame
pubmed['field'] = mapped_field_discipline.progress_map(lambda x: x[0])

# Add journal discipline to the pubmed data frame
pubmed['discipline'] = mapped_field_discipline.progress_map(lambda x: x[1])

def duplicate_remover(input_list):
    ordered_set = list()
    for element in input_list:
        if element not in ordered_set:
            ordered_set.append(element)
    return ordered_set

def grant_processor(grant):

    list_of_grants = [g.split("; ") for g in grant.split(" | ")]

    grant_ids = list()
    agencies = list()
    regions = list()
    for g in list_of_grants:
        for id in g[0].split(", "):
            if id not in grant_ids:
                grant_ids.append(id)
        if g[1] not in agencies:
            agencies.append(g[1])
        if g[2] not in regions:
            regions.append(g[2])

    return grant_ids, agencies, regions

grants = pubmed['grants'].progress_map(grant_processor, na_action='ignore')

pubmed['grant_ids'] = grants.map(lambda x: x[0], na_action='ignore')
pubmed['grant_funders'] = grants.map(lambda x: x[1], na_action='ignore')
pubmed['grant_region'] = grants.map(lambda x: x[2], na_action='ignore')
del pubmed['grants']

def keywords_mesh_combine(keywords, mesh):
    if str(keywords) == 'nan' and str(mesh) != 'nan':
        return mesh
    elif str(mesh) == 'nan' and str(keywords) != 'nan':
        return keywords
    elif str(mesh) == 'nan' and str(keywords) == 'nan':
        return np.NaN

    return "; ".join(set(keywords.split("; ") + mesh.split("; ")))

pubmed['keywords'] = pubmed.progress_apply(lambda x: keywords_mesh_combine(x['keywords'], x['mesh_terms']), axis=1)
del pubmed['mesh_terms']

# ------------------------------------------------------------------------- #
#                           Add Author+Afiliation                           #
# ------------------------------------------------------------------------- #

pubmed['author'] = pubmed['author'].str.split("; ")
pubmed['affiliation'] = pubmed['affiliation'].str.split("; ")

authors = pubmed['author'][0]
affiliations = pubmed['affiliation'][0]

# want: department + institution
def subsection_and_uni(affiliation, join_output=True, institution_only=False):
    # look into C Benz - Medicine
    # bazar result from:
    #   1. pubmed[pubmed['author'].map(lambda x: 'C Hu' in x if str(x) != 'nan' else False)]['institution'][62284]
    #   2. and the Eye and Ear Institute
    department = None
    institution = None

    affiliation_split = affiliation.split(", ")
    if affiliation_split == 1:
        return np.NaN

    department_terms = ['institute', 'department', 'division', 'dept']
    institution_terms = ['institute', 'university', 'centre', 'school', 'center', 'clinic',
                         'hospital', 'national labratory', 'research labratory', 'college', 'library']
    institution_deference = ['institute']

    department_match = [i for i in affiliation_split if any(w in i.lower() for w in department_terms)]
    if len(department_match) > 0:
        department = department_match[0]

    institution_match = [i for i in affiliation_split if any(w in i.lower() for w in institution_terms)]
    if len(institution_match) == 1:
        institution = institution_match[0]
    elif len(institution_match) > 1:
        institution = institution_match[-1]

    if (department is None and institution is None) or institution is None:
        return np.NaN
    elif institution_only or\
         (institution is not None and department is None) or\
         (any(i in department.lower() for i in institution_deference) and institution is not None):
        return institution

    if join_output:
        return ", ".join((department, institution))
    else:
        return ((department if department != None else np.NaN), (institution if institution != None else np.NaN))


def multi_affiliations(affiliations):
    processed_affiliations = (subsection_and_uni(a, institution_only=True) for a in affiliations)
    cleaned = [i for i in processed_affiliations if str(i) != 'nan']
    if len(cleaned):
        return "; ".join(cleaned)
    else:
        return np.NaN


def author_affil(authors, affiliations):
    # Remove emails?
    if 'nan' in [str(authors), str(affiliations)] or not len(authors) or not len(affiliations):
        return np.NaN

    if len(authors) > len(affiliations):
        authors = authors[:len(affiliations)]
    if len(affiliations) > len(authors):
        affiliations = affiliations[:len(authors)]

    cleaned_affilations = [a for a in map(subsection_and_uni, affiliations) if str(a) != 'nan']

    if len(cleaned_affilations):
        authors_afil = list(zip(authors, list(map(lambda a: subsection_and_uni(a), cleaned_affilations))))
        return [" | ".join(a) for a in authors_afil]
    else:
        return np.NaN

pubmed['institutions'] = pubmed['affiliation'].progress_map(lambda a: multi_affiliations(a), na_action='ignore')

pubmed['author_afil'] = pubmed.progress_apply(lambda x: author_affil(x['author'], x['affiliation']), axis=1)

# pubmed['institutions'][pubmed['institutions'].map(lambda x: ";" in x if str(x) != 'nan' else False)]

# TO DO: replace dept and dept.

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #

# Export
# pubmed['author_afil'] = pubmed['author_afil'].progress_map(lambda x: "; ".join(x))

# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------- #


# ------------------------------------------------------------------------- #
#                                Add Keywords                               #
# ------------------------------------------------------------------------- #

# Faster -- 42588.45 ms on average (N=3)
# title_keywords = pubmed['title'].map(lambda x: common_words(x, n=5, return_rank=False, digit_check=False), na_action='ignore')

# # Slower -- 47377.06 ms on average (N=3)...but easier to monitor.
# title_keywords = [0]*pubmed.shape[0]
# for t in range(len(pubmed['title'])):
#     if t % 1000 == 0: print(round(float(t)/len(pubmed['title'])*100, 2), "%")
#     title_keywords[t] = common_words(pubmed['title'][t], n=5, return_rank=False, digit_check=True, wrap_nans=False)
#
# # Add Keywords based on the title
# pubmed['keywords'] = title_keywords

# ------------------------------------------------------------------------- #
#                              Find Collaborations                          #
# ------------------------------------------------------------------------- #

# The most of the 'solutions' below are really just a series of hacks designed to
# drive down the run down because, frankly, this problem is a gemoetric nighmare when you have ~ 12 million rows.

# "...premature optimization is the root of all evil." ~ Donald Knuth
# So, you know, do as I say, not...

# ---------------------------------------------------------------------------------------- #

# Author + Index (to be used to locate field_discipline). This operation is vectorized (minus that map()...).
authors_field_discipline = pubmed['author_afil'] + pd.Series(mapped_field_discipline.index).progress_map(lambda x: [x])

# Try to work out collaborators.
# Thanks to @zvone on stackoverflow.
# see: http://stackoverflow.com/questions/39677070/procedure-to-map-all-relationships-between-elements-in-a-list-of-lists
collaborators_dict = defaultdict(set)
for paper in authors_field_discipline:
    if str(paper) != 'nan':
        for author in paper:
            if str(author) != 'nan':
                collaborators_dict[author].update(paper)

for author, collaborators in collaborators_dict.items():
    collaborators.remove(author)

# from itertools import chain
# a = list(chain.from_iterable(authors_field_discipline.dropna().tolist()))

# ------------------------------------------------------------------------- #
#                      Find the Fields For Each Author                      #
# ------------------------------------------------------------------------- #

# dict of fields with keys corresponding to the pubmed df
field_nan_drop = pubmed['field'].dropna().reset_index()
index_field_dict = dict(zip(field_nan_drop['index'], field_nan_drop['field']))

# dict of disciplines with keys corresponding to the pubmed df
discipline_nan_drop = pubmed['discipline'].dropna().reset_index()
discipline_field_dict = dict(zip(discipline_nan_drop['index'], discipline_nan_drop['discipline']))

def collaborators_domain_seperator(single_author):
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
    for i in collaborators_dict[single_author]:
        collab_dict[type(i)].append(i)

    fields = list()
    disciplines = list()
    for i in collab_dict[int]:
        if i in index_field_dict:
            fields += index_field_dict[i]
        if i in discipline_field_dict:
            disciplines += discipline_field_dict[i]

    set_fields = set(fields)
    set_disciplines = set(disciplines)

    info = {"index_of_papers": collab_dict[int]
            , "num_authored": len(collab_dict[int])
            , "collaborators": collab_dict[str] if len(collab_dict[str]) else np.NaN
            , "num_collaborators": len(collab_dict[str])
            , "fields": set_fields if len(set_fields) else np.NaN
            , "disciplines": set_disciplines if len(set_disciplines) else np.NaN}

    return info


# import cProfile
# cProfile.runctx("for i in range(10000): "
#                 "   collaborators_domain_seperator({'Yum SK', 'Youn YA', 55558, 'Lee IG', 55597, 'Kim JH', 'Moon CJ'})"
#                 , None, locals())


# def fast_flatten(input_list):
#     return list(chain.from_iterable(input_list))

c = 0
author_info = dict()
len_authors = len(pubmed['author_afil'])
for authors in pubmed['author_afil']:
    c += 1
    if c % 10000 == 0 or c == 1:
        print(round(float(c)/len_authors * 100, 2), "%")
    if str(authors) != 'nan':
        for a in authors:
            author_info[a] = collaborators_domain_seperator(a)


author_df = pd.DataFrame(list(author_info.values()))
author_full = [a.split(" | ") for a in list(author_info.keys())]

author_df['authors'] = [a[0] for a in author_full]
author_df['institutions'] = [a[1] for a in author_full]


author_df[(author_df.num_collaborators > 0) & pd.notnull(author_df.fields)]
































# NOTE:
# Problem: Authors Sharing Name.
# len(set([i for s in pubmed['author'] for i in s]))
# # !=
# len([i for s in pubmed['author'] for i in s])















































































