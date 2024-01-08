import re
import time
import math
import requests

from bs4 import BeautifulSoup

import ssl
import certifi
import urllib.request

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import UnexpectedAlertPresentException, StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException, TimeoutException, WebDriverException, InvalidArgumentException
#from selenium.webdriver.common.keys import Keys
from joblib import Parallel, delayed
#from bs4 import BeautifulSoup
#from datetime import datetime

from selenium_proxy_authentication.extension import proxies,USERNAME,PASSWORD,ENDPOINT,PORT
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from utils.exception import MaxErrorReached
from utils.crawling import PressRelease,is_file,from_tuple_retri,from_tuple_read,extract_normal_link,is_internal_link,extract_iso_date,is_iso_date,text_from_html,reverse_date_in_str,make_full_url
from company.company import *
from article.mining import _extracting_an_document        

ERROR_COUNT = 15
CONVERTION_RATE=1 #~70% hit rate
FLAT_MAX_PAGE=100

class Cp_1(PressRelease):
    def __init__(self):
        base_url="https://www.ftol.com.cn"
        press_release_url="https://www.ftol.com.cn/main/zjhy/mtjj/index.shtml"
        h_code="03678.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None:
        self.__success_count=self.__success_count+add_count
    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 9

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[@id='next_page']"
        #driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            #driver_action.scroll_to_element(page_div).perform()
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str,is_proxy)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            print("url is None")
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                print(f'downloaded the file: {url}')
                return from_tuple_retri(txt,"",date_in_iso=date_ele)
            except Exception as e:
                print(f'error in downloading the file {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            try:
                html=urllib.request.urlopen(url,context=context).read()
                target_ele=text_from_html(html)
                #txt_length=len(target_ele)
                #start_index=int(txt_length/2)
                #print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
                return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
            except Exception:
                return from_tuple_retri(None,url,date_in_iso='')
        #try:
            #url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            #for url_ele in url_eles:
                #new_url=url_ele.get_attribute('href')
                #isfile_2=is_file(new_url)
                #if isfile_2:
                    #url_list.append(url_ele.get_attribute('href'))
            #url_list=extract_normal_link(url_list)
            #for url_ in url_list:
                #total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                #print("extracting document {} inside a page {}".format(url_,url))
        #except Exception as e:
            #a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//body/div[5]/div[1]/div[2]"))).text
            #date_ele=extract_iso_date(WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,""))).text.replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-'),strip()
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.quit()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            rows_xpath="//div[@class='art_right']//ul/li"
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,rows_xpath)))
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_index in range(len(rows)):
            time.sleep(0.1)
            url=None
            title=None
            date_in_iso=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=row_xpath+"/a"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/span"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling elements of row {row_index} in this page: {driver.current_url}')
                message=''
                if url is None and title is not None:
                    message=message+'url is problematic in this row in page: {}'.format(driver.current_url)
                elif url is not None and title is None :
                    message=message+'title is problematic in this row in page: {}'.format(driver.current_url)
                else:
                    message=message+'both url and title is problematic in this row in page: {}'.format(driver.current_url)
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached(message))
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
        content_list = Parallel(n_jobs=-1)(delayed(Cp_1.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=(err_url=="" or err_url==None)
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            else:
                self.add_error_count()
                err_urls.append(err_url)
                if not is_doc_date_valid and not is_crawling_iso_date_valid:
                    print(f'published_at is problematic, doc:{doc_iso_date} and crawl:{crawling_iso_date}')
                else:
                    print('the crawling process of extracting text has error')
                    refined_document_list.append(document_list[i])
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        #chrome_options.add_argument('--headless')
        try:
            all_err_url:list[str]=[]
            if is_proxy:
                driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
            else:
                driver=webdriver.Chrome(options=chrome_options)
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
                        driver.exit()
                        raise(e)
            time.sleep(0.5)
            all_doc:list[Document]=[]
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    #print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url:
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(all_err_url,self.company_id))
      
class Cp_2(PressRelease):
    def __init__(self):
        base_url='http://www.zjshibao.com/tc/index.html'
        press_release_url='http://www.zjshibao.com/tc/tc_news/list-44.html'
        h_code='01057.HK'.lower()
        super().__init__(base_url, press_release_url, h_code)
        self.__error_count=0
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,1)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        pass

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        #check url is not empty
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        #extract txt if it is a document
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)[:5]
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
            
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR, '#mm-0>div.nybody_box').text
            
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#mm-0>div.nybody_box>div.wrap>div.nybox_box>div.nybox_right>ul.nynews_box")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
                
        content_list = Parallel(n_jobs=-1)(delayed(Cp_2.retrieve_content)(url) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else: 
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)

            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,9)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//body/div[@class='wrap']/div[contains(@class,'page') and contains(@class,'flex')]//a[last()]")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)[:5]
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
            
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR, 'body > div.wrap').text
            
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body>div.wrap>ul.support_list')))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
        content_list = Parallel(n_jobs=-1)(delayed(Cp_3.retrieve_content)(url) for url in urls)
        
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else: 
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)

            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1
    

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,6)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,f"//body//tbody//tr//a[text()='{cur_page+1}']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""        
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)[:5]
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//td[@class='word']").text      
                  
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li")))
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
        content_list = Parallel(n_jobs=-1)(delayed(Cp_4.retrieve_content)(url) for url in urls)
        
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else: 
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)

            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
        base_url="http://www.xhzy.com"
        press_release_url="http://www.xhzy.com/xwzx.php?cid=9"
        h_code="00719.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None:
        self.__success_count=self.__success_count+add_count
    def get_current_page(self,driver:WebDriver)->int:
        return 7

    def get_total_page(self,driver:WebDriver)->int:
        return 30

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="(//a[@title='下一页'][normalize-space()='>'])[2]"
        #driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            #driver_action.scroll_to_element(page_div).perform()
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str,is_proxy)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            print("url is None")
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                print(f'downloaded the file: {url}')
                return from_tuple_retri(txt,"",date_in_iso=date_ele)
            except Exception as e:
                print(f'error in downloading the file {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            try:
                html=urllib.request.urlopen(url,context=context).read()
                target_ele=text_from_html(html)
                #txt_length=len(target_ele)
                #start_index=int(txt_length/2)
                #print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
                return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
            except Exception:
                return from_tuple_retri(None,url,date_in_iso='')
        #try:
            #url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            #for url_ele in url_eles:
                #new_url=url_ele.get_attribute('href')
                #isfile_2=is_file(new_url)
                #if isfile_2:
                    #url_list.append(url_ele.get_attribute('href'))
            #url_list=extract_normal_link(url_list)
            #for url_ in url_list:
                #total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                #print("extracting document {} inside a page {}".format(url_,url))
        #except Exception as e:
            #a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='contentbox']"))).text
            #date_ele=extract_iso_date(WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,""))).text.replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-'),strip()
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.quit()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            rows_xpath="/html/body/div[5]/div/div[3]/a"
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,rows_xpath)))
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_index in range(len(rows)):
            time.sleep(0.1)
            url=None
            title=None
            date_in_iso=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=row_xpath
                title_ele_xpath=row_xpath+"/div/div/h5"
                date_xpath=row_xpath+"/div/div/span"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,title_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling elements of row {row_index} in this page: {driver.current_url}')
                message=''
                if url is None and title is not None:
                    message=message+'url is problematic in this row in page: {}'.format(driver.current_url)
                elif url is not None and title is None :
                    message=message+'title is problematic in this row in page: {}'.format(driver.current_url)
                else:
                    message=message+'both url and title is problematic in this row in page: {}'.format(driver.current_url)
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached(message))
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
        content_list = Parallel(n_jobs=-1)(delayed(Cp_5.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=(err_url=="" or err_url==None)
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            else:
                self.add_error_count()
                err_urls.append(err_url)
                if not is_doc_date_valid and not is_crawling_iso_date_valid:
                    print(f'published_at is problematic, doc:{doc_iso_date} and crawl:{crawling_iso_date}')
                else:
                    print('the crawling process of extracting text has error')
                    refined_document_list.append(document_list[i])
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        #chrome_options.add_argument('--headless')
        try:
            all_err_url:list[str]=[]
            if is_proxy:
                driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
            else:
                driver=webdriver.Chrome(options=chrome_options)
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
                        driver.exit()
                        raise(e)
            time.sleep(0.5)
            all_doc:list[Document]=[]
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=3
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    #print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url:
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_6(PressRelease):
    def __init__(self):
        base_url="https://www.panda.cn"
        press_release_url="https://www.panda.cn/mtjj/list_32.aspx"
        h_code="00553.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None:
        self.__success_count=self.__success_count+add_count
    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 4

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[@class='next']"
        #driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            #driver_action.scroll_to_element(page_div).perform()
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str,is_proxy)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            print("url is None")
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                print(f'downloaded the file: {url}')
                return from_tuple_retri(txt,"",date_in_iso=date_ele)
            except Exception as e:
                print(f'error in downloading the file {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            try:
                html=urllib.request.urlopen(url,context=context).read()
                target_ele=text_from_html(html)
                #txt_length=len(target_ele)
                #start_index=int(txt_length/2)
                #print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
                return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
            except Exception:
                return from_tuple_retri(None,url,date_in_iso='')
        #try:
            #url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            #for url_ele in url_eles:
                #new_url=url_ele.get_attribute('href')
                #isfile_2=is_file(new_url)
                #if isfile_2:
                    #url_list.append(url_ele.get_attribute('href'))
            #url_list=extract_normal_link(url_list)
            #for url_ in url_list:
                #total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                #print("extracting document {} inside a page {}".format(url_,url))
        #except Exception as e:
            #a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"https://www.panda.cn/mtjj/list_32.aspx"))).text
            #date_ele=extract_iso_date(WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,""))).text.replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-'),strip()
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.quit()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            rows_xpath="//div[@class='NewsList']/ul/li"
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,rows_xpath)))
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_index in range(len(rows)):
            time.sleep(0.1)
            url=None
            title=None
            date_in_iso=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=row_xpath+"/div[2]/h4/a"
                title_ele_xpath=row_xpath+"/div[2]/h4/a"
                date_xpath=row_xpath+"/div[2]/h4/span"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,title_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_string="20"+date_in_string
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling elements of row {row_index} in this page: {driver.current_url}')
                message=''
                if url is None and title is not None:
                    message=message+'url is problematic in this row in page: {}'.format(driver.current_url)
                elif url is not None and title is None :
                    message=message+'title is problematic in this row in page: {}'.format(driver.current_url)
                else:
                    message=message+'both url and title is problematic in this row in page: {}'.format(driver.current_url)
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached(message))
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
        content_list = Parallel(n_jobs=-1)(delayed(Cp_6.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=(err_url=="" or err_url==None)
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            else:
                self.add_error_count()
                err_urls.append(err_url)
                if not is_doc_date_valid and not is_crawling_iso_date_valid:
                    print(f'published_at is problematic, doc:{doc_iso_date} and crawl:{crawling_iso_date}')
                else:
                    print('the crawling process of extracting text has error')
                    refined_document_list.append(document_list[i])
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        #chrome_options.add_argument('--headless')
        try:
            all_err_url:list[str]=[]
            if is_proxy:
                driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
            else:
                driver=webdriver.Chrome(options=chrome_options)
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
                        driver.exit()
                        raise(e)
            time.sleep(0.5)
            all_doc:list[Document]=[]
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    #print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url:
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_7(PressRelease):
    def __init__(self):
        base_url='https://www.group.citic/'
        press_release_url='https://www.group.citic/html/medias/media_news/'
        h_code='06066.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,11)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        xpath_=f"//div[@class='content_box']//ul[@class='clearfix']//a[normalize-space(text())='{cur_page+1}']"
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,xpath_)))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        
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
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0
        while attempts<max_attempts:
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,target_date=None)
        
        # try:
        #     url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
        #     for url_ele in url_eles:
        #         new_url=url_ele.get_attribute('href')
        #         isfile_2=is_file(new_url)
        #         if isfile_2:
        #             url_list.append(url_ele.get_attribute('href'))
        #     url_list=extract_normal_link(url_list)[:5]
            
        #     for url_ in url_list:
        #         total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        # except Exception as e:
        #     ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
        #     b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='main-content']").text
            
            date_ele=extract_iso_date(driver2.find_element(By.XPATH,"//p[@class='detail-date']").text.split()[0])
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri("",url,target_date=None)
        
        return from_tuple_retri(target_ele,"",target_date=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='news']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else: 
                document_list[i].set_content(content_list[i]["content"])
                document_list[i].set_published_at(content_list[i]["target_date"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        #chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)

            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
        base_url="https://www.ccnew.com"
        press_release_url="https://www.ccnew.com/main/home/informationcenter/zhongyuannews/companynews/index.shtml"
        h_code="01375.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt=None 

    @property
    def error_count(self):
        return self.__error_count
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None:
        self.__success_count=self.__success_count+add_count
    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 114

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[@id='next_page']"
        #driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            #driver_action.scroll_to_element(page_div).perform()
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str,is_proxy)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            print("url is None")
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                print(f'downloaded the file: {url}')
                return from_tuple_retri(txt,"",date_in_iso=date_ele)
            except Exception as e:
                print(f'error in downloading the file {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            try:
                html=urllib.request.urlopen(url,context=context).read()
                target_ele=text_from_html(html)
                #txt_length=len(target_ele)
                #start_index=int(txt_length/2)
                #print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
                return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
            except Exception:
                return from_tuple_retri(None,url,date_in_iso='')
        #try:
            #url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            #for url_ele in url_eles:
                #new_url=url_ele.get_attribute('href')
                #isfile_2=is_file(new_url)
                #if isfile_2:
                    #url_list.append(url_ele.get_attribute('href'))
            #url_list=extract_normal_link(url_list)
            #for url_ in url_list:
                #total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                #print("extracting document {} inside a page {}".format(url_,url))
        #except Exception as e:
            #a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='article_cont']"))).text
            #date_ele=extract_iso_date(WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,""))).text.replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-'),strip()
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.quit()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            rows_xpath="//div[@class='page_right']/div[2]/ul/li"
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,rows_xpath)))
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_index in range(len(rows)):
            time.sleep(0.1)
            url=None
            title=None
            date_in_iso=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=row_xpath+"/a"
                title_ele_xpath=row_xpath+"/a/h5"
                date_xpath=row_xpath+"/a/span[1]"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('data-url')
                url=driver.current_url+url[1:]
                title=wait.until(EC.visibility_of_element_located((By.XPATH,title_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_com=date_in_string.split('\n')
                date_in_string=date_com[1]+'-'+date_com[0]
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling elements of row {row_index} in this page: {driver.current_url}')
                message=''
                if url is None and title is not None:
                    message=message+'url is problematic in this row in page: {}'.format(driver.current_url)
                elif url is not None and title is None :
                    message=message+'title is problematic in this row in page: {}'.format(driver.current_url)
                else:
                    message=message+'both url and title is problematic in this row in page: {}'.format(driver.current_url)
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached(message))
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
        content_list = Parallel(n_jobs=-1)(delayed(Cp_8.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=(err_url=="" or err_url==None)
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            else:
                self.add_error_count()
                err_urls.append(err_url)
                if not is_doc_date_valid and not is_crawling_iso_date_valid:
                    print(f'published_at is problematic, doc:{doc_iso_date} and crawl:{crawling_iso_date}')
                else:
                    print('the crawling process of extracting text has error')
                    refined_document_list.append(document_list[i])
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        #chrome_options.add_argument('--headless')
        try:
            all_err_url:list[str]=[]
            if is_proxy:
                driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
            else:
                driver=webdriver.Chrome(options=chrome_options)
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
                        driver.exit()
                        raise(e)
            time.sleep(0.5)
            all_doc:list[Document]=[]
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    #print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url:
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(all_err_url,self.company_id))
"""  
class Cp_9(PressRelease):
    def __init__(self):
        base_url="https://www.zhglb.com/"
        press_release_url="https://www.zhglb.com/news/4/"
        h_code="01108.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__success_count=0
        self.__robots_txt='https://www.zhglb.com/robots.txt'

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,23)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a.page_a.page_next')))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content with extracting doc: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"div[@class='main']").text
            
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele)     
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.p_list")))
            rows=target_ele.find_elements(By.CSS_SELECTOR,'div.cbox-24')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
"""

class Cp_9(PressRelease):
    def __init__(self):
        base_url="https://www.zhglb.com"
        press_release_url="https://www.zhglb.com/news/4/"
        h_code="01108.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt="https://www.zhglb.com/robots.txt"

    @property
    def error_count(self):
        return self.__error_count
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None:
        self.__success_count=self.__success_count+add_count
    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 4

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[normalize-space()='>']"
        #driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            #driver_action.scroll_to_element(page_div).perform()
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str,is_proxy)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            print("url is None")
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                print(f'downloaded the file: {url}')
                return from_tuple_retri(txt,"",date_in_iso=date_ele)
            except Exception as e:
                print(f'error in downloading the file {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        #url_list:list[str]=[]
        chrome_options=Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            try:
                html=urllib.request.urlopen(url,context=context).read()
                target_ele=text_from_html(html)
                #txt_length=len(target_ele)
                #start_index=int(txt_length/2)
                #print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
                return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
            except Exception:
                return from_tuple_retri(None,url,date_in_iso='')
        #try:
            #url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            #for url_ele in url_eles:
                #new_url=url_ele.get_attribute('href')
                #isfile_2=is_file(new_url)
                #if isfile_2:
                    #url_list.append(url_ele.get_attribute('href'))
            #url_list=extract_normal_link(url_list)
            #for url_ in url_list:
                #total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                #print("extracting document {} inside a page {}".format(url_,url))
        #except Exception as e:
            #a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//body"))).text
            #date_ele=extract_iso_date(WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,""))).text.replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-'),strip()
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.quit()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            rows_xpath="//div[@class='p_list']/div"
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,rows_xpath)))
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_index in range(len(rows)):
            time.sleep(0.1)
            url=None
            title=None
            date_in_iso=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=row_xpath+"/div/div[2]//a"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/div/div[3]/p"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling elements of row {row_index} in this page: {driver.current_url}')
                message=''
                if url is None and title is not None:
                    message=message+'url is problematic in this row in page: {}'.format(driver.current_url)
                elif url is not None and title is None :
                    message=message+'title is problematic in this row in page: {}'.format(driver.current_url)
                else:
                    message=message+'both url and title is problematic in this row in page: {}'.format(driver.current_url)
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached(message))
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
        content_list = Parallel(n_jobs=-1)(delayed(Cp_9.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=(err_url=="" or err_url==None)
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            else:
                self.add_error_count()
                err_urls.append(err_url)
                if not is_doc_date_valid and not is_crawling_iso_date_valid:
                    print(f'published_at is problematic, doc:{doc_iso_date} and crawl:{crawling_iso_date}')
                else:
                    print('the crawling process of extracting text has error')
                    refined_document_list.append(document_list[i])
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        #chrome_options.add_argument('--headless')
        try:
            all_err_url:list[str]=[]
            if is_proxy:
                driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
            else:
                driver=webdriver.Chrome(options=chrome_options)
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
                        driver.exit()
                        raise(e)
            time.sleep(0.5)
            all_doc:list[Document]=[]
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    #print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url:
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(all_err_url,self.company_id))

        
class Cp_10(PressRelease):
    def __init__(self):
        base_url="http://ssc.sinopec.com/"
        press_release_url="http://ssc.sinopec.com/sosc/news/com_news/"
        h_code="01033.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,12)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//*[@id='pager_p']//a[text()='下一页']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='container']").text
            
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='w_newslistpage_list']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//span[@class='date']").text.replace('年','-').replace('月','-').replace('日',''))
            except Exception as e:
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
        self.__success_count=0
        self.__robots_txt=None 

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,13)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""        
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ###print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
            a=True
        try:                                                    
            #target_ele=WebDriverWait(driver2,30).until(EC.visibility_of_element_located((By.XPATH,"//article[@class='bulletinshow']"))).text            
            target_ele=WebDriverWait(driver2,30).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='in_r']"))).text                        
        except Exception:
            try: 
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='newslist']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,"./span").text.replace('.','-'))
            except Exception as e:
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
        base_url="https://www.dongjiang.com.cn"
        press_release_url="https://www.dongjiang.com.cn/main/media/mtbd/index.shtml"
        h_code="00895.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None:
        self.__success_count=self.__success_count+add_count
    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 6

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[contains(text(),'下一页')]"
        #driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            #driver_action.scroll_to_element(page_div).perform()
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str,is_proxy)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            print("url is None")
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                print(f'downloaded the file: {url}')
                return from_tuple_retri(txt,"",date_in_iso=date_ele)
            except Exception as e:
                print(f'error in downloading the file {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            try:
                html=urllib.request.urlopen(url,context=context).read()
                target_ele=text_from_html(html)
                #txt_length=len(target_ele)
                #start_index=int(txt_length/2)
                print('With bs4')
                return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
            except Exception:
                print('bs4 fail')
                return from_tuple_retri(None,url,date_in_iso='')
        #try:
            #url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            #for url_ele in url_eles:
                #new_url=url_ele.get_attribute('href')
                #isfile_2=is_file(new_url)
                #if isfile_2:
                    #url_list.append(url_ele.get_attribute('href'))
            #url_list=extract_normal_link(url_list)
            #for url_ in url_list:
                #total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                #print("extracting document {} inside a page {}".format(url_,url))
        #except Exception as e:
            #a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//body"))).text
            #date_ele=extract_iso_date(WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,""))).text.replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-'),strip()
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.quit()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            rows_xpath="//div[@class='main-right']//ul/li"
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,rows_xpath)))
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_index in range(len(rows)):
            time.sleep(0.1)
            url=None
            title=None
            date_in_iso=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=row_xpath+"/a"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/span"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling elements of row {row_index} in this page: {driver.current_url}')
                message=''
                if url is None and title is not None:
                    message=message+'url is problematic in this row in page: {}'.format(driver.current_url)
                elif url is not None and title is None :
                    message=message+'title is problematic in this row in page: {}'.format(driver.current_url)
                else:
                    message=message+'both url and title is problematic in this row in page: {}'.format(driver.current_url)
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached(message))
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
        content_list = Parallel(n_jobs=-1)(delayed(Cp_12.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=(err_url=="" or err_url==None)
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            else:
                self.add_error_count()
                err_urls.append(err_url)
                if not is_doc_date_valid and not is_crawling_iso_date_valid:
                    print(f'published_at is problematic, doc:{doc_iso_date} and crawl:{crawling_iso_date}')
                else:
                    print('the crawling process of extracting text has error')
                    refined_document_list.append(document_list[i])
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        #chrome_options.add_argument('--headless')
        try:
            all_err_url:list[str]=[]
            if is_proxy:
                driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
            else:
                driver=webdriver.Chrome(options=chrome_options)
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
                        driver.exit()
                        raise(e)
            time.sleep(0.5)
            all_doc:list[Document]=[]
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    #print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url:
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_13(PressRelease):
    def __init__(self):
        base_url="https://www.cansinotech.com.cn/"
        press_release_url="https://www.cansinotech.com.cn/html/1//179/180/index.html"
        h_code="06185.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,26)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'末页')]")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='NewsTitle']").text
            
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='TrendsList']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,83)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//button[@class='btn-next']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//body").text
            
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='announce-list']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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

