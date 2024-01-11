# read and commit from source
import csv
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
    with open(filename,'r') as f: 
        reader=csv.reader(f)
        reader.__next__()
        for row in reader: 
            en_name,h_code,a_code,zh_name,others=row[0],row[1],row[2],row[3],row[4:]
            result_company.append(Company.from_tuple((h_code.lower(),a_code.lower(),zh_name,en_name)))
    object2relational_insert_commit(result_company,db_path)
    
    result_keyword=[]
    company_handler=Object2Relational(Company)
    with open(filename,'r') as f: 
        reader=csv.reader(f)
        reader.__next__()
        for row in reader: 
            en_name,h_code,a_code,zh_name,others=row[0],row[1],row[2],row[3],row[4:]
            company_id=company_handler.fetch_some(('h_code=?',h_code.lower()))[0].id
            for keyword in row: 
                keyword_obj=Keyword(keyword,company_id)
            
    all_cp=company_handler.fetch_all()
    mining_list=[]
    for cp in all_cp: 
        cp:Company
        cp_id=cp.id
        mining_list.append(CompanyMining(0,0,None,cp_id))
    object2relational_insert_commit(mining_list,db_path)
        
        


            

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
            result_indexcompany.append(IndexCompany.from_tuple((flag.lower(),listed_region.lower(),name.lower(),code.lower())))
    object2relational_insert_commit(result_indexcompany,db_path)


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
    csv_files = [file for file in glob.glob(os.path.join(foldername, '**/*.csv'), recursive=True)]
    #csv_files=[file for file in os.listdir(foldername) if file.endswith('.csv')]
    all_pricing=[]
    
    #define my ORM 
    company_handler=Object2Relational(Company,db_path)
    index_company_handler=Object2Relational(IndexCompany,db_path)
    for csv_file in csv_files:    
        #Get h_code/a_code information from filename
        listed_region=csv_file[-6:-4]
        csv_filename=csv_file.split('/')[-1]
        if csv_filename.startswith('index_'): 
            index_code=csv_filename.split('.csv')[0][6:]
            #resulting_row=Company(None,None,None,None)
            index_resulting_row=index_company_handler.fetch_some(('code=?',index_code.lower()))[0]
            flag,listed_region,index_name,index_code,index_company_id =index_company_handler.to_tuple(index_resulting_row)
            company_id=None
        elif listed_region.upper()=='HK': 
            flag='h'
            h_code=csv_filename[0:7]
            h_code=Company.reformat_h_code(h_code)
            resulting_row=company_handler.fetch_some(('h_code=?',h_code))[0]
            h_code,a_code,zh_name,en_name,company_id=company_handler.to_tuple(resulting_row) 
            index_company_id=None
            
        elif listed_region.upper()=='SZ' or listed_region.upper()=='SH':
            try:              
                flag='a'
                a_code=csv_filename[0:9]     
                resulting_row=company_handler.fetch_some(('a_code=?',a_code.lower()))[0]  
                h_code,a_code,zh_name,en_name,company_id=company_handler.to_tuple(resulting_row)  
                index_company_id=None                                 
            except Exception as e: 
                print(a_code)
                print(csv_filename)
                print(csv_filename[0:9])
                raise(e)
        else: 
            raise(ValueError(f'The folderpath{foldername} contain csv with wrong filename {csv_file}'))
        

        with open(csv_file,'r') as f: 
            reader=csv.reader(f)
            reader.__next__()
            for row in reader: 
                if 'null' not in row:
                    date_=row[0]
                    open_=float(row[1])
                    high_=float(row[2])
                    low_=float(row[3])
                    close_=float(row[4])
                    adjusted_close_=float(row[5])
                    volume_=float(row[6]) 
                    all_pricing.append(Pricing(date_,open_,high_,low_,close_,adjusted_close_,volume_,flag.lower(),listed_region.lower(),None,company_id,index_company_id))
            
            
    non_null_pricing=[]
    for one_pricing in all_pricing: 
        one_pricing:Pricing
        if type(one_pricing.adjusted_close) == float: 
            non_null_pricing.append(one_pricing)
    
    object2relational_insert_commit(non_null_pricing,db_path)        
    return non_null_pricing

    
