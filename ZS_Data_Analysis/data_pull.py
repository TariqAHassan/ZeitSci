'''

Main ZeitSci Script
~~~~~~~~~~~~~~~~~~~

Python 3.5

'''

# ---------------- #
#  Import Modules  #
# ---------------- #

import os
import re
import nltk
import usaddress
import numpy as np
import pandas as pd
from Bio import Entrez
from fuzzywuzzy import process
from bio_query import paper_extract
from supplementary_fns import *
from abstract_analysis import abstract_en
from abstract_analysis import common_words
from data_extractor import SummaryExtractor
from open_cage_functionality import ZeitOpenCage
# from ivory_tower_lookup import ResearchInstitutions


try:
    from my_keys import OPENCAGE_KEY
except:
    pass

# --------------------------------------------------------------------------- #
#              Construct a dataframe from the download information            #
# --------------------------------------------------------------------------- #


# Create a body of papers
papers = paper_extract(journal = "Neuron", retmax = 10)

# Create an instance of the SummaryExtractor
corpus_processor = SummaryExtractor(papers)

# Create an empty dataframe
df = pd.DataFrame(columns = corpus_processor.ordered_cols)

# ----------------------- #
# Check Length of df here #
# ----------------------- #

# Populate each row of the DF with a paper summary
# Try to find faster solution...
for p in range(len(papers)):
    df = df.append(corpus_processor.paper_row(p))

# --------------------------------------------------------------------------- #
#        Determine the Field, and possibly Discipline, of Each Journal        #
# --------------------------------------------------------------------------- #

# --------------------- #
#  Get unique Journals  #
# --------------------- #

unique_journals = list(set(df["Journal"].tolist()))

# Remove information after a comma
unique_journals = [re.sub(r"\:.*", "", j) for j in unique_journals]

unique_journals = sorted(unique_journals)

# --------------------- #
#   Import Databases    #
# --------------------- #

# Get the current dir
current_dir = os.getcwd()

# Move over to the data folder
os.chdir(current_dir.rsplit('/', 1)[0] + "/Data")

# Import the journal database
jdb = pd.read_pickle("journal_database")

# import country info
isodb = pd.read_csv("iso_country_codes.csv")

# Import
wldc = pd.read_csv("worldcities.csv")

# refine


# Change back to orig. dir.
os.chdir(current_dir)
#


def city_in_country(country, guess_threshold = 60):
    """

    Gets all the cities in a country


    :param country:
    :return:
    """

    if country == "":
        return None

    country = process.extract(cln(country, 1), wldc.Country.unique(), limit=1)[0]

    if country[1] < guess_threshold:
        return None

    return np.array(wldc.City[wldc.Country == country[0]])


# city_in_country("Saint Martin French")


# --------------------------------- #
#  Add Field, Disp & Impact to df   #
# --------------------------------- #

def journal_info_get(journal, info_type):
    """
    :param journal: e.g., Nature
    :param info_type: the type of information: 'f' for Field; 's' for SubDiscipline; 'h' for H-Index.
    :return:
    """

    # Initialize
    journal_info = ""
    fail_return = ""

    if info_type == 'f':
        request = "FieldComplete"
        fail_return = []
    elif info_type == 's':
        request = "SubDiscipline"
        fail_return = []
    elif info_type == 'h':
        request = "H index"
        fail_return = ""
    else:
        raise ValueError("info_type must be either 'f', 's' or 'h'")

    try:
        journal_info = jdb[request][jdb["Title"].str.lower() == journal.lower()].iloc[0]
        return journal_info
    except:
        return fail_return


# Get Field information for all journals
df["Field"] = df["Journal"].apply(journal_info_get, args=('f',))

# Get SubDiscipline information
df["SubDiscipline"] = df["Journal"].apply(journal_info_get, args=('s',))

# Get H-Index information
df["H_Index"] = df["Journal"].apply(journal_info_get, args=('h',))


# ------------------------------------------------------------------------- #
#                             Analyze the Abstracts                         #
# ------------------------------------------------------------------------- #

# Check your right to do this.
# probably have to remove...

# Get the language of the paper, baseed on the abstract
df["Language"] = [abstract_en(a) for a in np.array(df["Abstract"])]

# Get most common words in the abstract
top_n_words = 5

df["CommonWords"] = ""
df["CommonWordsCount"] = ""
for row in range(df.shape[0]):
    common_abs_words = common_words(df["Abstract"][row], n = top_n_words)
    df.set_value(index = row, col ='CommonWords', value = common_abs_words[0])
    df.set_value(index = row, col ='CommonWordsCount', value = common_abs_words[1])


# ------------------------------------------------------------------------- #
#                   Extract Author's Field, Institution                     #
# ------------------------------------------------------------------------- #


tester = df["Institution"]

test = tester[3]

any_of = ["school of"
        , "center for"
        , "department"
        , "dept."
        , "institute"
        , "laboratory"
        #, "division"
        , "graduate program"]

# break on on any_of
# next break on , De

# extract all any_of and the remove overlap (recusive approach)

# split on , any_of
#          ^ or start of string


def author_appointment(author_creds, any_of):
    """

    :param author_creds:
    :param any_of:
    :return:
    """

    author_info = {
          "Appointments" : []
        , "Institutions" : []
    }

    # author_creds = author_inst[18]

    appointments_set = [cln(i, 1).lstrip().strip() for i in author_creds.split(";")]

    for ac in appointments_set:

        apt = appointment_extractor(ac, any_of)
        if apt != None and apt not in author_info["Appointments"]:
            author_info["Appointments"] += apt

        inst = instution_extractor(ac, wdb, any_of)
        if inst != None and inst not in author_info["Institutions"]:
            author_info["Institutions"] += [inst]

    return author_info


for a in author_inst:
    print(author_appointment(a, any_of)['Appointments'])
    print(author_appointment(a, any_of)['Institutions'])


authors_apps = df["Institution"][0]

author_appointment(authors_apps[0], any_of)


all_author_info = {
     "Appointments" : []
    ,"Institutions" : []
}

for ap in authors_appointments:

    author = author_appointment(ap, any_of)

    apt = appointment_extractor(ap, any_of)
    if apt != None and apt not in all_author_info["Appointments"]:
        all_author_info["Appointments"] += apt


    inst = instution_extractor(ap, wdb, any_of, guess_threshold=50)
    if inst != None and inst not in all_author_info["Institutions"]:
        all_author_info["Institutions"] += [inst]


































df["FieldsInvolved"] = ""
df["InstitutionsInvolved"] = ""





# save dict to col with department, insit. for each author
# also save to another col a unique list of departments involved
# also save to another col a unique list of insit involved








































# ------------------------------------------------------------------------- #
#                   Extract Author's Institution, Field                     #
# ------------------------------------------------------------------------- #





# ------------------------------------------------------------------------- #
#    Look up Inst. information in wdb, if not present -- look up and add    #
# ------------------------------------------------------------------------- #

# Save to disk the number of requests made in the past 24 hours.

# Crate an instance of the ResearchInstitutions class
resInsts = ResearchInstitutions(insts_db = wdb)


resInsts.lookup('Northwestern')['Address']

# Create an instance of ZeitOpenCage
# zoc = ZeitOpenCage(api_key = OPENCAGE_KEY)

# zoc.lookup("UBC University, Canada")





























