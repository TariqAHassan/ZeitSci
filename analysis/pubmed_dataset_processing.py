"""

    Script to Convert XML Files --> Pandas DataFrame
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Rerun

"""
import os
import numpy as np
import pandas as pd
from itertools import chain
from analysis.supplementary_fns import fast_flatten
import analysis.pubmed_parser_master.pubmed_parser as pp
# from multiprocessing.dummy import Pool as ThreadPool
from tqdm import tqdm

# Multithread
# p = ThreadPool(3)

PATH = '/Users/tariq/Desktop/MedlineData'

xml_file_range = (440, np.inf)  # 440-all (812); 1999-2015. 372 files to process (11,160,000 articles)
files = [os.path.join(PATH, f) for f in os.listdir(PATH) if "xml.gz" in f.lower()]
xml_files = [x for x in files if xml_file_range[0] <= float(x.split("/")[-1].split('.')[0][-4:]) <= xml_file_range[1]]

print(xml_file_range)
data = p.map(lambda f: pp.parse_medline_xml(f, year_info_only=False), xml_files)
p.close()
p.join()

print("Flatten")
flattened_data = list(chain(*data))

print("Pandas")
df = pd.DataFrame(flattened_data).fillna(value=np.NaN)

print("Save")
df.to_pickle(PATH + '/MedlineCombinedPandas_Dates_' + "_".join(map(str, xml_file_range)) + '_.p')


# 47

# frames = list()
# for x in [i for i in os.listdir(PATH) if ".p" in i]:
#     temp_df = pd.read_pickle(PATH + "/" + x).drop('abstract')
#     print("complete:" + x)

# ---------------------------------------------------------------------------------------------------- #

def reincode(df, exclude):
    for c in [col for col in df.columns.tolist() if not col in exclude]:
        df[c] = df[c].str.decode('utf-8').str.encode('utf-8')
    return df


print("--------------------" * 3)
frames = list()
for f in [PATH + "/" + i for i in os.listdir(PATH) if ".p" in i and 'Date' not in i]:
    temp_df = pd.read_pickle(f)
    del temp_df['other_id']
    del temp_df['abstract']
    del temp_df['pmc']
    # temp_df = reincode(df=temp_df, exclude=['grants'])
    temp_df['journal_iso'] = temp_df['journal_iso'].str.replace(".", "")
    # print(temp_df.info())
    frames.append(temp_df)
    print("--------------------" * 3)
    print("complete: " + str(f.split("/")[-1]))
    print("--------------------" * 3)

print('Converting to dict')
df_dict = dict.fromkeys(frames[0].columns.tolist(), [])
for t in frames[0].columns.tolist():
    print("--------------------" * 3)
    print("extracting: " + str(t))
    extracted = (frame[t] for frame in frames)
    print("flattening: " + str(t))
    df_dict[t] = fast_flatten(extracted)
    print("Complete: " + str(t))
    print("--------------------" * 3)

del frames

print('to DF')
df = pd.DataFrame.from_dict(df_dict)
tqdm.pandas(desc="status")

dates = pd.read_pickle([PATH + "/" + i for i in os.listdir(PATH) if ".p" in i and 'Date' in i][0])
dates_dict = dict(zip(dates['pmid'], dates['pubdate']))

# Update Dates
df['pubdate'] = df['pmid'].progress_map(lambda k: dates_dict[k], na_action='ignore')


# Format Dates
def grant_formater(grant_dicts):
    funders = list()
    for g in grant_dicts:
        funding_info = [f if f != None else 'nan' for f in [g['grant_id'], g['agency'], g['country']]]
        funders.append("; ".join(funding_info))
    return " | ".join(funders)


df['grants'] = df['grants'].progress_map(grant_formater, na_action='ignore')

print("Saving as csv...")
df.to_csv('2Pubmed2000_to_2015.csv', index=False, chunksize=10000)
