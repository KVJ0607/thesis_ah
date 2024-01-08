import os
#DB instance path 
INSTANCE_PATH= 'instance'
#DB db path 
with open(os.path.join(INSTANCE_PATH,'config.py'),'r') as f: 
    for line in f:
        # If the line starts with 'abo_path', parse the value
        if line.startswith('DATABASE'):
            _, db_path = line.strip().split('=')
            db_path=db_path.strip('"').strip("'")
COMPANIES_DB=os.path.join(INSTANCE_PATH,db_path)

ZH_DICTIONARY='data/vsa/chi_sent_dict.csv'
EN_DICTIONARY='data/vsa/en_sent_dict.csv'
ZH_STOPWORDS='data/vsa/stopwords(ch)_encoded.txt'
EN_STOPWORDS='data/vsa/stopwords(en).txt'

# Source data
MASTER_DICTIONARY_FILENAME='data/master_dictionary/Loughran-McDonald_MasterDictionary_1993-2021.csv'
PRICING_DATA_SOURCE="data/pricing"
COMPANY_CSV="Company_Project/data/source/companies.csv"

# API keys 
with open('api_key.txt','r') as f: 
    for line in f: 
        if line.startswith('gnews'):
            _, api_key = line.strip().split('=')
            GNEWS_KEYS=api_key
GNEWS_KEYS








