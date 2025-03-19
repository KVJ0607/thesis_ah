import re
import time
import math
import requests

from bs4 import BeautifulSoup
import urllib.request
import ssl
import certifi


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
FLAT_MAX_PAGE=100

class Cp_41(PressRelease):
    def __init__(self):
        base_url="https://www.dfzq.com.cn"
        press_release_url="https://www.dfzq.com.cn/osoa/views/main/aboutus/mediacoverage/index.shtml"
        h_code="03958.HK".lower()
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='detail_box']"))).text
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
            rows_xpath="//div[@class='in_fr']//ul/li"
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
                date_xpath=row_xpath+"/a/em"

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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_41.retrieve_content)(url,is_proxy) for url in urls)
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
            return all_doc,self.company_id
            message_=""
            for err_url in all_err_url:
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(all_err_url,self.company_id))
   
class Cp_42(PressRelease):
    def __init__(self):
        base_url="https://www.portqhd.com/"
        press_release_url="https://www.portqhd.com/c/media_corporate.php"
        h_code="03369.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt='https://www.portqhd.com/robots.txt'

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

    def get_total_page(self,driver:WebDriver,year:int)->int:
        check_page={
            '2023':3,
            '2022':1,
            '2021':1,
            '2020':1,
            '2019':1,
            '2018':1,
            '2017':3,
            '2016':1,
            '2015':3,
            '2014':1,
        }
        return check_page[str(year)]

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="/html/body/div[1]/div[3]/div[2]/div/div[2]/div[3]/ul/li[{}]/a".format(cur_page+1)
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        if is_proxy:
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
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
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"html/body"))).text
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
            rows_xpath="/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[2]/div[2]/ul[1]/li"
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,rows_xpath)))
        except Exception as e:
            print("problem finding the list of news in a page")
            print(e)
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
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"div[1]/a[1]"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"div[2]/span[1]"
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_iso=extract_iso_date(wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text.replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').strip())
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_42.retrieve_content)(url,is_proxy) for url in urls)
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
            years=[2023,2022,2021,2020,2019,2018,2017,2016]
            for year_ in years: 
                total_page=self.get_total_page(driver,year_)
                current_page=self.get_current_page(driver)
                if year_ in [2023,2022,2021,2020]:
                    ul_index=1
                elif year_ in [2019,2018,2017,2016]:
                    ul_index=2
                else: 
                    ul_index=3 
                if year_ in[2023,2019,2015]: 
                    li_index=1
                elif year_ in [2022,2018,2014]: 
                    li_index=2
                elif year_ in [2021,2017]: 
                    li_index=3
                else: 
                    li_index=4                    
                year_xpath="/html/body//div[@class='page_right_wrap']//div[@class='ir_year']/ul[{}]/li[{}]".format(ul_index,li_index)
                year_ul_xpath="/html/body//div[@class='page_right_wrap']//div[@class='ir_year']/ul[{}]".format(ul_index)
                page_div=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,year_xpath)))
                ul_div=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,year_ul_xpath))).get_attribute('style')
                no_show= not 'block' in ul_div
                while no_show: 
                    button_xpath="/html/body//div[@class='page_right_wrap']//div[@class='ir_year']/div[@class='year_btn']/a[@id='next_a']"
                    button=WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,button_xpath)))
                    driver.execute_script('arguments[0].click();', button)
                    time.sleep(1)
                    ul_div=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,year_ul_xpath))).get_attribute('style')
                    no_show= not 'block' in ul_div
                page_div.get_attribute('')
                driver.execute_script('arguments[0].click();', page_div)
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
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))
        
    def __init__(self):
        base_url=""
        press_release_url=""
        h_code="06196.HK".lower()
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
        tot_page_xpath="/html/body/div[@class='container']//div[@class='main_right col-lg-9 col-md-9 col-sm-9']/div[@class='text-right']//div[@class='page_time hidden-xs']/div"
        page_text=WebDriverWait(driver,20).until(EC.visibility_of_element_located((By.XPATH,tot_page_xpath))).text
        page_num=int(re.search(r'\d+',page_text).group())        
        return min(FLAT_MAX_PAGE,page_num)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        #
        page_xpath="//div[@class='container']//ul[@class='pagination']/li/a[contains(text()={})]".format(cur_page+1)
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        if is_proxy:
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
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
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body"))).text
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
        rows_xpath="/html/body/div[@class='container']/div[@id='business']/div[@class='row']//ul/li"
        try:            
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
            # try:
            url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"a"
            date_xpath=rows_xpath+f"[{row_index+1}]/"+"a/span"
            url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
            title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('title')
            date_=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').strip()
            date_in_iso=extract_iso_date(date_)
            # except Exception as e:
            #     print(f'problem with crawling rows element in this page: {driver.current_url}')
            #     if driver.current_url not in err_urls:
            #         err_urls.append(driver.current_url)
            #     if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
            #         self.add_error_count()
            #         continue
            #     else:
            #         raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_43.retrieve_content)(url,is_proxy) for url in urls)
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
            
            years=[2023,2022,2021,2020,2019]
            all_doc:list[Document]=[]
            year_class={
                '2023':'hover686',
                '2022':'hover672',
                '2021':'hover661',
                '2020':'hover650',
                '2019':'hover641',
                '2018':'hover636'
            }
            for year_ in years:#//*[@id="business"]/div[2]
                time.sleep(3)
                curr_url='http://www.zzbank.cn/inversrtor_relations/ggth/agu/{}/'.format(year_)
                driver.get(curr_url)
                #year_xpath="div[@id='business']/div[2]/a[class='{}']".format(year_class[str(year_)])
                #year_ele=WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,year_xpath)))
                #driver.execute_script('arguments[0].click();', year_ele)
                time.sleep(4)
                total_page=self.get_total_page(driver)
                current_page=self.get_current_page(driver)
                
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
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))

