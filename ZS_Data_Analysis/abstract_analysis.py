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
from nltk import FreqDist
from langdetect import detect
from nltk.corpus import stopwords
from supplementary_fns import cln
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer


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

    # Initialize NLTK's WordNetLemmatizer
    lmr = WordNetLemmatizer()

    # Make all chars lower case
    str_vector = " ".join([i.lower() for i in str_vector])

    # Tokenize to remove unimportant chars.
    str_vector = RegexpTokenizer(r'\w+').tokenize(str_vector)

    # Remove stop words
    if len(str_vector) > 0:
        str_vector = list(set(str_vector) - set(stopwords.words('english')))
    else:
        return list()

    # Remove common suffixes, like s
    cleaned_vector = [lmr.lemmatize(i) for i in str_vector]

    # Make all words present tense
    cleaned_vector = [lmr.lemmatize(i, 'v') for i in cleaned_vector]

    return cleaned_vector

def common_words(input_str, n = 10):
    """

    :param input_str: an abstract
    :param n: number of most common words
    :return:
    """

    if not isinstance(n, int):
        raise ValueError("n must be an int")

    # Input Checks
    if not isinstance(input_str, str):
        return list(), list()
    if len(input_str) == 0:
        return list(), list()

    # Remove white space
    input_str = cln(input_str).split(" ")

    # Clean the unput with the word_vector_clean() method
    cleaned_input = word_vector_clean(input_str)

    # Compute the most common words (note: doesn't handle ties)
    top_common_words = dict(FreqDist(cleaned_input).most_common(n))

    return list(top_common_words.keys()), list(top_common_words.values())










































