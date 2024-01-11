import sqlite3
import logging
from company.company import *
from company.orm import Object2Relational,object2relational_ignore_commit
from sentiment.load_dict import load_dict_from_csv,load_dict_from_csv_eng,load_stopwords,load_stopwords_en
from utils.crawling import get_id_from_h_code,get_h_code_from_id

def calculate_tone_sums(text, tone_dict, stopwords):
    # Initialize counters for positive and negative tones
    positive_sum = 0
    negative_sum = 0

    # Split the text into words and remove stopwords
    words = text.split()
    filtered_words = [word for word in words if word not in stopwords]
    filtered_text = ' '.join(filtered_words)

    # Iterate through the dictionary to count positive and negative instances
    for phrase, flags in tone_dict.items():
        # Count occurrences of the phrase in the filtered text
        count = filtered_text.count(phrase)
        
        # Update positive and negative sums
        if 'positive' in flags:
            positive_sum += count * flags['positive']
        if 'negative' in flags:
            negative_sum += count * flags['negative']

    return positive_sum, negative_sum

def cal_tone_score():
    
    zh_dict=load_dict_from_csv()
    en_dict=load_dict_from_csv_eng()

    zh_stopwords=load_stopwords()
    en_stopwords=load_stopwords_en()
    #skip ['00719.hk','06178.hk','01800.hk','06099.hk','01336.hk','02607.hk','00753.hk','01898.hk','06690.hk','03996.hk','01766.hk','01816.hk','06881.hk','06881.hk','06066.hk']
    skip_h_code=set(['00719.hk','06178.hk','01800.hk','06099.hk','01336.hk','02607.hk','00753.hk','01898.hk','06690.hk'])
    skip_h_code.add('03996.hk')
    skip_h_code.add('01766.hk')
    skip_h_code.add('01816.hk')
    skip_h_code.add('06881.hk')
    skip_h_code.add('06066.hk')
    eng_h_code=set(['06821.hk','00914.hk','01288.hk','01088.hk','01398.hk','01919.hk','02359.hk'])
    tone_list:list[Tonescore]=[]
    for i in range(1,150): 
        try:
            cp_id=i 
            doc_h_code= get_h_code_from_id(cp_id)
            en_flag=False
            if doc_h_code in eng_h_code: 
                en_flag=True
            doc_handler=Object2Relational(Document)
            doc_list:list[Document]
            doc_list=doc_handler.fetch_some(('company_id=?',cp_id),('source <>?','HKEXNEWS'),('content IS NOT NULL',None))
            
            
            for doc_ in doc_list: 
                if doc_h_code in skip_h_code: 
                    continue
                doc_content=doc_.content
                if en_flag:
                    pos_tone,neg_tone=calculate_tone_sums(doc_content,en_dict,en_stopwords)
                else:
                    pos_tone,neg_tone=calculate_tone_sums(doc_content,zh_dict,zh_stopwords)
                net_score=pos_tone-neg_tone
                
                #tonescore	positive_tonescore	negative_tonescore	id	document_id	company_id
                tone_list.append(Tonescore(tonescore=net_score,positive_tonescore=pos_tone,negative_tonescore=neg_tone,id=None,document_id=doc_.id,company_id=cp_id,is_hkex=0))
            print(f"company tone {cp_id} succeeded.")
            logging.info(f"company tone {cp_id} succeeded.")
        except Exception as e:            
            print("An error occurred for {}: {}".format(cp_id, e))
            logging.error("An error occurred for %s: %s", str(cp_id),str(e))
            continue
    return tone_list

