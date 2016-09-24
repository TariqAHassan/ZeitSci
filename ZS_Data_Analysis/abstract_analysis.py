'''

Tools for the Analysis of Abstracts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 3.5

'''


# ---------------- #
#  Import Modules  #
# ---------------- #

import re
import string
import numpy as np
from nltk import FreqDist
from langdetect import detect
from nltk.corpus import stopwords
from supplementary_fns import cln
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer

# Initialize NLTK's WordNetLemmatizer
lmr = WordNetLemmatizer()

def abstract_en(abstract):
    """

    Makes a guess as to whether or not the abstract
    is in English

    :param abstract:
    :return:
    """

    if len(abstract) == 0:
        return "NA"

    language_guess = detect(abstract)

    # If it's english, return
    if language_guess == 'en':
        return language_guess

    # Otherwise
    return "non_en"

def word_vector_clean(str_vector):
    """

    Gets the most common words in a string
    Refinements:
        1. Removal of stop Words.
        2. Deploy a Lemmatizer to remove common suffixes
        3. Deploy a Lemmatizer to make all words (verbs) present tense

    :param str_vector:
    :return:
    """

    # Make all chars lower case
    joined_str_vector = " ".join([i.lower() for i in str_vector])

    # Tokenize to remove unimportant chars.
    joined_str_vector = RegexpTokenizer(r'\w+').tokenize(joined_str_vector)

    # Remove stop words
    if len(joined_str_vector) > 0:
        joined_str_vector = list(set(joined_str_vector) - set(stopwords.words('english')))
    else:
        return list()

    # Remove common suffixes, like s; Make all words present tense
    cleaned_vector = [lmr.lemmatize(lmr.lemmatize(i), 'v') for i in joined_str_vector]

    return cleaned_vector

def common_words(input_str, n = 10):
    """

    :param input_str: an abstract
    :param n: number of most common words
    :return:
    """

    if str(input_str) == 'nan':
        return [np.NaN]

    if not isinstance(n, int):
        raise ValueError("n must be an int")

    # Input Checks
    if not isinstance(input_str, str):
        return list(), list()
    if len(input_str) == 0:
        return list(), list()

    # Split the input
    split_input = cln(input_str).split(" ")

    # Remove white space and clean
    cleaned_input = word_vector_clean(split_input)

    to_count = [i for i in cleaned_input if not str(i).strip().isdigit()] +\
               [i for i in split_input if len(re.findall(r'[0-9]-.*', i)) != 0]

    # Return on an empty to_count list
    if len(to_count) == 0:
        return [np.NaN]

    # Compute the most common words (note: doesn't handle ties)
    top_common_words = np.array(FreqDist(to_count).most_common(n))

    return list(top_common_words[:,0]), list(top_common_words[:,1])










































