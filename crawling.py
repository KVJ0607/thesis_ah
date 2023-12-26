import time
from selenium.common.exceptions import WebDriverException
from company.company import * 
from company.orm import Object2Relational
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
    
    
