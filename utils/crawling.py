import sqlite3
from company.orm import Object2Relational
import time
from selenium.common.exceptions import WebDriverException
from company.company import * 
from company.orm import Object2Relational
from urllib.parse import urlparse

from bs4 import BeautifulSoup, SoupStrainer, Comment
import urllib.request
from urllib.parse import urljoin

from lxml import etree
import multiprocessing
from itertools import chain

def tag_visible(element):
    if element.parent.name in ('style', 'script', 'head', 'title', 'meta', '[document]'):
        return False
    if isinstance(element, Comment):
        return False
    return True

def text_from_html(body):
    # Use lxml for faster parsing
    only_body = SoupStrainer('body')
    soup = BeautifulSoup(body, 'lxml',parse_only=only_body)
    visible_texts = []
    for element in soup.descendants:
    # Skip any Comment elements or empty strings
        if isinstance(element, Comment) or isinstance(element, str) and not element.strip():
            continue
        if element.parent.name in ('script', 'style', 'head', 'title', 'meta', '[document]'):
            continue        
        # Add the stripped string of the element to our list
        text = element.string.strip()
        if text:
            visible_texts.append(text)
    # Join all the texts collected
    return ' '.join(visible_texts)        
        
    


# def text_from_html(body):
#     # Parse the HTML content using lxml
#     parser = etree.HTMLParser()
#     tree = etree.fromstring(body, parser)
    
#     # Get all the text within the document
#     texts = tree.xpath("//body//text()[not(ancestor::script) and not(ancestor::style) and not(ancestor::head) and not(ancestor::title) and not(ancestor::meta)]")
    
#     # Filter out whitespace strings and join non-empty strings
#     return ' '.join(filter(None, (t.strip() for t in texts)))

def make_full_url(base_url, relative_url_info):
    """
    take something like: location.href='../news_center/news_detail.html?id=830' and a base url 
    then return the full url
    
    """
    relative_url = relative_url_info.split('=')[1].strip('\'"')
    full_url = urljoin(base_url, relative_url)
    
    return full_url


def reverse_date_in_str(string:str): 
    if type(string) != str: 
        mes_="the date string should be of type string, not {}".format(type(string))
        raise(TypeError(mes_))
    else: 
        parts = string.split('-')
        return f"{parts[2]}-{parts[1]}-{parts[0]}"

def is_iso_date(string): 
    if string ==None or type(string)!=str: 
        return False
    iso_date_pattern = r'(\d{4}-\d{2}-\d{2})'
    iso_date_pattern2 = r'(\d{4}-\d{1}-\d{1})'
    iso_date_pattern3 = r'(\d{4}-\d{1}-\d{2})'
    iso_date_pattern4 = r'(\d{4}-\d{2}-\d{1})'
    
    match = re.search(iso_date_pattern, string)
    match2 = re.search(iso_date_pattern2, string)
    match3 = re.search(iso_date_pattern3, string)
    match4 = re.search(iso_date_pattern4, string)
    
    test_set=set()
    test_set.update([match,match2,match3,match4])
    
    if len(test_set) >1: 
        return True 
    else: 
        return False
    
def extract_iso_date(string):
    # ISO 8601 date format pattern (basic, without considering week numbers or ordinal dates)
    iso_date_pattern = r'(\d{4}-\d{2}-\d{2})'
    iso_date_pattern2 = r'(\d{4}-\d{1}-\d{1})'
    iso_date_pattern3 = r'(\d{4}-\d{1}-\d{2})'
    iso_date_pattern4 = r'(\d{4}-\d{2}-\d{1})'
    # Search for the pattern
    match = re.search(iso_date_pattern, string)
    if match:
        date_str = match.group()
        # Validate that the extracted string is a valid date
    else: 
        match2 = re.search(iso_date_pattern2, string)
        match3 = re.search(iso_date_pattern3, string)
        match4 = re.search(iso_date_pattern4, string)
        if match2: 
            date_str_ele=match2.group()
            date_str=date_str_ele[0:5]+'0'+date_str_ele[5:7]+'0'+date_str_ele[7:8]
        elif match3: 
            date_str_ele=match3.group()
            date_str=date_str_ele[0:5]+'0'+date_str_ele[5:7]+date_str_ele[7:9]
        elif match4:
            date_str_ele=match4.group()
            date_str=date_str_ele[0:5]+date_str_ele[5:8]+'0'+date_str_ele[8:9]
        else:
            if string is None:
                print('The input string is None')
                raise(ValueError('The input string is None'))
            else:
                print(f'This string does not contain date in iso format {string}')
                raise(ValueError('The string does not contain date in iso format'))
    return date_str

def is_internal_link(base_url:str, link:str)->bool:
    """
    Checks whether a given link is an internal link with respect to the base URL.
    
    :param base_url: The base URL of the site.
    :param link: The link to be checked.
    :return: True if the link is internal, False otherwise.
    """
    if  type(link) != str: 
        return False
    if isinstance(link, bytes):
        link = link.decode('utf-8')
        
    base_parsed = urlparse(base_url)
    link_parsed = urlparse(link)
    # Normalize the base domain to exclude 'www.' for consistent comparison
    base_domain = base_parsed.netloc.replace('www.', '')
    link_domain = link_parsed.netloc.replace('www.', '')
    
    # Links are considered internal if they have the same domain or subdomain
    return (link_domain == base_domain or link_domain.endswith('.' + base_domain)) and link_parsed.scheme in ('', 'http', 'https')

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
    result:Company=cp_handle.fetch_some(('h_code=?',h_code.lower()))[0]
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
    if type(url) !=str: 
        return False
    ext=url[-3:].lower()
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
        company_handler=Object2Relational(Company)
        result_id=company_handler.fetch_some(('h_code=',h_code))
        return result_id
        
    
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
    
    