class Cp_44(PressRelease):
    def __init__(self):
        base_url="http://www.liaoningport.com/"
        press_release_url="http://www.liaoningport.com/rdzx/index.jhtml"
        h_code="02880.HK".lower()
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
        return min(FLAT_MAX_PAGE,37)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//div[@class='page-large']//a[@class='next-page']"
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        if is_proxy:
            driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        else:
            driver2=webdriver.Chrome(options=chrome_options)
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
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='about_right']//article[@class='speech']/div[@class='bd']"))).text
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
            rows_xpath="//div[@class='about_right']//article[@class='speech']/div[@class='bd']/div"
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
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"div/div[@class='title']/a"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"div/div[@class='date']"
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_iso=extract_iso_date(wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text.replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').strip())
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_44.retrieve_content)(url,is_proxy) for url in urls)
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
            time.sleep(1.5)
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
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))

class Cp_45(PressRelease):
    def __init__(self):
        base_url="https://www.huahonggrace.com/"
        press_release_url="https://www.huahonggrace.com/c/news_press.php"
        h_code="01347.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt='https://www.huahonggrace.com/robots.txt'

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
        try: 
            pages_text=WebDriverWait(driver,5).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='inner_cont']//div[@class='page']/div[@class='page_list']"))).text
            pages_text=pages_text.split('\n')
            all_pages=[]
            digit_set=['0','1','2','3','4','5','6','7','8','9']
            for page_txt in pages_text: 
                is_num=True
                for page_str in page_txt: 
                    if page_str not in digit_set: 
                        is_num=False
                if is_num: 
                    all_pages.append(int(page_txt))
            return min(FLAT_MAX_PAGE,max(all_pages))
        except Exception: 
            return 1                                                    
                
        

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[normalize-space()='>']"
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        if is_proxy:
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
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/hmtl/body/div[@class='body_box']/div[@class='container']/div[@class='cont_right']"))).text
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
            rows_xpath="//div[@class='container']/div[@class='cont_right']/div[@class='inner_cont']/div[@class='inner_cont_ann']/ul/li"
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
            try:
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"p/a"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"div[@class='date']"
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').strip()
                date_obj = datetime.strptime(date_, '%d-%m-%Y')
                new_date_str = date_obj.strftime('%Y-%m-%d')
                date_in_iso=extract_iso_date(new_date_str)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_45.retrieve_content)(url,is_proxy) for url in urls)
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
            all_doc:list[Document]=[]
            years=list(range(2014,2024))
            for year_ in years:
                url_="https://www.huahonggrace.com/c/news_press.php?year={}".format(year_)
                time.sleep(1)
                driver.get(url_)
                time.sleep(1)
                # driver_action=ActionChains(driver)
                
                # target_list=driver.find_element(By.XPATH,"//div[@class='cont_right']/div[@class='inner_cont']/div[@class='inner_cont_year']")
                # driver_action.move_to_element(target_list).perform()
                # desired_year_xpath="//div[@class='cont_right']/div[@class='inner_cont']/div[@class='inner_cont_year']/div[@class='year_list']/a[contains(text()='{}')]".format(year_)
                # desired_option = driver.find_element(By.XPATH, desired_year_xpath)
                # desired_option.click()
                total_page=self.get_total_page(driver)
                current_page=self.get_current_page(driver)
                
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
            return all_doc,self.company_id
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))
        
