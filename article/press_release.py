import re
import time
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException, StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException, TimeoutException, WebDriverException, InvalidArgumentException
from selenium.webdriver.common.keys import Keys
from joblib import Parallel, delayed
from bs4 import BeautifulSoup
from datetime import datetime
from utils.exception import MaxErrorReached
from crawling import PressRelease, driver_connect, is_file,from_tuple_retri,from_tuple_read,extract_normal_link,is_internal_link,extract_iso_date
from company.company import *
from article.mining import _extracting_an_document
ERROR_COUNT = 20

class Cp_1(PressRelease):
    def __init__(self):
        base_url = "https://www.ftol.com.cn/"
        press_release_url = "https://www.ftol.com.cn/main/yfzx/cjxw/cjyw/index.shtml"
        h_code = "03678.hk"
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        #robot.txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,138)
    
    def next_page(self,cur_page:int,driver:WebDriver)->None:
        button = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#next_page")))
        driver.execute_script("arguments[0].click();", button)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        #check url is not empty
        if url is None:
            return from_tuple_retri(None,url)
        #extract txt if it is a document
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print("error in retrieve_content")
                return from_tuple_retri(None,url)
        #driver connect to url
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("--headless")
        driver2 = webdriver.Chrome(options=chrome_options)        
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
                
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute("href")                                
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(new_url)                    
            url_list=extract_normal_link(url_list)[:5]
            
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            print(f"Warning in extracting content from other url elements from one url in retrieve_content function:{url}")
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,"body div.Research_center_box div.early_box").text
        except Exception:
            print("error in retrieve_content")
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f"error in retrieve_content, content is empty, {url}")
            driver2.quit()
            return from_tuple_retri("",url)            
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.nr > div.Re_three > ul")))
            rows=target_ele.find_elements(By.TAG_NAME,"li")
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a")
                url=url_ele.get_attribute("href")
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.TAG_NAME, 'span').text)
                if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
                else:
                    continue
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
        content_list = Parallel(n_jobs=-1)(delayed(Cp_1.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(Exception("reach maximum error count"))
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)
        


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if "net::ERR_CONNECTION_RESET" in str(e):
                        attempts+=1
                        print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                        time.sleep(5)  # Wait for 5 seconds before retrying
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list        
                err_url_list=read_page_result["err_url_list"] 
                all_err_url=all_err_url+err_url_list               
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e: 
            raise(MaxErrorReached(all_err_url,self.company_id))
            
class Cp_2(PressRelease):
    def __init__(self):
        base_url='http://www.zjshibao.com/tc/index.html'
        press_release_url='http://www.zjshibao.com/tc/tc_news/list-44.html'
        h_code='01057.HK'.lower()
        super().__init__(base_url, press_release_url, h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,1)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        pass

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        #check url is not empty
        if url is None:
            return from_tuple_retri(None,url)
        #extract txt if it is a document
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)[:5]
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
            
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR, '#mm-0>div.nybody_box').text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#mm-0>div.nybody_box>div.wrap>div.nybox_box>div.nybox_right>ul.nynews_box")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a")
                url=url_ele.get_attribute('href')
                title=row_.find_element(By.CSS_SELECTOR,"div.name.ovh").text
                date_in_iso=extract_iso_date(row_.find_element(By.CSS_SELECTOR, 'div.time').text)
                if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
                else:
                    continue
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
                
        content_list = Parallel(n_jobs=-1)(delayed(Cp_2.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            # chrome_options.add_argument('--headless')
            # driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)  # Wait for 5 seconds before retrying
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_3(PressRelease):
    def __init__(self):
        base_url = 'https://www.jingchenggf.cn/'
        press_release_url = 'https://btic.cn/news-246.html'
        h_code = '00187.hk'.lower()
        super().__init__(base_url, press_release_url, h_code)
        self.__error_count = 0
        self.__robots_txt = None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,9)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//body/div[@class='wrap']/div[contains(@class,'page') and contains(@class,'flex')]//a[last()]")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        
        if url is None:
            return from_tuple_retri(None,url)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)[:5]
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
            
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR, 'body > div.wrap').text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body>div.wrap>ul.support_list')))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a")
                url=url_ele.get_attribute('href')
                date_in_iso=extract_iso_date(row_.find_element(By.TAG_NAME, 'span').text)
                title=url_ele.text.replace(date_in_iso,'').strip()
                if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
                else:
                    continue
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
        content_list = Parallel(n_jobs=-1)(delayed(Cp_3.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            # chrome_options.add_argument('--headless')
            # driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_4(PressRelease):
    def __init__(self):
        base_url = 'http://www.fd-zj.com/'
        press_release_url = 'http://www.fd-zj.com/desktopmodules/ht/Big5/News/Index.aspx?LS=1'
        h_code = '01349.hk'.lower()
        super().__init__(base_url, press_release_url, h_code)
        self.__error_count = 0
        self.__robots_txt = None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1
    

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,6)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,f"//body//tbody//tr//a[text()='{cur_page+1}']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:        
        if url is None:
            return from_tuple_retri(None,url)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)[:5]
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//td[@class='word']").text            
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 15)
        try:
            rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li")))
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        #pattern=r"^(.*)\s+(\d{4}-\d{2}-\d{2})$"
        
        for row_ in rows:
            try:
                
                url_ele=row_.find_element(By.XPATH,".//a[1]")
                url=url_ele.get_attribute('href')                
                url_text=url_ele.text.strip()                
                url_info=url_text.split(' ')
                if len(url_info)!=2: 
                    self.add_error_count()
                    print(f'problem with url info: {url_text}')
                    continue
                title=url_info[0]
                date_in_iso=extract_iso_date(url_info[1])
                if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
                else:
                    continue
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
        content_list = Parallel(n_jobs=-1)(delayed(Cp_4.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            # chrome_options.add_argument('--headless')
            # driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_5(PressRelease):
    def __init__(self):
        base_url = 'https://www.shandongxinhuapharma.com/'
        press_release_url = 'https://www.shandongxinhuapharma.com/'
        h_code = '00719.HK'.lower()
        super().__init__(base_url, press_release_url, h_code)
        self.__error_count=0
        self.__robots_txt = None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        #return min(100,)
        pass 

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        # wait = WebDriverWait(driver, 10)
        # #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        # driver.execute_script('arguments[0].click();', page_div)
        pass

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        pass         
        # if url is None:
        #     return from_tuple_retri(None,url)
        
        # isfile=is_file(url)
        # if isfile:
        #     try:
        #         txt=_extracting_an_document(Document.from_url(url))
        #         return from_tuple_retri(txt,"")
        #     except Exception as e:
        #         print(f'error in retrieve_content: {url}')
        #         return from_tuple_retri(None,url)
        
        # url_list:list[str]=[]
        # chrome_options = Options()
        # chrome_options.add_argument("--enable-javascript")
        # chrome_options.add_argument('--headless')
        # driver2 = webdriver.Chrome(options=chrome_options)
        # driver2.set_page_load_timeout(30) 
        # max_attempts=5
        # attempts=0 
        # while attempts<max_attempts: 
        #     try:
        #         driver2.get(url)
        #         break
        #     except WebDriverException as e:
        #         attempts += 1
        #         if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
        #             print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
        #             time.sleep(5)  # Wait for 5 seconds before retrying
        #         else: 
        #             return from_tuple_retri(None,url)
        
        # try:
        #     url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
        #     for url_ele in url_eles:
        #         new_url=url_ele.get_attribute('href')
        #         isfile_2=is_file(new_url)
        #         if isfile_2:
        #             url_list.append(url_ele.get_attribute('href'))
        #     url_list=extract_normal_link(url_list)[:5]
        #     total_txt=""
        #     for url_ in url_list:
        #         total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        # except Exception as e:
        #     ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            #b=True
        # try:
        #     #target_ele=driver2.find_element(By.XPATH,"").text
        # except Exception:
        #     print(f'error in retrieve_content: {url}')
        #     driver2.quit()
        #     return from_tuple_retri(None,url)
        # if target_ele==0 or target_ele==None:
        #     print(f'error in retrieve_content, content is empty, {url}')
        #     from_tuple_retri("","")
        # driver2.quit()
        #return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        pass 
        # wait = WebDriverWait(driver, 10)
        # try:
        #     #target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "")))
        #     rows=target_ele.find_elements(By.TAG_NAME,'li')
        # except Exception as e:
        #     if self.error_count<ERROR_COUNT:
        #         self.add_error_count(5)
        #         return from_tuple_read([],[driver.current_url])
        #     else:
        #         raise(MaxErrorReached())
        # document_list:list[Document]=[]
        # urls:list[str]=[]
        # err_urls:list[str]=[]
        # for row_ in rows:
        #     try:
        #         #url_ele=row_.find_element(By.XPATH,"")
        #         url=url_ele.get_attribute('href')
        #         title=url_ele.text
        #         #date_in_iso=extract_iso_date(row_.find_element(By.XPATH,"")
        #         if is_internal_link(base_url=self.base_url,link=url):
                #     urls.append(url)
                # else:
                #     continue
        #         document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        #     except Exception as e:
        #         if self.error_count<ERROR_COUNT:
        #             self.add_error_count()
        #             continue
        #         else:
        #             raise(MaxErrorReached())
        # content_list = Parallel(n_jobs=-1)(delayed(Cp_5.retrieve_content)(url) for url in urls)
        # for i in range(len(content_list)):
        #     document_list[i].set_content(content_list[i]["content"])
        #     err_url=content_list[i]["err_url"]
        #     if err_url!="" or err_url!=None:
        #         self.add_error_count()
        #         err_urls.append(err_url)
        #         if self.error_count>ERROR_COUNT:
        #             raise(MaxErrorReached())
        # return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        return [],self.company_id
        # try:
        #     all_err_url:list[str]=[]
        #     chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        #     chrome_options.add_argument('--headless')
        #     driver = webdriver.Chrome(options=chrome_options)
        #     max_attempts=5
        #     attempts=0
        #     while attempts<max_attempts:
        #         try:
        #             driver.get(self.press_release_url)
        #             break
        #         except WebDriverException as e:
        #             if 'net::ERR_CONNECTION_RESET' in str(e):
        #                 attempts+=1
        #                 print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
        #                 time.sleep(5)
        #             else:
        #                 print('Problem with requesting the main page')
        #                 raise(e)
        #     time.sleep(0.5)
        #     total_page=self.get_total_page(driver)
        #     current_page=self.get_current_page(driver)
        #     all_doc:list[Document]=[]
        #     while(current_page<=total_page):
        #         read_page_result=self.read_page(driver)
        #         doc_list=read_page_result["doc_list"]
        #         all_doc=all_doc+doc_list
        #         err_url_list=read_page_result["err_url_list"]
        #         all_err_url=all_err_url+err_url_list
        #         if(current_page<total_page):
        #             self.next_page(current_page,driver)
        #         time.sleep(0.5)
        #         current_page=current_page+1
        #     driver.quit()
        #     return all_doc,self.company_id
        # except MaxErrorReached as e:
        #     raise(MaxErrorReached(all_err_url,self.company_id))
        
class Cp_6(PressRelease):
    def __init__(self):
        base_url="https://www.panda.cn/"
        press_release_url="https://www.panda.cn/qyxw/list_31.aspx"
        h_code="00553.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,112)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@class='Page']//a[contains(text(),' > ')]")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        
        if url is None:
            return from_tuple_retri(None,url)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            
            url_list=extract_normal_link(url_list)[:5]
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='SinglePage']").text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='NewsList']//ul")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//div[@class='LiRight']/h4/a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//div[@class='LiRight']/h4/span").text)
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_6.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            # chrome_options.add_argument('--headless')
            # driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
        
