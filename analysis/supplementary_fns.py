

import re
import time
from itertools import chain

def pprint(string, n = 80):
    """
    Pretty print a string, breaking it in chucks on length n.
    """

    if not isinstance(string, str):
        raise ValueError("Input must be a string!")

    if len(string) < n:
        print(string)
    else:
        string_split = [string[i:i + n] for i in range(0, len(string), n)] # see http://stackoverflow.com/questions/9475241/split-python-string-every-nth-character
        for l in string_split:
            print(l.lstrip())

def lprint(input_list, tstep = None):
    """

    :param input_list:
    :return:
    """

    if isinstance(input_list, dict):
        for k, v in input_list.items():
            print(k, "  --->  ", v)

    if not isinstance(input_list, list) and not isinstance(input_list, dict):
        print(input_list)

    if len(input_list) == 0:
        print("--- Empty List ---")

    elif isinstance(input_list, list):
        for l in range(len(input_list)):
            if isinstance(tstep, int) or isinstance(tstep, float):
                time.sleep(tstep)
            print(str(l) + ":", input_list[l])

def cln(i, extent = 1):
    """

    String white space 'cleaner'.

    :param i:
    :param extent: 1 --> all white space reduced to length 1; 2 --> removal of all white space.
    :return:
    """

    if isinstance(i, str) and i != "":
        if extent == 1:
            return re.sub(r"\s\s+", " ", i)
        elif extent == 2:
            return re.sub(r"\s+", "", i)
    else:
        return i

    # else:
    #     return None
    #
    # if es:
    #     return to_return.lstrip().rstrip()
    # else:
    #     return to_return



def insen_replace(input_str, term, replacement):
    """

    String replace function which is insentiive to case

    replaces string regardless of case.
    see: http://stackoverflow.com/questions/919056/case-insensitive-replace

    :param input_str:
    :param term:
    :param replacement:
    :return:
    """

    disp_term = re.compile(re.escape(term), re.IGNORECASE)

    return disp_term.sub(replacement, disp[i]).lstrip().rstrip()

def partial_match(input_str, looking_for):
    """

    :param input_str:
    :param looking_for:
    :return:
    """

    if isinstance(input_str, str) and isinstance(looking_for, str):
        return cln(looking_for.lower(), 1) in cln(input_str.lower(), 1)
    else:
        return False

def partial_list_match(input_str, allowed_list):
    """

    :param input_str:
    :param allowed_list:
    :return:
    """

    allowed_list = [cln(i.lower(), 1).lstrip().rstrip() for i in allowed_list]

    for i in allowed_list:
        if partial_match(input_str = input_str, looking_for = i):
            return True

    return False

def endpoints_str(input, start, end = ","):
    """

    :param input:
    :param start:
    :param end:
    :return:
    """

    try:
        return cln(start + input[len(start):-len(end)],1).lstrip().rstrip()
    except:
        return None

def pandas_col_shift(data_frame, column, move_to = 0):
    """

    Please see Sachinmm's StackOverflow answer:
    http://stackoverflow.com/questions/25122099/move-column-by-name-to-front-of-table-in-pandas

    :param data_frame: a pandas dataframe
    :param column: the column to be moved
    :param move_to: position in df to move the column to; defaults to 0 (first)
    :return:
    """

    if not (0 <= move_to <= data_frame.shape[1]):
        raise AttributeError("Invalid move_to value.")

    if not isinstance(column, str):
        raise ValueError("the column was not provided as a string.")

    if column not in data_frame.columns.tolist():
        raise AttributeError("the dataframe has no column: %s." % (column))

    cols = data_frame.columns.tolist()
    cols.insert(move_to, cols.pop(cols.index(column)))

    return data_frame.reindex(columns = cols)


def items_present_test(input_list, clist):
    """

    Check if any of the items in clist are in input_list

    :param input_list: a list to look for them in
    :param clist: things you're looking for
    :return:
    """

    return any(x in input_list for x in clist)


def fast_flatten(input_list):
    return list(chain.from_iterable(input_list))

def multi_replace(input_str, to_remove):
    for tr in to_remove:
        input_str = input_str.replace(tr, "")
    return input_str

