class Cp_46(PressRelease):
    def __init__(self):
        base_url="https://www.ccccltd.cn/"
        press_release_url="https://www.ccccltd.cn/news/gsyw/"
        h_code="01800.HK".lower()
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
        return min(FLAT_MAX_PAGE,100)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//ul[@class='pageion mhide']/li/a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        if is_proxy:
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
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='TRS_Editor']"))).text
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
            rows_xpath="//dd[@class='cloumn-content-box tzzgx-padding-reset']/div[@class='tzzgx-gszl-items']/dl"
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
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"dt/a"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"dd"
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_iso=extract_iso_date(wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').strip())
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_46.retrieve_content)(url,is_proxy) for url in urls)
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
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))
"""        
class Cp_47(PressRelease):
    def __init__(self):
        base_url="https://www.china-cdt.com/"
        press_release_url="http://www.cdt-re.com/xnygsweb/showNewsListForSiteControlAction!showNewsList.action?site=re_site&program=xnyEN_XWZX_GSYW"
        h_code="00991.HK".lower()
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
        return min(FLAT_MAX_PAGE,)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath=""
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        if is_proxy:
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
            try:
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+""
                date_xpath=rows_xpath+f"[{row_index+1}]/"+""
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_iso=extract_iso_date(wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').strip())
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_47.retrieve_content)(url,is_proxy) for url in urls)
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
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))
"""
class Cp_48(PressRelease):
    def __init__(self):
        base_url="http://www.mcc.com.cn/"
        press_release_url="http://www.mcc.com.cn/xwzx_7388/lddt/"
        h_code="01618.HK".lower()
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
        return min(FLAT_MAX_PAGE,25)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="/html/body/div[@class='main qs_clear']//div[@class='page']//a[contains(text(),'下一页')]"
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
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body//div[@class='contant']"))).text
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
            rows_xpath="/html/body//div[@class='main qs_clear']/div[@class='rightpart']/div[@class='sortlist']/ul/li"
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
                date_in_iso=extract_iso_date(wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').strip())
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_48.retrieve_content)(url,is_proxy) for url in urls)
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
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))

class Cp_49(PressRelease):
    def __init__(self):
        base_url="https://www.tjcep.com/"
        press_release_url="https://tjcep.com/html/list-30-1.html"
        h_code="01065.HK".lower()
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
        return min(FLAT_MAX_PAGE,193)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="/html/body//div[@class='content_right_content full-width']/div/nav[@class='pagination_wrap']/ul[@class='pagination']/li/a[contains(text(),'下一页')]"
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
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body"))).text
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
            rows_xpath="/html/body//div[@class='content_right_content full-width']/div/ul[@class='news_list']/li"
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
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"div[2]/p[@class='news_item_tit']/a"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"div[2]/p[@class='news_item_time']"
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_iso=extract_iso_date(wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').strip())
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_49.retrieve_content)(url,is_proxy) for url in urls)
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
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
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
            start_page=20
            all_doc:list[Document]=[]
            while(current_page<=total_page):
                if(current_page>=start_page):
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
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))

