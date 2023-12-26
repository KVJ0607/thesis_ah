import sqlite3
from concurrent.futures import ThreadPoolExecutor
from article.press_release import * 
from utils.constant import COMPANIES_DB

def documents_commit(docs:list[Document]):
    con=sqlite3.connect(COMPANIES_DB)
    c=con.cursor()
    sql_="""
        INSERT INTO document (url,title,published_at,source,content,company_id)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(url,company_id) DO UPDATE SET
        title = excluded.title, 
        published_at = excluded.published_at,
        source = excluded.source ,
        content = excluded.content
        """
    for doc in docs: 
        para=(doc.url,doc.title,doc.published_at,doc.source,doc.content,doc.company_id)
        c.execute(sql_,para)
    con.commit()
    c.close()
    con.close()
        
# all_doc:list[Document]=[]

# temp_doc=Cp_1().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc)

# temp_doc=[]
# temp_doc=Cp_2().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc)

# temp_doc=[]
# temp_doc=Cp_3().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc)

# temp_doc=[]
# temp_doc=Cp_4().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc)

# temp_doc=[]
# temp_doc=Cp_5().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc)



# temp_doc=Cp_6().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc)

# temp_doc=Cp_7().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc)

# temp_doc=Cp_8().crawling()
# for my_doc_ in temp_doc: 
#     print(my_doc_.url)
#     print(my_doc_.title," ",my_doc_.published_at )
# documents_commit(temp_doc)

temp_doc=Cp_9().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)


temp_doc=Cp_10().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)
print('success')
"""
temp_doc=Cp_11().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)


temp_doc=Cp_12().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_13().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_14().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_15().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_16().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_17().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)


temp_doc=Cp_18().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_19().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_20().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_21().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_22().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_23().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_24().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_25().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_26().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_27().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_28().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_29().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_30().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_31().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_32().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_33().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_34().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)


temp_doc=Cp_35().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_36().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_37().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_38().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)


temp_doc=Cp_39().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)


temp_doc=Cp_40().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_41().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_42().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_43().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_44().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_45().crawling()
for my_doc_ in temp_doc: 
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at )
documents_commit(temp_doc)

temp_doc=Cp_46().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title," ",my_doc_.published_at)
documents_commit(temp_doc)


temp_doc=Cp_47().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,my_doc_.published_at )
documents_commit(temp_doc)


temp_doc=Cp_48().crawling()
for my_doc_ in temp_doc:
    print(my_doc_.url)
    print(my_doc_.title,' ',my_doc_.published_at)
documents_commit(temp_doc)
"""
