"""

    Builds Journal database from Scimagojr.com
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Python 3.5

"""

import re
import os
from xlrd import *
import numpy as np
import pandas as pd
from collections import Counter
from supplementary_fns import lprint, cln

# Get the current dir
current_dir = os.getcwd()

# Move over to the data folder
path = os.chdir(current_dir.rsplit('/', 1)[0] + "/Data/scimagorjr_rankings")

# Remove .ds_store
files = [i for i in os.listdir(path) if str(i).lower() != ".ds_store"]

# Build df from source files
to_concat = []
for f in files:
    temp_df = pd.read_excel(f)
    temp_df["Field"] = os.path.splitext(f)[0]
    to_concat.append(temp_df)

df = pd.concat(to_concat)
df.index = range(df.shape[0])

# Import wikipedia_journal_info
os.chdir(current_dir.rsplit('/', 1)[0] + "/Data")
jdf = pd.read_pickle("wiki_science_journal_db")


# -------------------------- #
#    Refine Field Column     #
# -------------------------- #


# Make field a fields of lists
df.Field = [[i] for i in df.Field.tolist()]

# Split field on __
df.Field = [i[0].split("__") for i in df.Field.tolist()]


# ------------------------------------ #
#  For duplicates: combine field info  #
# ------------------------------------ #


# Start off matching Field
df["FieldComplete"] = df["Field"]

duplicate_entries = []
for i in list(Counter(df["Title"].tolist()).items()):
    if float(i[1]) > 1:
        duplicate_entries.append(i[0])

# Combine for duplicate entries
# a bit of a slow solution, but only ever needs to be run once.
for j in duplicate_entries:
    dup_rows = df[df.Title == j]

    dup_indices = list(dup_rows.index)

    field_complete = list(set([i for sublist in dup_rows.Field.tolist() for i in sublist]))

    for i in dup_indices:
        df.set_value(i, 'FieldComplete', field_complete)


# -------------------------- #
#   Add SubDiscipline Info   #
# -------------------------- #

# Start off empty
df["SubDiscipline"] = [""]*df.shape[0]

# Add Sub Discipline information from jdf
match_index = df.ix[df.Title.isin(jdf.Title.tolist()), "SubDiscipline"].index
for m in match_index:
    df.set_value( m, 'SubDiscipline', jdf.ix[jdf.Title == df.loc[m, "Title"], "Discipline"].tolist()[0] )


# -------------------------- #
#      Save Final Result     #
# -------------------------- #


# Pickle and Save
df.to_pickle("journal_database")

# Change back to orig. dir.
os.chdir(current_dir)





































































