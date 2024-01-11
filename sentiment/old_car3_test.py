import pickle
import csv
import sqlite3
from scipy.stats import shapiro, ttest_rel, wilcoxon, kendalltau
import logging

from utils.constant import COMPANIES_DB,ACAR3_NO_HKEX,HCAR3_NO_HKEX,TONEMERGE_NO_HKEX,ACAR3_HKEX,HCAR3_HKEX,TONEMERGE_HKEX,SKIP_ID
from utils.basic import to_iso_date
from company.orm import Object2Relational
from company.company import TonescoreMerge,Car3

#Helper function
def get_acar3_no_hkex()->dict[int,list[Car3]]:
    with open(ACAR3_NO_HKEX, 'rb') as file:
        multiple_companies_acar3s = pickle.load(file)
    return multiple_companies_acar3s

def get_hcar3_no_hkex()->dict[int,list[Car3]]:
    with open(HCAR3_NO_HKEX, 'rb') as file:
        multiple_companies_hcar3 = pickle.load(file)
    return multiple_companies_hcar3

def get_refined_tonemerge_no_hkex()->dict[int,list[TonescoreMerge]]:
    with open(TONEMERGE_NO_HKEX, 'rb') as file:
        refined_multiple_companies_nonhkex_tonemerge = pickle.load(file)
    return refined_multiple_companies_nonhkex_tonemerge

def get_acar3_hkex()->dict[int,list[Car3]]:
    with open(ACAR3_HKEX, 'rb') as file:
        multiple_companies_acar3s = pickle.load(file)
    return multiple_companies_acar3s

def get_hcar3_hkex()->dict[int,list[Car3]]:
    with open(HCAR3_HKEX, 'rb') as file:
        multiple_companies_hcar3 = pickle.load(file)
    return multiple_companies_hcar3

def get_refined_tonemerge_hkex()->dict[int,list[TonescoreMerge]]:
    with open(TONEMERGE_HKEX, 'rb') as file:
        refined_multiple_companies_nonhkex_tonemerge = pickle.load(file)
    return refined_multiple_companies_nonhkex_tonemerge




#Main function
def generate_car3_testdata(): 
    multiple_companies_acar3s:dict[int,list[Car3]]={}
    multiple_companies_hcar3:dict[int,list[Car3]]={}
    refined_multiple_companies_nonhkex_tonemerge:dict[int,list[TonescoreMerge]]={}
    for cp_id in range(1,150):
        #Find all the car3 seperately for a and h for each company and order by date 
        all_nonhkex_tonemerge:list[TonescoreMerge]=Object2Relational(TonescoreMerge).fetch_some(('company_id=?',cp_id),('is_hkex=?',0),order_by='date')
        
        all_acar3:list[Car3]=Object2Relational(Car3).fetch_some(('flag=?','a'),('company_id=?',cp_id),order_by='date')
        all_hcar3:list[Car3]=Object2Relational(Car3).fetch_some(('flag=?','h'),('company_id=?',cp_id),order_by='date')
    
        
        all_acar3_dict:dict[str,Car3]={one_car3.date :one_car3 for one_car3 in all_acar3}
        all_hcar3_dict:dict[str,Car3]={one_car3.date :one_car3 for one_car3 in all_hcar3}
        
        result_acar3s:list[Car3]=[]
        result_hcar3s:list[Car3]=[]
        result_tonemerge:list[TonescoreMerge]=[]
        
        for one_tone in all_nonhkex_tonemerge: 
            iso_date=to_iso_date(one_tone.date)
            if iso_date:                             
                acar3_with_date=all_acar3_dict.get(iso_date)
                hcar3_with_date=all_hcar3_dict.get(iso_date)                
                if acar3_with_date and hcar3_with_date: 
                    result_acar3s.append(acar3_with_date)
                    result_hcar3s.append(hcar3_with_date)
                    result_tonemerge.append(one_tone)                                                                            
            else: 
                continue
        multiple_companies_acar3s[cp_id]=result_acar3s
        multiple_companies_hcar3[cp_id]=result_hcar3s
        refined_multiple_companies_nonhkex_tonemerge[cp_id]=result_tonemerge
    with open(ACAR3_NO_HKEX, 'wb') as file:
        pickle.dump(multiple_companies_acar3s, file)

    with open(HCAR3_NO_HKEX, 'wb') as file:
        pickle.dump(multiple_companies_hcar3, file)

    with open(TONEMERGE_NO_HKEX, 'wb') as file:
        pickle.dump(refined_multiple_companies_nonhkex_tonemerge, file)
        
    
