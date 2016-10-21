'''

Interactions with the OpenCage API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 3.5

'''

# ---------------- #
#  Import Modules  #
# ---------------- #

from time import sleep
from random import uniform

from supplementary_fns import cln, partial_match, partial_list_match
from opencage.geocoder import OpenCageGeocode


class ZeitOpenCage(object):
    """


    ZeitSci relavant tools for interacting with the OpenCage API.

    """

    def __init__(self, api_key = None):
        """

        :param key: an OpenSci API key; defaults to None.
        """

        if api_key == None:
            raise ValueError("An OpenCage API key must be supplied via api_key.")

        self.geocoder = OpenCageGeocode(key = api_key)

    def parser(self, result, request):
        """

        :param result: JSON from geocoder.geocode(query)
        :param request: 'address', 'geo' or 'conf', all --> formatted addgress, longditude, confidence, all three
        :return:
        """

        if len(result) == 0:
            raise ValueError("The result param is invalid")
        else:
            if request == 'address':
                return result[0]['formatted']
            if request == 'conf':
                return result[0]['confidence']
            if request == 'geo':
                return (result[0]['geometry']['lng'], result[0]["geometry"]["lat"])
            if request == 'all':
                loc_dict = {
                          'Address'     :  result[0]['formatted']
                        , 'Coordinates' : (result[0]['geometry']['lng'], result[0]["geometry"]["lat"])
                        , 'Confidence'  :  result[0]['confidence']
                }
                return loc_dict

    def lookup(self, query, request = 'all', double_check = False, min_conf = 1, sleep_bounds = (1, 3)):
        """

        TO CHANGE: double_check --> validate_list, e.g., ['Harvard', 'University', 'United States of America']

        :param query: the search term
        :param request: 'address', 'geo' or 'conf', all --> formatted addgress, (long, lat), confidence, all three
        :param double_check:
        :param min_conf:
        :param sleep_bounds: (min, max) wait time (select from a uniform probability density function).
        :return:
        """

        # Pause between calls
        sleep(uniform(sleep_bounds[0], sleep_bounds[1]))

        if cln(query, 2) == "":
            raise ValueError("query is an emptry string.")

        try:
            parse_return = self.parser(self.geocoder.geocode(query), request)
        except:
            return {}

        # Validate that the country is in the address.

        # Improve this check and/at least refactor the code...
        if double_check and "," in query and not \
                    partial_list_match(parse_return['Address'].lower(), \
                        [cln(i, 1).lstrip().rstrip().lower() for i in query.split(",")]) \
                   and int(parse_return["Confidence"]) < min_conf:
            return {}

        return parse_return




















