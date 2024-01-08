import logging
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from company.orm import Object2Relational
from utils.crawling import get_id_from_h_code
#from article.press_release import * 
#from article.press_release_2 import * 
#from article.press_release_3 import * 
#from article.press_release_4 import * 
#from article.press_release_5 import * 
#from article.press_release_6 import * 
#from article.press_release_7 import * 
from article.press_release_8 import * 
#from article.temp_pr import *
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


# temp_doc,cp_id=Cp_1().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# fill_up_id("http://www.zjshibao.com/tc/tc_news/list-44.html",Cp_2().h_code)

# fill_up_id("https://btic.cn/news-246.html",Cp_3().h_code)

# fill_up_id("http://www.fd-zj.com/desktopmodules/ht/Big5/News/Index.aspx?LS=1",Cp_4().h_code)


# fill_up_id(Cp_10().press_release_url,Cp_10().h_code)
# fill_up_id(Cp_11().press_release_url,Cp_11().h_code)
# fill_up_id(Cp_13().press_release_url,Cp_13().h_code)
# fill_up_id(Cp_15().press_release_url,Cp_15().h_code)
# fill_up_id(Cp_16().press_release_url,Cp_16().h_code)
# fill_up_id(Cp_17().press_release_url,Cp_17().h_code)

# fill_up_id(Cp_20().press_release_url,Cp_20().h_code)
# fill_up_id(Cp_21().press_release_url,Cp_21().h_code)

# fill_up_id(Cp_23().press_release_url,Cp_23().h_code)
# fill_up_id(Cp_24().press_release_url,Cp_24().h_code)
# fill_up_id(Cp_25().press_release_url,Cp_25().h_code)
# fill_up_id(Cp_27().press_release_url,Cp_27().h_code)
# fill_up_id(Cp_28().press_release_url,Cp_28().h_code)
# fill_up_id(Cp_29().press_release_url,Cp_29().h_code)

#fill_up_id(Cp_26().press_release_url,Cp_26().h_code)
# fill_up_id(Cp_14().press_release_url,Cp_14().h_code)

# fill_up_id(Cp_30().press_release_url,Cp_30().h_code)
# fill_up_id(Cp_32().press_release_url,Cp_32().h_code)
# fill_up_id(Cp_33().press_release_url,Cp_33().h_code)
# fill_up_id(Cp_34().press_release_url,Cp_34().h_code)
# fill_up_id(Cp_35().press_release_url,Cp_35().h_code)
# fill_up_id(Cp_36().press_release_url,Cp_36().h_code)

# fill_up_id(Cp_39().press_release_url,Cp_39().h_code)
# fill_up_id(Cp_40().press_release_url,Cp_40().h_code)

# fill_up_id(Cp_42().press_release_url,Cp_42().h_code)
# fill_up_id(Cp_43().press_release_url,Cp_43().h_code)
# fill_up_id(Cp_44().press_release_url,Cp_44().h_code)
# fill_up_id(Cp_46().press_release_url,Cp_46().h_code)
# fill_up_id(Cp_48().press_release_url,Cp_48().h_code)
# fill_up_id(Cp_49().press_release_url,Cp_49().h_code)
# fill_up_id(Cp_50().press_release_url,Cp_50().h_code)
# fill_up_id(Cp_51().press_release_url,Cp_51().h_code)
# fill_up_id(Cp_52().press_release_url,Cp_52().h_code)
# fill_up_id(Cp_54().press_release_url,Cp_54().h_code)
# fill_up_id(Cp_55().press_release_url,Cp_55().h_code)
# fill_up_id(Cp_57().press_release_url,Cp_57().h_code)
# fill_up_id(Cp_58().press_release_url,Cp_58().h_code)
#fill_up_id(Cp_60().press_release_url,Cp_60().h_code)
#fill_up_id(Cp_61().press_release_url,Cp_61().h_code)