class Cp_7(PressRelease):
    def __init__(self):
        base_url='https://www.group.citic/'
        press_release_url='https://www.group.citic/html/medias/media_news/'
        h_code='06066.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,11)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        xpath_=f"//div[@class='content_box']//ul[@class='clearfix']//a[normalize-space(text())='{cur_page+1}']"
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,xpath_)))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=None)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"",date_in_iso=None)
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=None)
        
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0
        while attempts<max_attempts:
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,target_date=None)
        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)[:5]
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='main-content']").text
            date_ele=extract_iso_date(driver2.find_element(By.XPATH,"//p[@class='detail-date']").text.split()[0])
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url,None)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri("",url,target_date=None)
        
        return from_tuple_retri(target_ele,"",target_date=date_ele)

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='news']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//div[@class='title']//a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
            
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,None,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_7.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            document_list[i].set_published_at(content_list[i]["target_date"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            # chrome_options.add_argument('--headless')
            # driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
        
class Cp_8(PressRelease):
    def __init__(self):
        base_url="https://www.ccnew.com.hk/"
        press_release_url="https://www.ccnew.com.hk/tc/company/cctrend"
        h_code="01375.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,5)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//ul[@class='inner_paging']//a[normalize-space(text())='下一頁']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        
        if url is None:
            return from_tuple_retri(None,url)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            #//*[@id='asset']
            target_ele=driver2.find_element(By.XPATH,"//*[@id='asset']").text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url)
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='aboutcc']/div[@class='left']/div[@class='aboutccin']/table/tbody")))
            rows=target_ele.find_elements(By.TAG_NAME,'tr')
        except Exception as e:
            print(f"problem finding the list of news in a page:{driver.current_url}")
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//td[2]//a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//td[1]").text)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_8.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
        
