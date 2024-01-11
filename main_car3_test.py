from pprint import pprint
from scipy.stats import shapiro, ttest_rel, wilcoxon, kendalltau
import numpy as np

from sentiment.car3_test import * 
from utils.constant import HKEX_CAR3_TEST_RESULT, NOT_HKEX_CAR3_TEST_RESULT

acar3_hkex=get_acar3_hkex()
hcar3_hkex=get_hcar3_hkex()

acar3_not_hkex=get_acar3_no_hkex()
hcar3_not_hkex=get_hcar3_no_hkex()





results_by_test_hkex, results_by_test_not_hkex = generate_test_results_by_group(acar3_hkex,hcar3_hkex,acar3_not_hkex,hcar3_not_hkex)

# from pprint import pprint
# pprint(results_by_test_hkex['shapiro_acar3'])

# # To inspect the results by test for all NOT HKEX companies:
# pprint(results_by_test_not_hkex['shapiro_acar3'])

# Usage
write_results_to_csv(results_by_test_hkex, HKEX_CAR3_TEST_RESULT)
write_results_to_csv(results_by_test_not_hkex, NOT_HKEX_CAR3_TEST_RESULT)
