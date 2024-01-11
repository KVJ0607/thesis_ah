import pickle
import csv
import sqlite3
from scipy.stats import shapiro, ttest_rel, wilcoxon, kendalltau, pearsonr, spearmanr
import statsmodels.api as sm

import logging
import pandas as pd


from utils.constant import COMPANIES_DB,ACAR3_NO_HKEX,HCAR3_NO_HKEX,TONEMERGE_NO_HKEX,ACAR3_HKEX,HCAR3_HKEX,TONEMERGE_HKEX,SKIP_ID,HKEX_TONEMERGE_ACAR3_HCAR3,NO_HKEX_TONEMERGE_ACAR3_HCAR3,HKEX_TONECAR_CORRELATION_RESULT,NO_HKEX_TONECAR_CORRELATION_RESULT
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

def get_hkex_tonemerge_acar3_hcar3()->dict[int,list[tuple]]:    
    with open(HKEX_TONEMERGE_ACAR3_HCAR3, 'rb') as file:
        return_dict = pickle.load(file)
    return return_dict

def get_no_hkex_tonemerge_acar3_hcar3()->dict[int,list[tuple]]:    
    with open(NO_HKEX_TONEMERGE_ACAR3_HCAR3, 'rb') as file:
        return_dict = pickle.load(file)
    return return_dict

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
    shapiro_results_acar3 = shapiro(acar3_values).pvalue
    shapiro_results_hcar3 = shapiro(hcar3_values).pvalue

    # Perform paired t-test
    ttest_results = ttest_rel(acar3_values, hcar3_values).pvalue

    # Perform Wilcoxon Test
    wilcoxon_results = wilcoxon(acar3_values, hcar3_values).pvalue

    # Perform Kendall's tau test
    kendalltau_results = kendalltau(acar3_values, hcar3_values).pvalue

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
        sorted_companies = sorted(companies.items(), key=lambda item: item[1])

        # Create a unique filename for each test
        filename = f"data/test_result/{filename_}_{test_name}_results.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["H-Code", "p-value", "Pass < 0.1", "Pass < 0.05"])

            for company_id, p_value in sorted_companies:
                # Fetch the h_code for the company
                h_code = get_company_code(cursor, company_id)
                if not h_code:
                    continue

                # Directly use p_value as it is no longer a list or tuple
                pass_01 = "Pass" if p_value < 0.1 else "Fail"
                pass_005 = "Pass" if p_value < 0.05 else "Fail"
                
                writer.writerow([h_code, p_value, pass_01, pass_005])

    # Close the database connection
    conn.close()
    
##
def generate_tonemerge_car_list_old(): 
    no_hkex_tone_car3_by_companies_id:dict[int,tuple]={}
    
    for cp_id in range(1,150): 
        if cp_id in SKIP_ID: 
            continue
        with sqlite3.connect(COMPANIES_DB) as conn:
            c=conn.cursor()
            sql_="""
            SELECT 
                tm.tonescore,
                tm.positive_tonescore,
                tm.negative_tonescore,
                CASE
                    WHEN a.flag = 'a' THEN a.car3
                    ELSE NULL
                END AS a_car3,
                CASE
                    WHEN h.flag = 'h' THEN h.car3
                    ELSE NULL
                END AS h_car3
            FROM 
                tonescore_merge tm
            LEFT JOIN 
                car3 a ON tm.date = a.date AND a.flag = 'a' AND tm.company_id = a.company_id
            LEFT JOIN 
                car3 h ON tm.date = h.date AND h.flag = 'h' AND tm.company_id = h.company_id
            WHERE
                tm.company_id = ? and is_hkex=0;
            """
        no_hkex_tonemerge_acar3_hcar3=c.execute(sql_,(cp_id,)).fetchall()
        no_hkex_tone_car3_by_companies_id[cp_id]=no_hkex_tonemerge_acar3_hcar3
    with open(NO_HKEX_TONEMERGE_ACAR3_HCAR3, 'wb') as file:
        pickle.dump(no_hkex_tone_car3_by_companies_id, file)

    hkex_tone_car3_by_companies_id:dict[int,tuple]={}    
    for cp_id in range(1,150): 
        if cp_id in SKIP_ID: 
            continue
        with sqlite3.connect(COMPANIES_DB) as conn:
            c=conn.cursor()
            sql_="""
            SELECT 
                tm.tonescore,
                tm.positive_tonescore,
                tm.negative_tonescore,
                CASE
                    WHEN a.flag = 'a' THEN a.car3
                    ELSE NULL
                END AS a_car3,
                CASE
                    WHEN h.flag = 'h' THEN h.car3
                    ELSE NULL
                END AS h_car3
            FROM 
                tonescore_merge tm
            LEFT JOIN 
                car3 a ON tm.date = a.date AND a.flag = 'a' AND tm.company_id = a.company_id
            LEFT JOIN 
                car3 h ON tm.date = h.date AND h.flag = 'h' AND tm.company_id = h.company_id
            WHERE
                tm.company_id = ? and is_hkex=1;
            """
        hkex_tonemerge_acar3_hcar3=c.execute(sql_,(cp_id,)).fetchall()
        hkex_tone_car3_by_companies_id[cp_id]=hkex_tonemerge_acar3_hcar3        
    with open(HKEX_TONEMERGE_ACAR3_HCAR3, 'wb') as file:
        pickle.dump(hkex_tone_car3_by_companies_id, file)