class Cp_9(PressRelease):
    def __init__(self):
        base_url="https://www.zhglb.com/"
        press_release_url="https://www.zhglb.com/news/1/"
        h_code="01108.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt='https://www.zhglb.com/robots.txt'

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,23)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a.page_a.page_next')))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        
        if url is None:
            return from_tuple_retri(None,url)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'#js_content > section:nth-child(1) > section > section').text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url)     
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.p_list")))
            rows=target_ele.find_elements(By.CSS_SELECTOR,'div.cbox-24')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.CSS_SELECTOR,'div > div:nth-child(3)>p').text)
            
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_9.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
        
class Cp_10(PressRelease):
    def __init__(self):
        base_url="http://ssc.sinopec.com/"
        press_release_url="http://ssc.sinopec.com/sosc/news/com_news/"
        h_code="01033.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,12)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//*[@id='pager_p']//a[text()='下一页']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        if url is None:
            return from_tuple_retri(None,url)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='container']").text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='w_newslistpage_list']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//span[@class='title']//a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//span[@class='date']").text)
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_10.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_11(PressRelease):
    def __init__(self):
        base_url="https://www.fmsh.com/"
        press_release_url="https://www.fmsh.com/f4debf45-f44a-a17d-dcad-8e82db4cc6f4/"
        h_code="01385.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None 

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,13)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:        
        if url is None:
            return from_tuple_retri(None,url)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ###print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
            a=True
        try:                                                    
            #target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//article[@class='bulletinshow']"))).text            
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='in_r']"))).text                        
        except Exception:
            try: 
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='newslist']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,"./a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,"./span").text)
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_11.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_12(PressRelease):
    def __init__(self):
        base_url="https://www.dongjiang.com.cn/"
        press_release_url="https://www.dongjiang.com.cn/main/media/djxw/index.shtml"
        h_code="00895.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,234)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        
        if url is None:
            print('The url is None')
            return from_tuple_retri(None,'None')
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)                                
            
        
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='main-right1']").text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='news']//ul")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//span").text)
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_12.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_13(PressRelease):
    def __init__(self):
        base_url="https://www.cansinotech.com.cn/"
        press_release_url="https://www.cansinotech.com.cn/html/1//179/180/index.html"
        h_code="06185.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,26)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'末页')]")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        
        if url is None:
            return from_tuple_retri(None,url)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='NewsTitle']").text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='TrendsList']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//div[@class='title']//a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//div[@class='date']").text.replace('"','').strip())
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_13.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
        
