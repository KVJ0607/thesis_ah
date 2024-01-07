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
from utils.crawling import PressRelease,is_file,from_tuple_retri,from_tuple_read,extract_normal_link,is_internal_link,extract_iso_date,is_iso_date,text_from_html,reverse_date_in_str,make_full_url
from company.company import *
from article.mining import _extracting_an_document        

ERROR_COUNT = 15
CONVERTION_RATE=0.4 #~70% hit rate
FLAT_MAX_PAGE=100

#
class Cp_120(PressRelease):
    def __init__(self):
        base_url="https://www.gpc.com.cn"
        press_release_url="https://www.gpc.com.cn/news/media.html"
        h_code="00874.HK".lower()
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
        return 15

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[contains(text(),'下一页 >')]"
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
                txt_length=len(target_ele)
                start_index=int(txt_length/2)
                print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='artical']"))).text
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
            rows_xpath="//div[@class='fr section']/div[1]/div"
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
                #rows_xpath="//div[@class='fr section']/div[1]/div"
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=row_xpath+"/div[2]/div[1]/div[1]/h2[1]/a[1]"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/div[2]/div/div/div/span"

                #scroll to row 
                # row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                # driver_action=ActionChains(driver)
                # driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                try: 
                    row_xpath=rows_xpath+f"[{row_index+1}]"
                    url_ele_xpath=row_xpath+"/div/div/div/h2[1]/a[1]"
                    #title_ele_xpath=row_xpath+"/"
                    date_xpath=row_xpath+"/div/div/div/div/span"

                    #scroll to row 
                    # row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                    # driver_action=ActionChains(driver)
                    # driver_action.scroll_to_element(row_ele).perform()

                    #other row elements
                    url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                    title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                    date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                    date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                    print(url)
                    print(title)
                    print(date_in_iso)
                except:
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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_120.retrieve_content)(url,is_proxy) for url in urls)
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
                start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
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

class Cp_121(PressRelease):
    def __init__(self):
        base_url="http://www.cqrcb.com"
        press_release_url="http://www.cqrcb.com/cqrcb/aboutus/presscenter/ourdynamic/index.html"
        h_code="03618.HK".lower()
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
        return 10

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
                txt_length=len(target_ele)
                start_index=int(txt_length/2)
                print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='contBox']"))).text
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
            rows_xpath="//div[@class='sideCont']//ul/li"
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
                #rows_xpath="//div[@class='sideCont']//ul/li"
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=row_xpath+"/a"
                title_ele_xpath=row_xpath+"/a/p"
                date_xpath=row_xpath+"/a/span"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()

            #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,title_ele_xpath))).text
                date_in_string=wait.until(EC.presence_of_element_located((By.XPATH,date_xpath))).text
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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_121.retrieve_content)(url,is_proxy) for url in urls)
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
                start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
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

class Cp_122(PressRelease):
    def __init__(self):
        base_url="http://www.yanzhoucoal.com.cn/"
        press_release_url="http://www.yanzhoucoal.com.cn/node_51468.html"
        h_code="01171.HK".lower()
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
                txt_length=len(target_ele)
                start_index=int(txt_length/2)
                print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='display-right']"))).text
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
            rows_xpath="//body/div/div/div/ul/li"
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
                url_ele_xpath=row_xpath+"//h2[1]//a[1]"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"//p[2]//span[1]"

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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_122.retrieve_content)(url,is_proxy) for url in urls)
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
                start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
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

class Cp_123(PressRelease):
    def __init__(self):
        base_url="http://www.sinopec.com"
        press_release_url="http://www.sinopec.com/listco/media_centre/news/"
        h_code="00386.HK".lower()
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
        return 1

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        pass

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
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            try:
                html=urllib.request.urlopen(url,context=context).read()
                target_ele=text_from_html(html)
                txt_length=len(target_ele)
                start_index=int(txt_length/2)
                print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='container-right-one-l']"))).text
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
            rows_xpath="//body[1]/div[1]/span[1]/div[1]/div[2]/div[3]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/ul[1]/li"
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
                url_ele_xpath=row_xpath+"/div[1]/a"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/div[1]/span[1]"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()
                
                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text.replace('(',"").replace(")","")
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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_123.retrieve_content)(url,is_proxy) for url in urls)
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
                start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
                content_len=len(content_to_be_set)
                start_index=int(content_len/2)
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

class Cp_124(PressRelease):
    def __init__(self):
        base_url="https://www.tsingtao.com.cn"
        press_release_url="https://www.tsingtao.com.cn/news/news.html"
        h_code="00168.HK".lower()
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
        return 1    

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//div[@class='layui-flow-more']//a"
        #driver_action=ActionChains(driver)
        count_=0
        while count_<200:             
            try:
                page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
                #driver_action.scroll_to_element(page_div).perform()
                driver.execute_script('arguments[0].click();', page_div)
                count_+=1
            except Exception:
                break

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
        except WebDriverException as e:
            print(f'error: receive_content function cannot connect to {url}')
            context=ssl.create_default_context(cafile=certifi.where())
            try:
                html=urllib.request.urlopen(url,context=context).read()
                target_ele=text_from_html(html)
                txt_length=len(target_ele)
                start_index=int(txt_length/2)
                print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='page-news']"))).text
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
            rows_xpath="//div[@class='page-list']//ul/li"
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
                title_ele_xpath=row_xpath+"/a/div[3]"
                date_xpath=row_xpath+"/a/div[2]"

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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_124.retrieve_content)(url,is_proxy) for url in urls)
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

