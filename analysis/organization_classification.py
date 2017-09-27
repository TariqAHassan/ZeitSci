"""

    Tools for Guessing the Category of an Organization
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""
import numpy as np
from itertools import permutations
from collections import defaultdict

# Heuristics for Classifying Organizations ('!' means ends with)
org_classes = {
    'Educational': ['Univ ',
                    'academy',
                    'agency',
                    'college',
                    'ecole',
                    'laboratory',
                    'observatory',
                    'polytechnic',
                    'polyteknik',
                    'school',
                    'universit'],
    'Governmental': ['Serv ',
                     'Servs ',
                     'Srvs ',
                     ' national',
                     'affairs',
                     'bureau',
                     'department',
                     'federal',
                     'services'],
    'Individual': [' phd ',
                   ' phd,',
                   '! phd',
                   'Dr.',
                   'Prof. '
                   "professor"
                   'MD',
                   'Miss.',
                   'Mr.',
                   'Mrs.'],
    'Industry': [' Corp',
                 '!Inc',
                 '!Inc.',
                 '!llc',
                 '!llc.',
                 '!ltd',
                 '!ltd.',
                 'Co. ',
                 'R&D',
                 'communications',
                 'company',
                 'consulting',
                 'corporation',
                 'incorporated',
                 'limited',
                 'radio',
                 'solutions',
                 'technologies',
                 'television'],
    'Institute': [' institut'],
    'Medical': ['clinic',
                ' dental',
                'dentistry',
                'health',
                'hospital',
                'medical',
                'physiotherapy',
                'rehabilitation'],
    'NGO': ['asociacion',
            'association',
            'foundation',
            'charity']
}

blocked_pairings = [
    ('Educational', 'Governmental'),
    ('Educational', 'Industry'),
    ('Educational', 'Individual'),
    ('Educational', 'NGO'),
    ('Governmental', 'Individual'),
    ('Governmental', 'Industry'),
    ('Governmental', 'NGO'),
    ('Individual', 'Industry'),
    ('Individual', 'Institute'),
    ('Individual', 'Medical'),
    ('Individual', 'NGO'),
]


def check_against(search_term, input_str):
    """

    String Matching
    :param search_term:
    :param input_str:
    :return:
    """
    if "!" == search_term[0]:
        if any(x.isupper() for x in search_term):
            return input_str.endswith(search_term[1:])
        else:
            return input_str.lower().endswith(search_term[1:])
    else:
        if any(x.isupper() for x in search_term):
            return search_term in input_str
        else:
            return search_term in input_str.lower()


def individual_name(input_str):
    """

    Determines if the input string is an individual's name.
    :param input_str:
    :return:
    """
    if "," in input_str:
        return []
    input_str_split = input_str.split(" ")
    if len(input_str_split) == 3 and \
            all([j[0].isupper() for j in [input_str_split[0], input_str_split[-1]]]) and \
                    len(input_str_split[1].replace(".", "").strip()) == 1:
        return ["Individual"]
    else:
        return []


def class_conflict_remover(candidate_classes):
    """

    Resolves conflicts between impossible combinations of categories (e.g., Governmental and NGO).
    (Somewhat tricky to write...but it appears to fuction properly).
    :param candidate_classes:
    :return:
    """
    class_permutations = list(permutations(candidate_classes.keys(), r=2))
    to_block = [i for i in class_permutations if i in blocked_pairings]

    if not len(to_block):
        return candidate_classes.keys()

    # Use number of values (whichever is smaller) for each category to
    # decide which of the two conflicted items to remove.
    # If the count is the same, default to the second entry.
    to_remove = set()
    for t in to_block:
        class_a = len(candidate_classes[t[0]])
        class_b = len(candidate_classes[t[1]])
        if class_a < class_b:
            to_remove.add(t[0])
        elif t[0] not in to_remove:
            to_remove.add(t[1])

    return [k for k in candidate_classes if k not in to_remove]


def organization_classifier(organization):
    """

    Classifies an organization as belonging to one (possibly more) of the keys in the org_classes dictionary.
    :param organization:
    :return:
    """
    # Check if 'organization' is actually an individual
    individual_check = individual_name(organization)

    if len(individual_check):
        org_class_list = individual_check
    else:
        # Search the organization string for markers for each category
        candidate_classes = defaultdict(list)
        for class_type, class_markers in org_classes.items():
            for search_term in class_markers:
                if check_against(search_term, organization):
                    candidate_classes[class_type] += [search_term]

        # Resolve conflicts
        org_class_list = sorted(class_conflict_remover(dict(candidate_classes)))

    if not len(org_class_list):
        return np.NaN

    return "; ".join(org_class_list)