def generate_car3_testdata_with_hkex(): 
    multiple_companies_acar3s:dict[int,list[Car3]]={}
    multiple_companies_hcar3:dict[int,list[Car3]]={}
    refined_multiple_companies_hkex_tonemerge:dict[int,list[TonescoreMerge]]={}
    for cp_id in range(1,150):
        #Find all the car3 seperately for a and h for each company and order by date 
        all_hkex_tonemerge:list[TonescoreMerge]=Object2Relational(TonescoreMerge).fetch_some(('company_id=?',cp_id),('is_hkex=?',1),order_by='date')
        
        all_acar3:list[Car3]=Object2Relational(Car3).fetch_some(('flag=?','a'),('company_id=?',cp_id),order_by='date')
        all_hcar3:list[Car3]=Object2Relational(Car3).fetch_some(('flag=?','h'),('company_id=?',cp_id),order_by='date')
    
        
        all_acar3_dict:dict[str,Car3]={one_car3.date :one_car3 for one_car3 in all_acar3}
        all_hcar3_dict:dict[str,Car3]={one_car3.date :one_car3 for one_car3 in all_hcar3}
        
        result_acar3s:list[Car3]=[]
        result_hcar3s:list[Car3]=[]
        result_tonemerge:list[TonescoreMerge]=[]
        
        for one_tone in all_hkex_tonemerge: 
            iso_date=to_iso_date(one_tone.date)
            if iso_date:                             
                acar3_with_date=all_acar3_dict.get(iso_date)
                hcar3_with_date=all_hcar3_dict.get(iso_date)                
                if acar3_with_date and hcar3_with_date: 
                    result_acar3s.append(acar3_with_date)
                    result_hcar3s.append(hcar3_with_date)
                    result_tonemerge.append(one_tone)                                                                            
            else: 
                continue
        multiple_companies_acar3s[cp_id]=result_acar3s
        multiple_companies_hcar3[cp_id]=result_hcar3s
        refined_multiple_companies_hkex_tonemerge[cp_id]=result_tonemerge
        


    with open(ACAR3_HKEX, 'wb') as file:
        pickle.dump(multiple_companies_acar3s, file)

    with open(HCAR3_HKEX, 'wb') as file:
        pickle.dump(multiple_companies_hcar3, file)

    with open(TONEMERGE_HKEX, 'wb') as file:
        pickle.dump(refined_multiple_companies_hkex_tonemerge, file)
        
    


#Helper function 
def perform_tests(acar3_values, hcar3_values):
    # Perform Shapiro-Wilk Test for normality
    shapiro_results_acar3 = shapiro(acar3_values)
    shapiro_results_hcar3 = shapiro(hcar3_values)

    # Perform paired t-test
    ttest_results = ttest_rel(acar3_values, hcar3_values)

    # Perform Wilcoxon Test
    wilcoxon_results = wilcoxon(acar3_values, hcar3_values)

    # Perform Kendall's tau test
    kendalltau_results = kendalltau(acar3_values, hcar3_values)

    return {
        'shapiro_acar3': shapiro_results_acar3,
        'shapiro_hcar3': shapiro_results_hcar3,
        'paired_ttest': ttest_results,
        'wilcoxon': wilcoxon_results,
        'kendalls_tau': kendalltau_results
    }

