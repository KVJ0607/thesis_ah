import sqlite3
from concurrent.futures import ThreadPoolExecutor
#from article.press_release import * 
#from article.press_release_2 import * 
#from article.press_release_3 import * 
#from article.press_release_4 import * 
from article.press_release_5 import * 
#from article.temp_pr import *
from utils.constant import COMPANIES_DB

def documents_commit(docs:list[Document],cp_id:int):
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
        

# temp_doc,cp_id=Cp_1().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at)
# documents_commit(temp_doc,cp_id)

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
#     print(my_doc_.title," ",my_doc_.published_at )
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

temp_doc,cp_id=Cp_92().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc,cp_id)