class Cp_50(PressRelease):
    def __init__(self):
        base_url="https://www.junshipharma.com"
        press_release_url="https://www.junshipharma.com/news/"
        h_code="01877.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt='https://www.junshipharma.com/robots.txt'

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
        
    def get_current_year(self,driver:WebDriver)->int:
        wait=WebDriverWait(driver,15)
        cur_year=wait.until(EC.visibility_of_element_located((By.XPATH,"/html/body//div[@class='content']/div[@class='head content flex about-experience mb7']/div[@class='month flex align-center']/div/span[@class='current-year']"))).text
        cur_year=cur_year.replace(" ","").replace('"','')
        return int(cur_year)

    def get_previous_year(self,driver:WebDriver)->None:
        wait=WebDriverWait(driver,15)
        cur_year=wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body//div[@class='content']/div[@class='head content flex about-experience mb7']/div[@class='month flex align-center']/span[@class='prev month-button']")))
        driver.execute_script('arguments[0].click();', cur_year)
        time.sleep(2)
        
    def is_more(self,driver:WebDriver)->bool: 
        wait=WebDriverWait(driver,15)
        is_more=True
        while is_more:
            try:
                more_button=wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[@class='news-view  month-select']/div[@class='content']/p[@class='text-center hide-btn scroll-load']/button[@class='button-red button load_more_post_ajax']")))
                driver.execute_script('arguments[0].click();', more_button)
                is_more=True
                time.sleep(3)                
            except TimeoutException: 
                is_more=False
                return False
        return True
        
    def get_total_page(self,driver:WebDriver)->int:
        return min(FLAT_MAX_PAGE,)
        
    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath=""
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
        if is_proxy:
            proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
            chrome_options.add_extension(proxies_extension)
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
        if is_proxy:
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
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body//div[@class='container']"))).text
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
            rows_xpath="/html/body//div[@class='content']/ul/li"
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
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"a/div[@class='mess flex1']/span[@class='date']"
                title_xpath=rows_xpath+f"[{row_index+1}]/"+"a/div[@class='mess flex1']/h3"
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.presence_of_element_located((By.XPATH,title_xpath))).text
                date_text=wait.until(EC.presence_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_text.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').strip())
                print(url,'\n','title','\n',date_text)
                
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_50.retrieve_content)(url,is_proxy) for url in urls)
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
            years_list=[2023,2022,2021]
            all_doc:list[Document]=[]
            for year_ in years_list:                 
                current_year=self.get_current_year(driver)
                while current_year > year_: 
                    self.get_previous_year(driver)
                    current_year=self.get_current_year(driver)
                    time.sleep(1)
                time.sleep(1)
                self.is_more(driver)                          
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{year_} of {self.company_id}')
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                time.sleep(3)
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))
        
