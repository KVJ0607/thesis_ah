import os 
from pathlib import Path

from utils.constant import COMPANIES_DB



def downloading_document(output_path,db_path=COMPANIES_DB): 
    
    


def downloading_document_old(output_path,company_list): 
    company_list:list[Company]=get_company()
    for company in company_list: 
        print(company.get_hcode())
        os.makedirs(output_path+"/"+company.get_hcode(), exist_ok=True)
        company.set_news_filename()
        print(company.get_id())
        index=0
        print("total doc:"+str(len(company.get_news_list())))
        for new in company.get_news_list():
            new.download_news(index)
            index=index+1       


def update_file_name(file_path):
    companies=get_company()
    for company in companies:

        directory_path=Path(file_path+'/'+company.hcode)
        files = [f for f in directory_path.iterdir() if f.is_file()]
        sorted_files = sorted(files, key=lambda f: int(f.stem),reverse=False)
        index_i=0
        company.news.sort(key=lambda news: news.date_in_date_time, reverse=True)
        for news in company.news:
            news.set_filename(Path(sorted_files[index_i]))
            index_i=index_i+1
    set_company(companies)
