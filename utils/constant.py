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


ACAR3_NO_HKEX='data/car3_pkl/acar3s_no_hkex.pkl'
HCAR3_NO_HKEX='data/car3_pkl/hcar3_no_hkex.pkl'
TONEMERGE_NO_HKEX='data/car3_pkl/refined_tonemerge_no_hkex.pkl'

ACAR3_HKEX='data/car3_pkl/acar3s_hkex.pkl'
HCAR3_HKEX='data/car3_pkl/hcar3_hkex.pkl'
TONEMERGE_HKEX='data/car3_pkl/refined_tonemerge_hkex.pkl'

HKEX_TONEMERGE_ACAR3_HCAR3='data/car3_pkl/hkex_tonemerge_acar3_hcar3.pkl'
NO_HKEX_TONEMERGE_ACAR3_HCAR3='data/car3_pkl/no_hkex_tonemerge_acar3_hcar3.pkl'

HKEX_CAR3_TEST_RESULT='data/test_result/results_hkex.csv'
NOT_HKEX_CAR3_TEST_RESULT='data/test_result/results_not_hkex.csv'

HKEX_TONECAR_CORRELATION_RESULT='data/test_result/hkex_tonecar_correlation.csv'
NO_HKEX_TONECAR_CORRELATION_RESULT='data/test_result/no_hkex_tonecar_correlation.csv'
# Source data
MASTER_DICTIONARY_FILENAME='data/master_dictionary/Loughran-McDonald_MasterDictionary_1993-2021.csv'
PRICING_DATA_SOURCE="data/pricing"
COMPANY_CSV="Company_Project/data/source/companies.csv"



#Crawling 
SKIP_HCODE=['00719.hk','06178.hk','01800.hk','06099.hk','01336.hk','02607.hk','00753.hk','01898.hk','06690.hk','03996.hk','01766.hk','01816.hk','06881.hk','06881.hk','06066.hk']
#SKIP_ID_old=[5,7,18,24,38,46,53,63,90,91,103,110,113,147]
SKIP_ID=[5,7,18,24,38,46,53,63,90,91,103,110,113,147]

# API keys 
with open('api_key.txt','r') as f: 
    for line in f: 
        if line.startswith('gnews'):
            _, api_key = line.strip().split('=')
            GNEWS_KEYS=api_key
GNEWS_KEYS








