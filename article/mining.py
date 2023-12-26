import os

import requests
import sqlite3
from company.company import Document,Company
from utils.constant import COMPANIES_DB

from company.orm import Object2Relational
from company.text_extraction import extracting_text
_FILENAME='data/temp/extracting_text'

def _extracting_an_document(document:Document)->str:
### Downloading doc
    f_name = document.url.split('/')[-1]
    ext_name = f_name.split('.')[-1]
    
    if ext_name == 'pdf': 
        txt=_extract_news_pdf(document.url,f_name)
    elif ext_name == 'htm':
        txt=_extract_news_htm(document.url,f_name)
    elif ext_name =='doc': 
        txt=_extract_news_doc(document.url,f_name)
    elif ext_name=='html': 
        txt=_extract_news_html(document.url,f_name)
    elif ext_name=='docx': 
        txt=_extract_news_docx(document.url,f_name)
    elif ext_name=='xls':
        txt=_extract_news_xls(document.url,f_name)
    elif ext_name=='rtf':
        txt=_extract_news_rtf(document.url,f_name)
    else: 
        raise(ValueError(f"the extension is {ext_name}"))
    return txt 

def _extract_news_pdf_old (document_url:str,file_name:str=_FILENAME):
    response = requests.get(document_url,timeout=100)
    with open(file_name,'wb') as file: 
        file.write(response.content)
    txt=extracting_text(file_name,'pdf')
    os.remove(file_name)
    return txt

def _extract_news_pdf (document_url:str,file_name:str=_FILENAME)->str:
    if document_url=='https://www1.hkexnews.hk/listedco/listconews/sehk/2018/1011/ltn201810111441.pdf': 
        return ''
    
    try:
        with requests.get(document_url, stream=True, timeout=100) as response:
            response.raise_for_status()
            with open(file_name,'wb') as file: 
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
        
        txt=extracting_text(file_name,'pdf')
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        print(document_url)
        txt=''
        # Or, raise the exception if you prefer
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)
    return txt

def _extract_news_htm(document_url:str,file_name:str=_FILENAME):
    response = requests.get(document_url)
    with open(file_name,'w',encoding='utf-8') as file:
        file.write(response.text)
    txt=extracting_text(file_name,'htm')
    os.remove(file_name)
    return txt

def _extract_news_html(document_url:str,file_name:str=_FILENAME):
    response = requests.get(document_url)
    with open(file_name,'w',encoding='utf-8') as file:
        file.write(response.text)
    txt=extracting_text(file_name,'html')
    os.remove(file_name)
    return txt
    
def _extract_news_doc(document_url:str,file_name:str=_FILENAME):
    response = requests.get(document_url)
    with open(file_name,'wb') as file:
        file.write(response.content)
    txt=extracting_text(file_name,'doc')
    os.remove(file_name)
    return txt
    
def _extract_news_docx(document_url:str,file_name:str=_FILENAME): 
    response = requests.get(document_url)
    with open(file_name,'wb') as file:
        file.write(response.content)    
    txt=extracting_text(file_name,'docx')
    os.remove(file_name)
    return txt
    
def _extract_news_xls(document_url:str,file_name:str=_FILENAME):
    response = requests.get(document_url)
    with open(file_name,'wb') as file:
        file.write(response.content)  
    txt=extracting_text(file_name,'xls')
    os.remove(file_name)
    return txt
        
def _extract_news_rtf(document_url:str,file_name:str=_FILENAME):
    response = requests.get(document_url)
    with open(file_name, "wb") as f:
        f.write(response.content)
    txt=extracting_text(file_name,'rtf')
    os.remove(file_name)
    return txt
    
def extracting_all_document(db_path:str=COMPANIES_DB): 
    """extract text of documents of all companies
    and updating the database
    Args:
        db_path (_type_, optional): the sqlite3 database filename. Defaults to COMPANIES_DB.
    """
    
    company_handler=Object2Relational(Company)
    document_handler=Object2Relational(Document)
    
    company_list=company_handler.fetch_all()

    print(f'len of company_list {len(company_list)}')
    for company in company_list: 
        company:Company
        company_id=company.id
        print(f'Company id {company_id}')
        document_list:list[Document]=document_handler.fetch_some(('company_id=?',company_id),order_by='published_at')
        print(f'len of document_list{len(document_list)}')
        con= sqlite3.connect(db_path)
        c=con.cursor()
        for document in document_list:
            txt=_extracting_an_document(document)
            update_sql = """
                            UPDATE document
                            SET content = ?
                            WHERE id = ?;
                            """
            para=(txt,document.id)
            c.execute(update_sql,para)
        con.commit()
        c.close()
        con.close()
        print(f'For company {company_id} \n {txt}')
            

            
            
            


