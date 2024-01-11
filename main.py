from utils.constant import COMPANIES_DB,HKEX_CAR3_TEST_RESULT,NOT_HKEX_CAR3_TEST_RESULT,SKIP_ID
#from company.data_management import init_db
from company.main import read_and_commit_companies_from_csv,read_and_commit_index_company_from_csv,read_and_commit_pricing_from_a_directory
from company.orm import object2relational_insert_commit,object2relational_ignore_commit
from company.returns import cal_adjusted_daily_returns,cal_abnormal_returns,cal_car3s,cal_car3_dual
#from article.hkexnews.hkexnews import generate_document,populate_causing
#from article.gnews import request_with_keyword
from sentiment.doc_tone import cal_tone_score, cal_tone_score_hkex,cal_tone_merge,cal_tone_merge_hkex
from sentiment.car3_test import generate_car3_testdata,generate_car3_testdata_with_hkex,generate_test_results_by_group,write_results_to_csv,generate_tonemerge_car_list,tonemerge_car3_analysis,tonemerge_car3_regression
from sentiment.car3_test import get_acar3_hkex,get_hcar3_hkex,get_acar3_no_hkex,get_hcar3_no_hkex,get_hkex_tonemerge_acar3_hcar3,get_no_hkex_tonemerge_acar3_hcar3
import logging
logging.basicConfig(level=logging.INFO,filename="cal_ton_log.txt")
#init_db()
#read_and_commit_companies_from_csv('data/company/companies.csv')
#read_and_commit_index_company_from_csv('data/company/index_companies.csv')

#read_and_commit_pricing_from_a_directory('data/pricing') 

# ADJUSTED_DAILY_RETURNS=cal_adjusted_daily_returns() 
# print(len(ADJUSTED_DAILY_RETURNS))
# object2relational_insert_commit(ADJUSTED_DAILY_RETURNS)

# ABNORMAL_RETURNS=cal_abnormal_returns()
# object2relational_insert_commit(ABNORMAL_RETURNS)
# print(len(ABNORMAL_RETURNS))


# CAR3S=cal_car3s()
# object2relational_insert_commit(CAR3S)



#cal_car3_dual()


# CAR3_DUAL=cal_car3_dual()
# object2relational_insert_commit(CAR3_DUAL)

# generate_document()
# populate_causing()


#from run_pr import *

#tone_score=cal_tone_score()
#object2relational_insert_commit(tone_score)
#tone_score_hkex=cal_tone_score_hkex()
#object2relational_insert_commit(tone_score_hkex)


#tone_merge=cal_tone_merge()
# object2relational_insert_commit(tone_merge)

# tone_merge_hkex=cal_tone_merge_hkex()
# object2relational_insert_commit(tone_merge_hkex)
# generate_car3_testdata()
# generate_car3_testdata_with_hkex()

# acar3_no_hkex=get_acar3_no_hkex()
# hcar3_no_hkex=get_hcar3_no_hkex()

# acar3_hkex=get_acar3_hkex()
# hcar3_hkex=get_hcar3_hkex()

# results_by_test_hkex, results_by_test_not_hkex = generate_test_results_by_group(acar3_hkex,hcar3_hkex,acar3_no_hkex,hcar3_no_hkex)

# write_results_to_csv(results_by_test_hkex,'hkex')
#write_results_to_csv(results_by_test_not_hkex,'nohkex')

#generate_tonemerge_car_list()

no_hkex_tonemerge_acar3_hcar3=get_no_hkex_tonemerge_acar3_hcar3()
hkex_tonemerge_acar3_hcar3= get_hkex_tonemerge_acar3_hcar3()
# result_dict=tonemerge_car3_analysis(hkex_tonemerge_acar3_hcar3,no_hkex_tonemerge_acar3_hcar3)




tonemerge_car3_regression(hkex_tonemerge_acar3_hcar3, no_hkex_tonemerge_acar3_hcar3)