"""
class Cp_14(PressRelease):
    
    def __init__(self):
        base_url="https://www.glsc.com.cn"
        press_release_url="https://www.glsc.com.cn/#/IntoGL/news"
        h_code="01456.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None:
        self.__success_count=self.__success_count+add_count
    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 28

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//li[@class='ant-pagination-next']//button[@type='button']"
        #driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            #driver_action.scroll_to_element(page_div).perform()
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str,is_proxy)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            print("url is None")
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                print(f'downloaded the file: {url}')
                return from_tuple_retri(txt,"",date_in_iso=date_ele)
            except Exception as e:
                print(f'error in downloading the file {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            try:
                html=urllib.request.urlopen(url,context=context).read()
                target_ele=text_from_html(html)
                #txt_length=len(target_ele)
                #start_index=int(txt_length/2)
                #print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
                return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
            except Exception:
                return from_tuple_retri(None,url,date_in_iso='')
        #try:
            #url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            #for url_ele in url_eles:
                #new_url=url_ele.get_attribute('href')
                #isfile_2=is_file(new_url)
                #if isfile_2:
                    #url_list.append(url_ele.get_attribute('href'))
            #url_list=extract_normal_link(url_list)
            #for url_ in url_list:
                #total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                #print("extracting document {} inside a page {}".format(url_,url))
        #except Exception as e:
            #a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//body/div/div/div/div[2]/div[1]"))).text
            #date_ele=extract_iso_date(WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,""))).text.replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-'),strip()
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.quit()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            rows_xpath="//div[@id='table']/div/div/div/div//tbody/tr"
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,rows_xpath)))
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_index in range(len(rows)):
            time.sleep(0.1)
            url=None
            title=None
            date_in_iso=None
            url_str=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=row_xpath+"/td[1]"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/td[2]"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                url=wait.until(EC.element_to_be_clickable((By.XPATH,url_ele_xpath))).click()                
                content=WebDriverWait(driver,15).until(EC.visibility_of_element_located((By.XPATH,"//body/div/div/div/div[2]/div[1]"))).text
                url_str=driver.current_url
                driver.back()
                print(url_str)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling elements of row {row_index} in this page: {driver.current_url}')
                message=''
                if url_str is None and title is not None:
                    message=message+'url is problematic in this row in page: {}'.format(driver.current_url)
                elif url_str is not None and title is None :
                    message=message+'title is problematic in this row in page: {}'.format(driver.current_url)
                else:
                    message=message+'both url and title is problematic in this row in page: {}'.format(driver.current_url)
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached(message))
            if (type(url_str)==str and url_str!="" and url_str!=None) or is_file(url_str):
                urls.append(url_str)
                document_list.append(Document(url_str,title,date_in_iso,self.press_release_url,content,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue

            
            
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        #chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        #chrome_options.add_argument('--headless')
        try:
            all_err_url:list[str]=[]
            if is_proxy:
                driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
            else:
                driver=webdriver.Chrome(options=chrome_options)
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
                        driver.exit()
                        raise(e)
            time.sleep(0.5)
            all_doc:list[Document]=[]
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    #print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url:
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(all_err_url,self.company_id))
"""        
class Cp_15(PressRelease):
    def __init__(self):
        base_url="http://www.clypg.com.cn/"
        press_release_url="http://www.clypg.com.cn/lydlww/gsyw/list.shtml"
        h_code="00916.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,38)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='artcon']").text
            
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.fl.list_all.w900")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,5)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"",date_in_iso=None)
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=None)
        
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
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
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='post_article']").text
            
            date_ele=extract_iso_date(driver2.find_element(By.XPATH,"//li[@class='li1']").text.strip())
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri("",url,date_in_iso=None)
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='list_newspic2']")))
            rows=target_ele.find_elements(By.TAG_NAME,'dl')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,100)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),' >> ')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='darticle']").text
            
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='list_con']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
"""
class Cp_18(PressRelease):
    def __init__(self):
        base_url="http://www.ebscn.com/"
        press_release_url="http://www.ebscn.com/zjgd/mtgz/"
        h_code="06178.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 1

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        pass

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=None)
        
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=None)
        
        # try:
        #     url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
        #     for url_ele in url_eles:
        #         new_url=url_ele.get_attribute('href')
        #         isfile_2=is_file(new_url)
        #         if isfile_2:
        #             url_list.append(url_ele.get_attribute('href'))
        #     url_list=extract_normal_link(url_list)
            
        #     for url_ in url_list:
        #         total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        # except Exception as e:
        #     ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
        #     b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='words']").text
            
            date_ele=driver2.find_element(By.XPATH,"//body/div/div/div/div/div/div/div[1]/p[1]").text 
            date_ele=extract_iso_date(date_ele)
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri("",url,date_in_iso=None)
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='gd_news']/div[1]/ul")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
            except Exception as e:
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]            
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)
        
    


    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        #chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
"""

