import re
import time
import math
import requests

from bs4 import BeautifulSoup

import ssl
import certifi
import urllib.request

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
from utils.crawling import PressRelease,is_file,from_tuple_retri,from_tuple_read,extract_normal_link,is_internal_link,extract_iso_date,is_iso_date,text_from_html
from company.company import *
from article.mining import _extracting_an_document        

ERROR_COUNT = 15
CONVERTION_RATE=0.4 #~70% hit rate

class Cp_60(PressRelease):
    def __init__(self):
        base_url="http://www.cqcbank.com/"
        press_release_url="http://www.cqcbank.com/cn/tzzgx/gsgg/gsggH/index.html"
        h_code="01963.HK".lower()
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
        return min(100,93)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        #>
        page_xpath="//a[normalize-space(text())='>']"
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            time.sleep(2)
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        max_attempts=5
        attempts=0
        while attempts<max_attempts:
            try:
                driver2.get(url)
                time.sleep(2)
                break
            except WebDriverException as e:
                attempts += 1
                if "net::ERR_CONNECTION_RESET" in str(e) and attempts<max_attempts:
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else:
                    print(f'error: receive_content function cannot connect to {url}')
                    driver2.quit()
                    return from_tuple_retri(None,url,date_in_iso=date_ele)
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            for url_ in url_list:                
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                print("extracting document {} inside a page {}".format(url_,url))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='main_content']"))).text
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
            rows_xpath="//ul[@class='dhy_b']/li"
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
            try:
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"a"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"span"
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) and (is_internal_link(base_url=self.base_url,link=url) or is_file(url)):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_60.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=err_url=="" or err_url==None
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                document_list[i].set_content(content_list[i]["content"])
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
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
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
                    time.sleep(2)
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
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=3
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                if current_page>=start_page:
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

class Cp_61(PressRelease):
    def __init__(self):
        base_url="http://www.clzd.com/"
        press_release_url="http://www.clzd.com/tc/news.php"
        h_code="01858.HK".lower()
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



    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        all_doc:list[Document]=[]
        
        url1="https://manager.wisdomir.com/files/339/2023/0517/20230523113413_56300161_tc.pdf"
        url2="https://manager.wisdomir.com/files/339/2023/0313/20230313102413_10719198_tc.pdf"
        url3="https://manager.wisdomir.com/files/339/2023/0130/20230130151159_54167493_tc.pdf"
        all_doc.append(Document(url1,"春立醫療“康覆機器人+”項目啟動","2023-05-17",self.base_url,_extracting_an_document(Document.from_url(url1)),None,self.company_id))
        all_doc.append(Document(url2,"『企業動態』國家重點研發計劃項目在京順利啓動！","2023-03-13",self.base_url,_extracting_an_document(Document.from_url(url2)),None,self.company_id))
        all_doc.append(Document(url3,"【企業動態】喜訊！春立醫療再次獲批國家重點研發計劃項目","2023-01-30",self.base_url,_extracting_an_document(Document.from_url(url3)),None,self.company_id))

        return all_doc,self.company_id
    