def generate_tonemerge_car_list():
    no_hkex_tone_car3_by_companies_id = {}
    hkex_tone_car3_by_companies_id = {}

    with sqlite3.connect(COMPANIES_DB) as conn:
        c = conn.cursor()

        for cp_id in range(1, 150):
            if cp_id in SKIP_ID:
                continue

            for is_hkex in [0, 1]:
                sql_ = """
                SELECT 
                    tm.tonescore,
                    tm.positive_tonescore,
                    tm.negative_tonescore,
                    CASE
                        WHEN a.flag = 'a' THEN a.car3
                        ELSE NULL
                    END AS a_car3,
                    CASE
                        WHEN h.flag = 'h' THEN h.car3
                        ELSE NULL
                    END AS h_car3
                FROM 
                    tonescore_merge tm
                LEFT JOIN 
                    car3 a ON tm.date = a.date AND a.flag = 'a' AND tm.company_id = a.company_id
                LEFT JOIN 
                    car3 h ON tm.date = h.date AND h.flag = 'h' AND tm.company_id = h.company_id
                WHERE
                    tm.company_id = ? and is_hkex = ?;
                """

                tonemerge_acar3_hcar3 = c.execute(sql_, (cp_id, is_hkex)).fetchall()

                if is_hkex == 0:
                    no_hkex_tone_car3_by_companies_id[cp_id] = tonemerge_acar3_hcar3
                else:
                    hkex_tone_car3_by_companies_id[cp_id] = tonemerge_acar3_hcar3
                print(f"finish for {cp_id}")

    with open(NO_HKEX_TONEMERGE_ACAR3_HCAR3, 'wb') as file:
        pickle.dump(no_hkex_tone_car3_by_companies_id, file)
    
    with open(HKEX_TONEMERGE_ACAR3_HCAR3, 'wb') as file:
        pickle.dump(hkex_tone_car3_by_companies_id, file)
    