class Cp_18(PressRelease):
    def __init__(self):
        base_url="http://www.ebscn.com"
        press_release_url="http://www.ebscn.com/zjgd/mtgz/"
        h_code="06178.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt=None 

    @property
    def error_count(self):
        return self.__error_count
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None:
        self.__success_count=self.__success_count+add_count
    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 5

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[@class='next']"
        #driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            #driver_action.scroll_to_element(page_div).perform()
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str,is_proxy)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            print("url is None")
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                print(f'downloaded the file: {url}')
                return from_tuple_retri(txt,"",date_in_iso=date_ele)
            except Exception as e:
                print(f'error in downloading the file {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            try:
                html=urllib.request.urlopen(url,context=context).read()
                target_ele=text_from_html(html)
                #txt_length=len(target_ele)
                #start_index=int(txt_length/2)
                #print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
                return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
            except Exception:
                return from_tuple_retri(None,url,date_in_iso='')
        #try:
            #url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            #for url_ele in url_eles:
                #new_url=url_ele.get_attribute('href')
                #isfile_2=is_file(new_url)
                #if isfile_2:
                    #url_list.append(url_ele.get_attribute('href'))
            #url_list=extract_normal_link(url_list)
            #for url_ in url_list:
                #total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                #print("extracting document {} inside a page {}".format(url_,url))
        #except Exception as e:
            #a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='words']"))).text
            date_ele=extract_iso_date(WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//p[contains(text(),'时间')]]"))).text.replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-').strip())
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.quit()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            rows_xpath="//div[@class='gd_news']/div[1]/ul/li"
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,rows_xpath)))
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_index in range(len(rows)):
            time.sleep(0.1)
            url=None
            title=None
            date_in_iso=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=row_xpath+"/a"
                #title_ele_xpath=row_xpath+"/"
                #date_xpath=row_xpath+"/"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                #date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                #date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling elements of row {row_index} in this page: {driver.current_url}')
                message=''
                if url is None and title is not None:
                    message=message+'url is problematic in this row in page: {}'.format(driver.current_url)
                elif url is not None and title is None :
                    message=message+'title is problematic in this row in page: {}'.format(driver.current_url)
                else:
                    message=message+'both url and title is problematic in this row in page: {}'.format(driver.current_url)
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached(message))
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
        content_list = Parallel(n_jobs=-1)(delayed(Cp_18.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=(err_url=="" or err_url==None)
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            else:
                self.add_error_count()
                err_urls.append(err_url)
                if not is_doc_date_valid and not is_crawling_iso_date_valid:
                    print(f'published_at is problematic, doc:{doc_iso_date} and crawl:{crawling_iso_date}')
                else:
                    print('the crawling process of extracting text has error')
                    refined_document_list.append(document_list[i])
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        #chrome_options.add_argument('--headless')
        try:
            all_err_url:list[str]=[]
            if is_proxy:
                driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
            else:
                driver=webdriver.Chrome(options=chrome_options)
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
                        driver.exit()
                        raise(e)
            time.sleep(0.5)
            all_doc:list[Document]=[]
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    #print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url:
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(all_err_url,self.company_id))

"""
class Cp_19(PressRelease):
    def __init__(self):
        base_url="https://www.suntien.com/"
        press_release_url="https://www.suntien.com/info.php?id=105&en=c"
        h_code="00956.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__success_count=0
        self.__robots_txt='https://www.suntien.com/robots.txt'

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,54)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        
        driver.execute_script('arguments[0].click();', page_div)



    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)        
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)        
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//body").text
            
            #date_ele=driver2.find_element(By.XPATH,"").text
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)



    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele:WebElement
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='nylisttt']")))
            rows=target_ele.find_elements(By.XPATH,'.//li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,".//a[1]")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                # print(url)
                # print(title)
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,".//span[@class='spantime']").text.replace('[','').replace(']','').strip())

            except Exception as e:
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)


    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
            # temp_ele=driver.find_element(By.XPATH,'//body')
            # print('success find the body')
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
"""

class Cp_19(PressRelease):
    def __init__(self):
        base_url="https://www.suntien.com"
        press_release_url="https://www.suntien.com/info.php?id=14&en=c"
        h_code="00956.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt="https://www.suntien.com/robots.txt"

    @property
    def error_count(self):
        return self.__error_count
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None:
        self.__success_count=self.__success_count+add_count
    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 16

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[contains(text(),'下一页')]"
        #driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            #driver_action.scroll_to_element(page_div).perform()
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str,is_proxy)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            print("url is None")
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                print(f'downloaded the file: {url}')
                return from_tuple_retri(txt,"",date_in_iso=date_ele)
            except Exception as e:
                print(f'error in downloading the file {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #chrome_options.add_argument('--headless')
        #chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            try:
                html=urllib.request.urlopen(url,context=context).read()
                target_ele=text_from_html(html)
                #txt_length=len(target_ele)
                #start_index=int(txt_length/2)
                print('With bs4')
                return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
            except Exception:
                print('bs4 fail')
                return from_tuple_retri(None,url,date_in_iso='')
        #try:
            #url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            #for url_ele in url_eles:
                #new_url=url_ele.get_attribute('href')
                #isfile_2=is_file(new_url)
                #if isfile_2:
                    #url_list.append(url_ele.get_attribute('href'))
            #url_list=extract_normal_link(url_list)
            #for url_ in url_list:
                #total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                #print("extracting document {} inside a page {}".format(url_,url))
        #except Exception as e:
            #a=True
        try:
            first_target=WebDriverWait(driver2,15).until(EC.presence_of_element_located((By.XPATH,"//div[@class='detasilcontent']")))
            ActionChains(driver2).scroll_to_element(first_target).perform()
            time.sleep(1.5)
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='detasilcontent']"))).text
            #date_ele=extract_iso_date(WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,""))).text.replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-'),strip()
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.quit()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            rows_xpath="//body/div[@class='neiye']/div[@class='middle']/div[@id='right']/div[@class='nycontent wow fadeInRight animated']/div[@class='small_nycontent']/div[@class='nylisttt']/li"
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,rows_xpath)))
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_index in range(len(rows)):
            time.sleep(0.1)
            url=None
            title=None
            date_in_iso=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=row_xpath+"/div/a[1]"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/div/span"

                #scroll to row 
                row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                driver_action=ActionChains(driver)
                driver_action.scroll_to_element(row_ele).perform()
                time.sleep(2)
                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text.replace("[","").replace("]","")
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling elements of row {row_index} in this page: {driver.current_url}')
                message=''
                if url is None and title is not None:
                    message=message+'url is problematic in this row in page: {}'.format(driver.current_url)
                elif url is not None and title is None :
                    message=message+'title is problematic in this row in page: {}'.format(driver.current_url)
                else:
                    message=message+'both url and title is problematic in this row in page: {}'.format(driver.current_url)
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached(message))
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
        content_list = Parallel(n_jobs=-1)(delayed(Cp_19.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=(err_url=="" or err_url==None)
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            else:
                self.add_error_count()
                err_urls.append(err_url)
                if not is_doc_date_valid and not is_crawling_iso_date_valid:
                    print(f'published_at is problematic, doc:{doc_iso_date} and crawl:{crawling_iso_date}')
                else:
                    print('the crawling process of extracting text has error')
                    refined_document_list.append(document_list[i])
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        #chrome_options.add_argument('--headless')
        try:
            all_err_url:list[str]=[]
            if is_proxy:
                driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
            else:
                driver=webdriver.Chrome(options=chrome_options)
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
                        driver.exit()
                        raise(e)
            time.sleep(0.5)
            all_doc:list[Document]=[]
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=3
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    #print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url:
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_20(PressRelease):
    def __init__(self):
        base_url="https://zlgj.chinalco.com.cn/"
        press_release_url="https://zlgj.chinalco.com.cn/xwzx/gsyw/"
        h_code="02068.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,25)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(8)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='xl_main']").text
            
            #date_ele=driver2.find_element(By.XPATH,"").text
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='list list2']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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