class Cp_14(PressRelease):
    def __init__(self):
        base_url="https://www.glsc.com.cn/"
        press_release_url="https://www.glsc.com.cn/subsite/ir/#/detail/announce/A/zh-CN"
        h_code="01456.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,83)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//button[@class='btn-next']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        
        if url is None:
            return from_tuple_retri(None,url)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//body").text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='announce-list']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,"a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                day_in_iso=row_.find_element(By.XPATH,".//span[@class='item-left-day']").text.replace('"','').strip()
                month_in_iso=row_.find_element(By.XPATH,".//span[@class='item-left-date']").text.replace('"','').replace('.','-').strip()
                date_in_iso=extract_iso_date(month_in_iso+'-'+day_in_iso)
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_14.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
        
class Cp_15(PressRelease):
    def __init__(self):
        base_url="http://www.clypg.com.cn/"
        press_release_url="http://www.clypg.com.cn/lydlww/gsyw/list.shtml"
        h_code="00916.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,38)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        
        if url is None:
            return from_tuple_retri(None,url)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='artcon']").text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.fl.list_all.w900")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//b/a[2]")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//b//span").text.replace('"','').strip())
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_15.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_16(PressRelease):
    def __init__(self):
        base_url="https://sh.yofc.com/"
        press_release_url="https://sh.yofc.com/list/220.html"
        h_code="06869.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,5)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        
        if url is None:
            return from_tuple_retri(None,url)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"",date_in_iso=None)
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=None)
        
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=None)
        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='post_article']").text
            date_ele=extract_iso_date(driver2.find_element(By.XPATH,"//li[@class='li1']").text.strip())
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url,date_in_iso=None)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri("",url,date_in_iso=None)
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='list_newspic2']")))
            rows=target_ele.find_elements(By.TAG_NAME,'dl')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a")                
                url=url_ele.get_attribute('href')
                title_ele=row_.find_element(By.XPATH,".//a//h3")
                title=title_ele.text
                #date_in_iso=extract_iso_date(row_.find_element(By.XPATH,"").text.replace('"','').strip()
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,None,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_16.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            document_list[i].set_published_at(content_list[i]["date_in_iso"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
        
class Cp_17(PressRelease):
    def __init__(self):
        base_url="https://www.e-chinalife.com/"
        press_release_url="https://www.e-chinalife.com/xwzx/"
        h_code="02628.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,100)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),' >> ')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        
        if url is None:
            return from_tuple_retri(None,url)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='darticle']").text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='list_con']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//span").text.replace('"','').strip())
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_17.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_18(PressRelease):
    def __init__(self):
        base_url="http://www.ebscn.com/"
        press_release_url="http://www.ebscn.com/inverstorRelations/dqgg/hggg/"
        h_code="06178.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,57)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//*[@id='next_page']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        
        if url is None:
            return from_tuple_retri(None,url)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=None)
        
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=None)
        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='words']").text
            date_ele=driver2.find_element(By.XPATH,"//div[@class='content']//div[@class='article_detail']//div[@class='top']//p[@class='p1']").text 
            date_ele=extract_iso_date(date_ele.split(":")[1].strip().split(' ')[0])
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url,date_in_iso=None)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri("",url,date_in_iso=None)
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='bk_child']//ul")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,None,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_18.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            document_list[i].set_published_at(content_list[i]["date_in_iso"])
            err_url=content_list[i]["err_url"]            
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)
        
    


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))


