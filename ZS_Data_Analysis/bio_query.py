'''

Gets all Scholarly work in the Life-Science
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 3.5

'''


# ---------------- #
#  Import Modules  #
# ---------------- #


from time import sleep
from random import uniform
from Bio import Entrez
from data_extractor import SummaryExtractor
from pubmed_searcher import adv_search


# ------------------------------------------------------------------------- #
#                   Procedure to get a paper from Pubmed                    #
# ------------------------------------------------------------------------- #


# Declare email to Pubmed
my_email = 'tariqaahassan@gmail.com'
tool_name = "ZeitSci"


def general_search(query, retmax):
    """

    from Marco Bonzanini. See: https://marcobonzanini.com/2015/01/12/searching-pubmed-with-python/

    :param query:
    :param retmax:
    :return:
    """

    Entrez.email = my_email
    Entrez.tool = tool_name
    try:
        handle = Entrez.esearch(  db = 'pubmed'
                                , sort ='relevance'
                                , retmax = str(retmax)
                                , retmode = 'xml'
                                , term = query)
        results = Entrez.read(handle)
    except:
        return None

    return results


def fetch_details(id_list):
    """

    from Marco Bonzanini. See: https://marcobonzanini.com/2015/01/12/searching-pubmed-with-python/

    # Add more error handling!

    :param id_list:
    :return:
    """

    if id_list == None:
        return id_list

    # Add Error Handling here #

    Entrez.email = my_email
    Entrez.tool = tool_name

    ids = ','.join(id_list)
    handle = Entrez.efetch(db='pubmed',
                           retmode='xml',
                           id=ids)
    results = Entrez.read(handle)

    return results


def paper_extract(  search_term = ""
                  , retmax = 1
                  , title = ""
                  , author = ""
                  , journal = ""
                  , start = ""
                  , end = ""
                  , grant_number = ""
                  , sleep_bounds = [0.5]):
    """

    Adapted from code by Marco Bonzanini. See: https://marcobonzanini.com/2015/01/12/searching-pubmed-with-python/

    # Add more error handling!

    :param search_term: a string
    :param retmax:
    :param title:
    :param author:
    :param start:
    :param end:
    :param grant_number:
    :param sleep_bounds: defaults to waiting 0.5 seconds
    :return:
    """

    if len(sleep_bounds) == 1:
        sleep(sleep_bounds[0])
    elif len(sleep_bounds) == 2:
        sleep(uniform(sleep_bounds[0], sleep_bounds[1]))
    else:
        raise ValueError("sleep_bounds is invalid")

    if title == author == journal == start == end == grant_number == "":
        if search_term != "":
            results = general_search(search_term, retmax)
        else:
            raise ValueError("search_term cannot be left to its default!")
    else:
        search_term = adv_search(  general = search_term
                                 , title = title
                                 , author = author
                                 , journal = journal
                                 , start_date = start
                                 , end_date = end
                                 , grant_number = grant_number)
        results = general_search(search_term, retmax)

    id_list = results['IdList']
    papers = fetch_details(id_list)

    return papers














































