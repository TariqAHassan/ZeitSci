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
RTokenizer = RegexpTokenizer(r'\w+')

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

def word_vector_clean(input_str, RTokenizer=RTokenizer):
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
    lower_input_str = input_str.lower()

    # Tokenize to remove unimportant chars.
    lower_input_str = RTokenizer.tokenize(lower_input_str)

    # Remove stop words
    if len(lower_input_str) > 0:
        lower_input_str = list(set(lower_input_str) - set(stopwords.words('english')))
    else:
        return list()

    # Remove common suffixes, like s; Make all words present tense
    cleaned_vector = [lmr.lemmatize(lmr.lemmatize(i), 'v') for i in lower_input_str]

    return cleaned_vector

def common_words(input_str, n = 10, return_rank = True, digit_check = True, wrap_nans=True):
    """

    :param input_str: an abstract
    :param n: number of most common words
    :param return_rank:
    :param digit_check: block digits from being included
    :param wrap_nans:
    :return: a list of common words in the input_str (note: single letters are blocked)
    :rtpe: list
    """
    # Initialize
    to_count = list()

    if str(input_str) == 'nan':
        return [np.NaN] if wrap_nans else np.NaN

    if not isinstance(n, int):
        raise ValueError("n must be an int")

    # Input Checks -- CHANGE TO NANs (but check usage first).
    if not isinstance(input_str, str):
        return list(), list()
    if len(input_str) == 0:
        return list(), list()

    # Remove extra white space and clean
    cleaned_input = word_vector_clean(cln(input_str))

    if digit_check:
        to_count = [i for i in cleaned_input if not str(i).strip().isdigit() and len(str(i)) > 1] +\
                   [i for i in cln(input_str).split() if len(re.findall(r'[0-9]-.*', i)) != 0 and len(str(i)) > 1]
    else:
        to_count = cleaned_input

    # Return on an empty to_count list
    if len(to_count) == 0:
        return [np.NaN] if wrap_nans else np.NaN

    # Compute the most common words (note: doesn't handle ties)
    top_common_words = np.array(FreqDist(to_count).most_common(n))

    if return_rank:
        return list(top_common_words[:,0]), list(top_common_words[:,1])
    else:
        return list(top_common_words[:,0])










