#Main function 
def generate_test_results_by_group(acar3_hkex, hcar3_hkex, acar3_not_hkex, hcar3_not_hkex):
    """
    This function processes the test results for two groups of companies (HKEX and not HKEX).
    It returns two dictionaries containing the test results organized by test type for each group.

    :param acar3_hkex: Dictionary with company_id as keys and list of objects with .car3 attribute as values for HKEX group
    :param hcar3_hkex: Dictionary with company_id as keys and list of objects with .car3 attribute as values for HKEX group
    :param acar3_not_hkex: Dictionary with company_id as keys and list of objects with .car3 attribute as values for non-HKEX group
    :param hcar3_not_hkex: Dictionary with company_id as keys and list of objects with .car3 attribute as values for non-HKEX group
    :return: Two dictionaries containing the test results for each test type, for HKEX and not HKEX groups respectively
    """
    
    results_by_test_hkex = {
        'shapiro_acar3': {},
        'shapiro_hcar3': {},
        'paired_ttest': {},
        'wilcoxon': {},
        'kendalls_tau': {}
    }

    results_by_test_not_hkex = {
        'shapiro_acar3': {},
        'shapiro_hcar3': {},
        'paired_ttest': {},
        'wilcoxon': {},
        'kendalls_tau': {}
    }
    insufficient_data_companies = []
    
    # Loop over each company by keys and perform tests
    for company_id in acar3_hkex.keys():
        if company_id in SKIP_ID:
            continue
        acar3_hkex_values = [obj.car3 for obj in acar3_hkex[company_id]]
        hcar3_hkex_values = [obj.car3 for obj in hcar3_hkex[company_id]]
        acar3_not_hkex_values = [obj.car3 for obj in acar3_not_hkex[company_id]]
        hcar3_not_hkex_values = [obj.car3 for obj in hcar3_not_hkex[company_id]]
        
        if len(acar3_not_hkex_values) < 3:
            logging.info(f"company {company_id} has less then 3 not hkex news")
            insufficient_data_companies.append(company_id)
            continue
        # Perform all tests for hkex and not_hkex
        results_hkex = perform_tests(acar3_hkex_values, hcar3_hkex_values)
        results_not_hkex = perform_tests(acar3_not_hkex_values, hcar3_not_hkex_values)

        # Store results by test for hkex
        for test_name in results_by_test_hkex.keys():
            results_by_test_hkex[test_name][company_id] = results_hkex[test_name]

        # Store results by test for not_hkex
        for test_name in results_by_test_not_hkex.keys():
            results_by_test_not_hkex[test_name][company_id] = results_not_hkex[test_name]
    return results_by_test_hkex, results_by_test_not_hkex

def print_company_test_results(company_id, results_by_test_hkex, results_by_test_not_hkex):
    print(f"Test results for company ID {company_id}:")
    print("\nHKEX Group:")
    for test_name, results in results_by_test_hkex.items():
        print(f"{test_name}: {results.get(company_id, 'No data')}")

    print("\nNot HKEX Group:")
    for test_name, results in results_by_test_not_hkex.items():
        print(f"{test_name}: {results.get(company_id, 'No data')}")



def write_results_to_csv_old(results, filename):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Test", "Company ID", "Result"])
        for test_name, companies in results.items():
            for company_id, result in companies.items():
                writer.writerow([test_name, company_id, result])





#Helper function
def get_company_code(cursor, company_id):
    cursor.execute("SELECT h_code FROM company WHERE id = ?", (company_id,))
    result = cursor.fetchone()
    return result[0] if result else None

#Main function
def write_results_to_csv(results, filename_: str):
    # Connect to the SQL database
    conn = sqlite3.connect(COMPANIES_DB)
    cursor = conn.cursor()

    for test_name, companies in results.items():
        # Sort companies by their p-value
        sorted_companies = sorted(companies.items(), key=lambda item: item[1][0])

        # Create a unique filename for each test
        filename = f"data/test_result/{filename_}_{test_name}_results.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write the header with new columns for p-value thresholds
            writer.writerow(["H-Code", "p-value", "Pass < 0.1", "Pass < 0.05"])
            
            # Write the sorted test results for each company
            for company_id, test_result in sorted_companies:
                # Fetch the h_code for the company
                h_code = get_company_code(cursor, company_id)
                if not h_code:
                    # Handle the case where h_code is not found, e.g., by writing a placeholder or skipping
                    continue

                p_value = test_result[0]  # Extract the p-value

                # Determine pass/fail for each threshold
                pass_01 = "Pass" if p_value < 0.1 else "Fail"
                pass_005 = "Pass" if p_value < 0.05 else "Fail"
                
                writer.writerow([h_code, p_value, pass_01, pass_005])

    # Close the database connection
    conn.close()