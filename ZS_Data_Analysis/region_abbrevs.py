
# North America #

US_states = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FM': 'Federated States of Micronesia',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MH': 'Marshall Islands',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PR': 'Puerto Rico',
        'PW': 'Palau',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
}

Canada_prov_terr = {
    'AB': 'Alberta',
    'BC': 'British Columbia',
    'MB': 'Manitoba',
    'NB': 'New Brunswick',
    'NL': 'Newfoundland and Labrador',
    'NT': 'Northwest Territories',
    'NS': 'Nova Scotia',
    'NU': 'Nunavut',
    'ON': 'Ontario',
    'PE': 'Prince Edward Island',
    'QC': 'Quebec',
    'SK': 'Saskatchewan',
    'YT': 'Yukon'
}

Australian_states = {
      "ACT" : "Australian Capital Territory"
    , "NSW" : "New South Wales"
    , "NT"  : "Northern Territory"
    , "QLD" : "Queensland"
    , "SA"  : "South Australia"
    , "TAS" : "Tasmania"
    , "VIC" : "Victoria"
    , "WA"  : "Western Australia"
}


# Partyly obtained with this:
# (corrected by hand)
# zoc = ZeitOpenCage(api_key = OPENCAGE_KEY)
# aus_uni_dict = dict.fromkeys([i + " (Australia)" for i in aus_df.administering_institution.unique().tolist()], "")
# for k, v in aus_uni_dict.items():
#     aus_uni_dict[k] = zoc.lookup(k, request = 'address')


Australia_Inist_Cities = {
      'Charles Darwin University'                 : 'Darwin'
    , 'Royal Melbourne Institute of Technology'   : 'Melbourne'
    , 'James Cook University'                     : 'Cairns' #
    , 'Australian National University'            : 'Canberra'
    , 'Curtin University of Technology'           : 'Perth'
    , 'Australian Catholic University'            : 'Brisbane'
    , 'University of Canberra'                    : 'Canberra'
    , 'Edith Cowan University'                    : 'Perth'
    , 'University of Western Australia'           : 'Perth'
    , 'University of Western Sydney'              : 'Sydney'
    , 'University of Southern Queensland'         : 'Toowoomba'
    , 'University of South Australia'             : 'Adelaide'
    , 'University of Tasmania'                    : 'Hobart'
    , 'Swinburne University of Technology'        : 'Melbourne'
    , 'Griffith University'                       : 'Brisbane'
    , 'University of the Sunshine Coast'          : 'Sunshine Coast'
    , 'Bond University'                           : 'Gold Coast'
    , 'University of Adelaide'                    : 'Adelaide'
    , 'University of New England'                 : 'Armidale'
    , 'Macquarie University'                      : 'Sydney'
    , 'Monash University'                         : 'Melbourne'
    , 'University of Newcastle'                   : 'Newcastle'
    , 'Murdoch University'                        : 'Perth'
    , 'University of Technology, Sydney'          : 'Sydney'
    , 'The University of Western Australia'       : 'Perth'
    , 'University of Sydney'                      : 'Sydney'
    , 'University of New South Wales'             : 'Sydney'
    , 'Central Queensland University'             : 'Berserker'
    , 'La Trobe University'                       : 'Victoria'
    , 'Victoria University of Technology'         : 'Victoria'
    , 'Victoria University'                       : 'Victoria'
    , 'University of Melbourne'                   : 'Melbourne'
    , 'University of Wollongong'                  : 'Wollongong'
    , 'University of Technology Sydney'           : 'Sydney'
    , 'Queensland University of Technology'       : 'Brisbane'
    , 'RMIT University'                           : 'Melbourne'
    , 'University of Queensland'                  : 'Brisbane'
    , 'Deakin University'                         : 'Victoria'
    , 'Northern Territory University'             : 'Darwin'
 }


European_Countries = {
          'AL': 'Albania'
        , 'AT': 'Austria'
        , 'BE': 'Belgium'
        , 'BG': 'Bulgaria'
        , 'HR': 'Croatia'
        , 'CY': 'Cyprus'
        , 'CZ': 'Czech Republic'
        , 'DK': 'Denmark'
        , 'EE': 'Estonia'
        , 'FI': 'Finland'
        , 'FR': 'France'
        , 'DE': 'Germany'
        , 'EL': 'Greece'
        , 'HU': 'Hungary'
        , 'IS': 'Iceland'
        , 'IE': 'Ireland'
        , 'IT': 'Italy'
        , 'LV': 'Latvia'
        , 'LI': 'Liechtenstein'
        , 'LT': 'Lithuania'
        , 'LU': 'Luxembourg'
        , 'MD': 'Moldova'
        , 'MK': 'Macedonia'
        , 'MT': 'Malta'
        , 'ME': 'Montenegro'
        , 'NL': 'Netherlands'
        , 'NO': 'Norway'
        , 'PL': 'Poland'
        , 'PT': 'Portugal'
        , 'RO': 'Romania'
        , 'RS': 'Serbia'
        , 'SK': 'Slovakia'
        , 'SI': 'Slovenia'
        , 'ES': 'Spain'
        , 'SE': 'Sweden'
        , 'CH': 'Switzerland'
        , 'TR': 'Turkey'
        , 'UK': 'United Kingdom'
}














































































































