class Cp_19(PressRelease):
    def __init__(self):
        base_url="https://www.suntien.com/"
        press_release_url="https://www.suntien.com/info.php?id=105&en=c"
        h_code="00956.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt='https://www.suntien.com/robots.txt'

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,54)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'尾 页')]")))
        driver.execute_script('arguments[0].click();', page_div)



    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        if url is None:
            return from_tuple_retri(None,url)        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)        
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//body").text
            #date_ele=driver2.find_element(By.XPATH,"").text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")



    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li")))            
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//div[1]//a[1]")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//span[@class='spantime']").text.replace('[','').replace(']','').strip())
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_19.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            #document_list[i].set_published_at(content_list[i]["date_in_iso"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_20(PressRelease):
    def __init__(self):
        base_url="https://zlgj.chinalco.com.cn/"
        press_release_url="https://zlgj.chinalco.com.cn/xwzx/gsyw/"
        h_code="02068.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,25)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        if url is None:
            return from_tuple_retri(None,url)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='xl_main']").text
            #date_ele=driver2.find_element(By.XPATH,"").text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='list2']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//span[@class='mhide']").text.replace('"','').strip())
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_20.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            #document_list[i].set_published_at(content_list[i]["date_in_iso"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_21(PressRelease):
    def __init__(self):
        base_url="http://www.first-tractor.com.cn/"
        press_release_url="http://www.first-tractor.com.cn/xwzx/gsxw/"
        h_code="00038.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,88)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        if url is None:
            return from_tuple_retri(None,url)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"div[@class='compon_particulars']").text
            #date_ele=driver2.find_element(By.XPATH,"").text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='serve_list']//ul")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//h5//a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//h5//span").text.replace('"','').strip())
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_21.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            #document_list[i].set_published_at(content_list[i]["date_in_iso"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_22(PressRelease):
    def __init__(self):
        base_url="https://www.hepalink.com/"
        press_release_url="https://www.hepalink.com/News/index.aspx"
        h_code="09989.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,10)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,".//a[@class='a_next']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        if url is None:
            return from_tuple_retri(None,url)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='Text-box']").text
            #date_ele=driver2.find_element(By.XPATH,"").text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:                                                            
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, """
                                                                    //ul[contains(concat(' ', normalize-space(@class), ' '), ' ul ') and
                                                                    contains(concat(' ', normalize-space(@class), ' '), ' padd ') and
                                                                    contains(concat(' ', normalize-space(@class), ' '), ' clearfix ') and
                                                                    not(contains(concat(' ', normalize-space(@class), ' '), ' class4 '))]
                                                                    """)))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a")
                url=url_ele.get_attribute('href')
                title=row_.find_element(By.XPATH,".//a//h2[@class='dot']")
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//a//time").text.replace('\n','-').strip())
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_22.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            #document_list[i].set_published_at(content_list[i]["date_in_iso"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_23(PressRelease):
    def __init__(self):
        base_url="http://www.swhygh.com/"
        press_release_url="http://www.swhygh.com/zxzx/zxlist.jsp?classid=0001000200030001"
        h_code="06806.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,12)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        if url is None:
            return from_tuple_retri(None,url)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='m_n']").text
            #date_ele=driver2.find_element(By.XPATH,"").text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")
        #return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='ul_list]")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//span").text.replace('"','').strip())
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_23.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            #document_list[i].set_published_at(content_list[i]["date_in_iso"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_24(PressRelease):
    def __init__(self):
        base_url="https://www.china-galaxy.com.cn/"
        press_release_url="https://www.china-galaxy.com.cn/index.php?m=content&c=index&a=lists&catid=14"
        h_code="06881.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,4)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[img[@src='/statics/images/j17.png']]")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        if url is None:
            return from_tuple_retri(None,url)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@clas='xwxq']").text
            date_ele=driver2.find_element(By.XPATH,"//div[@class='xwxq-top']//p").text.split(' ')[0]
            
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")
        

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH,"//div[@class='qydt-box-con']")))
            rows=target_ele.find_elements(By.TAG_NAME,'div')
        except Exception as e:
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a")
                url=url_ele.get_attribute('href')
                title=row_.find_element(By.XPATH,'.//a//h5').text
            except Exception as e:
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,None,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_24.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            document_list[i].set_published_at(content_list[i]["date_in_iso"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_25(PressRelease):
    def __init__(self):
        base_url="https://www.gwm.com.cn/"
        press_release_url="https://www.gwm.com.cn/company.html"
        h_code="02333.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt='https://www.gwm.com.cn/robots.txt'

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,136)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='>']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        if url is None:
            return from_tuple_retri(None,url)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            print(f'Error in extracting content from other url elements from one url in retrieve_content function:{url}')
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='news_content']").text
            date_ele=driver2.find_element(By.XPATH,"//div[@class='news_title_tool']//span[@class'r']").text
        except Exception:
            print(f'error in retrieve_content: {url}')
            driver2.quit()
            return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")
        

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)    
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='gwm_news']/ul")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,"a")
                url=url_ele.get_attribute('href')
                title=url_ele.get_attribute('data-title')
                #date_in_iso=extract_iso_date(row_.find_element(By.XPATH,"").text.replace('"','').strip()
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,None,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_25.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            document_list[i].set_published_at(content_list[i]["date_in_iso"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
        
class Cp_26(PressRelease):
    def __init__(self):
        base_url="https://www.dynagreen.com.cn/"
        press_release_url="https://www.dynagreen.com.cn/newsList_19_page1.html"
        h_code="01330.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt='https://www.dynagreen.com.cn/robots.txt'

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,49)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[@title='下一页]")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        if url is None:
            return from_tuple_retri(None,url)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url)
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ###print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
            a=True
        try:
            target_ele=WebDriverWait(driver2,10).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='newsInfo']"))).text
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")
        #return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='mod-news-5']")))
            rows=target_ele.find_elements(By.TAG_NAME,'div')
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//div[@class='item-tit']//a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,"""
                                              .//div[contains(
                                                  (concat(" ",normalize-space(@class)," "),' item-date ') and 
                                                  (concat(" ",normalize-space(@class)," "),' md-mobile ') and 
                                                  )]//span""").text.replace('年','-').replace('月','-').replace('日','-').strip())
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_26.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            #document_list[i].set_published_at(content_list[i]["date_in_iso"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_27(PressRelease):
    def __init__(self):
        base_url="http://spc.sinopec.com/"
        press_release_url="http://spc.sinopec.com/spc/news/news_report/"
        h_code="00338.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,9)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        if url is None:
            return from_tuple_retri(None,url)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print('error in retrieve_content')
                return from_tuple_retri(None,url)
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except Exception:
            print('error in driver_connect')
            driver2.quit()
            return from_tuple_retri(None,url)
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ###print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
            a=True
        try:
            target_ele=WebDriverWait(driver2,10).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='lfnews-content']"))).text
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")
        #return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='w_newslistpage_list']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//span[@class='date']").text.replace('"','').strip())
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_27.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            #document_list[i].set_published_at(content_list[i]["date_in_iso"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_28(PressRelease):
    def __init__(self):
        base_url="https://www.cicc.com/"
        press_release_url="https://www.cicc.com/news/list_104_311_1.html"
        h_code="03908.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,87)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[@class='next']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        if url is None:
            return from_tuple_retri(None,url)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print('error in retrieve_content')
                return from_tuple_retri(None,url)
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        max_attempts=5
        attempts=0
        while attempts<max_attempts:
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else:
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)

        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,10).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='main-content']"))).text
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")
        #return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='ui-article-list']")))
            rows=target_ele.find_elements(By.TAG_NAME,'div')
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//p[@class='time']").text.replace('"','').strip())
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_28.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            #document_list[i].set_published_at(content_list[i]["date_in_iso"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_29(PressRelease):
    def __init__(self):
        base_url="https://development.coscoshipping.com/"
        press_release_url="https://development.coscoshipping.com/col/col1555/index.html"
        h_code="02866.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt=None 

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,26)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[@class='layui-laypage-next']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        if url is None:
            return from_tuple_retri(None,url)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print('error in retrieve_content')
                return from_tuple_retri(None,url)
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        max_attempts=5
        attempts=0
        while attempts<max_attempts:
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else:
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
            return from_tuple_retri(None,url)
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,10).until(EC.visibility_of_element_located((By.XPATH,"//*[@id='c']"))).text
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")
        #return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='page-content']")))
            rows=target_ele.find_elements(By.TAG_NAME,'table')
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//td[1]").text.replace('[','').replace(']','').strip())
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_29.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            #document_list[i].set_published_at(content_list[i]["date_in_iso"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
        

