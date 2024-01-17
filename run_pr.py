import logging
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from company.orm import Object2Relational
from utils.crawling import get_id_from_h_code
from article.press_release import * 
from article.press_release_2 import * 
from article.press_release_3 import * 
from article.press_release_4 import * 
from article.press_release_5 import * 
from article.press_release_6 import * 
from article.press_release_7 import * 
from article.press_release_8 import * 
from article.temp_pr import *
from utils.constant import COMPANIES_DB

def delete_other_than_hkex(h_code,db_path=COMPANIES_DB): 

    logging.basicConfig(level=logging.INFO,filename="temp_log.txt")
    try:
        conn = sqlite3.connect(db_path)

        # Create a cursor object
        cursor = conn.cursor()
        sql_delete_query = """
        DELETE FROM document
        WHERE company_id IS NULL
        AND source <> 'HKEXNEWS';
        """
        # Execute the SQL command
        cursor.execute(sql_delete_query)    
    # Commit the changes to the database
        conn.commit()
        print(f"{cursor.rowcount} rows deleted.")
        
    except sqlite3.Error as error:
        # Rollback in case of an error
        conn.rollback()
        print(f"Failed to delete rows from sqlite table. Error: {error}")

    finally:
        # Close the cursor and connection to the database
        cursor.close()
        conn.close()   
        
def fill_up_id(source_url:str,h_code:str): 
    document_handler=Object2Relational(Document)    
    company_id=get_id_from_h_code(h_code)
    document_handler.update_single_col('document','company_id',company_id,'source',source_url)
    
def documents_commit(docs:list[Document],cp_id:int):
    logging.basicConfig(level=logging.INFO,filename="temp_log.txt")
    try:
        print("The cp_id is {}".format(docs[1].company_id))
        refined_docs=[redoc for redoc in docs if redoc.url is not None ]
        print(cp_id,f" len of doc:{len(refined_docs)}")
        con=sqlite3.connect(COMPANIES_DB)
        c=con.cursor()
        sql_="""
            INSERT INTO document (url,title,published_at,source,content,company_id)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(url,company_id) DO UPDATE SET
            title = excluded.title, 
            published_at = excluded.published_at,
            source = excluded.source,
            content = excluded.content,
            company_id = excluded.company_id    
            """
        for redoc in refined_docs: 
            para=(redoc.url,redoc.title,redoc.published_at,redoc.source,redoc.content,cp_id)
            c.execute(sql_,para)
        
        con.commit()
        c.close()
        con.close()
        logging.info(f"Function {cp_id} succeeded.")
    except Exception as e: 
        logging.info(f"Function {cp_id} fail and {e}.")
    finally:
        logging.info(f"Function {cp_id} is now finished.")


temp_doc,cp_id=Cp_1().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc=[]
temp_doc,cp_id=Cp_2().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc=[]
temp_doc,cp_id=Cp_3().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc=[]
temp_doc,cp_id=Cp_4().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc=[]
temp_doc,cp_id=Cp_5().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_6().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_7().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_8().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_9().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_10().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_11().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_12().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_13().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_14().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_15().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_16().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_17().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)



temp_doc,cp_id=Cp_18().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_19().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_20().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_21().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_22().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_23().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_24().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_25().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_26().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_27().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_28().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_29().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_30().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_31().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_32().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_33().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_34().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_35().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_36().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_37().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_38().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)




temp_doc,cp_id=Cp_39().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_40().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_41().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_42().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_43().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_44().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_45().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_46().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_47().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,my_doc_.published_at )
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_48().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)




temp_doc,cp_id=Cp_49().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_50().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_51().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_52().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_53().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_54().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_55().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_56().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_57().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_58().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_59().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)



temp_doc,cp_id=Cp_60().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)



temp_doc,cp_id=Cp_61().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_62().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

Skipped 
temp_doc,cp_id=Cp_63().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_64().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_65().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_66().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_67().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_68().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_69().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_70().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_71().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_72().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_73().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_74().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_75().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_76().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_77().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_78().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_79().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_80().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_81().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_82().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_83().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_84().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_85().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_86().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)



temp_doc,cp_id=Cp_87().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_88().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_89().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_90().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_91().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_92().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_93().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_94().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)



temp_doc,cp_id=Cp_95().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_96().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_97().crawling()
for my_doc_ in temp_doc:
    con_len=len(my_doc_.content)
    start_index=int(con_len/2)
    print(my_doc_.content[start_index:start_index+20])
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_98().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_99().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_100().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_101().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_102().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_103().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_104().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_105().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_106().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_107().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_108().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_109().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_110().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_111().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_112().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_113().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_114().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_115().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_116().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_117().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_118().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_119().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_120().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_121().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_122().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_123().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_124().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_125().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)




temp_doc,cp_id=Cp_125().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_126().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_127().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_128().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_129().crawling(290,251)
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_130().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_131().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_132().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_133().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


temp_doc,cp_id=Cp_134().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_135().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_136().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_137().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_138().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_139().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_141().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_142().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_143().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_144().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_145().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_146().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_148().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_149().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)
