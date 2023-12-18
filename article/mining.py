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
        txt=_extract_news_pdf(document.url)
    elif ext_name == 'htm':
        txt=_extract_news_htm(document.url)
    elif ext_name =='doc': 
        txt=_extract_news_doc(document.url)
    elif ext_name=='html': 
        txt=_extract_news_html(document.url)
    elif ext_name=='docx': 
        txt=_extract_news_docx(document.url)
    elif ext_name=='xls':
        txt=_extract_news_xls(document.url)
    elif ext_name=='rtf':
        txt=_extract_news_rtf(document.url)
    else: 
        raise(ValueError(f"the extension is {ext_name}"))
    return txt 

def _extract_news_pdf (document_url:str,file_name:str=_FILENAME):
    response = requests.get(document_url,timeout=80)
    with open(file_name+'.pdf','wb') as file: 
        file.write(response.content)
    txt=extracting_text(file_name,'pdf')
    return txt

def _extract_news_htm(document_url:str,file_name:str=_FILENAME):
    response = requests.get(document_url)
    with open(file_name +".htm",'w',encoding='utf-8') as file:
        file.write(response.text)
    txt=extracting_text(file_name,'htm')
    return txt

def _extract_news_html(document_url:str,file_name:str=_FILENAME):
    response = requests.get(document_url)
    with open(file_name +".html",'w',encoding='utf-8') as file:
        file.write(response.text)
    txt=extracting_text(file_name,'html')
    return txt
    
def _extract_news_doc(document_url:str,file_name:str=_FILENAME):
    response = requests.get(document_url)
    with open(file_name +".doc",'wb') as file:
        file.write(response.content)
    txt=extracting_text(file_name,'doc')
    return txt
    
def _extract_news_docx(document_url:str,file_name:str=_FILENAME): 
    response = requests.get(document_url)
    with open(file_name+'.docx','wb') as file:
        file.write(response.content)    
    txt=extracting_text(file_name,'docx')
    return txt
    
def _extract_news_xls(document_url:str,file_name:str=_FILENAME):
    response = requests.get(document_url)
    with open(file_name+'.xls','wb') as file:
        file.write(response.content)  
    txt=extracting_text(file_name,'xls')
    return txt
        
def _extract_news_rtf(document_url:str,file_name:str=_FILENAME):
    response = requests.get(document_url)
    with open(file_name+'.rtf', "wb") as f:
        f.write(response.content)
    txt=extracting_text(file_name,'rtf')
    return txt
    
def extracting_all_document(db_path:str=COMPANIES_DB): 
    """extract text of documents of all companies
    and updating the database
    Args:
        db_path (_type_, optional): the sqlite3 database filename. Defaults to COMPANIES_DB.
    """
    con= sqlite3.connect(db_path)
    c=con.cursor()
    
    company_handler=Object2Relational(Company)
    document_handler=Object2Relational(Document)
    
    company_list=company_handler.fetch_all()
    
    for company in company_list: 
        company_id=company.id
        document_list:list[Document]=document_handler.fetch_object_with_columns_values(column_value_pair=[('company_id',company_id)],order_column='publish_at')

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
            
            
            