"""
class Cp_21(PressRelease):
    def __init__(self):
        base_url="http://www.first-tractor.com.cn/"
        press_release_url="http://www.first-tractor.com.cn/xwzx/gsxw/"
        h_code="00038.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count   
    

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

        
    def get_current_page(self,driver:WebDriver)->int:
        return 1

    
        
    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,88)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@class='serve_list']/div[@class='tpxw1-2']//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"div[@class='compon_particulars']").text
            
            #date_ele=driver2.find_element(By.XPATH,"").text
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='serve_list']//ul")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
"""
"""
class Cp_21(PressRelease):
    def __init__(self):
        base_url="http://www.first-tractor.com.cn/"
        press_release_url="http://www.first-tractor.com.cn/xwzx/mtgz/"
        h_code="00038.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count   
    

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

        
    def get_current_page(self,driver:WebDriver)->int:
        return 1

    
        
    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,88)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//div[@class='serve_list']/div[@class='tpxw1-2']//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"div[@class='compon_particulars']").text
            
            #date_ele=driver2.find_element(By.XPATH,"").text
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='serve_list']//ul")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
"""
class Cp_21(PressRelease):
    def __init__(self):
        base_url="http://www.first-tractor.com.cn"
        press_release_url="http://www.first-tractor.com.cn/xwzx/mtgz/"
        h_code="00038.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None:
        self.__success_count=self.__success_count+add_count
    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 16

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[contains(text(),'下一页')]"
        #driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            #driver_action.scroll_to_element(page_div).perform()
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str,is_proxy)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            print("url is None")
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                print(f'downloaded the file: {url}')
                return from_tuple_retri(txt,"",date_in_iso=date_ele)
            except Exception as e:
                print(f'error in downloading the file {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            try:
                context=ssl.create_default_context(cafile=certifi.where())
                html=urllib.request.urlopen(url,context=context).read()
                target_ele=text_from_html(html)
                
                #txt_length=len(target_ele)
                #start_index=int(txt_length/2)
                print('With bs4')
                return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
            except Exception:
                print('bs4 fail')
                return from_tuple_retri(None,url,date_in_iso='')
        #try:
            #url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            #for url_ele in url_eles:
                #new_url=url_ele.get_attribute('href')
                #isfile_2=is_file(new_url)
                #if isfile_2:
                    #url_list.append(url_ele.get_attribute('href'))
            #url_list=extract_normal_link(url_list)
            #for url_ in url_list:
                #total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                #print("extracting document {} inside a page {}".format(url_,url))
        #except Exception as e:
            #a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//body/div/div[2]/div[2]"))).text
            #date_ele=extract_iso_date(WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,""))).text.replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-').strip())
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.quit()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            rows_xpath="//div[@class='sidebarR']//ul/li"
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,rows_xpath)))
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_index in range(len(rows)):
            time.sleep(0.1)
            url=None
            title=None
            date_in_iso=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=row_xpath+"/h5/a"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/h5/span"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling elements of row {row_index} in this page: {driver.current_url}')
                message=''
                if url is None and title is not None:
                    message=message+'url is problematic in this row in page: {}'.format(driver.current_url)
                elif url is not None and title is None :
                    message=message+'title is problematic in this row in page: {}'.format(driver.current_url)
                else:
                    message=message+'both url and title is problematic in this row in page: {}'.format(driver.current_url)
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached(message))
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
        content_list = Parallel(n_jobs=-1)(delayed(Cp_21.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=(err_url=="" or err_url==None)
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            else:
                self.add_error_count()
                err_urls.append(err_url)
                if not is_doc_date_valid and not is_crawling_iso_date_valid:
                    print(f'published_at is problematic, doc:{doc_iso_date} and crawl:{crawling_iso_date}')
                else:
                    print('the crawling process of extracting text has error')
                    refined_document_list.append(document_list[i])
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        #chrome_options.add_argument('--headless')
        try:
            all_err_url:list[str]=[]
            if is_proxy:
                driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
            else:
                driver=webdriver.Chrome(options=chrome_options)
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
                        driver.exit()
                        raise(e)
            time.sleep(0.5)
            all_doc:list[Document]=[]
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    #print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url:
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(all_err_url,self.company_id))


class Cp_22(PressRelease):
    def __init__(self):
        base_url="https://www.hepalink.com/"
        press_release_url="https://www.hepalink.com/News/index.aspx"
        h_code="09989.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,10)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,".//a[@class='a_next']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='Text-box']").text
            
            #date_ele=driver2.find_element(By.XPATH,"").text
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:                                                            
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='ul padd clearfix']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                title=row_.find_element(By.XPATH,".//a//h2[@class='dot']").text
                date_ele=row_.find_element(By.XPATH,".//a//time").text.split('\n')
                date_in_iso=extract_iso_date(date_ele[1]+'-'+date_ele[0])
            except Exception as e:
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,12)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='m_n']").text
            
            #date_ele=driver2.find_element(By.XPATH,"").text
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)
        #return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='ul_list']")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,4)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[img[@src='/statics/images/j17.png']]")))
        # xpath_my=f"//div[@class='aos-animate']/p[{cur_page+2}]/a"
        # page_div=wait.until(EC.element_to_be_clickable((By.XPATH,xpath_my)))
        #/html/body/div[4]/div[4]/div[4]/p[6]/a
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ##print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@clas='xwxq']").text
            
            date_ele=driver2.find_element(By.XPATH,"//div[@class='xwxq-top']//p").text.split(' ')[0]
            
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
                date_ele=driver2.find_element(By.XPATH,"//div[@class='xwxq-top']//p").text.split(' ')[0]
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)
        

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH,"//div[@class='qydt-box-con']")))
            rows=target_ele.find_elements(By.TAG_NAME,'div')
        except Exception as e:
            print(f"problem with finding the list of news: {driver.current_url}")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:  
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
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        print(f'success in read page of company_id:{self.company_id}')
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
        self.__success_count=0
        self.__robots_txt='https://www.gwm.com.cn/robots.txt'

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,136)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='>']")))
        #news_list
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/main/div[@class='news_bottom_bg']/div[@class='news_bottom']/div[@class='news_list']/div/div/div/a[@class='layui-laypage-next']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso="")
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso="")
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"/html/body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            print(f'Error in extracting content from other url elements from one url in retrieve_content function:{url}')
        try:
            target_ele=driver2.find_element(By.XPATH,"//div[@class='news_content']").text            
        except Exception:
            try: 
                target_ele=driver2.find_element(By.XPATH,'//body').text
            except Exception:
                print(f'error in retrieve_content: {url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso="")
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso="") 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)
        

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)    
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='gwm_news']/ul")))
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/main/div[@class='news_bottom_bg']/div[@class='news_bottom']/div[@class='news_list']/div/ul")))
            rows=target_ele.find_elements(By.XPATH,'./li')
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
                title=url_ele.get_attribute('data-title')
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,"./a/div[@class='time_box']/div[@class='pub-times']").text.replace('"','').strip())
            except Exception as e:
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url):
                    urls.append(url)
            else:
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_25.retrieve_content)(url) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):

            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        #chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)
            


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome://extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)

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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
        self.__success_count=0
        self.__robots_txt='https://www.dynagreen.com.cn/robots.txt'

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,49)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[@class='wrap-layer']/div/div[@class='in-right in-right2']/div[@class='page-wrap ft18']/div[@class='page']/ul/li[@class='next']/a")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print(f'error in retrieve_content: {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(45) 
        max_attempts=5
        attempts=0 
        while attempts<max_attempts: 
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ###print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
            a=True
        try:
            target_ele=WebDriverWait(driver2,30).until(EC.visibility_of_element_located((By.XPATH,"html/body/div[@class='wrap-layer']/div[@class='in-right in-right2']/div[@class='newsInfo']"))).text
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)
        #return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[@class='wrap-layer']/div/div[@class='in-right in-right2']/div[@class='mod-news-5']")))
            rows=target_ele.find_elements(By.XPATH,'./div')
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            if 'item-nopic' in row_.get_attribute('class'):
                continue
            try:#contains(@class, 'class1')
                url_ele=row_.find_element(By.XPATH,"./div[@class='item-cnt']/div[contains(@class,'item-tit')]/a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_ele=row_.find_element(By.XPATH,"./div[@class='item-date md-pc']").text.split('\n')
                date_in_iso=date_ele[1].replace('/','-')+'-'+date_ele[0]
            except Exception as e:
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        #chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)
            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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

"""
class Cp_26(PressRelease):
    def __init__(self):
        base_url="https://www.dynagreen.com.cn"
        press_release_url="https://www.dynagreen.com.cn/newsList_22_page1.html"
        h_code="01330.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None:
        self.__success_count=self.__success_count+add_count
    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 4

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//li[@class='next']//a[@class='page_control']"
        #driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            #driver_action.scroll_to_element(page_div).perform()
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str,is_proxy)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            print("url is None")
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                print(f'downloaded the file: {url}')
                return from_tuple_retri(txt,"",date_in_iso=date_ele)
            except Exception as e:
                print(f'error in downloading the file {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        #try:
            #driver2.get(url)
        #except WebDriverException as e:
            #rint(f'error: receive_content function cannot connect to {url}')
        try:
            context=ssl.create_default_context(cafile=certifi.where())
            html=urllib.request.urlopen(url,context=context).read()
            target_ele=text_from_html(html)
            #txt_length=len(target_ele)
            #start_index=int(txt_length/2)
            print('With bs4')
            return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
        except Exception:
            print('bs4 fail')
            return from_tuple_retri(None,url,date_in_iso='')
        #try:
            #url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            #for url_ele in url_eles:
                #new_url=url_ele.get_attribute('href')
                #isfile_2=is_file(new_url)
                #if isfile_2:
                    #url_list.append(url_ele.get_attribute('href'))
            #url_list=extract_normal_link(url_list)
            #for url_ in url_list:
                #total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                #print("extracting document {} inside a page {}".format(url_,url))
        #except Exception as e:
            #a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='newsInfo']"))).text
            #date_ele=extract_iso_date(WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,""))).text.replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-'),strip()
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.quit()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            rows_xpath="/html/body/div[4]/div/div[2]/div[2]/div"
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,rows_xpath)))
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_index in range(len(rows)):
            time.sleep(0.1)
            url=None
            title=None
            date_in_iso=None
            try:
                
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"

                #scroll to row 
                row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                if "item-nopic" in row_ele.get_attribute('class'):
                    url_ele_xpath=row_xpath+"/div[2]/div[1]/a"
                    #title_ele_xpath=row_xpath+"/"
                    date_xpath=row_xpath+"/div[1]"
                else: 
                    url_ele_xpath=row_xpath+"/div[3]/div[1]/a"
                    #title_ele_xpath=row_xpath+"/"
                    date_xpath=row_xpath+"/div[1]"
                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_com=date_in_string.split('\n')
                date_in_string=date_com[1].strip()+'-'+date_com[0].strip()
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling elements of row {row_index} in this page: {driver.current_url}')
                message=''
                if url is None and title is not None:
                    message=message+'url is problematic in this row in page: {}'.format(driver.current_url)
                elif url is not None and title is None :
                    message=message+'title is problematic in this row in page: {}'.format(driver.current_url)
                else:
                    message=message+'both url and title is problematic in this row in page: {}'.format(driver.current_url)
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached(message))
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
        content_list = Parallel(n_jobs=-1)(delayed(Cp_26.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=(err_url=="" or err_url==None)
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                #content_len=len(content_to_be_set)
                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            else:
                self.add_error_count()
                err_urls.append(err_url)
                if not is_doc_date_valid and not is_crawling_iso_date_valid:
                    print(f'published_at is problematic, doc:{doc_iso_date} and crawl:{crawling_iso_date}')
                else:
                    print('the crawling process of extracting text has error')
                    refined_document_list.append(document_list[i])
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        #chrome_options.add_argument("--enable-javascript")
        chrome_options.page_load_strategy = 'eager' 
        
        #chrome_options.add_argument('--headless')
        try:
            all_err_url:list[str]=[]
            if is_proxy:
                driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
            else:
                driver=webdriver.Chrome(options=chrome_options)
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
                        driver.exit()
                        raise(e)
            time.sleep(0.5)
            all_doc:list[Document]=[]
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    #print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url:
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(all_err_url,self.company_id))
"""
class Cp_27(PressRelease):
    def __init__(self):
        base_url="http://spc.sinopec.com/"
        press_release_url="http://spc.sinopec.com/spc/news/news_report/"
        h_code="00338.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,9)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))                                                                    
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/span[@id='DeltaPlaceHolderMain']/div[2]/div[@class='column-right']/div[@class='conlumn-right-one']/div//p[@id='pager_p']//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print('error in retrieve_content')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument('--headless')
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        max_attempts=5
        attempts=0
        while attempts<max_attempts:
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else:
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            ###print(f'Warning in extracting content from other url elements from one url in retrieve_content function:{url}')
            b=True
            a=True
        try:
            target_ele=WebDriverWait(driver2,30).until(EC.visibility_of_element_located((By.XPATH,"/html/body/span[@id='DeltaPlaceHolderMain']/div[@class='lfnews-content']"))).text
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)
        #return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/span[@id='DeltaPlaceHolderMain']/div[2]/div[@class='column-right']/div//div[@id='MSOZoneCell_WebPartWPQ3']/div/div/div[@id='ctl00_SPWebPartManager1_g_9bcf6e15_e0de_4d64_8db9_15227dcb295e']/div[@class='w_newslistpage_box']/div/div[@class='w_newslistpage_body']/ul")))
            rows=target_ele.find_elements(By.TAG_NAME,'li')
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,"./span[@class='title']/a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,"./span[@class='date']").text.replace('"','').strip())
            except Exception as e:
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
        self.__success_count=0
        self.__robots_txt=None

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,87)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[@class='page-box news-page news-list-page']/div/div[@class='main-content']/div[@id='Pagination']/div[@class='page']/a[@class='next']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print('error in retrieve_content')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        max_attempts=5
        attempts=0
        while attempts<max_attempts:
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else:
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)

        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,30).until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[includes(@class,'main-container')]/div[@class='main-content']"))).text
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)
        #return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:                                                                    #page-box news-page news-list-page
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[contains(@class,'page-box') and contains(@class,'news-page') and contains(@class,'news-list-page')]/div/div[@class='main-content']/div[@class='ui-article-list']")))
            rows=target_ele.find_elements(By.XPATH,'./div')
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,"./div/a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,"./p").text.replace('"','').strip())
            except Exception as e:
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
        self.__success_count=0
        self.__robots_txt=None 
        #common='/html/body/div/table[4]/tbody/tr'

    @property
    def error_count(self):
        return self.__error_count
    
    @property
    def success_count(self):
        return self.__success_count

    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None: 
        self.__success_count=self.__success_count+add_count

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,26)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,30)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]"))) 
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div/table[4]/tbody/tr/td[3]/table[2]/tbody/tr/td/div/div[@class='pagination']//a[@class='layui-laypage-next']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                return from_tuple_retri(txt,"")
            except Exception as e:
                print('error in retrieve_content')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        max_attempts=5
        attempts=0
        while attempts<max_attempts:
            try:
                driver2.get(url)
                #driver2.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                #driver2.find_element(By.ID,'username_field').send_keys(proxy_username)
                #driver2.find_element(By.ID,'password_field').send_keys(proxy_password)
                #driver2.find_element(By.ID,'save_button').click() 
                #driver2.get(url)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else:
                    print(f'error: receive_content function cannot connect to {url}')
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,30).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,30).until(EC.visibility_of_element_located((By.XPATH,"//*[@id='c']"))).text
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.quit()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.quit()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)
        #return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div/table[4]/tbody/tr/td[3]/table[2]/tbody/tr/td/div/div[@class='page-content']")))
            rows=target_ele.find_elements(By.TAG_NAME,'table')
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[str]=[]
        err_urls:list[str]=[]
        for row_ in rows:
            try:
                url_ele=row_.find_element(By.XPATH,"./tbody/tr/td[2]/a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,"./tbody/tr/td[1]").text.replace('[','').replace(']','').strip())
            except Exception as e:
                print(f'issue with find doc info in a row of a page {driver.current_url}')
                if driver.current_url not in err_urls: 
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count: 
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
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            if err_url!="" and err_url!=None:
                self.add_error_count()
                err_urls.append(err_url)
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
            else:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None: 
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--enable-javascript")
        #chrome_options.page_load_strategy = 'eager' 
        #chrome_options.add_argument("--headless")
        try:
            all_err_url:list[str]=[]
            driver=webdriver.Chrome(options=chrome_options)


            max_attempts=5
            attempts=0
            while attempts<max_attempts:
                try:
                    driver.get(self.press_release_url)
                    #driver.get('chrome-extension://ajkhmmldknmfjnmeedkbkkojgobmljda/options.html')
                    #driver.find_element(By.ID,'username_field').send_keys(proxy_username)
                    #driver.find_element(By.ID,'password_field').send_keys(proxy_password)
                    #driver.find_element(By.ID,'save_button').click()    
                    #driver.get(self.press_release_url)
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
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
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
    