'''

This Script Extracts key data from the XML BioPython Returns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 3.5

'''


# ---------------- #
#  Import Modules  #
# ---------------- #


import re
import nltk
import numpy as np
import pandas as pd
from Bio import Entrez
from unidecode import unidecode
from nltk.corpus import stopwords
from supplementary_fns import pprint
from abstract_analysis import common_words
from abstract_analysis import word_vector_clean


# Make sure no nonalphanumeric chars can end up in any these, except for commas and '

# ------------------------------------------------------------------------- #
#                    Parse the above XML data in `papers`                   #
# ------------------------------------------------------------------------- #


class SummaryExtractor(object):
    """

     Procedure to Extract the following
     from a BioPython paper:
            1. Title
            2. Authors
            3. Institution
            4. Journal
            5. Month
            6. Year
            7. Keywords
            8. Abstract

    """

    def __init__(self, papers = None):

        self.papers = papers
        self.ordered_cols = [  "Title"
                             , "Authors"
                             , "Institution"
                             , "Journal"
                             , "Month"
                             , "Year"
                             , "Keywords"
                             , "Abstract"
                            ]

    # Extract the Authors
    def author_extractor(self, n):
        """

        :param n:
        :return:
        """

        try:
            author_list = self.papers[n]['MedlineCitation']['Article']['AuthorList']
        except:
            return list(), list()

        if len(author_list) == 0:
            return list(), list()

        author_names = list()
        author_insts = list()
        for a in range(len(author_list)):
            try:
                full_name = str(author_list[a]["ForeName"]) + " " + str(author_list[a]["LastName"])
            except:
                full_name = ""

            try:
                institution = str(author_list[a]["AffiliationInfo"][0]['Affiliation'])
                # Remove Emails, if present
                # see http://stackoverflow.com/questions/17681670/extract-email-sub-strings-from-large-document
                institution = re.sub(r'[\w\.-]+@[\w\.-]+', "",institution).replace("Electronic address:", "")
                institution = institution.replace("e-mail:", "").replace("email:", "").lstrip().rstrip()
            except:
                institution = ""

            author_names.append(full_name)
            author_insts.append(institution)

        return author_names, author_insts

    def pretty_cap(self, input_str):
        """

        Produces a clean capitlization of a title, e.g., a Journal's name.
        E.g.: 'USA Journal OF Apples And oranges' --> 'USA Journal of Apples and Oranges'

        Note: if a word is in all caps, it will be left as is.

        :param input_str:
        :return:
        """

        # note: doesn't seem to lower() 'And'...not clear why.

        # Clean the string by correcting spaces about a `:`
        input_str = re.sub(r'[\s+]?[:][\s+]?', ": ", input_str)

        # Remove spaces > length 1.
        input_str = re.sub(r"\s\s+", " ", input_str)

        # Split by a single space
        word_vector = input_str.split(" ")

        # Get stop words from the NLTK library
        stop_words_eng = stopwords.words('english')

        for w in range(len(word_vector)):
            if word_vector[w].lower() not in stop_words_eng and word_vector[w] != word_vector[w].upper():
                word_vector[w] = word_vector[w].lower().title()
            elif word_vector[w] in stop_words_eng and word_vector[w] != word_vector[w].upper():
                word_vector[w] = word_vector[w].lower()

        return " ".join(word_vector)

    # Get the Journal's Name + Publication Month & Year
    def journal_info_extractor(self, n):
        """

        :param n:
        :return:
        """

        # Somewhat clunky code, but there are many ways for this to break.

        try:
            journal_info = self.papers[n]['MedlineCitation']['Article']['Journal']
        except:
            return list(), list(), list()

        # Try to get the Journal Name
        try:
            journal_name = str(journal_info['Title']).lstrip().rstrip()

            # Remove info. after ; or : or =
            journal_name = re.sub(';.*|=.*', '', journal_name).lstrip().rstrip()

            # Clean up the Journal Name string
            journal_name = self.pretty_cap(journal_name)
        except:
            journal_name = ""

        # Try to get the Publication data Information
        try:
            pub_date = journal_info['JournalIssue']['PubDate']
            if isinstance(pub_date, dict) and len(pub_date.keys()) > 0:
                pub_date = {k.lower(): v for k, v in pub_date.items()}
                # see: http://stackoverflow.com/questions/30732915/convert-all-keys-of-a-dictionary-into-lowercase
            else:
                return journal_name, "", ""
        except:
            return journal_name, "", ""

        # Try to get the Publication Year
        try:
            year = pub_date['year']
        except:
            year = ""

        # Try to get the Publication Month
        try:
            month = pub_date['month']
        except:
            month = ""

        return journal_name, month, year

    # Extract the keywords provided in the paper, if any
    def keyword_extractor(self, n):
        """

        :param n:
        :return:
        """

        try:
            keywords = self.papers[n]['MedlineCitation']['KeywordList']
        except:
            return list()

        if len(keywords) == 0 or len(keywords[0]) == 0:
            return list()

        # Generate the list of keywords
        paper_keywords = list()
        for k in range(len(keywords[0])):
            keyword_list = str(keywords[0][k]).lower()
            paper_keywords.append(keyword_list)

        # Attempt to standardize the keywords
        # so keywords it's easier to relate keywords between papers
        paper_keywords = word_vector_clean(paper_keywords)

        return paper_keywords

    # Extract the abstract
    def abstract_extractor(self, n):
        """

        # Depreciate.

        :param abstract:
        :return:
        """

        try:
            abstract = self.papers[n]['MedlineCitation']['Article']['Abstract']['AbstractText']
        except:
            return("")

        if len(abstract) == 0:
            return("")

        full_abstract = ""
        for a in range(len(abstract)):
            if a == 0:
                full_abstract += str(abstract[a])
            else:
                full_abstract += " " + str(abstract[a])

            # Normalize the unicode
            #full_abstract = unidecode(str(abstract))
            full_abstract = unidecode(str(abstract[0]))             # recent change...

        return full_abstract

    def paper_row(self, n):
        """

        Corrdinates the parsing of the XML file.

        :param n: paper in papers, e.g., n = 2 for the second paper
        :return: a pandas data frame
        """

        if n >= len(self.papers):
            return None

        # Extract Title
        try:
            title = self.papers[n]['MedlineCitation']['Article']['ArticleTitle']
        except:
            title = ""

        # Extract Authors, and their Institutions
        authors, insts = self.author_extractor(n)

        # Extract the Journals' name & the publication month, year
        journal_name, month, year = self.journal_info_extractor(n)

        # Extract the paper's keywords
        keywords = self.keyword_extractor(n)

        # Extract the paper's abstract
        abstract = self.abstract_extractor(n)

        # Create temp df
        df_temp = pd.DataFrame(index = [n], columns = self.ordered_cols)

        # Perform an abstract analysis
        abstract_analysis = common_words(abstract)

        # Add dict to temp pandas df
        # Change to .loc
        df_temp["Title"][n]         =   title
        df_temp["Authors"][n]       =   np.array(authors)
        df_temp["Institution"][n]   =   np.array(insts)
        df_temp["Journal"][n]       =   journal_name
        df_temp["Month"][n]         =   month
        df_temp["Year"][n]          =   year
        df_temp["Keywords"][n]      =   np.array(keywords)
        df_temp["Abstract"][n]      =   abstract

        return df_temp




















































