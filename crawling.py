import time
from selenium.common.exceptions import WebDriverException
from company.company import * 
from company.orm import Object2Relational
from urllib.parse import urlparse

def extract_iso_date(string):
    # ISO 8601 date format pattern (basic, without considering week numbers or ordinal dates)
    iso_date_pattern = r'\d{4}-\d{2}-\d{2}'

    # Search for the pattern
    match = re.search(iso_date_pattern, string)
    if match:
        date_str = match.group()
        # Validate that the extracted string is a valid date
        datetime.fromisoformat(date_str)
        return date_str

    else:
        # If no pattern is found, return None
        raise(ValueError('The string does not contain date in iso format'))

def is_internal_link(base_url:str, link:str)->bool:
    """
    Checks whether a given link is an internal link with respect to the base URL.
    
    :param base_url: The base URL of the site.
    :param link: The link to be checked.
    :return: True if the link is internal, False otherwise.
    """
    base_parsed = urlparse(base_url)
    link_parsed = urlparse(link)

    # Links are considered internal if they have the same netloc or
    # if the link doesn't have a netloc but has a path (relative link).
    return (link_parsed.netloc == base_parsed.netloc or not link_parsed.netloc) and link_parsed.scheme in ('', 'http', 'https')

def extract_normal_link(url_list:list[str]): 
    result_list:list[str]=[]
    for url_ in url_list: 
        if (url_ and not url_.startswith('#') and not url_.startswith('mailto:') and not url_.startswith('tel:')and not url_.startswith('javascript:')):
            result_list.append(url_)
    return result_list

def from_tuple_retri(content:str|None,url:str,**args): 
    return_dict= {
        'content':content,
        'err_url':url
    }
    for key_,value_ in args.items(): 
        return_dict[key_]=value_
    return return_dict

def from_tuple_read(doc_list:list[Document],err_url_list:list[str]):
    return{
        'doc_list':doc_list,
        'err_url_list':err_url_list
    }


def get_id_from_h_code(h_code:str): 
    cp_handle=Object2Relational(Company)
    result:Company=cp_handle.fetch_some(('h_code=?',h_code))[0]
    return result.id

def driver_connect(driver,url):
    driver.set_page_load_timeout(60)
    max_attempts=5
    attempts=0
    while attempts<max_attempts: 
        try:
            driver.get(url)
            break
        except WebDriverException as e:
            if "net::ERR_CONNECTION_RESET" in str(e):
                attempts += 1
                print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                time.sleep(5)  # Wait for 5 seconds before retrying
            else: 
                raise(e)

def is_file(url:str): 
    ext=url[-3:]
    if ext == 'pdf': 
        return True
    elif ext =='doc': 
        return True
    elif ext=='docx': 
        return True
    elif ext=='xls':
        return True
    elif ext=='rtf':
        return True
    else: 
        return False


class PressRelease: 
    def __init__(self,base_url:str,press_release_url:str,h_code:str):
        self.__base_url=base_url
        self.__press_release_url=press_release_url
        self.__h_code=h_code
        self.__company_id=get_id_from_h_code(h_code)
        self.__driver_path = '/Users/kelvinyuen/Documents/GitHub/thesis_ah/article/hkexnews/chrome-mac-arm64'
        
    @property
    def base_url(self)->str:
        return self.__base_url
    
    @property
    def press_release_url(self)->str:
        return self.__press_release_url
    
    @property
    def h_code(self)->str:
        return self.__h_code
    
    @property
    def company_id(self):
        return self.__company_id
    
    @property
    def driver_path(self):
        return self.__driver_path
    
    
    def get_id_from_h_code(h_code:str,db_path=COMPANIES_DB):
        pass 
    
    def get_current_page(self,driver)->int:
        pass

    def get_total_page(self,driver)->int:
        pass
    
    def next_page(self,driver)->None:
        pass
    
    def read_page(self,driver)->list[Document]:
        pass 
    
    def crawling(self)->list[Document]: 
        pass 
    
    
