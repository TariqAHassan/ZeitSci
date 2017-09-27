"""

    Wikipedia Information
    ~~~~~~~~~~~~~~~~~~~~~

"""
import datetime
import os
import re
import time
import urllib
import urllib.request as urllib2
from random import uniform

import lxml.etree
import numpy as np
from fuzzywuzzy import fuzz
from nltk.corpus import stopwords

from analysis.supplementary_fns import cln
from analysis.my_keys import WIKI_USER_AGENT, MAIN_FOLDER

# TO DO:
# - Clean up imports
# - import currency abbres.

# Get the current dir
# current_dir = os.getcwd()

# Move over to the data folder
os.chdir(MAIN_FOLDER + "/Data")


# Change back to orig. dir.
# os.chdir(current_dir)


def wiki_complete(title):
    """

    # Note: this cannot handle redirects

    :param title:
    :return:
    """

    # Wait 1-2 seconds between requests
    time.sleep(uniform(1.5, 3.5))

    params = {"format": "xml",
              "action": "query",
              "prop": "revisions",
              "rvprop": "timestamp|user|comment|content"}

    # See: provide source!

    # Construct the URL
    params["titles"] = "API|%s" % urllib.parse.quote(title.encode("utf8"))
    qs = "&".join("%s=%s" % (k, v) for k, v in params.items())
    url = "http://en.wikipedia.org/w/api.php?%s" % qs

    # Make a request
    req = urllib.request.Request(url, headers={'User-Agent': WIKI_USER_AGENT})
    page = urllib.request.urlopen(req)

    # Parse the returned xml
    tree = lxml.etree.parse(page)
    revs = tree.xpath('//rev')

    # Get the Raw page
    raw_page = revs[-1].text

    # Remove spaces > length 1.
    raw_page = re.sub(r"\s\s+", " ", raw_page)

    return raw_page


def sw_remove(input_string):
    """

    :param input_string:
    :return:
    """

    input_string = cln(input_string, 1)

    return " ".join([w for w in input_string.split(" ") if w not in stopwords.words('english')])


def wiki_complete_get(title, allow_redirect=True, similarity_threshold=90):
    """

    :param title: the title of the wikipedia page desired.
    :param allow_redirect: allow attempt to handle wikipedia page redirects
    :param similarity_threshold: 0-100; similarity of redirect page to the title agrument (uses the fuzzywuzzy package).
    :return:
    """

    title = cln(title, 1)

    raw_page = wiki_complete(title=title)
    redirect_pages = None
    new_title = None

    # Nothing useful can be obtained from this, return ""
    if "Application programming interface" in cln(raw_page, 1):
        return ""

    # If it was a redirect
    if allow_redirect:

        if "#REDIRECT" in cln(raw_page, 2):

            # assess number of redirect titles present
            if cln(raw_page, 2).count("[[") == 1 and cln(raw_page, 2).count("]]") == 1:
                redirect_pages = re.findall(re.compile(".*?\[\[(.*?)\]\]"), raw_page)

                # double check there is only only redirect wiki page title, if so, save it to new_title
                if len(redirect_pages) == 1:
                    new_title = cln(redirect_pages[0].replace("_", " "), 1).lstrip().rstrip()

                    # Review the similarity between the orig. request and the new title
                    if fuzz.ratio(sw_remove(title), sw_remove(new_title)) > similarity_threshold:
                        raw_page = wiki_complete_get(title=new_title)

    return raw_page.lower()