class Cp_51(PressRelease):
    def __init__(self):
        base_url="https://www.magang.com.hk/"
        press_release_url="https://www.magang.com.hk/tchi/announcement.asp"
        h_code="00323.HK".lower()
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
        return min(FLAT_MAX_PAGE,1)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        pass 

    @staticmethod
    def retrieve_content(url:str,is_proxy)->dict[str,str|None]:
        date_ele=None
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
            
        # for url that is not files resource
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
        total_txt=""
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
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body"))).text
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
            years_xpath="/html/body/table[2]/tbody/tr[1]/td/table/tbody/tr[1]/td[2]/table/tbody/tr[3]/td/table"
            years=wait.until(EC.presence_of_all_elements_located((By.XPATH,years_xpath)))
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
        for year_index in range(len(years)):
            rows_xpath=years_xpath+"[{}]/tbody/tr".format(year_index+1)
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,rows_xpath)))
            for row_index in range(len(rows)):
                if row_index==0:
                    continue
                try:
                    url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"td[3]/span/a"
                    date_xpath=rows_xpath+f"[{row_index+1}]/"+"td[4]/span"
                    url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                    title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                    date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                    date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                    print(url)
                    print(title)
                    print(date_in_iso)
                except Exception as e:
                    print(f'problem with crawling rows element in this page: {driver.current_url}')
                    if driver.current_url not in err_urls:
                        err_urls.append(driver.current_url)
                    if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                        self.add_error_count()
                        continue
                    else:
                        raise(MaxErrorReached())
                if (type(url)==str and url!="" and url!=None) or is_file(url):
                    urls.append(url)
                    document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
                else:
                    print(f'This {url} is not an internal link')
                    continue

        content_list = Parallel(n_jobs=-1)(delayed(Cp_51.retrieve_content)(url,is_proxy) for url in urls)
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
                    print('the crawling process of extracting text has error for {}'.format(urls[i]))
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
                time.sleep(0.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))
        
class Cp_52(PressRelease):
    def __init__(self):
        base_url="https://www.htsec.com/"
        press_release_url="https://www.htsec.com/ChannelHome/20170915/index.shtml"
        h_code="06837.HK".lower()
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
        return min(FLAT_MAX_PAGE,19)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        pages_next=[6,11,16]
        if (cur_page+1) in pages_next:
            next_section_button_xpath="/html/body//div[@class='main']/div[@class='fy']/a[span[contains(text()='>>')]]"
            next_section_button=wait.until(EC.element_to_be_clickable((By.XPATH,next_section_button_xpath)))
            driver.execute_script('arguments[0].click();', next_section_button)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        
        page_xpath="/html/body//div[@class='main']/div[@class='fy']/a[span[contains(text()='{}')]]".format(cur_page+1)
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
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body//div[@class='con_art']/article[@class='article']"))).text
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
            rows_xpath="/html/body//div[@class='main']/div[@class='main_list']/div/ul/li"
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
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_52.retrieve_content)(url,is_proxy) for url in urls)
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
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))

class Cp_53(PressRelease):

    def __init__(self):
        base_url="https://www.cmhk.com/"
        press_release_url="https://www.cmhk.com/main/xwzx/xsgsdt/index.shtml"
        h_code="06099.HK".lower()
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
        return min(FLAT_MAX_PAGE,)

    def next_page(self,cur_page:int,driver:WebDriver)->bool:
        wait = WebDriverWait(driver,20)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="/html/body//div[@class='w1200']/div[@class='box']/div[@class='jtjx_move']/a[@class='btn_bottom']"
        count=0
        while count<100:
            try:
                page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
                ActionChains(driver).scroll_to_element(page_div).perform()
                driver.execute_script('arguments[0].click();', page_div)                
                count+=1
                time.sleep(3)
            except: 
                return True

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
            time.sleep(4)
            
        except WebDriverException as e:
            try:
                requests_result=requests.get(url)
                soup=BeautifulSoup(requests_result.content,'html')
                target_ele=soup.find('body').text
                #"/html/body//div[@class='page_warp jtyw-xqy']/div[@class='w1200']/div[@class='box]/div[@class='article_box']/div[@class='article_box_title']/span/i
                date_eles=soup.find_all('div','i')
                for date_ele in date_eles: 
                    date_flag=is_iso_date(date_ele)
                    if date_flag: 
                        date_ele=extract_iso_date(date_flag)
                        return from_tuple_retri(target_ele,date_ele,date_in_iso=date_ele)
                raise(e)
                
            except Exception:
                print(f'error: receive_content function cannot connect to {url}')
                driver2.quit()
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
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body//div[@class='page_warp jtyw-xqy']/div[@class='w1200']/div[@class='box]/div[@class='article_box']/div[@class='articl_box']"))).text
            date_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body//div[@class='page_warp jtyw-xqy']/div[@class='w1200']/div[@class='box]/div[@class='article_box']/div[@class='article_box_title']/span/i"))).text
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
            rows_xpath="/html/body//div[@class='w1200']/div[@class='box']/div[@class='jtjx_right']/ul/li"
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
            time.sleep(1)
            try:

                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"div/a"
                title_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"div/a/span[@class='liR']/b"
                row_xpath=rows_xpath+f"[{row_index+1}]"
                row=wait.until(EC.visibility_of_element_located((By.XPATH,row_xpath)))
                ActionChains(driver).scroll_to_element(row).perform()
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,title_ele_xpath))).text
                print(url)
                print(title)
            except Exception as e:
                message=''
                if url is None and title is not None: 
                    message=message+"url is problematic in this row in page: {}".format(driver.current_url)
                elif url is not None and title is None : 
                    message=message+'title is problematic in this row in page: {}'.format(driver.current_url)
                else: 
                    message=message+'both url and title is problematic in this row in page: {}'.format(driver.current_url)
                print(message)
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
                
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,None,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-2)(delayed(Cp_53.retrieve_content)(url,is_proxy) for url in urls)
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
            self.next_page(1,driver)
            all_doc:list[Document]=[]
            read_page_result=self.read_page(driver,is_proxy)
            doc_list=read_page_result["doc_list"]
            all_doc=all_doc+doc_list
            err_url_list=read_page_result["err_url_list"]
            all_err_url=all_err_url+err_url_list
            time.sleep(0.5)
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            return all_doc,self.company_id
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))