def cal_tone_score_hkex():
    
    zh_dict=load_dict_from_csv()
    en_dict=load_dict_from_csv_eng()

    zh_stopwords=load_stopwords()
    en_stopwords=load_stopwords_en()

    skip_h_code=set(['00719.hk','06178.hk','01800.hk','06099.hk','01336.hk','02607.hk','00753.hk','01898.hk','06690.hk'])
    eng_h_code=set(['06821.hk','00914.hk','01288.hk','01088.hk','01398.hk','01919.hk','02359.hk'])
    tone_list:list[Tonescore]=[]
    for i in range(1,150): 
        try:
            cp_id=i 
            doc_h_code= get_h_code_from_id(cp_id)
            en_flag=False
            if doc_h_code in eng_h_code: 
                en_flag=True
            doc_handler=Object2Relational(Document)
            doc_list:list[Document]
            doc_list=doc_handler.fetch_some(('company_id=?',cp_id),('source =?','HKEXNEWS'),('content IS NOT NULL',None))
            
            
            for doc_ in doc_list: 
                if doc_h_code in skip_h_code: 
                    continue
                doc_content=doc_.content
                if en_flag:
                    pos_tone,neg_tone=calculate_tone_sums(doc_content,en_dict,en_stopwords)
                else:
                    pos_tone,neg_tone=calculate_tone_sums(doc_content,zh_dict,zh_stopwords)
                net_score=pos_tone-neg_tone
                
                #tonescore	positive_tonescore	negative_tonescore	id	document_id	company_id
                tone_list.append(Tonescore(tonescore=net_score,positive_tonescore=pos_tone,negative_tonescore=neg_tone,id=None,document_id=doc_.id,company_id=cp_id,is_hkex=1))
            print(f"company tone {cp_id} succeeded.")
            logging.info(f"company tone {cp_id} succeeded.")
        except Exception as e:            
            print("An error occurred for {}: {}".format(cp_id, e))
            logging.error("An error occurred for %s: %s", str(cp_id),str(e))
            continue
    return tone_list



        

def cal_tone_merge():
    tone_merge_list = []
    with sqlite3.connect(COMPANIES_DB) as conn:
        cursor = conn.cursor()
        for cp_id in range(1, 150):
            query = """
            SELECT SUM(tonescore.tonescore) AS sum_r_tonescore,
                   SUM(tonescore.positive_tonescore) AS sum_r_positive_tonescore,
                   SUM(tonescore.negative_tonescore) AS sum_r_negative_tonescore,
                   strftime('%Y-%m-%d', document.published_at) AS date_only,
                   tonescore.company_id
            FROM tonescore
            JOIN document ON tonescore.document_id = document.id
            WHERE tonescore.is_hkex = 0 AND tonescore.company_id = ?
            GROUP BY date_only
            ORDER BY date_only 
            """
            cursor.execute(query, (cp_id,))
            results = cursor.fetchall()
            # Assuming TonescoreMerge is a namedtuple or a class that takes these parameters in order.
            for row in results:
                r_tone,r_positive,r_negative,date,cp_id=row
                tone_merge_list.append(TonescoreMerge(r_tone,r_positive,r_negative,date,None,cp_id,0))

    return tone_merge_list

def cal_tone_merge_hkex():
    tone_merge_list = []
    with sqlite3.connect(COMPANIES_DB) as conn:
        cursor = conn.cursor()
        for cp_id in range(1, 150):
            query = """
            SELECT SUM(tonescore.tonescore) AS sum_r_tonescore,
                   SUM(tonescore.positive_tonescore) AS sum_r_positive_tonescore,
                   SUM(tonescore.negative_tonescore) AS sum_r_negative_tonescore,
                   strftime('%Y-%m-%d', document.published_at) AS date_only,
                   tonescore.company_id
            FROM tonescore
            JOIN document ON tonescore.document_id = document.id
            WHERE tonescore.is_hkex = 1 AND tonescore.company_id = ?
            GROUP BY date_only
            ORDER BY date_only 
            """
            cursor.execute(query, (cp_id,))
            results = cursor.fetchall()
            # Assuming TonescoreMerge is a namedtuple or a class that takes these parameters in order.
            for row in results:
                r_tone,r_positive,r_negative,date,cp_id=row
                tone_merge_list.append(TonescoreMerge(r_tone,r_positive,r_negative,date,None,cp_id,1))

    return tone_merge_list