#fill_up_id(Cp_62().press_release_url,Cp_62().h_code)
# fill_up_id(Cp_64().press_release_url,Cp_64().h_code)#ok
# fill_up_id(Cp_65().press_release_url,Cp_65().h_code)#ok
# fill_up_id(Cp_66().press_release_url,Cp_66().h_code)#ok
# fill_up_id(Cp_67().press_release_url,Cp_67().h_code)#ok
# fill_up_id(Cp_68().press_release_url,Cp_68().h_code)#ok
# fill_up_id(Cp_69().press_release_url,Cp_69().h_code)#ok
# fill_up_id(Cp_70().press_release_url,Cp_70().h_code)
# fill_up_id(Cp_71().press_release_url,Cp_71().h_code)
# fill_up_id(Cp_72().press_release_url,Cp_72().h_code)
# fill_up_id(Cp_73().press_release_url,Cp_73().h_code)

# fill_up_id(Cp_75().press_release_url,Cp_75().h_code)
# fill_up_id(Cp_76().press_release_url,Cp_76().h_code)
# fill_up_id(Cp_77().press_release_url,Cp_77().h_code)
# fill_up_id(Cp_78().press_release_url,Cp_78().h_code)
# fill_up_id(Cp_79().press_release_url,Cp_79().h_code)
# fill_up_id(Cp_80().press_release_url,Cp_80().h_code)



# temp_doc=[]
# temp_doc,cp_id=Cp_2().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc=[]
# temp_doc,cp_id=Cp_3().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc=[]
# temp_doc,cp_id=Cp_4().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc=[]
# temp_doc,cp_id=Cp_5().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_6().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_7().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_8().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_9().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_10().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_11().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_12().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_13().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_14().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_15().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_16().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_17().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)



# temp_doc,cp_id=Cp_18().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_19().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_20().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_21().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_22().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_23().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_24().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_25().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_26().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_27().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_28().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_29().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_30().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_31().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_32().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_33().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_34().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_35().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_36().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_37().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_38().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)




# temp_doc,cp_id=Cp_39().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_40().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_41().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_42().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_43().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_44().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_45().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_46().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_47().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,my_doc_.published_at )
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_48().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)




# temp_doc,cp_id=Cp_49().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_50().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_51().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_52().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_53().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_54().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_55().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_56().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_57().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_58().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_59().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)



# temp_doc,cp_id=Cp_60().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)



# temp_doc,cp_id=Cp_61().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_62().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

#Skipped 
# temp_doc,cp_id=Cp_63().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_64().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_65().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)x

# temp_doc,cp_id=Cp_66().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_67().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_68().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_69().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_70().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_71().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_72().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_73().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_74().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_75().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_76().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_77().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_78().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_79().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_80().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_81().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_82().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_83().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_84().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_85().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_86().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)



# temp_doc,cp_id=Cp_87().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_88().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_89().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_90().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_91().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_92().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_93().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_94().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)



# temp_doc,cp_id=Cp_95().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_96().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_97().crawling()
# for my_doc_ in temp_doc:
#     con_len=len(my_doc_.content)
#     start_index=int(con_len/2)
#     print(my_doc_.content[start_index:start_index+20])
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_98().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_99().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_100().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_101().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_102().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_103().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_104().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_105().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_106().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_107().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_108().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_109().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_110().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_111().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_112().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_113().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_114().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_115().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_116().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_117().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_118().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_119().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_120().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_121().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_122().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_123().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_124().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_125().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# fill_up_id(Cp_91().press_release_url,Cp_91().h_code)
# fill_up_id(Cp_92().press_release_url,Cp_92().h_code)
# fill_up_id(Cp_93().press_release_url,Cp_93().h_code)
# fill_up_id(Cp_94().press_release_url,Cp_94().h_code)



# fill_up_id(Cp_95().press_release_url,Cp_95().h_code)
# fill_up_id(Cp_96().press_release_url,Cp_96().h_code)
# fill_up_id(Cp_97().press_release_url,Cp_97().h_code)
# fill_up_id(Cp_98().press_release_url,Cp_98().h_code)
# fill_up_id(Cp_99().press_release_url,Cp_99().h_code)