def tonemerge_car3_analysis(hkex_tonemerge_acar3_hcar3:dict[int,list[tuple]],no_hkex_tonemerge_acar3_hcar3:dict[int,list[tuple]]): 
    conn = sqlite3.connect(COMPANIES_DB)
    cursor = conn.cursor()   
    try: 
        hkex_result_dict={
            "pearson":{},
            "spearman":{}
        }
        for cp_id in range(1,150): 
            if cp_id in SKIP_ID: 
                continue

            data=hkex_tonemerge_acar3_hcar3[cp_id]

            # Convert the list of tuples into a pandas DataFrame
            df = pd.DataFrame(data, columns=['net_tonescore', 'positive_tonescore', 'negative_tonescore', 'acar3', 'hcar3'])

            # Calculate Pearson correlation coefficients - assumes linear relationship and data is normally distributed
            pearson_corr = df.corr(method='pearson')
            

            # Calculate Spearman correlation coefficients - makes no assumption about the distribution of the data
            spearman_corr = df.corr(method='spearman')

            hkex_result_dict["pearson"][cp_id]=pearson_corr
            hkex_result_dict["spearman"][cp_id]=spearman_corr
        
                
        with open(HKEX_TONECAR_CORRELATION_RESULT, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['pearson','spearman'])
            for cp_id_ in range(1,150): 
                if cp_id_ in SKIP_ID: 
                    continue
                pearson_=hkex_result_dict['pearson'][cp_id_]
                spearman_=hkex_result_dict['spearman'][cp_id_]
                h_code_=get_company_code(cursor,cp_id)
                writer.writerow([h_code_,pearson_,spearman_])


        no_hkex_result_dict={
            "pearson":{},
            "spearman":{}
        }
        for cp_id in range(1,150): 
            if cp_id in SKIP_ID: 
                continue

            no_hkex_data=no_hkex_tonemerge_acar3_hcar3[cp_id]

            # Convert the list of tuples into a pandas DataFrame
            df = pd.DataFrame(no_hkex_data, columns=['net_tonescore', 'positive_tonescore', 'negative_tonescore', 'acar3', 'hcar3'])

            # Calculate Pearson correlation coefficients - assumes linear relationship and data is normally distributed
            pearson_corr = df.corr(method='pearson')
            

            # Calculate Spearman correlation coefficients - makes no assumption about the distribution of the data
            spearman_corr = df.corr(method='spearman')

            no_hkex_result_dict["pearson"][cp_id]=pearson_corr
            no_hkex_result_dict["spearman"][cp_id]=spearman_corr
        
                
        with open(NO_HKEX_TONECAR_CORRELATION_RESULT, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['pearson','spearman'])
            for cp_id_ in range(1,150): 
                if cp_id_ in SKIP_ID: 
                    continue
                pearson_=no_hkex_result_dict['pearson'][cp_id_]
                spearman_=no_hkex_result_dict['spearman'][cp_id_]
                h_code_=get_company_code(cursor,cp_id)
                writer.writerow([h_code_,pearson_,spearman_])
    except Exception as e: 
        conn.close()
        raise(Exception(e))
        
    return hkex_result_dict,no_hkex_result_dict


def tonemerge_car3_regression_old(hkex_tonemerge_acar3_hcar3:dict[int,list[tuple]],no_hkex_tonemerge_acar3_hcar3:dict[int,list[tuple]]): 
    for cp_id in range(1,150):
        if cp_id in SKIP_ID: 
            continue
        
        hkex_data=hkex_tonemerge_acar3_hcar3[cp_id]
        # Convert the list of tuples into a pandas DataFrame
        df = pd.DataFrame(hkex_data, columns=['net_tonescore', 'positive_tonescore', 'negative_tonescore', 'acar3', 'hcar3'])

        # Define the dependent variable
        y = df['hcar3']  # or use 'acar3' if you want to predict A-share CAR

        # Define the independent variables
        X = df[['net_tonescore', 'positive_tonescore', 'negative_tonescore']]

        # Add a constant to the model (the intercept term)
        X = sm.add_constant(X)

        # Fit the model
        model = sm.OLS(y, X).fit()

        # Print the summary of the model
        print(model.summary())       
        
        
        
        no_hkex_data=hkex_tonemerge_acar3_hcar3[cp_id]
        # Convert the list of tuples into a pandas DataFrame
        no_hkex_df = pd.DataFrame(no_hkex_data, columns=['net_tonescore', 'positive_tonescore', 'negative_tonescore', 'acar3', 'hcar3'])

        # Define the dependent variable
        no_hkex_y = df['hcar3']  # or use 'acar3' if you want to predict A-share CAR

        # Define the independent variables
        no_hkex_X = df[['net_tonescore', 'positive_tonescore', 'negative_tonescore']]

        # Add a constant to the model (the intercept term)
        no_hkex_X = sm.add_constant(no_hkex_X)

        # Fit the model
        no_hkex_model = sm.OLS(no_hkex_y, no_hkex_X).fit()

        # Print the summary of the model
        print(no_hkex_model.summary())            
        
# Assuming get_company_code and SKIP_ID are defined elsewhere in your code