class Cp_30(PressRelease):
    def __init__(self):
        base_url="https://www.andre.com.cn/"
        press_release_url="https://www.andre.com.cn/index.php?m=content&c=index&a=lists&catid=14"
        h_code="02218.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt='https://www.andre.com.cn/robots.txt'

    @property
    def error_count(self):
        return self.__error_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(100,5)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 10)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        if url is None:
            return from_tuple_retri(None,url)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print('error in retrieve_content')
                return from_tuple_retri(None,url)
        url_list:list[str]=[]
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        max_attempts=5
        attempts=0
        while attempts<max_attempts:
            try:
                driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else:
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url)
            return from_tuple_retri(None,url)
        try:
            url_eles=WebDriverWait(driver2,10).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            total_txt=""
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,10).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='content-in']"))).text
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url)
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url) 
        driver2.quit()
        return from_tuple_retri(target_ele,"")
        #return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver, 10)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "ul[@class='list-new']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,"a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                month_in_iso=row_.find_element(By.XPATH,".//div[@class='month']").text.replace('年','-').replace('月','')
                day_in_iso=row_.find_element(By.XPATH,".//div[@class='day']").text.replace('日','')                                
                date_in_iso=extract_iso_date(month_in_iso+'-'+day_in_iso)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if self.error_count<ERROR_COUNT:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_30.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)):
            document_list[i].set_content(content_list[i]["content"])
            #document_list[i].set_published_at(content_list[i]["date_in_iso"])
            err_url=content_list[i]["err_url"]
            if err_url!="" or err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self)->tuple[list[Document],str]:
        try:
            all_err_url:list[str]=[]
            chrome_options = Options()
            chrome_options.add_argument("--enable-javascript")
            #chrome_options.add_argument('--headless')
            #driver = webdriver.Chrome(options=chrome_options)
            driver = webdriver.Chrome()
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    break
                except WebDriverException as e:
                    if 'net::ERR_CONNECTION_RESET' in str(e):
                        attempts+=1
                        print(f'Attempt {attempts} of {max_attempts} failed with error: {e}')
                        time.sleep(5)
                    else:
                        print('Problem with requesting the main page')
                        raise(e)
            time.sleep(0.5)
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver)
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