class Cp_62(PressRelease):
    def __init__(self):
        base_url="http://www.chenmingpaper.com/"
        press_release_url="http://www.chenmingpaper.com/news/news.aspx"
        h_code="01812.HK".lower()
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
        return min(100,41)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[normalize-space(text())='下一页']"
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            time.sleep(2)
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        
        #connect to page

        try:
            driver2.get(url)
            time.sleep(2)
        except WebDriverException as e:
            print(f'Warning: fail to connect to page via selenium, now trying bs4 {url}')
            context = ssl.create_default_context(cafile=certifi.where())
            html = urllib.request.urlopen(url,context=context).read()
            target_ele=text_from_html(html)    
            txt_length=len(target_ele)   
            start_index=int(txt_length/2)
            print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
            return from_tuple_retri(target_ele,None,date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                print("extracting document {} inside a page {}".format(url_,url))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body/form/div[5]/div[2]"))).text
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
            rows_xpath="/html/body//div[@class='ty3']/div"
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
            #get rid of the header and footer 
            if row_index<4 or row_index==len(rows)-1: 
                continue
            try:
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"div[1]/a"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"div[2]/a"
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) and (is_internal_link(base_url=self.base_url,link=url) or is_file(url)):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-2)(delayed(Cp_62.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=err_url=="" or err_url==None
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                document_list[i].set_content(content_list[i]["content"])
                document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            else:
                self.add_error_count()
                err_urls.append(err_url)                    
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
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
                    time.sleep(2)
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
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                if current_page>=start_page:
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
        

#63 is skipped
class Cp_64(PressRelease):
    def __init__(self):
        base_url="https://www.gsrc.com/"
        press_release_url="https://www.gsrc.com/list/11.html"
        h_code="00525.HK".lower()
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
        return min(100,7)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[contains(text(),'下一页')]"
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            time.sleep(2)
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
            time.sleep(2)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context = ssl.create_default_context(cafile=certifi.where())
            html = urllib.request.urlopen(url,context=context).read()
            target_ele=text_from_html(html)
            print(target_ele[0:30])
            return from_tuple_retri(None,url,date_in_iso=date_ele)
    
        try:
            url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                print("extracting document {} inside a page {}".format(url_,url))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@id='contentRight']"))).text
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
            rows_xpath="//div[@id='down_list_s']/ul/li"
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
            url=None
            title=None
            date_in_iso=None
            try:
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"span[1]/a[1]"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"span[2]"
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) and (is_internal_link(base_url=self.base_url,link=url) or is_file(url)):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-2)(delayed(Cp_64.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=err_url=="" or err_url==None
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                document_list[i].set_content(content_list[i]["content"])
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
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
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
                    time.sleep(2)
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
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                if current_page>=start_page:
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

class Cp_65(PressRelease):
    def __init__(self):
        base_url="https://www.joinnlabs.com/"
        press_release_url="https://www.joinnlabs.com/news.php?tid=4"
        h_code="06127.HK".lower()
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
        return min(100,8)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        page_xpath="//a[normalize-space()={}]".format(cur_page+1)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            time.sleep(2)
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
            time.sleep(2)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context = ssl.create_default_context(cafile=certifi.where())
            html = urllib.request.urlopen(url,context=context).read()
            target_ele=text_from_html(html)
            txt_length=len(target_ele)
            start_index=int(txt_length/2)
            print('With bs4, content has length{} \n{}'.format(txt_length,target_ele[start_index:start_index+35]))
            return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                print("extracting document {} inside a page {}".format(url_,url))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//body/main/div/div/div[1]"))).text
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
            rows_xpath="//ul[@class='clear news_list']/li"
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
            url=None
            title=None
            date_in_iso=None
            try:
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"/a"
                title_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"/a/div[1]/h4[1]"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"/a/span[1]"
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,title_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) and (is_internal_link(base_url=self.base_url,link=url) or is_file(url)):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-2)(delayed(Cp_65.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=err_url=="" or err_url==None
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                document_list[i].set_content(content_list[i]["content"])
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
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
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
                    time.sleep(2)
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
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(2.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
        
        
class Cp_66(PressRelease):
    def __init__(self):
        base_url="http://www.cqgtjt.com/"
        press_release_url="http://www.cqgtjt.com/news/3/#c_portalResNews_list-16117296919612765-1"
        h_code="01053.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt='http://www.cqgtjt.com/robots.txt'

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
        return min(100,2)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//div[@class='next']"
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            time.sleep(2)
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
            time.sleep(2)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context = ssl.create_default_context(cafile=certifi.where())
            html = urllib.request.urlopen(url,context=context).read()
            target_ele=text_from_html(html)
            txt_length=len(target_ele)
            start_index=int(txt_length/2)
            print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
            return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                print("extracting document {} inside a page {}".format(url_,url))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@data-ename='资讯详情']"))).text
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
            rows_xpath="//div[@class='p_news container']/div"
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
            url=None
            title=None
            date_in_iso=None
            try:
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"a"
                yearmonth_date_xpath=rows_xpath+f"[{row_index+1}]/"+"a/div[1]/div[@class='newYearMon']"
                day_date_xpath=rows_xpath+f"[{row_index+1}]/"+"a/div[1]/div[@class='newData']"
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                yearmonth_date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,yearmonth_date_xpath))).text
                day_date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,day_date_xpath))).text
                date_in_string=yearmonth_date_in_string+'-'+day_date_in_string
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) and (is_internal_link(base_url=self.base_url,link=url) or is_file(url)):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-2)(delayed(Cp_66.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=err_url=="" or err_url==None
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                document_list[i].set_content(content_list[i]["content"])
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
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
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
                    time.sleep(2)
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
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                if current_page>=start_page:
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

    
class Cp_67(PressRelease):
    def __init__(self):
        base_url="https://www.cimcvehiclesgroup.com/"
        press_release_url="https://www.cimcvehiclesgroup.com/portal/list/index/id/18.html?year=2023"
        h_code="01839.HK".lower()
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

    def get_total_page(self,year:int,driver:WebDriver)->int:
        page_dict={
            '2014':0,
            '2015':0,
            '2016':0,
            '2017':1,
            '2018':1,
            '2019':0,
            '2020':1,
            '2021':2,
            '2022':2,
            '2023':1,
        }
        return min(100,page_dict[str(year)])

    def get_year(self,year:int,driver:WebDriver)->None:
        #//a[normalize-space()='2022']
        wait = WebDriverWait(driver,15)
        year_button_xpath="//a[normalize-space()={}]".format(year)
        year_button=wait.until(EC.element_to_be_clickable((By.XPATH,year_button_xpath)))
        driver.execute_script('arguments[0].click();', year_button)
        
    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//div[@class='arrow fa fa-chevron-right']"
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            time.sleep(2)
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
            time.sleep(2)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context = ssl.create_default_context(cafile=certifi.where())
            html = urllib.request.urlopen(url,context=context).read()
            target_ele=text_from_html(html)
            txt_length=len(target_ele)
            start_index=int(txt_length/2)
            print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
            return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                print("extracting document {} inside a page {}".format(url_,url))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='info']"))).text
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
            rows_xpath="//ul[@class='news-company-list']/li"
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
            url=None
            title=None
            date_in_iso=None
            try:
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"a"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"a/div[2]/div"
                title_xpath=rows_xpath+f"[{row_index+1}]/"+"a/div[2]/h4"
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,title_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) and (is_internal_link(base_url=self.base_url,link=url) or is_file(url)):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-2)(delayed(Cp_67.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=err_url=="" or err_url==None
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                document_list[i].set_content(content_list[i]["content"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                document_list[i].set_content(content_list[i]["content"])
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
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
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
                    time.sleep(2)
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
            
            
            start_page=1
            all_doc:list[Document]=[]
            years=list(range(2014,2024))
            
            for year_ in years: 
                current_page=1
                total_page=self.get_total_page(year_,driver)
                if total_page !=0:
                    self.get_year(year_,driver)
                else: 
                    continue
                
                
                while(current_page<=total_page):
                    if current_page>=start_page:
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


class Cp_68(PressRelease):
    def __init__(self):
        base_url="https://www.zmj.com/"
        press_release_url="https://www.zmj.com/corporate-news"
        h_code="00564.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt='https://www.zmj.com/robots.txt'

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


    def next_page(self,driver:WebDriver)->None:
        wait = WebDriverWait(driver,10)
        page_xpath="//a[cite[contains(text(),'加载更多')]]"
        end_xpath="//div[contains(text(),'没有更多了')]"
        
        try: 
            end_div=wait.until(EC.visibility_of_element_located((By.XPATH,end_xpath)))
            is_more=False
        except: 
            is_more=True
            
        while is_more:
            time.sleep(1)
            try:
                page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
                driver.execute_script('arguments[0].click();', page_div)
            except Exception:                
                a=True
            finally: 
                try: 
                    end_div=wait.until(EC.visibility_of_element_located((By.XPATH,end_xpath)))
                    is_more=False 
                except: 
                    is_more=True
                    

    def get_year_(self,year_:str,driver:WebDriver):                
        time.sleep(0.5)
        print("Please click the element on the {} now...".format(year_))
        input() 
        #driver.execute_script('arguments[0].click();', year_div)
        time.sleep(1)
        
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
            time.sleep(2)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            html=urllib.request.urlopen(url,context=context).read()
            target_ele=text_from_html(html)
            txt_length=len(target_ele)
            start_index=int(txt_length/2)
            print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
            return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                print("extracting document {} inside a page {}".format(url_,url))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='article-equity']"))).text
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
            rows_xpath="//div[@id='newsList']/a"
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
            url=None
            title=None
            date_in_iso=None
            try:
                
                #element_xpath
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=rows_xpath+f"[{row_index+1}]"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"div[2]"
                title_xpath=rows_xpath+f"[{row_index+1}]/"+"div[3]"
                
                #scroll to row element 
                driver_action=ActionChains(driver)
                row_ele=wait.until(EC.visibility_of_element_located((By.XPATH,row_xpath)))
                driver_action.scroll_to_element(row_ele).perform()
                
                #other element in that row
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,title_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) and (is_internal_link(base_url=self.base_url,link=url) or is_file(url)):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-2)(delayed(Cp_68.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=err_url=="" or err_url==None
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
                print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
                print(content_to_be_set[start_index:start_index+30])
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
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
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
                    time.sleep(2)
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
            years=['2022-2023','2020-2021','2018-2019']
            for year_ in years: 
                self.get_year_(year_,driver)
                time.sleep(1)
                self.next_page(driver)        
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{year_} of {self.company_id}')
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list                        
                time.sleep(0.5)                    
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_69(PressRelease):
    def __init__(self):
        base_url="http://www.molonggroup.com/"
        press_release_url="http://www.molonggroup.com/news19.asp"
        h_code="00568.HK".lower()
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
        return min(100,11)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[contains(text(),'下一页')]"
        driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver_action.scroll_to_element(page_div).perform()
            time.sleep(1.5)
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            time.sleep(2)
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
            time.sleep(2)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            html=urllib.request.urlopen(url,context=context).read()
            target_ele=text_from_html(html)
            txt_length=len(target_ele)
            start_index=int(txt_length/2)
            print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
            return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                print("extracting document {} inside a page {}".format(url_,url))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='about']"))).text
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
            rows_xpath="//div[@class='newsline']/a"
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
            url=None
            title=None
            date_in_iso=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+""
                year_date_xpath=rows_xpath+f"[{row_index+1}]/"+"div[@class='newstime']/span/div[@class='newstime_bot']"
                monthday_date_xpath=rows_xpath+f"[{row_index+1}]/"+"div[@class='newstime']/span/div[@class='newstime_top']"

                #scroll to row 
                row_ele=wait.until(EC.visibility_of_element_located((By.XPATH,row_xpath)))
                driver_action=ActionChains(driver)
                driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                year_date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,year_date_xpath))).text
                monthday_date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,monthday_date_xpath))).text
                date_in_string=year_date_in_string+monthday_date_in_string
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) and (is_internal_link(base_url=self.base_url,link=url) or is_file(url)):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-2)(delayed(Cp_69.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=err_url=="" or err_url==None
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
                print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
                print(content_to_be_set[start_index:start_index+30])
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
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
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
                    time.sleep(2)
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
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(2)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_70(PressRelease):
    def __init__(self):
        base_url="http://crcc-hr.com/"
        press_release_url="http://crcc-hr.com/col/col108/index.html"
        h_code="01186.HK".lower()
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
        return min(100,146)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[@title='下页']"
        driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver_action.scroll_to_element(page_div).perform()
            time.sleep(1.5)
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            time.sleep(2)
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
            time.sleep(2)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            html=urllib.request.urlopen(url,context=context).read()
            target_ele=text_from_html(html)
            txt_length=len(target_ele)
            start_index=int(txt_length/2)
            print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
            return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                print("extracting document {} inside a page {}".format(url_,url))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='EaCvy']"))).text
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
            rows_xpath="//div[@id='12006']/div/ul/li"
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
            url=None
            title=None
            date_in_iso=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"a"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"span"

                #scroll to row 
                row_ele=wait.until(EC.visibility_of_element_located((By.XPATH,row_xpath)))
                driver_action=ActionChains(driver)
                driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) and (is_internal_link(base_url=self.base_url,link=url) or is_file(url)):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-2)(delayed(Cp_70.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=err_url=="" or err_url==None
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
                print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
                print(content_to_be_set[start_index:start_index+30])
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
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
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
                    time.sleep(2)
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
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(2)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_71(PressRelease):
    def __init__(self):
        base_url="https://www.chinaredstar.com/"
        press_release_url="https://www.chinaredstar.com/news"
        h_code="01528.HK".lower()
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
        return min(100,21)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[normalize-space()='>']"
        driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver_action.scroll_to_element(page_div).perform()
            time.sleep(1.5)
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            time.sleep(2)
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
            time.sleep(2)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            html=urllib.request.urlopen(url,context=context).read()
            target_ele=text_from_html(html)
            txt_length=len(target_ele)
            start_index=int(txt_length/2)
            print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
            return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                print("extracting document {} inside a page {}".format(url_,url))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='news-detail']"))).text
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
            rows_xpath="//ul[@class='news-list']/li"
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
            url=None
            title=None
            date_in_iso=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"a"
                title_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"a/div[@class='news-words']/p[@class='news-title']"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"a/div[@class='news-words']/p[@class='news-date']"

                #scroll to row 
                row_ele=wait.until(EC.visibility_of_element_located((By.XPATH,row_xpath)))
                driver_action=ActionChains(driver)
                driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,title_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) and (is_internal_link(base_url=self.base_url,link=url) or is_file(url)):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-2)(delayed(Cp_71.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=err_url=="" or err_url==None
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
                print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
                print(content_to_be_set[start_index:start_index+30])
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
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
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
                    time.sleep(2)
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
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(2)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_72(PressRelease):
    def __init__(self):
        base_url="https://www.cygs.com/"
        press_release_url="https://www.cygs.com/news.aspx?mid=85"
        h_code="00107.HK".lower()
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
        return min(100,)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[contains(text(),'下一页')]"
        driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver_action.scroll_to_element(page_div).perform()
            time.sleep(1.5)
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            time.sleep(2)
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
            time.sleep(2)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            html=urllib.request.urlopen(url,context=context).read()
            target_ele=text_from_html(html)
            txt_length=len(target_ele)
            start_index=int(txt_length/2)
            print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
            return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                print("extracting document {} inside a page {}".format(url_,url))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='pmain w clearfix']"))).text
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
            rows_xpath="//ul[@class='pnews-list']/li"
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
            url=None
            title=None
            date_in_iso=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"a"
                title_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"a/div[@class='word fr']/h3"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"a/div[@class='word fr']/div[@class='d']/span[@class='date']"

                #scroll to row 
                row_ele=wait.until(EC.visibility_of_element_located((By.XPATH,row_xpath)))
                driver_action=ActionChains(driver)
                driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,title_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) and (is_internal_link(base_url=self.base_url,link=url) or is_file(url)):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-2)(delayed(Cp_72.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=err_url=="" or err_url==None
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
                print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
                print(content_to_be_set[start_index:start_index+30])
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
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
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
                    time.sleep(2)
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
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(2)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_73(PressRelease):
    def __init__(self):
        base_url=""
        press_release_url=""
        h_code="01138.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt=

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
        return min(100,)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath=""
        driver_action=ActionChains(driver)
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver_action.scroll_to_element(page_div).perform()
            time.sleep(1.5)
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            time.sleep(2)
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
        driver2.set_page_load_timeout(30)
        try:
            driver2.get(url)
            time.sleep(2)
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            html=urllib.request.urlopen(url,context=context).read()
            target_ele=text_from_html(html)
            txt_length=len(target_ele)
            start_index=int(txt_length/2)
            print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
            return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
        try:
            url_eles=WebDriverWait(driver2,15).until(EC.presence_of_all_elements_located((By.XPATH,"//body//a")))
            for url_ele in url_eles:
                new_url=url_ele.get_attribute('href')
                isfile_2=is_file(new_url)
                if isfile_2:
                    url_list.append(url_ele.get_attribute('href'))
            url_list=extract_normal_link(url_list)
            for url_ in url_list:
                total_txt=total_txt+_extracting_an_document(Document.from_url(url_))
                print("extracting document {} inside a page {}".format(url_,url))
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,""))).text
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
            rows_xpath=""
            #rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,rows_xpath)))
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
            url=None
            title=None
            date_in_iso=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+""
                date_xpath=rows_xpath+f"[{row_index+1}]/"+""

                #scroll to row 
                row_ele=wait.until(EC.visibility_of_element_located((By.XPATH,row_xpath)))
                driver_action=ActionChains(driver)
                driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) and (is_internal_link(base_url=self.base_url,link=url) or is_file(url)):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-2)(delayed(Cp_73.retrieve_content)(url,is_proxy) for url in urls)
        refined_document_list:list[Document]=[]
        for i in range(len(content_list)):
            err_url=content_list[i]["err_url"]
            doc_iso_date=document_list[i].published_at
            crawling_iso_date=content_list[i]["date_in_iso"]
            is_url_valid=err_url=="" or err_url==None
            is_doc_date_valid=is_iso_date(doc_iso_date)
            is_crawling_iso_date_valid=is_iso_date(crawling_iso_date)
            if is_url_valid and is_doc_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
                print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
                print(content_to_be_set[start_index:start_index+30])
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
                if self.error_count>ERROR_COUNT and self.success_count*CONVERTION_RATE<self.error_count:
                    raise(MaxErrorReached())
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
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
                    time.sleep(2)
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
            total_page=self.get_total_page(driver)
            current_page=self.get_current_page(driver)
            start_page=1
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                if current_page>=start_page:
                    read_page_result=self.read_page(driver,is_proxy)
                    print(f'finish crawling page{current_page} of {self.company_id}')
                    doc_list=read_page_result["doc_list"]
                    all_doc=all_doc+doc_list
                    err_url_list=read_page_result["err_url_list"]
                    all_err_url=all_err_url+err_url_list
                if(current_page<total_page):
                    self.next_page(current_page,driver)
                time.sleep(2)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
