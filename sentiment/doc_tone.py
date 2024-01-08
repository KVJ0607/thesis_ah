
from company.company import *
from company.orm import Object2Relational
from sentiment.load_dict import load_dict_from_csv,load_dict_from_csv_eng,load_stopwords,load_stopwords_en
from utils.crawling import get_id_from_h_code

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


zh_dict=load_dict_from_csv()
en_dict=load_dict_from_csv_eng()

zh_stopwords=load_stopwords()
en_stopwords=load_stopwords_en()

skip_h_code=set(['00719.HK','06178.HK','01800.HK','06099.HK','01336.HK','02607.HK','00753.HK','01898.HK','06690.HK'])
eng_h_code=set(['06821.HK','00914.HK','01288.HK','01088.HK','01398.HK','01919.HK','02359.HK'])
for i in range(1,150): 
    cp_id=i 
    doc_h_code= get_id_from_h_code(cp_id)
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
        pos_tone,neg_tone=calculate_tone_sums(doc_content)
        net_score=pos_tone-neg_tone
        ()
        



        

# from company.orm import Object2Relational
# from company.company import *
# doc_handler=Object2Relational(Document)
# doc_list:list[Document]
# doc_list=doc_handler.fetch_some(('company_id=?',130),('source <>?','HKEXNEWS'))

# print(len(doc_list))
# for doc_ in doc_list[0:20]: 
#     print(doc_.content)
#     print(doc_.company_id)