class Cp_54(PressRelease):
    def __init__(self):
        base_url="https://www.hpi.com.cn/"
        press_release_url="https://www.hpi.com.cn/HPINews/publish.aspx"
        h_code="00902.HK".lower()
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
        return min(FLAT_MAX_PAGE,)

    def next_page(self,cur_page:int,driver:WebDriver)->bool:
        wait = WebDriverWait(driver,15)
        try:
            page_xpath="/html/body//table[@id='bottomPagingWPQ3']/tbody/tr/td[@class='ms-vb ms-bottompagingline']//a[@class='ms-commandLink ms-promlink-button ms-promlink-button-enabled']"
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)
            time.sleep(1)             
        except Exception: 
            return False
        return True 
            
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
            try:
                requests_result=requests.get(url)
                soup=BeautifulSoup(requests_result.content,'html')
                target_ele=soup.find('body').text
                print(target_ele)
                return from_tuple_retri(target_ele,url,date_in_iso=date_ele)
            except Exception:
                print(f'error: receive_content function cannot connect to {url}')
                driver2.quit()
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
        except Exception as e:
            a=True
        try:
            iframe_ele=WebDriverWait(driver2,10).until(EC.presence_of_element_located((By.XPATH,"//iframe[@id='WebApplicationFrame']")))
            driver2.switch_to(iframe_ele)
            target_ele=driver2.find_element(By.XPATH,'/html/body').text
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
            rows_xpath="/html/body//table[@id='onetidDoclibViewTbl0']/tbody/tr"
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,rows_xpath)))
        except Exception as e:
            print("problem finding the list of news in a page")
            if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                self.add_error_count(5)
                return from_tuple_read([],[driver.current_url])
            else:
                raise(MaxErrorReached())
        document_list:list[Document]=[]
        urls:list[WebElement]=[]
        err_urls:list[str]=[]
        for row_index in range(len(rows)):
            time.sleep(0.1)
            try:
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"td[2]/a"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"td[4]"
                url_ele=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath)))
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())

            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()
                    continue
                else:
                    raise(MaxErrorReached())
            if (url_ele!=None):
                urls.append(url_ele)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
                
            for url_ in urls: 
                url_.send_keys()
            
            
            
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_54.retrieve_content_by_new_tab)(url,is_proxy) for url in urls)
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
            all_doc:list[Document]=[]
            is_next_page=True
            current_page=1
            while(is_next_page):
                read_page_result=self.read_page(driver,is_proxy)
                print(f'finish crawling page{current_page} of {self.company_id}')
                doc_list=read_page_result["doc_list"]
                all_doc=all_doc+doc_list
                err_url_list=read_page_result["err_url_list"]
                all_err_url=all_err_url+err_url_list
                is_next_page=self.next_page(current_page,driver)
                current_page+=1
                time.sleep(0.5)
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))
      
