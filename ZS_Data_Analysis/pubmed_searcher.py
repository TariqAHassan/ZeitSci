'''

Creates a Search Construct for searching Pubmed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 3.5


Notes:
    Deceptive complexity...seemed simple at first.
    Still, try to refactor; a far simplier solution must be possible.

'''

# ---------------- #
#  Import Modules  #
# ---------------- #

from copy import deepcopy

# ------------------------------------------------------------------------- #
#           Procedure to get a Develop Pubmed Adv. Search String            #
# ------------------------------------------------------------------------- #


# Not needed as start date and end date should not be provided alone

# def single_search_term(search_dict):
#     """
#
#     :param search_dict:
#     :return:
#     """
#
#     search_param = list(search_dict.keys())[0]
#     search_candidate = list(search_dict.values())[0]
#     if search_param not in ["Start_Date", "End_Date"]:
#         search_term = search_candidate
#     elif search_param == "Start_Date":
#         search_term = "(" + "\"" + search_candidate + "\"" + "[Date - Publication] : \"3000\"[Date - Publication])"
#     elif search_param == "End_Date":
#         search_term = "(\"1800/01/01\"[Date - Publication] :" + "\"" + search_candidate + "\"" + "[Date - Publication])"
#
#     return search_term


def multi_search_term(search_dict):
    """

    :param search_dict:
    :return:
    """

    # Define Vars and Dict
    date_range = None
    search_dict_b = deepcopy(search_dict)
    if "Start_Date" in search_dict_b:
        search_dict_b.pop("Start_Date", None)
    if "End_Date" in search_dict_b:
        search_dict_b.pop("End_Date", None)

    # Constuct the Search Term for date range
    if "Start_Date" in search_dict and "End_Date" in search_dict:
        date_range = "(" + "\"" + search_dict["Start_Date"] + "\"" + "[Date - Publication] : " + \
                     "\"" + search_dict["End_Date"] + "\"" + "[Date - Publication])"
    elif ("Start_Date" in search_dict) and (not "End_Date" in search_dict):
        date_range = single_search_term({"Start_Date": search_dict["Start_Date"]})
    elif (not "Start_Date" in search_dict) and ("End_Date" in search_dict):
        date_range = single_search_term({"End_Date": search_dict["End_Date"]})

    # Constuct the Search Term for everything but the date information
    if date_range == None:
        non_date_search = [i + ")" for i in list(search_dict_b.values())[:-1]]
        search_term = "".join(["(" for i in range(len(non_date_search))]) + ' AND '.join(non_date_search) + \
                      " AND " + list(search_dict_b.values())[-1]
    elif date_range != None:
        non_date_search = [i + ")" for i in list(search_dict_b.values())]
        search_term = "".join(["(" for i in range(len(non_date_search))]) + ' AND '.join(non_date_search)

        # Combine with date_range
        search_term = " AND ".join([search_term, date_range])

    return search_term


def adv_search(  general = ""
               , title = ""
               , author = ""
               , journal = ""
               , grant_number = ""
               , start_date = ""
               , end_date = ""):

    """

    Note: this does not compare start_date with end_date.
          Be sure end_date > start_date


    :param general: a general search term
    :param title: the title of the paper
    :param author: the title of the paper(s)
    :param journal:
    :param grant_number:
    :param start_date: MUST be of the form 1993 (str or int) or 1993/12/31 (str)
    :param end_date:   MUST be of the form 2000 (str or int) or 2000/12/31 (str)
    :return:
    """

    # Absorb arguments into params() and check for invalid args.
    params = [general, title, author, journal, str(grant_number), str(start_date), str(end_date)]
    if params.count("") == 7:
        raise ValueError("At least one param must not be empty")
    if len(set(params[0:5])) == 1 and (params[6] != "" or params[7] != ""):
        raise ValueError("Invalid Search Definition: start and/or end dates cannot be provided alone.")

    # Cleanup input
    try:
        params = [str(i.strip()) for i in params]
    except:
        raise ValueError("At least one of the param is not a string")

    # Structure params in a "search term" dict.
    search_dict = {
          "General":      "" if params[0]  ==  "" else params[0]
        , "Title":        "" if params[1]  ==  "" else params[1] + "[Title]"
        , "Author":       "" if params[2]  ==  "" else params[2] + "[Author]"
        , "Journal":      "" if params[3]  ==  "" else "\"" + params[3] + "\"" + "[Journal]"
        , "Grant Number": "" if params[4]  ==  "" else params[4] + "[Grant Number]"
        , "Start_Date":   "" if params[5]  ==  "" else params[5]
        , "End_Date":     "" if params[6]  ==  "" else params[6]
    }

    # Clear our Empty Search Terms
    search_dict = {k: v for k, v in search_dict.items() if v != ""}

    if len(search_dict) == 1:
        search_term = list(search_dict.values())[0]
    elif len(search_dict) > 1:
        search_term = multi_search_term(search_dict)

    return search_term

















