# fill_up_id(Cp_100().press_release_url,Cp_100().h_code)
# fill_up_id(Cp_101().press_release_url,Cp_101().h_code)
# fill_up_id(Cp_102().press_release_url,Cp_102().h_code)
# fill_up_id(Cp_103().press_release_url,Cp_103().h_code)
# fill_up_id(Cp_104().press_release_url,Cp_104().h_code)
# fill_up_id(Cp_105().press_release_url,Cp_105().h_code)
# fill_up_id(Cp_106().press_release_url,Cp_106().h_code)
# fill_up_id(Cp_107().press_release_url,Cp_107().h_code)
# fill_up_id(Cp_108().press_release_url,Cp_108().h_code)
# fill_up_id(Cp_109().press_release_url,Cp_109().h_code)
# fill_up_id(Cp_110().press_release_url,Cp_110().h_code)
# fill_up_id(Cp_111().press_release_url,Cp_111().h_code)


# fill_up_id(Cp_81().press_release_url,Cp_81().h_code)
# fill_up_id(Cp_82().press_release_url,Cp_82().h_code)
# fill_up_id(Cp_83().press_release_url,Cp_83().h_code)
# fill_up_id(Cp_84().press_release_url,Cp_84().h_code)
# fill_up_id(Cp_85().press_release_url,Cp_85().h_code)
# fill_up_id(Cp_86().press_release_url,Cp_86().h_code)
# fill_up_id(Cp_87().press_release_url,Cp_87().h_code)
# fill_up_id(Cp_88().press_release_url,Cp_88().h_code)
# fill_up_id(Cp_89().press_release_url,Cp_89().h_code)
# fill_up_id(Cp_90().press_release_url,Cp_90().h_code)

# fill_up_id(Cp_100().press_release_url,Cp_100().h_code)
# fill_up_id(Cp_101().press_release_url,Cp_101().h_code)
# fill_up_id(Cp_102().press_release_url,Cp_102().h_code)
# fill_up_id(Cp_103().press_release_url,Cp_103().h_code)
# fill_up_id(Cp_104().press_release_url,Cp_104().h_code)
# fill_up_id(Cp_105().press_release_url,Cp_105().h_code)
# fill_up_id(Cp_106().press_release_url,Cp_106().h_code)
# fill_up_id(Cp_107().press_release_url,Cp_107().h_code)
# fill_up_id(Cp_108().press_release_url,Cp_108().h_code)
# fill_up_id(Cp_109().press_release_url,Cp_109().h_code)
# fill_up_id(Cp_110().press_release_url,Cp_110().h_code)
# fill_up_id(Cp_111().press_release_url,Cp_111().h_code)

# fill_up_id(Cp_112().press_release_url,Cp_112().h_code)
# fill_up_id(Cp_113().press_release_url,Cp_113().h_code)
# fill_up_id(Cp_114().press_release_url,Cp_114().h_code)
# fill_up_id(Cp_115().press_release_url,Cp_115().h_code)
# fill_up_id(Cp_116().press_release_url,Cp_116().h_code)
# fill_up_id(Cp_117().press_release_url,Cp_117().h_code)
# fill_up_id(Cp_118().press_release_url,Cp_118().h_code)
# fill_up_id(Cp_119().press_release_url,Cp_119().h_code)



# fill_up_id(Cp_120().press_release_url,Cp_120().h_code)
# fill_up_id(Cp_121().press_release_url,Cp_121().h_code)
# fill_up_id(Cp_122().press_release_url,Cp_122().h_code)
# fill_up_id(Cp_123().press_release_url,Cp_123().h_code)
# fill_up_id(Cp_124().press_release_url,Cp_124().h_code)


# temp_doc,cp_id=Cp_125().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_126().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_127().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_128().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_129().crawling(290,251)
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_130().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_131().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_132().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_133().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)


# temp_doc,cp_id=Cp_134().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_135().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_136().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_137().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_138().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_139().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_141().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_142().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_143().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_144().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_145().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_146().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

# temp_doc,cp_id=Cp_148().crawling()
# for my_doc_ in temp_doc:
#     print(my_doc_.url)
#     print(my_doc_.title,' ',my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

temp_doc,cp_id=Cp_149().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)