class Cp_55(PressRelease):
    def __init__(self):
        base_url="https://www.winshare.com.cn/"
        press_release_url="https://www.winshare.com.cn/mtgz/index.jhtml"
        h_code="00811.HK".lower()
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
        return min(FLAT_MAX_PAGE,23)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="/html/body//div[@class='page-numb']/ul[@id='pagination']/li/a[contains(text(),'下一页')]"
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
        except Exception as e:
            a=True
        try:

            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[@class='main-right-detail']/div[@class='text']"))).text
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
            rows_xpath="/html/body/div[4]/div/div[2]/div"
                        
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
        url=None
        title=None
        for row_index in range(len(rows)):
            if row_index >5:
                continue
            try:
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"div[1]/a[1]"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"div[2]/p"
                title_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"div[1]/a[1]/h4"
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
                    raise(MaxErrorReached(message))
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_55.retrieve_content)(url,is_proxy) for url in urls)
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
                time.sleep(1)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))







"""  
class Cp_56(PressRelease):

    def __init__(self):
        base_url="https://www.huaxincem.com/"
        press_release_url="https://www.huaxincem.com/xinwenzhongxin/meitijujiao.html"
        h_code="06655.HK".lower()
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
        return min(FLAT_MAX_PAGE,165)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        try:
            page_xpath="/html/body/div[1]/div[5]/div[2]/div/a[@class='next']"
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)
        except Exception: 
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            time.sleep(2)
            page_xpath="/html/body/div[1]/div[5]/div[2]/div/a[@class='next']"
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
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body//div[@class='nyMain passage w1200']/div[@class='psgCont']"))).text
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
            rows_xpath="/html/body//div[@class='nyMain p2_1 w1200']/div[@class='item2']/ul[@class='list']/li"
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
                title_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"a/div/div[@class='cont fr']/h5"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"a/div/div[@class='date fl']"
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
                    raise(MaxErrorReached(message))
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_56.retrieve_content)(url,is_proxy) for url in urls)
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
                    time.sleep(1.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))
"""            
class Cp_56(PressRelease):
    def __init__(self):
        base_url="https://www.huaxincem.com/"
        press_release_url="https://www.huaxincem.com/xinwenzhongxin/meitijujiao.html"
        h_code="06655.HK".lower()
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
        return 42

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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//body/div/div[5]"))).text
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
            rows_xpath="//body/div/div/div[2]/ul[1]/li"
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
                title_ele_xpath=row_xpath+"/a/div[2]/h5"
                date_xpath=row_xpath+"/a/div[1]"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,title_ele_xpath))).text
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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_56.retrieve_content)(url,is_proxy) for url in urls)
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
            start_page=2
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
            return all_doc,self.company_id
            message_=""
            for err_url in all_err_url:
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(all_err_url,self.company_id))
        





class Cp_57(PressRelease):
    def __init__(self):
        base_url="https://m.picc.com/"
        press_release_url="https://m.picc.com/home/news/wapmtjj/"
        h_code="01339.HK".lower()
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
        return min(FLAT_MAX_PAGE,14)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="/html/body/div[3]/div/ol/li[1]/a"
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
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[2]/div"))).text
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
            rows_xpath="/html/body/div[3]/ul/li"
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
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"a/span[2]"
                title_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"a/b"
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
                    raise(MaxErrorReached(message))
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_57.retrieve_content)(url,is_proxy) for url in urls)
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
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))
            
            
            