class Cp_125(PressRelease):
    def __init__(self):
        base_url="https://www.anhui-expressway.net"
        press_release_url="https://www.anhui-expressway.net/info_107101_1.html"
        h_code="00995.HK".lower()
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
        return 27

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
                txt_length=len(target_ele)
                start_index=int(txt_length/2)
                print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='article']"))).text
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
            rows_xpath="//div[@class='newsList']//ul/li"
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
                url_ele_xpath=row_xpath+"/div[2]/div[1]//a"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/div[1]"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_string=date_in_string.split('\n')[1]+'-'+date_in_string.split('\n')[0]
                date_in_iso=extract_iso_date(date_in_string.strip())
                # print(url)
                # print(title)
                # print(date_in_iso)
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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_125.retrieve_content)(url,is_proxy) for url in urls)
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

class Cp_126(PressRelease):
    def __init__(self):
        base_url="http://www.petrochina.com.cn"
        press_release_url="http://www.petrochina.com.cn/petrochina/mtbd/xwgg_list.shtml"
        h_code="".lower()
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
        return 20

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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//body/div/div/div/div[1]/div[2]/div[1]"))).text
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
            rows_xpath="//div[@class='middleRow']//ul/li"
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
                url_ele_xpath=row_xpath+"/span[1]/a"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/span[2]"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()

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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_126.retrieve_content)(url,is_proxy) for url in urls)
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

class Cp_127(PressRelease):
    def __init__(self):
        base_url="https://www.beigene.com.cn/"
        press_release_url="https://www.beigene.com.cn/mediacenter/news/"
        h_code="06160.HK".lower()
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

    @staticmethod
    def reject_button(driver:WebDriver):
        try:
            button=WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.XPATH,"//button[@id='onetrust-reject-all-handler']")))
            driver.execute_script('arguments[0].click();', button)
        except:
            pass
    def add_error_count(self,add_error_count_:int=1)->None:
        self.__error_count=self.__error_count+add_error_count_

    def add_success_count(self,add_count:int=1)->None:
        self.__success_count=self.__success_count+add_count
    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 12

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
        Cp_127.reject_button(driver2)
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='entry-content']"))).text
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
            rows_xpath="/html/body/main/div/div/div[2]/div"
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
                url_ele_xpath=row_xpath+"/div[2]/a"
                title_ele_xpath=row_xpath+"/div[2]"
                date_xpath=row_xpath+"/div[1]"

                #scroll to row 
                row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                if row_ele.get_attribute('class') !="news-item":
                    continue
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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_127.retrieve_content)(url,is_proxy) for url in urls)
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
            Cp_127.reject_button(driver)
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
                    Cp_127.reject_button(driver)
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

class Cp_128(PressRelease):
    def __init__(self):
        base_url="https://www.asymchem.com.cn"
        press_release_url="https://www.asymchem.com.cn/qyzs2/qyxw/"
        h_code="06821.HK".lower()
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='main-r fr']"))).text
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
            rows_xpath="//div[@class='index-news news-list']//ul/li"
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
                title_ele_xpath=row_xpath+"/a/div[2]"
                date_xpath=row_xpath+"/a/div[3]"

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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_128.retrieve_content)(url,is_proxy) for url in urls)
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

class Cp_129(PressRelease):
    def __init__(self):
        base_url="https://www.cebbank.com"
        press_release_url="https://www.cebbank.com/site/ceb/gddt/mtgz/index.html"
        h_code="06818.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt="https://www.cebbank.com/robots.txt"

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

    def get_total_page(self,driver:WebDriver,my_max:int)->int:
        return min(301,my_max)
    
    def get_to_page(self,driver,start_page:int):
        from selenium.webdriver.common.keys import Keys
        input_box=WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,"//input[@type='text']")))
        input_box.clear()
        time.sleep(0.5)
        input_box.send_keys(str(start_page))
        input_box.send_keys(Keys.ENTER)
        
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='gd_xilan']"))).text
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
            rows_xpath="//div[@class='main']//ul/li"
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
                url_ele_xpath=row_xpath+"/div[1]/a"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/span[2]"

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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_129.retrieve_content)(url,is_proxy) for url in urls)
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

    def crawling(self,my_max:int,my_start:int,is_proxy=False)->tuple[list[Document],str]:
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
            total_page=self.get_total_page(driver,my_max)
            start_page=my_start
            self.get_to_page(start_page)
            time.sleep(1)
            current_page=start_page
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

class Cp_130(PressRelease):
    def __init__(self):
        base_url="http://www.tianqilithium.com"
        press_release_url="http://www.tianqilithium.com/medium/media.html"
        h_code="09696.HK".lower()
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
        return 7

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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//body/div/div[2]/div[1]/div[1]"))).text
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
            rows_xpath="//body/div/div[2]/div[1]/div[1]/ul/li"
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
                url_ele_xpath=row_xpath+"/"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/"

                #scroll to row 
                row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                driver_action=ActionChains(driver)
                driver_action.scroll_to_element(row_ele).perform()

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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_130.retrieve_content)(url,is_proxy) for url in urls)
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