def perform_regression(data,cp_id):
    # Convert the list of tuples into a pandas DataFrame
    df = pd.DataFrame(data, columns=['net_tonescore', 'positive_tonescore', 'negative_tonescore', 'acar3', 'hcar3'])
    # df = df[df['net_tonescore'].apply(lambda x: isinstance(x, float))]
    # df = df[df['positive_tonescore'].apply(lambda x: isinstance(x, float))]
    # df = df[df['negative_tonescore'].apply(lambda x: isinstance(x, float))]
    # df = df[df['acar3'].apply(lambda x: isinstance(x, float))]
    # df = df[df['hcar3'].apply(lambda x: isinstance(x, float))]
    
    
    if not data:
        print(cp_id)
        return False
    # Results dictionary to hold regression results
    df['net_tonescore'] = pd.to_numeric(df['net_tonescore'], errors='coerce')
    df['positive_tonescore'] = pd.to_numeric(df['positive_tonescore'], errors='coerce')
    df['negative_tonescore'] = pd.to_numeric(df['negative_tonescore'], errors='coerce')
    df['acar3'] = pd.to_numeric(df['acar3'], errors='coerce')
    df['hcar3'] = pd.to_numeric(df['hcar3'], errors='coerce')
    
    df.fillna(0, inplace=True)
    regression_results = {}

    for dependent_var in ['hcar3', 'acar3']:
        # Define the dependent variable
        y = df[dependent_var]

        # Define the independent variables
        X = df[['net_tonescore', 'positive_tonescore', 'negative_tonescore']]

        # Add a constant to the model (the intercept term)
        X = sm.add_constant(X)

        # Fit the model
        model = sm.OLS(y, X).fit()

        # Store the regression coefficients
        regression_results[f'{dependent_var}_coefficients'] = model.params.tolist()

        # Optionally store other regression statistics such as p-values, R-squared, etc.
        regression_results[f'{dependent_var}_pvalues'] = model.pvalues.tolist()
        regression_results[f'{dependent_var}_rsquared'] = model.rsquared

    return regression_results

    """

    """
def tonemerge_car3_regression(hkex_tonemerge_acar3_hcar3, no_hkex_tonemerge_acar3_hcar3):
    with sqlite3.connect(COMPANIES_DB) as conn:
        cursor=conn.cursor()
        # Create lists to store the data for HKEX and non-HKEX companies
        hkex_results = []
        no_hkex_results = []

        for cp_id in range(1, 150):
            if cp_id in SKIP_ID: 
                continue
            
            company_code = get_company_code(cursor, cp_id)

            # Perform regression for HKEX companies
            if cp_id in hkex_tonemerge_acar3_hcar3:
                hkex_data = hkex_tonemerge_acar3_hcar3[cp_id]
                regression_results = perform_regression(hkex_data,cp_id)
                if regression_results:
                    regression_results['company_hcode'] = company_code
                    hkex_results.append(regression_results)
            
            # Perform regression for non-HKEX companies
            if cp_id in no_hkex_tonemerge_acar3_hcar3:
                no_hkex_data = no_hkex_tonemerge_acar3_hcar3[cp_id]
                regression_results = perform_regression(no_hkex_data,cp_id)
                if regression_results:
                    regression_results['company_hcode'] = company_code
                    no_hkex_results.append(regression_results)

        # Convert lists to DataFrames
        hkex_df = pd.DataFrame(hkex_results)
        no_hkex_df = pd.DataFrame(no_hkex_results)

        # Output the DataFrames to CSV files
        hkex_df.to_csv('data/test_result/hkex_regression_results.csv', index=False)
        no_hkex_df.to_csv('data/test_result/no_hkex_regression_results.csv', index=False)

def tonemerge_car3_regression_old2(hkex_tonemerge_acar3_hcar3, no_hkex_tonemerge_acar3_hcar3):
    with sqlite3.connect(COMPANIES_DB) as conn:
        cursor = conn.cursor()

        # Create a list to store the regression results
        results = []

        for cp_id in range(1, 150):
            if cp_id in SKIP_ID:
                continue

            company_code = get_company_code(cursor, cp_id)

            # Perform regression for HKEX companies
            if cp_id in hkex_tonemerge_acar3_hcar3:
                hkex_data = hkex_tonemerge_acar3_hcar3[cp_id]
                regression_results = perform_regression(hkex_data)
                regression_results['company_hcode'] = company_code
                results.append(regression_results)

            # Perform regression for non-HKEX companies
            if cp_id in no_hkex_tonemerge_acar3_hcar3:
                no_hkex_data = no_hkex_tonemerge_acar3_hcar3[cp_id]
                regression_results = perform_regression(no_hkex_data)
                regression_results['company_hcode'] = company_code
                results.append(regression_results)

        # Convert the list to a DataFrame
        df = pd.DataFrame(results)

        # Output the DataFrame to a CSV file
        df.to_csv('data/test_result/regression_results.csv', index=False)