def property_extractor(raw_page, start, end="", easy=True, anumeric=True, ws_complete=True, csplit=False):
    """

    :param raw_page: a raw wikipedia page, as extracted by wiki_complete_get()
    :param start: start of the parse
    :param end: end of the parse
    :param easy: construct the compete start and end bounds
    :param anumeric: treat output as soley alpha-numeric (i.e., remove all nonalpha-numeric chars.)
    :param ws_complete: if True, remove all white space; if False reduce all white spaces to length 1
    :param csplit: split into a list by comma
    :return:
    """

    # Construct the start and end, based on @start alone
    if easy:
        start = "| " + start.lower() + " ="
        end = "|"

    # Try to get the information between start and end
    try:
        page_property = raw_page.split(start)[-1].split(end)[0]  # see:
    except:
        return ""

    # Only keep alphanumeric chars (and commas)
    if anumeric:
        page_property = re.sub(r'[^a-zA-Z0-9,]', ' ', page_property).lower().title()
    else:
        page_property = page_property.lstrip().rstrip().title()

    # Remove all white space
    if ws_complete:
        page_property = re.sub(r"\s", "", page_property)
    else:
        page_property = re.sub(r"\s\s+", " ", page_property).lstrip().rstrip()

    # Split by comma
    if csplit:
        page_property = page_property.split(",")

        # Remove extra white space
        page_property = [p.lstrip().rstrip() for p in page_property]

    return page_property


def clean_extract(input_str):
    """

    If the extracted information contains anything but alphanumeric, underscores,
    commas, ampersand, colons or a peroid, assume the extracted information is junk

    :param input_str:
    :return: input_str if OK; "" otherwise.
    """

    try:
        if input_str == None:
            return ("")
        if any(x in str(input_str).lower() for x in ["{", "}"]):
            return ("")
        if re.match('^[a-zA-Z0-9_,&:.]+$', str(input_str)) == None or re.match('^[0-9.]+$', str(input_str)) != None:
            to_return = str(input_str).replace("[", "").replace("]", "").replace("'", "")
            return (str(to_return))
        else:
            return ("")
    except:
        return ("")


def journal_specs(raw_page):
    """

    :param raw_page:
    :return:
    """

    # Get the Journal's abbreviation journal_abbrev =
    journal_abbrev = clean_extract(
        property_extractor(raw_page, start='abbreviation', anumeric=False, ws_complete=False))

    # Try to get the journal's discipline
    journal_discipline = clean_extract(property_extractor(raw_page, start='discipline', ws_complete=False, csplit=True))

    # It is also sometimes called 'categories'...standards...
    if journal_discipline == "":
        journal_discipline = clean_extract(
            property_extractor(raw_page, start='categories', ws_complete=False, csplit=True))

    # Try to get the journal's impact
    impact = clean_extract(property_extractor(raw_page, start='impact', anumeric=False))

    # Try to get the journal's impact-year
    impact_year = clean_extract(property_extractor(raw_page, start='impact-year', anumeric=False))

    return journal_abbrev, journal_discipline, impact, impact_year


def journal_lookup(jname):
    """

    :param jname:
    :return:
    """

    at_least_one_of = ["abbreviation", "discipline", "categories", "impact", "impact-year"]

    try:
        raw_page = wiki_complete_get(jname)
        if not any(s in str(raw_page).lower() for s in at_least_one_of):
            return ["VOID", "VOID", "VOID", "VOID"]
    except:
        return None

    return list(journal_specs(raw_page))


# def is_digit_test(input_string, remove_peroid = True):
#     """
#
#     :param input_string:
#     :param remove_peroid:
#     :return:
#     """
#
#     if remove_peroid:
#         input_string = input_string.replace(".", "")
#
#     return all(char.isdigit() for char in input_string)


