# read and commit from source
from company.company import * 
from company.orm import *

def read_and_commit_companies_from_csv(filename:str,db_path=COMPANIES_DB)->None: 
    """read companies info from csv and commit it to database
    
    Args:
        filename (str): the csv filename
        db_path (_type_, optional): sqlite3 database file path. Defaults to COMPANIES_DB.
    """
    import csv
    result_company=[]
    result_keyword=[]
    with open(filename,'r') as f: 
        reader=csv.reader(f)
        reader.__next__()
        for row in reader: 
            en_name,h_code,a_code,zh_name,others=row[0],row[1],row[2],row[3],row[4:]
            result_company.append(Company.from_tuple(h_code,a_code,zh_name,en_name))
            for keyword_ in row:                 
                result_keyword.append(Keyword.from_tuple(keyword_,h_code,a_code,zh_name,en_name))
    object2relational_commit(result_company,db_path)
    object2relational_commit(result_company,db_path)
            

def read_and_commit_index_company_from_csv(filename:str,db_path=COMPANIES_DB)->None:
    """read index_company information from csv file and commit it to database
    
    Expect a csv file with column name:flag,listed_region,name,code
        e.g. H,HK,HANG SENG CHINA ENTERPRISES IND,HSCE
             
    Args:
        filename (str): The filename of the csv file
        db_path (_type_, optional): sqlite3 database file path. Defaults to COMPANIES_DB.

    """
    import csv 
    result_indexcompany=[]
    with open(filename,'r') as f: 
        reader=csv.reader(f)
        reader.__next__()
        for row in reader: 
            flag,listed_region,name,code=row[0].lower(),row[1].lower(),row[2].lower(),row[3].lower()
            result_indexcompany.append(IndexCompany.from_tuple(flag,listed_region,name,code))
    object2relational_commit(result_indexcompany,db_path)


def read_and_commit_pricing_from_a_directory(foldername:str,db_path=COMPANIES_DB)->None: 
    """Read shock pricing data from a folder and commit it to databases.
    
    Expecting a csv file with column of order Date,Open,High,Low,Close,Adj Close,Volume.
    Expecting with pricing data from company having filename =a_code.csv|h_code.csv.
    Expecting with pricing data from index_company having filename= index_%code%.csv, where %code% is the code of the index_company.
    
    Args:
        foldername (str): The folder path where all subfolders contain the csv files
        db_path (_type_, optional): sqlite3 database file path. Defaults to COMPANIES_DB.

    """
    import os
    import glob
    import pandas as pd
    csv_files = [file for file in glob.glob(os.path.join(foldername, '**/*.csv'), recursive=True)]
    #csv_files=[file for file in os.listdir(foldername) if file.endswith('.csv')]
    all_pricing=[]
    
    #define my ORM 
    pricing_handler=Object2Relational(Pricing,db_path)
    company_handler=Object2Relational(Company,db_path)
    index_company_handler=Object2Relational(IndexCompany,db_path)
    for csv_file in csv_files: 
        file_path=os.path.join(foldername,csv_file)
        data_=pd.read_csv(file_path)
        #Get h_code/a_code information from filename
        listed_region=csv_file[-6:-4]

        if csv_file.startswith('index_'): 
            index_code=csv_file.split('.csv')[0][6:]
            resulting_row=[None,None,None,None]
            index_resulting_row=index_company_handler.fetch_some(('code',index_code))
        elif listed_region.upper()=='HK': 
            flag='h'
            h_code=csv_file[0:-6]
            resulting_row=company_handler.fetch_some(('h_code',h_code))
            index_resulting_row=IndexCompany(None,None,None,None,None)
        elif listed_region.upper()=='SZ' or listed_region.upper()=='SH':             
            flag='a'
            a_code=csv_file[0:-6]
            resulting_row=company_handler.fetch_some(('a_code',a_code))
            index_resulting_row=IndexCompany(None,None,None,None,None)
        else: 
            raise(ValueError(f'The folderpath{foldername} contain csv with wrong filename {csv_file}'))
        

        flag,listed_region,index_name,index_code,index_company_id =index_company_handler.to_tuple(index_resulting_row)
        h_code,a_code,zh_name,en_name,company_id=company_handler.to_tuple(resulting_row)
        
        for index_i,row in data_.iterrows():             
            
            all_pricing.append(pricing_handler.from_tuple((row.iloc[0],row.iloc[1],row.iloc[2],row.iloc[3],row.iloc[4],row.iloc[5],row.iloc[6],flag,listed_region,company_id,index_company_id)))

    object2relational_commit(all_pricing,db_path)        
    return all_pricing 

    