def cal_tone_merge_old():
    tone_merge_list:list[TonescoreMerge]=[]
    with sqlite3.connect(COMPANIES_DB) as conn:         
        cursor=conn.cursor()
        query="""
        SELECT tonescore.*,
            CASE
                WHEN typeof(document.published_at) = 'text' AND
                        strftime('%Y-%m-%d', document.date_column) IS NOT NULL THEN
                        strftime('%Y-%m-%d', document.date_column)
                ELSE NULL
            END AS date_only
        FROM tonescore 
        JOIN document on tonescore.document_id = document.id
        WHERE tonescore.is_hkex = 0
        ORDERED BY document.published_at            
        """ 
              
        non_hkex_tones=cursor.execute(query).fetchall() 
        non_hkex_tones=[one_tone for one_tone in non_hkex_tones if one_tone[7] is not None]
        for cp_id in range(1,150):
            cp_non_hkex_tones=[one_tone for one_tone in non_hkex_tones if one_tone[5]==cp_id]            
            last_date=cp_non_hkex_tones[0][7]
            r_tonescore=0
            r_positive_tonescore=0
            r_negative_tonescore=0
            for i,cp_tone in enumerate(cp_non_hkex_tones):                 
                cp_date=cp_tone[7]                
                if cp_date==last_date:
                    r_tonescore=r_tonescore+cp_tone[0]
                    r_positive_tonescore=r_positive_tonescore+cp_tone[1]
                    r_negative_tonescore=r_negative_tonescore+cp_tone[2]
                    last_date=cp_tone[7]
                    if i==len(cp_non_hkex_tones)-1: 
                        tone_merge_list.append(TonescoreMerge(r_tonescore,r_positive_tonescore,r_negative_tonescore,last_date,None,cp_id,0))    
                else:
                    tone_merge_list.append(TonescoreMerge(r_tonescore,r_positive_tonescore,r_negative_tonescore,last_date,None,cp_id,0))
                    r_tonescore=cp_tone[0]
                    r_positive_tonescore=cp_tone[1]
                    r_negative_tonescore=cp_tone[2]                                    
                    last_date=cp_tone[7]

def cal_tone_merge_hkex_old():
    tone_merge_list:list[TonescoreMerge]=[]
    with sqlite3.connect(COMPANIES_DB) as conn:         
        cursor=conn.cursor()
        query="""
        SELECT tonescore.*,
            CASE
                WHEN typeof(document.published_at) = 'text' AND
                        strftime('%Y-%m-%d', document.date_column) IS NOT NULL THEN
                        strftime('%Y-%m-%d', document.date_column)
                ELSE NULL
            END AS date_only
        FROM tonescore 
        JOIN document on tonescore.document_id = document.id
        WHERE tonescore.is_hkex = 1 AND date_only IS NOT NULL
        ORDER BY document.published_at            
        """ 
              
        hkex_tones=cursor.execute(query).fetchall() 
        hkex_tones=[one_tone for one_tone in hkex_tones if one_tone[7] is not None]
        for cp_id in range(1,150):
            cp_hkex_tones=[one_tone for one_tone in hkex_tones if one_tone[5]==cp_id]            
            last_date=cp_hkex_tones[0][7]
            r_tonescore=0
            r_positive_tonescore=0
            r_negative_tonescore=0
            for i,cp_tone in enumerate(cp_hkex_tones):                 
                cp_date=cp_tone[7]                
                if cp_date==last_date:
                    r_tonescore=r_tonescore+cp_tone[0]
                    r_positive_tonescore=r_positive_tonescore+cp_tone[1]
                    r_negative_tonescore=r_negative_tonescore+cp_tone[2]
                    last_date=cp_tone[7]
                    if i==len(cp_hkex_tones)-1: 
                        tone_merge_list.append(TonescoreMerge(r_tonescore,r_positive_tonescore,r_negative_tonescore,last_date,None,cp_id,1))    
                else:
                    tone_merge_list.append(TonescoreMerge(r_tonescore,r_positive_tonescore,r_negative_tonescore,last_date,None,cp_id,1))
                    r_tonescore=cp_tone[0]
                    r_positive_tonescore=cp_tone[1]
                    r_negative_tonescore=cp_tone[2]                                    
                    last_date=cp_tone[7]
                
                
                                

            
                
            

