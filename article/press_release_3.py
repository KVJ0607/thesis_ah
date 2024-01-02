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
from utils.crawling import PressRelease,is_file,from_tuple_retri,from_tuple_read,extract_normal_link,is_internal_link,extract_iso_date,is_iso_date
from company.company import *
from article.mining import _extracting_an_document        

ERROR_COUNT = 15
CONVERTION_RATE=0.4 #~70% hit rate


class Cp_41(PressRelease):
    def __init__(self):
        base_url="https://asia.tools.euroland.com/"
        press_release_url="https://asia.tools.euroland.com/tools/pressreleases/?companycode=cn-600958&lang=zh-cn#"
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
        return min(100,13)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))#/html[1]/body[1]/div[1]/div[3]/div[2]/table[1]/tbody[1]/tr[1]/td[2]/a[2]/span[1]
        next_page_xpath=f"/html/body//div[@id='PageFlickContainer']/div[@id='PagesContainer']/table/tr/td[2]/a[span[contains(text(),{cur_page+1})]]"
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,next_page_xpath)))
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
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        #chrome_options.add_argument("--disable-extensions")
        #chrome_options.add_argument('--headless')
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
        time.sleep(1)
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
        if target_ele==0 or target_ele==None:
            driver2.quit()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            rows_xpath="/html/body//div[@id='PageFlickContainer']/div[@id='PressReleases']/div"
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH, rows_xpath)))
            
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
                url_ele_xpath=rows_xpath+f"[{row_index}]/"+"div[1]/div/div[2]/div[1]/a/img"
                date_xpath=rows_xpath+f"[{row_index}]/"+"div[1]/div[1]/div[@class='PressRelease-Attachment']//span[@class='PressRelease-NewsDate']"
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('src')
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
            if (is_internal_link(base_url=self.base_url,link=url) and type(url)==str and url is not None) or is_file(url):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_41.retrieve_content)(url,is_proxy) for url in urls)
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
        #chrome_options.add_argument("--disable-extensions")
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
            WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,'/html[1]/body[1]/div[1]/div[1]/table[1]/tbody[1]/tr[1]/td[2]/a[6]'))).click()
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
            driver2=webdriver.Chrome(service=Service(options=chrome_options))
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
            if is_internal_link(base_url=self.base_url,link=url) and type(url)==str and url is not None or is_file(url):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
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
            raise(MaxErrorReached(all_err_url,self.company_id))
        
class Cp_43(PressRelease):
    def __init__(self):
        base_url="http://www.zzbank.cn/"
        press_release_url="http://www.zzbank.cn/inversrtor_relations/ggth/agu/2023/"
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
        return min(100,page_num)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        #
        page_xpath="//div[@class='container']//ul[@class='pagination']/li/a[text()={}]".format(cur_page+1)
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
            driver2=webdriver.Chrome(service=Service(options=chrome_options))
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
            if is_internal_link(base_url=self.base_url,link=url) and type(url)==str and url is not None or is_file(url):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
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
            raise(MaxErrorReached(all_err_url,self.company_id))

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
        return min(100,37)

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
            driver2=webdriver.Chrome(service=Service(options=chrome_options))
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
            if is_internal_link(base_url=self.base_url,link=url) and type(url)==str and url is not None or is_file(url):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
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
            raise(MaxErrorReached(all_err_url,self.company_id))

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
            return min(100,max(all_pages))
        except Exception: 
            return 1                                                    
                
        

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath=WebDriverWait(driver,5).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='inner_cont']//div[@class='page']/div[@class='page_list']/a[text()='>']")))
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
            driver2=webdriver.Chrome(service=Service(options=chrome_options))
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
            if is_internal_link(base_url=self.base_url,link=url) and type(url)==str and url is not None or is_file(url):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
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
                # desired_year_xpath="//div[@class='cont_right']/div[@class='inner_cont']/div[@class='inner_cont_year']/div[@class='year_list']/a[text()='{}']".format(year_)
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
            raise(MaxErrorReached(all_err_url,self.company_id))
        
        
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
        return min(100,100)

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
            driver2=webdriver.Chrome(service=Service(options=chrome_options))
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
            if is_internal_link(base_url=self.base_url,link=url) and type(url)==str and url is not None or is_file(url):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
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
            raise(MaxErrorReached(all_err_url,self.company_id))
"""        
class Cp_47(PressRelease):
    def __init__(self):
        base_url="https://www.china-cdt.com/"
        press_release_url="https://www.china-cdt.com/dtwz_site_HTML/index.html"
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
        return min(100,)

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
            driver2=webdriver.Chrome(service=Service(options=chrome_options))
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
            if is_internal_link(base_url=self.base_url,link=url) and type(url)==str and url is not None or is_file(url):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
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
            raise(MaxErrorReached(all_err_url,self.company_id))
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
        return min(100,25)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="/html/body/div[@class='main qs_clear']//div[@class='page']//a[text()='下一页']"
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
            driver2=webdriver.Chrome(service=Service(options=chrome_options))
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
            if is_internal_link(base_url=self.base_url,link=url) and type(url)==str and url is not None or is_file(url):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
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
            raise(MaxErrorReached(all_err_url,self.company_id))

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
        return min(100,193)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_xpath="/html/body//div[@class='content_right_content full-width']/div/nav[@class='pagination_wrap']/ul[@class='pagination']/li/a[text()='下一页']"
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
            driver2=webdriver.Chrome(service=Service(options=chrome_options))
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
            if is_internal_link(base_url=self.base_url,link=url) and type(url)==str and url is not None or is_file(url):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
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
            raise(MaxErrorReached(all_err_url,self.company_id))

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
                more_button=wait.until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[@class='news-view  month-select']/div[@class='content']/p[@class='text-center hide-btn scroll-load']/button[@class='button-red button load_more_post_ajax']")))
                driver.execute_script('arguments[0].click();', more_button)
                is_more=True
                time.sleep(3)                
                return True
            except TimeoutException: 
                is_more=False
                return False
        
    def get_total_page(self,driver:WebDriver)->int:
        return min(100,)
        
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
            driver2=webdriver.Chrome(service=Service(options=chrome_options))
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
        if target_ele==0 or target_ele==None:
            driver2.quit()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.quit()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            rows_xpath="/html/body//div[@class='content']/ul[@class='post-list container']/li"
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
                url=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,title_xpath))).text
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
            if is_internal_link(base_url=self.base_url,link=url) and type(url)==str and url is not None or is_file(url):
                urls.append(url)
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
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
            years_list=[2023,2022,2021]
            for year_ in years_list: 
                
                all_doc:list[Document]=[]
                current_year=self.get_current_year(driver)
                while current_year > year_: 
                    self.get_previous_year(driver)
                    current_year=self.get_current_year(driver)
                
                self.is_more(driver)                          
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