class WikiUniversities(object):
    """

    Class for extract a Universty's: Endowment, [log,width] and whether it's public or private.

    """

    def __init__(self, iso_currencies=None):
        self.ccdf = iso_currencies
        self.money_denoters = ['billion', 'million', 'hundred thousand', 'hundred-thousand']
        # self.UnitedKingdom = ["England", "Northren Ireland", "Wales", "Scotland"]

    def dms2des(self, dms):
        """

        Degree, Minutes, Seconds --> Decimal Degrees

        :param dms: lists; [degrees, minutes, seconds]; this function checks if all entries are floats.
        :return: decimal Degrees
        """

        if len([i for i in dms if isinstance(i, (float, int))]) != 3:
            return None

        deg = dms[0]
        min = dms[1]
        sec = dms[2]

        return (float(deg)) + (float(min) / 60.0) + (float(sec) / 3600.0)

    def try_float(self, input_str):
        """

        :param input_str:
        :return:
        """
        try:
            float(cln(input_str, 2))
            return True
        except:
            return False

    def dash_correct(self, input_str):
        """

        :param input_str:
        :return:
        """
        neg_count = str(input_str).count("-")
        if neg_count == 0:
            return input_str
        if neg_count in [0, 1] and input_str[0] == '-':
            return input_str
        elif neg_count == 1 and input_str[0] == '-':
            return input_str
        elif neg_count >= 1 and input_str[0] != '-':
            return input_str.replace("-", "")
        elif neg_count > 1 and input_str[0] == '-':
            return "-" + input_str.replace("-", "")

    def twoDlist_to_dec(self, coordinates, raw_cords=None):
        """
        Adds Direction information to Coords.

        :param coordinates: processed coordinates
        :param coordinates: raw extract from raw_page.
        :return:
        """
        dec_result = None
        if raw_cords != None:
            dirs = list(map(str.lower, filter(lambda x: x.strip().lower() in ['n', 'w', 's', 'e'], raw_cords)))
            dirs = [cln(x, 2) for x in dirs]
            height_scalar = -1 if 's' in dirs else 1
            width_scalar = -1 if 'w' in dirs else 1
        else:
            width_scalar = height_scalar = 1

        try:
            if np.array(coordinates).shape == (2, 3):
                height_width = [self.dms2des(coordinates[0]), self.dms2des(coordinates[1])]
                if len(list(filter(None, height_width))) == 2:
                    dec_result = [height_width[0] * height_scalar, height_width[1] * width_scalar]
            elif len(coordinates) == 2 and all(isinstance(i, (float, int)) for i in coordinates):
                dec_result = [coordinates[0] * height_scalar, coordinates[1] * width_scalar]
        except:
            return None

        return dec_result

    def x_degrees_extractor(self, raw_page):
        """

        Yet another format on wikipedia for GIS info.
        Very uninspired code...but this is becoming very tedious and dull...

        Regex from: http://stackoverflow.com/a/3368993/4898004.

        :param raw_page:
        :return:
        """
        geo_info = dict()
        raw_page_cln_whited_space = str(cln(raw_page, 2))
        terms = ["degrees", 'minutes', 'seconds', 'direction']
        look_for = [[y + "_" + x + "=" for x in terms] for y in ['lat', 'long']]
        look_for_flat = [i for s in look_for for i in s]

        end = "|"
        for s in look_for_flat:
            try:
                term = re.findall(re.escape(s) + "(.*)" + re.escape(end), raw_page_cln_whited_space)[0].split(end)[0]
            except:
                return None
            if "direction" not in s:
                try:
                    geo_info[s.replace("=", "")] = int(term)
                except:
                    return None
            else:
                geo_info[s.replace("=", "")] = term

        height_scalar = -1 if 's' in geo_info['lat_direction'] else 1
        width_scalar = -1 if 'w' in geo_info['long_direction'] else 1

        try:
            coords = [
                self.dms2des(
                    [geo_info['lat_degrees'], geo_info['lat_minutes'], geo_info['lat_seconds']]) * height_scalar,
                self.dms2des(
                    [geo_info['long_degrees'], geo_info['long_minutes'], geo_info['long_seconds']]) * width_scalar
            ]
            return coords
        except:
            return None

    def wiki_coords_extractor(self, raw_page, start="{{coor"):
        """

        This function tries to get coordinates (long/lat) from a wikipedia page.

        Note:
            While a bit of effort has gone towards to make this procedure a juggernaut,
            this data can take many different forms on wikipedia.
            Thus, unconsidered forms are likely to defeat this algorithm, and thus the function
            will fail to return any coordinate information.

        :param start: where to start the extract from the raw page. Defaults to "{{coor".
        :param raw_page: a raw wikipedia page as extract by wiki_complete_get().
        :return: the [longtitude, latitude] from a wikipedia page in decimal degrees.
        """
        dms = ""
        temp = list()
        height_width = list()
        coordinates = list()
        specified_dms = ["lat" + p for p in [i + "=" for i in ['d', 'm', 's']]] + \
                        ["long" + p for p in [i + "=" for i in ['d', 'm', 's']]]

        try:
            coord = raw_page.split(start)[-1].split("}}")[0].replace("{{", "").split("|")
        except:
            return None

        # 1. Try to get Degrees, Minutes and Seconds
        for c in coord:
            if self.try_float(c):
                height_width.append(float(cln(c, 2)))
            if cln(c.lower(), 2) in ['n', 'w', 's', 'e'] and len(height_width) == 3:
                coordinates.append(height_width)
                height_width = []

        # If 1. worked, convert the answer into decimal degrees and return
        if np.array(coordinates).shape == (2, 3):
            return self.twoDlist_to_dec(coordinates, coord)

        # 2. if 1. doesn't work, look for all of (latd, latm, lats) and (longd, longm, longs)
        if all(x in cln(raw_page, 2) for x in specified_dms):
            print(raw_page)
            print("^Could be backwards...check.")
            for s in specified_dms:
                dms = self.dash_correct(re.sub(r'[^-?+?0-9.]', "", cln(cln(raw_page, 2).split(s)[-1].split("|")[0]), 2))
                if dms.count(".") <= 1 and self.try_float(dms):
                    temp.append(float(dms))
                if s[-2] == "s":
                    coordinates.append(temp)  # flip? [::-1]
                    temp = list()

        # If 2 worked, convert the answer (as above) and return
        if np.array(coordinates).shape == (2, 3):
            return self.twoDlist_to_dec(coordinates)

        # 3. If 2. also doesn't work, try to extract decimal degrees
        if len(coordinates):  # Clear above attempt
            coordinates = list()

        for c in coord:
            if "." in c and self.try_float(c):
                coordinates.append(float(cln(c, 2)))

        # Check attempt 3. for Success or failure.
        if len(coordinates) == 2:
            return self.twoDlist_to_dec(coordinates, raw_cords=coord)
        else:
            coordinates = list()

        # Attempt 4.
        coordinates = self.x_degrees_extractor(raw_page)
        if coordinates != None and len(coordinates) == 2:
            return coordinates
        else:
            return None  # give up

    def money_scale_denoters(self, input_str):
        """

        :param input_str:
        :return:
        """
        denoters_found = []
        for md in self.money_denoters:
            if md in input_str.lower():
                denoters_found.append(md)

        if len(denoters_found) != 1:
            return None

        return denoters_found[0]

    def money_str_parser(self, input_str):
        """

        E.g., "$300.234 <Billions!>[1] Euro8383822s *#*<<>3838w<1>><><ref>"  --->  "300.2 billons"

        Expects year, e.g., (2015) and note, e.g., [1] information has been cleaned,
        though it should generally be robust against those additions.

        :param input_str:
        :return:
        """

        # Note: there may be cases such as: "0.3 billion"...though, no such examples could be found
        # if so, they would break this procedure.

        # Remove all nonnumeric chars (except a peroid).
        try:
            input_str = cln(re.sub("[^0-9.]", "", input_str), 2)
        except:
            return None

        # Try to convert it into
        # an int, e.g., 96, --> float --> str for output
        if "." not in input_str:
            try:
                return str(float(int(cln(input_str, 2))))
            except:
                pass

        # Try the input as a float next
        elif "." in input_str and input_str.count(".") == 1 and len(
                [cln(i, 2) for i in input_str.split(".") if cln(i, 2) != 0]) == 2:

            if cln(input_str.split(".", 1)[1], 2) == '0':
                return None  # See above note

            input_str = input_str.split(".", 1)[0] + "." + input_str.split(".", 1)[1][0]
        else:
            return None  # lowers risk of a bad return, at a very small potential completeness cost.

        # Try to convert to a string
        try:
            input_str = str(input_str)
        except:
            return None

        # Return a string
        return cln((input_str), 2).lstrip().rstrip()

    def currency_lookup(self, input_str, common_currencies, region=None, assume_USD=True):
        """

        :param input_str:
        :param common_currencies: the popular_ISO_currencies.csv file as a pandas dataframe.
        :param assume_USD: assume $ = USD
        :return:
        """

        if self.ccdf.columns.tolist() != ['Name', 'ISO', 'Symbol', "Region"]:
            raise AttributeError("the common_currencies columns must be in the follow"
                                 "order: Name, ISO, Symbol. Make sure to use popular_ISO_currencies.csv"
                                 "in the ZeitSci data folder.")

        # if region is provided, try to return the ISO code
        if region != None:
            try:
                return self.ccdf.ISO[self.ccdf['Region'] == region].tolist()[0]
            except:
                pass

        # Initialize
        currency = ""
        symbol_ignore = ["Fr", "kr", "R", "R$"]  # not clear if the last entry causes problems with USD, CAN, AUD, etc.

        # first try name, then ISO and lasly, symbol
        cc = 0
        currency_info_type = ""
        found = False
        while not found and cc < 3:
            for n in self.ccdf[self.ccdf.columns[cc]].tolist():
                if n.upper() in input_str.upper() and n.upper() not in symbol_ignore:
                    currency_info_type = self.ccdf.columns[cc]
                    currency = n
                    found = True  # end the while loop
                    break  # end the for loop
            cc += 1

        # Return if no currency info found
        if currency == "":
            return None

        # if Assume '$' == 'USD', return 'USD'
        if assume_USD and currency == "$":
            return "USD"

        # Return none if it's unclear what currency the symbol corresponds to.
        if currency in self.ccdf.Symbol.tolist():
            if self.ccdf.Symbol.tolist().count(currency) > 1:
                return None

        # Get ISO entry, if other type.
        if currency_info_type != 'ISO':
            return self.ccdf.ISO[self.ccdf[currency_info_type] == currency].tolist()[0]
        elif urrency_info_type == 'ISO':
            return currency
        else:
            return None

    def currency_convert(self, endowment_dict):
        """

        :param endowment_list:
        :return: returns a dict with nominal endowment info (not adjusted for infwidthion).
        """

        num_scale = 1
        scaled_curr = 0

        if len([i for i in endowment_dict.values() if isinstance(i, str) and cln(i, 2) != ""]) != 4:
            return None

        if endowment_dict["scale"] == self.money_denoters[0]:
            num_scale = 1000000000.0
        if endowment_dict["scale"] == self.money_denoters[1]:
            num_scale = 1000000
        if endowment_dict["scale"] in self.money_denoters[2:4]:
            num_scale = 100000.0

        if self.try_float(cln(endowment_dict['amount'], 2)):
            scaled_curr = float(cln(endowment_dict['amount'], 2)) * num_scale
        else:
            return None

        try:
            return [scaled_curr, endowment_dict["currency"], endowment_dict["year"]]
        except:
            return None

    def endowment_extractor(self, raw_page, region=None, start="{{"):
        """

        :param raw_page:
        :param start:
        :return:
        """

        money_scale = ""
        em = ""

        try:
            endmt = [i for i in raw_page.split(start) if "|endowment=" in cln(i, 2)]
            if len(endmt) != 1:
                return None
            else:
                endmt = endmt[0].split('endowment', 1)[-1].replace("endowment = ", "").lstrip().rstrip()
        except:
            return None

        # Try to get year information
        if endmt.count("(") == endmt.count(")") == 1:
            braceless_info = re.findall(re.compile(".*?\((.*?)\)"), endmt)
            if len(braceless_info) == 1 and self.try_float(braceless_info[0]):
                em = int(cln(braceless_info[0], 2))
                endmt = endmt.replace("(" + cln(braceless_info[0], 2) + ")", "")

        # Try to get the scale of the money
        scale = self.money_scale_denoters(endmt) if isinstance(self.money_scale_denoters(endmt), str) else ""

        if scale == "":
            return None

        # remove everything to the right of the money scale, i.e., billion.
        endmt = cln(endmt.split(scale)[0]).lstrip().rstrip()

        # get currency
        amount = self.money_str_parser(input_str=endmt)
        currency = self.currency_lookup(endmt.split(amount)[0], common_currencies=self.ccdf, region=region)

        endowment = {"amount": amount
            , "scale": scale
            , "year": str(em) if str(em) != "" else str(datetime.datetime.now().timetuple()[0])  # "" == current.
            , "currency": currency}

        try:
            return self.currency_convert(endowment)
        except:
            return None

    def inst_type(self, raw_page):
        """

        Gets whether the Inst. is Public or Private

        :param raw_page:
        :return:
        """

        # what to look for if Case A
        looking_for_a = ['[private', '[public']

        # what to look for if Case B
        looking_for_b = ['private]', 'public]']

        # Try to Extract
        try:
            itype = [i for i in raw_page.split("|") if "type=" in cln(i, 2)]  # split on "|"

            if len(itype) != 1:

                if any(x in cln(itype[0], 2) for x in looking_for_a):
                    itype = itype[0]

                # if that failed, try this:
                elif not any(x in cln(itype[0], 2) for x in looking_for):
                    itype = [i for i in raw_page.split("]]|") if "type=" in cln(i, 2)]  # split on "]]|"
                    if len(itype) != 1:

                        if any(x in cln(itype[0], 2) for x in looking_for_b):
                            itype = itype[0]
                        else:
                            return None
            else:
                itype = itype[0]
        except:
            return None

        # Label result.
        if 'public' in itype.lower():
            return 'Public'
        elif 'private' in itype.lower():
            return 'Private'
        else:
            return None

    def university_information(self, wiki_page_title, region=None, allow_redirect=True, similarity_threshold=90):
        """


        :param raw_page: a page extracted by wiki_complete_get()
        :param region: The region of the university, e.g., Canada.
                       This information is  * not *  extacted from wikipedia page and should be supplied
                       manually for the most relable endowment information. Defaults to None.
        :return: a dictionary with institution_type, longitude, latitude and endowment information.
        """
        # Create the dict
        institution_data = {"institution_type": "", "lng": "", "lat": "", "endowment": ""}

        if wiki_page_title in ["", "nan", "NaN", None, np.nan]:
            return institution_data

        # Ensure the first letter is a capital -- this a standard on wikipedia.
        if wiki_page_title != wiki_page_title[0].capitalize() + wiki_page_title[1:]:
            wiki_page_title = wiki_page_title[0].capitalize() + wiki_page_title[1:]

        try:
            raw_page = wiki_complete_get(title=wiki_page_title
                                         , allow_redirect=allow_redirect
                                         , similarity_threshold=similarity_threshold)
            if "infobox" not in raw_page:  # not a perfect heuristic...
                return None
        except:
            return None

        # Extract the infomation from the page
        institution_type = self.inst_type(raw_page)
        location = self.wiki_coords_extractor(raw_page)
        endowment = self.endowment_extractor(raw_page, region)

        # Add to dict
        institution_data["institution_type"] = institution_type if institution_type != None else ""
        institution_data["lat"] = location[0] if location != None and None not in location else ""
        institution_data["lng"] = location[1] if location != None and None not in location else ""
        institution_data["endowment"] = endowment if endowment != None else ""

        return institution_data
