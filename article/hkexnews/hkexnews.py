from utils.constant import COMPANIES_DB
from company.company import Company,Return,Document,Car3,Causing,CompanyMining
from company.orm import Object2Relational,object2relational_ignore_commit,object2relational_insert_commit
from article.mining import extracting_all_document
from article.hkexnews.parser import get_hkexnews_var3

def _fetch_all_company_without_document(db_path=COMPANIES_DB)->list[Company]: 
    import sqlite3 
    con=sqlite3.connect(db_path)
    c=con.cursor()
    result=c.execute(
        """
        SELECT company.h_code,company.a_code,company.zh_name,company.en_name,company.id
        FROM company 
        JOIN company_mining ON company.id= company_mining.company_id
        WHERE company_mining.document_flag = ? 
        """,(0,)
    ).fetchall()
    result_in_obj=[]
    for one_result in result: 
        result_in_obj.append(Company.from_tuple(one_result))
    c.close()
    con.close()
    return result_in_obj

def generate_document(db_path=COMPANIES_DB): 
    import sqlite3
    from sqlite3 import Error
    from company.orm import general_lookup_with_undetermined_type,object2relational_ignore_commit
    """crawling document found in hkexnews and populate the table docuement

    Args:
        db_path (_type_, optional): sqlite3 . Defaults to COMPANIES_DB.
    """
    #All company that hasn't update hkexnews document
    all_company=_fetch_all_company_without_document()
    for one_company in all_company: 
        cp_documents=get_hkexnews_var3(one_company)
        try: 
            con=sqlite3.connect(db_path)
            c=con.cursor()
            c.execute('BEGIN TRANSACTION;')
            object2relational_ignore_commit(cp_documents,db_path=db_path)
            
            #for all cp, in cp_mining, turn on the document_flag 
            c.execute(
                """
                UPDATE company_mining 
                SET document_flag = ?
                WHERE company_id = ?
                """, (1,one_company.id)
            )
            con.commit()
            print(f'finish commit of {one_company.id}')
        except Error as e:
        # An error occurred, roll back the transaction
            con.rollback()
            print(e)
        finally:
            c.close()
            con.close()    
    extracting_all_document(db_path)

def populate_causing(db_path=COMPANIES_DB): 
    """populate the table causing

    Args:
        db_path (_type_, optional): sqlite3. Defaults to COMPANIES_DB.
    """
    document_handler=Object2Relational(Document)
    car3_handler=Object2Relational(Car3)
    
    #causing:document_id,car3_id,return_id,company_id
    
    documents:list[Document]=document_handler.fetch_all()
    for document_info in documents: 
        doc_id,cp_id,datetime_in_iso=document_info.id,document_info.company_id,document_info.published_at
        date_in_iso= datetime_in_iso.split("'")[0]
        col_requirement={'date=?':date_in_iso,'company_id':cp_id}
        #this car3_in_date_and_company has A flag and H flag version
        car3_in_date_and_company=car3_handler.fetch_object_with_columns_values(column_value_pair=col_requirement,flatten=True)
        causing_obj=[]
        for flagged_car3 in car3_in_date_and_company: 
            flagged_car3:Car3
            car3_id=flagged_car3.id
            ldr_id=flagged_car3.last_day_return_id
            tdr_id=flagged_car3.today_return_id
            ndr_id=flagged_car3.next_day_return_id
            causing_obj.append(Causing(None,doc_id,car3_id,ldr_id,cp_id))
            causing_obj.append(Causing(None,doc_id,car3_id,tdr_id,cp_id))
            causing_obj.append(Causing(None,doc_id,car3_id,ndr_id,cp_id))
        object2relational_insert_commit(causing_obj)
    
    
    