class Cp_58(PressRelease):
    def __init__(self):
        base_url="https://www.dec-ltd.cn/"
        press_release_url="https://www.dec-ltd.cn/xwzx.htm"
        h_code="01072.HK".lower()
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
        return min(FLAT_MAX_PAGE,38)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="//a[contains(text(),'下页')]"                                                                        
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
        except Exception as e:
            a=True
        try:
            #swiper-slide 
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[8]/div/div[1]/form/div[1]/div[2]/div[1]/div"))).text
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
            rows_xpath="/html/body/div[7]/div/div/div/div/div/dl"
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
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"dd/a"
                monthday_date_xpath=rows_xpath+f"[{row_index+1}]/"+"dt/span"
                year_date_xpath=rows_xpath+f"[{row_index+1}]/"+"dt/i"
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                
                monthday_date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,monthday_date_xpath))).text
                year_date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,year_date_xpath))).text
                date_in_string=year_date_in_string+'-'+monthday_date_in_string
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
                print(url)
                print(title)
                print(date_in_iso)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                print(rows[row_index].text)[0:20]
                print(rows)
                print(rows[row_index].get_attribute('outerhtml'))
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
            if (type(url)==str and url!= "" and url!=None) and (is_internal_link(base_url=self.base_url,link=url) or is_file(url)):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_58.retrieve_content)(url,is_proxy) for url in urls)
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
            attempts=1
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
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))
        
        
"""
class Cp_59(PressRelease):

    def __init__(self):
        base_url="http://www.crsc.cn/"
        press_release_url="http://www.crsc.cn/g1097/m3796/mp2.aspx"
        h_code="03969.HK".lower()
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
        return min(FLAT_MAX_PAGE,120)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        time.sleep(1)
        page_xpath="//*[@id='Content-3796']/div/div[2]/div[22]/a[@class='i-pager-next ']"
        
        try:
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)
        except Exception:
            print('problem getting next page, now reload the page')
            driver.get(driver.current_url)
            time.sleep(4)
            page_div=wait.until(EC.element_to_be_clickable((By.XPATH,page_xpath)))
            driver.execute_script('arguments[0].click();', page_div)

#
#


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
        except Exception as e:
            a=True
        try:
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body/form/div[3]/div[4]/div[2]/div[2]/div/div/div[2]/div/div/div[3]"))).text
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
            rows_xpath="//div[@id='Content-3796']/div/div[2]/div"
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
                url_ele_xpath=rows_xpath+f"[{row_index+1}]/"+"div[1]/a"
                date_xpath=rows_xpath+f"[{row_index+1}]/"+"div[2]"
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
                    raise(MaxErrorReached(message))
            if (type(url)==str and url!="" and url!=None) or is_file(url):
                urls.append(url)
                document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_59.retrieve_content)(url,is_proxy) for url in urls)
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
                    time.sleep(3)
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
            time.sleep(2)
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
                time.sleep(1.5)
                current_page=current_page+1
            driver.quit()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            message_=""
            for err_url in all_err_url: 
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(message_))
"""            

class Cp_59(PressRelease):
    def __init__(self):
        base_url="http://www.crsc.cn"
        press_release_url="http://www.crsc.cn/1100.html"
        h_code="03969.HK".lower()
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
        page_xpath="//span[contains(text(),'下一页')]"
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='Gnews-detail ']"))).text
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
            rows_xpath="//div[@class='second-lb-module-module ']/div"
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
        len_rows=len(rows)
        for row_index in range(len_rows):
            if row_index==len_rows-1 or row_index==len_rows-2:
                continue
            time.sleep(0.1)
            url=None
            title=None
            date_in_iso=None
            try:
                #xpath of row_elements 
                row_xpath=rows_xpath+f"[{row_index+1}]"
                url_ele_xpath=row_xpath+"/div[1]/a"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/div[2]"

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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_59.retrieve_content)(url,is_proxy) for url in urls)
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
            return all_doc,self.company_id
            message_=""
            for err_url in all_err_url:
                message_=message_+err_url+"\n"
            message_=message_+"For company id: {}".format(self.company_id)
            message_=message_+"The press release link {}".format(self.press_release_url)
            raise(MaxErrorReached(all_err_url,self.company_id))
