from utils.constant import COMPANIES_DB
from company.company import Company
from company.orm import Object2Relational,object2relational_commit
from article.mining import extracting_all_document
from article.hkexnews.parser import get_hkexnews

def generate_document(db_path=COMPANIES_DB): 
    company_hander=Object2Relational(Company)
    all_company=company_hander.fetch_all()
    for one_company in all_company: 
        cp_documents=get_hkexnews(one_company)
        object2relational_commit(cp_documents)
    extracting_all_document(db_path)
    