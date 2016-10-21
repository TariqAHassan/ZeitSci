"""

    Abstracted tools for Manipulating Databases for Graphing
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# Imports
import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from pprint import pprint
from funding_database_tools import MAIN_FOLDER

# ------------------------------------------------------------------------------------------------ #

def money_printer(money, currency=None, year=None, round_to=2):
    """

    Pretty Prints an Amount of Money.

    :param money: a numeric amount.
    :type money: float or int
    :param round_to: places to round to after the desimal.
    :type round_to: int
    """
    # Initialize
    money_to_handle = str(round(float(money), round_to))
    split_money = money_to_handle.split(".")
    to_return = None
    to_print = None

    if len(split_money[1]) == 1:
        to_return = money_to_handle + "0"
    elif len(split_money[1]) == 2:
        to_return = money_to_handle
    elif len(split_money[1]) > 2:
        to_return = ".".join([split_money[0], str(round(float(split_money[1]), -3))[:2]])
    else:
        raise ValueError("Invalid money conversion requested.")

    if currency != None or year != None:
        tail = (str(year) if year != None else '') + \
               (" " if isinstance(currency, str) and year != None else '') + \
               (str(currency) if isinstance(currency, str) else '')
        to_print = to_return + (" " + tail if isinstance(currency, str) and year == None else " (" + tail + ")")
    else:
        to_print = to_return

    return str(to_return)

def org_group(data_frame, additiona_cols=None):

    # Group by
    groupby_cols = ['Researcher', 'OrganizationBlock', 'lat', 'lng', 'NormalizedAmount', 'GrantYear'] +\
                   (additiona_cols if additiona_cols != None else [])
    df = data_frame.groupby(['OrganizationName']).progress_apply(
        lambda x: [x[c].tolist() for c in groupby_cols]).reset_index()

    for i in range(len(groupby_cols)):
        if i % 1000: print(i, "of", len(groupby_cols))
        df[groupby_cols[i]] = [df[0][r][i] for r in range(len(df))]
    del df[0]

    # Restrict DF
    df = df[df['Researcher'].astype(str).str.strip() != '[]'].reset_index(drop=True)

    df['lat'] = df['lat'].map(lambda x: x[0])
    df['lng'] = df['lng'].map(lambda x: x[0])
    df['Researcher'] = df['Researcher'].map(lambda x: list(set(x))[:5], na_action='ignore').str.join("<br>")
    df['NormalizedAmount'] = df['NormalizedAmount'].map(lambda x: sum(x),  na_action='ignore')
    df['OrganizationBlock'] = df['OrganizationBlock'].map(lambda x: "; ".join(list(set(x))), na_action='ignore')

    return df


