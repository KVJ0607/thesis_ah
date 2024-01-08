import re
import time
import math
import requests

from bs4 import BeautifulSoup
import urllib.request
import ssl
import certifi

# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
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
from utils.exception import MaxErrorReached
from utils.crawling import PressRelease,is_file,from_tuple_retri,from_tuple_read,extract_normal_link,is_internal_link,extract_iso_date,is_iso_date,text_from_html,convert_to_iso_from_full_eng_or_abv_eng
from company.company import *
from article.mining import _extracting_an_document        

from selenium_proxy_authentication.extension import proxies,USERNAME,PASSWORD,ENDPOINT,PORT
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
 
ERROR_COUNT = 20
CONVERTION_RATE=0.7 #~70% hit rate
FLAT_MAX_PAGE=100

class Cp_30(PressRelease):
    def __init__(self):
        base_url="https://www.andre.com.cn/"
        press_release_url="https://www.andre.com.cn/index.php?m=content&c=index&a=lists&catid=14"
        h_code="02218.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__success_count=0
        self.__robots_txt='https://www.andre.com.cn/robots.txt'

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
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[@class='page-main main']/div/div/div[@class='pm-r']/div[@class='pages Ybox']//a[contains(text(),'下一页')]")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str,is_proxy)->dict[str,str|None]:
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
            target_ele=WebDriverWait(driver2,30).until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[4]/div/div/div[2]/div[2]/div"))).text
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.close()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=total_txt+target_ele
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            print(f'error in retrieve_content, content is empty, {url}')
            driver2.close()
            return from_tuple_retri(target_ele,url,date_in_iso=date_ele) 
        driver2.close()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)
        

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,40)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[@class='page-main main']/div/div/div[@class='pm-r']/ul[@class='list-new']")))
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
                url_ele=row_.find_element(By.XPATH,"./div[2]/h1/a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                month_in_iso=row_.find_element(By.XPATH,"./div[1]/div[@class='month']").text.replace('年','-').replace('月','')
                day_in_iso=row_.find_element(By.XPATH,"./div[1]/div[@class='day']").text.replace('日','')                                
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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_30.retrieve_content)(url) for url in urls)
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
            driver.close()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))

class Cp_31(PressRelease):
    def __init__(self):
        base_url="https://www.smics.com/en/site/news"
        press_release_url="https://www.smics.com/en/site/news"
        h_code="00981.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__robots_txt="https://www.smics.com/robots.txt"

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

    def click_more(self,driver:WebDriver,is_return=True)->list[str]: 
        count_=0 
        wait = WebDriverWait(driver,15)
        while count_<20: 
            try: 
                tar_xpath="//a[normalize-space()='Click for more']"
                page_div=wait.until(EC.element_to_be_clickable((By.XPATH,tar_xpath)))
                driver.execute_script('arguments[0].click();', page_div)
                count_+=1
            except: 
                break 
        if is_return:
            target_xpath="//div[@class='news_left']/ul/li"
            rows=wait.until(EC.presence_of_all_elements_located((By.XPATH,target_xpath)))
            result_list=[]
            for row_index in range(len(rows)): 
                row_xpath=target_xpath+f"[{row_index+1}]/a"            
                row_str=wait.until(EC.visibility_of_element_located((By.XPATH,row_xpath))).text.strip()
                result_list.append(row_str)
            return result_list
    
    def get_year(self,driver:WebDriver,year_:str):
        wait = WebDriverWait(driver,15)
        self.click_more(driver,False)
        target_xpath="//div[@class='news_left']/ul/li/a[contains(text(),'{}')]".format(year_)
        button=wait.until(EC.visibility_of_element_located((By.XPATH,target_xpath)))
        driver.execute_script('arguments[0].click();', button)
        
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='content']"))).text
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
            rows_xpath="//div[@class='news_right']/table/tbody/tr"
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
                url_ele_xpath=row_xpath+"/td[2]/p/a"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/td[1]/p"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_string=convert_to_iso_from_full_eng_or_abv_eng(date_in_string)
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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_31.retrieve_content)(url,is_proxy) for url in urls)
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
            all_years_in_str=self.click_more(driver)
            for year_ in all_years_in_str: 
                self.get_year(driver,year_)
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

class Cp_32(PressRelease):
    def __init__(self):
        base_url="https://www.gac.com.cn/cn/"
        press_release_url="https://www.gac.com.cn/cn/invest/notice?type=1"
        h_code="02238.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
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
        return min(FLAT_MAX_PAGE,24)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[@id='__nuxt']/div[@id='__layout']/div/div[@class='fullPage']/div[@class='infoBox']/div[@class='content']/div/div[@class='mixPagination']/div[@class='fullPage page-butt']/div/button[@class='btn-next']")))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(url:str,is_proxy)->dict[str,str|None]:
        date_ele=None
        total_txt=""
        if url is None:
            print("url is None")
            return from_tuple_retri(None,url,date_in_iso=date_ele)
        isfile=is_file(url)
        print(f'is this a file: {is_file}')
        if isfile:
            try:
                txt=_extracting_an_document(Document.from_url(url))
                print(f'downloaded the file: {url}')
                return from_tuple_retri(txt,"",date_in_iso=date_ele)
            except Exception as e:
                print(f'error in retrieve_content {url}')
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        url_list:list[str]=[]
        chrome_options=Options()
        # if PROXY is not None:
        #     chrome_options.add_extension(extension_path)
        #     chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
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
                driver2.close()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.close()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.close()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[@id='__nuxt']/div[@id='__layout']/div/div[@class='fullPage']/div[@class='infoBox']/div[@class='content']/div/div[2]/ul/li[1]")))
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
                url_ele=row_.find_element(By.XPATH,"./a[1]")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,"./p[@class='date']").text.replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').strip())
                #print(title,date_in_iso,'\n',url)
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_32.retrieve_content)(url) for url in urls)
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
                #document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        # if PROXY is not None:
        #     chrome_options.add_argument(f'--proxy-server=http://{PROXY}')
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--headless')
        try:
            all_err_url:list[str]=[]
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
            driver.close()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
        
class Cp_33(PressRelease):
    def __init__(self):
        base_url="https://asia.tools.euroland.com/"
        press_release_url="https://asia.tools.euroland.com/tools/pressreleases/?companycode=cn-9bm&lang=zh-cn"
        h_code="02009.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
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
        wait = WebDriverWait(driver,25)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[@id='Main']/div[@id='PageFlickContainer']/div[@id='PagesContainer']/table[@class='Pages']/tbody/tr/td[3]/a")))
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
        #if PROXY is not None:
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
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
                    driver2.close()
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
                driver2.close()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.close()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.close()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            target_ele=wait.until(EC.presence_of_element_located((By.XPATH,"/html/body/div[@id='Main']/div[@id='PageFlickContainer']/div[@id='PressReleases']")))
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
            time.sleep(4)                       
            try:                                  
                url_ele=row_.find_element(By.XPATH,"./div[1]/div/div[2]/div/a/img")
                url=url_ele.get_attribute('src')
                title=row_.find_element(By.XPATH,"./div[1]/div/a").text                
                date_ele=row_.find_element(By.XPATH,".//span[@class='PressRelease-NewsDate']").text            
                
                date_in_iso=extract_iso_date(date_ele.replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').strip())
                print(f'url:{url}')
                print(f'title:{title},date:{date_in_iso}')
        
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
                if driver.current_url not in err_urls:
                    err_urls.append(driver.current_url)
                if self.error_count<ERROR_COUNT or self.success_count*CONVERTION_RATE>self.__error_count:
                    self.add_error_count()                    
                    continue
                else:
                    raise(MaxErrorReached())
            if is_internal_link(base_url=self.base_url,link=url) and url is not None and url !='':
                urls.append(url)
                
            else:
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_33.retrieve_content)(url) for url in urls)
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
                #document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None:
            #chrome_options.add_argument(f'--proxy-server=http://{PROXY}')
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--hedless')
        try:
            all_err_url:list[str]=[]
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
                        raise(e)
            time.sleep(0.5)
            wait = WebDriverWait(driver,25)
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
            driver.close()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
        
class Cp_34(PressRelease):
    def __init__(self):
        base_url="http://comec.cssc.net.cn"
        press_release_url="http://comec.cssc.net.cn/component_news/index.php"
        h_code="00317.HK".lower()
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
        page_xpath="//a[contains(text(),'后页')]"
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//body[1]/div[1]/table[1]/tbody[1]/tr[1]/td[1]/div[1]/table[2]/tbody[1]/tr[1]/td[2]/table[1]/tbody[1]/tr[4]/td[1]/table[1]/tbody[1]/tr[1]/td[1]/div[1]/table[1]/tbody[1]/tr[6]/td[1]/div[1]/table[1]/tbody[1]/tr[1]/td[1]"))).text
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
            rows_xpath="//div[@id='result']/table/tbody/tr"
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
                url_ele_xpath=row_xpath+"/td[1]//a"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/td[2]"

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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_34.retrieve_content)(url,is_proxy) for url in urls)
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

class Cp_35(PressRelease):
    def __init__(self):
        base_url="https://www.shanghai-electric.com/"
        press_release_url="https://www.shanghai-electric.com/listed/xwzx/rdzx/"
        h_code="02727.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
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
        return min(FLAT_MAX_PAGE,110)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//*[@id='content']/div/div/nav/div/ul/li[@class='page_next']//a")))
        #div[@class='news-list news-list-hotinfo']/ul
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
        #if PROXY is not None:
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
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
                    driver2.close()
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[@id='content']/div/div/div[@class='news-detail clearfix']"))).text
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.close()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.close()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.close()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='content']/div/div/div[contains(@class,'news-list') and contains (@class,'news-list-hotinfo')]/ul")))
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
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,"./span[@class='badge']").text.replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').strip())
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_35.retrieve_content)(url) for url in urls)
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
                #document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None:
            #chrome_options.add_argument(f'--proxy-server=http://{PROXY}')
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--hedless')
        try:
            all_err_url:list[str]=[]
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
            driver.close()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
        
class Cp_36(PressRelease):
    def __init__(self):
        base_url="https://www.3healthcare.com/"
        press_release_url="https://www.3healthcare.com/news.html"
        h_code="06826.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
        self.__robots_txt='https://www.3healthcare.com/robots.txt'
        self.start_xpath="/html/body//div[@id='about']/div/div/div"
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
        return min(FLAT_MAX_PAGE,7)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,20)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body//div[@id='about']//div[@class='pager']/a[contains(text(),'下一页')]")))
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
        #if PROXY is not None:
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
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
                    driver2.close()
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"/html/body//div[@id='about']//div[@class='main_col']//div[@class='about_content_news']"))).text
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.close()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.close()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.close()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body//div[@id='about']//div[@class='about_content']//div[@class='news-show']/ul")))
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
                url_ele=row_.find_element(By.XPATH,"./span[1]/a")
                url=url_ele.get_attribute('href')
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,"./span[2]").text.replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').strip())
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_36.retrieve_content)(url) for url in urls)
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
                #document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None:
            #chrome_options.add_argument(f'--proxy-server=http://{PROXY}')
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--hedless')
        try:
            all_err_url:list[str]=[]
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
            driver.close()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
        
class Cp_37(PressRelease):
    def __init__(self):
        base_url="https://www.beijingns.com.cn"
        press_release_url="https://www.beijingns.com.cn/news/"
        h_code="00588.hk".lower()
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
        return 70

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
        #url_list:list[str]=[]
        #chrome_options=Options()
        #chrome_options.add_argument('--headless')
        #chrome_options.add_argument("--enable-javascript")
        # if is_proxy:
        #     proxies_extension=proxies(USERNAME,PASSWORD,ENDPOINT,PORT)
        #     chrome_options.add_extension(proxies_extension)
        #     driver2=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        # else:
        #     driver2=webdriver.Chrome(options=chrome_options)
        # driver2.set_page_load_timeout(30)
        # try:
        #     driver2.get(url)
        # except WebDriverException as e:
            # print(f'error: receive_content function cannot connect to {url}')
        try:
            context=ssl.create_default_context(cafile=certifi.where())
                # try:
            html=urllib.request.urlopen(url,context=context).read()
            target_ele=text_from_html(html)
            # txt_length=len(target_ele)
            # start_index=int(txt_length/2)
            # print('With bs4, content has length{} \n {}'.format(txt_length,target_ele[start_index:start_index+35]))
            return from_tuple_retri(target_ele,'',date_in_iso=date_ele)
        except: 
            return from_tuple_retri("",url,date_in_iso=date_ele)
            # except Exception:
            #     return from_tuple_retri(None,url,date_in_iso='')
        # try:
        #     target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='edit_con_original edit-con-original']"))).text
        #     #date_ele=extract_iso_date(WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,""))).text.replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-'),strip()
        # except Exception:
        #     try:
        #         target_ele=driver2.find_element(By.TAG_NAME,'body').text
        #     except:
        #         print(f'error in retrieve_content: {driver2.current_url}')
        #         driver2.quit()
        #         return from_tuple_retri(None,url,date_in_iso=date_ele)
        # target_ele=target_ele+total_txt
        # if target_ele==0 or target_ele==None:
        #     driver2.quit()
        #     print(f'error in retrieve_content, content is empty, {url}')
        #     from_tuple_retri("",url)
        # driver2.quit()
        #return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            rows_xpath="//div[@class='news_cont']//ul/li"
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
                url_ele_xpath=row_xpath+"/div/h3/a"
                #title_ele_xpath=row_xpath+"/"
                date_xpath=row_xpath+"/div/div[1]"

                #scroll to row 
                #row_ele=wait.until(EC.presence_of_element_located((By.XPATH,row_xpath)))
                #driver_action=ActionChains(driver)
                #driver_action.scroll_to_element(row_ele).perform()

                #other row elements
                url=wait.until(EC.presence_of_element_located((By.XPATH,url_ele_xpath))).get_attribute('href')
                title=wait.until(EC.visibility_of_element_located((By.XPATH,url_ele_xpath))).text
                date_in_string=wait.until(EC.visibility_of_element_located((By.XPATH,date_xpath))).text
                date_in_iso=extract_iso_date(date_in_string.replace(' ','').replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-').strip())
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
        content_list = Parallel(n_jobs=-1)(delayed(Cp_37.retrieve_content)(url,is_proxy) for url in urls)
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

                #start_index=int(content_len/2)
                #print(content_to_be_set[start_index:start_index+30])
                document_list[i].set_content(content_to_be_set)
                refined_document_list.append(document_list[i])
                self.add_success_count()
            elif is_url_valid and is_crawling_iso_date_valid:
                content_to_be_set=content_list[i]["content"]
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
            start_page=15
            current_page=start_page
            start_page_url="https://www.beijingns.com.cn/news/index_{}.html".format(start_page)
            driver.get(start_page_url)
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


class Cp_38(PressRelease):
    def __init__(self):
        base_url="https://www.ceec.net.cn"
        press_release_url="https://www.ceec.net.cn/col/col11023/index.html"
        h_code="03996.HK".lower()
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
        return 83 

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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='wz_article atcl-viedo']"))).text
            date_ele=extract_iso_date(WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//li[@class='fl time']"))).text.replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-').strip())
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
            rows_xpath="//div[@class='lucidity_pgContainer']//ul/li"
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
                url_ele_xpath=row_xpath+"/div[2]/p/a"
                #title_ele_xpath=row_xpath+"/"
                #date_xpath=row_xpath+"/div[1]"

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
                #print(date_in_iso)
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
                document_list.append(Document(url,title,None,self.press_release_url,None,None,self.company_id))
            else:
                print(f'This {url} is not an internal link')
                continue
        content_list = Parallel(n_jobs=-1)(delayed(Cp_38.retrieve_content)(url,is_proxy) for url in urls)
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
            start_page=5
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


class Cp_39(PressRelease):
    def __init__(self):
        base_url="https://www.dzug.cn/"
        press_release_url="https://www.dzug.cn/Article/235_1570,1600"
        h_code="01635.HK".lower()
        self.__error_count=0
        self.__success_count=0
        super().__init__(base_url,press_release_url,h_code)
        self.__error_count=0
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
        return min(FLAT_MAX_PAGE,16)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"html/body//div[@class='width1132']//div[@class='wordcontent']/div[@class='paging']/a[@class='next']")))
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
        #if PROXY is not None:
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
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
                    driver2.close()
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"html/body//div[@class='content']/div[2]"))).text
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.close()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.close()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.close()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "html/body//div[@class='bd']/dl[@class='listype1']")))
            rows=target_ele.find_elements(By.XPATH,'./dd')
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
                title=url_ele.text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,"./span").text.replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').strip())
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_39.retrieve_content)(url) for url in urls)
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
                #document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None:
            #chrome_options.add_argument(f'--proxy-server=http://{PROXY}')
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--hedless')
        try:
            all_err_url:list[str]=[]
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
            driver.close()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))
        
class Cp_40(PressRelease):
    def __init__(self):
        base_url="https://www.goldwind.com/"
        press_release_url="https://www.goldwind.com/cn/news/focus/"
        h_code="02208.HK".lower()
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
        return min(FLAT_MAX_PAGE,3)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver,15)
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[normalize-space(text())='下一页']")))
        #page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(text(),'下一页')]")))
        page_div=wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body//a[normalize-space()='>']")))
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
        #if PROXY is not None:
            #chrome_options.add_extension(extension_path)
            #chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--enable-javascript")
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
                    driver2.close()
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
            target_ele=WebDriverWait(driver2,15).until(EC.visibility_of_element_located((By.XPATH,"//body/div[@id='__nuxt']/div[@id='__layout']/div/div[2]/div[2]"))).text
        except Exception:
            try:
                target_ele=driver2.find_element(By.TAG_NAME,'body').text
            except:
                print(f'error in retrieve_content: {driver2.current_url}')
                driver2.close()
                return from_tuple_retri(None,url,date_in_iso=date_ele)
        target_ele=target_ele+total_txt
        if target_ele==0 or target_ele==None:
            driver2.close()
            print(f'error in retrieve_content, content is empty, {url}')
            from_tuple_retri("",url)
        driver2.close()
        return from_tuple_retri(target_ele,"",date_in_iso=date_ele)

    def read_page(self,driver:WebDriver,is_proxy)->tuple[list[Document],list[str]]:
        wait = WebDriverWait(driver,15)
        try:
            target_ele = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body//div[@id='list']/div[@class='news']/ul")))
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
                url_ele=row_.find_element(By.XPATH,"./div/a")
                url=url_ele.get_attribute('href')
                title=row_.find_element(By.XPATH,"./div/h3").text
                date_in_iso=extract_iso_date(row_.find_element(By.XPATH,"./div/label").text.replace('"','').replace('年','-').replace('月','-').replace('日','').replace('.','-').strip())
            except Exception as e:
                print(f'problem with crawling rows element in this page: {driver.current_url}')
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
                print(f'This {url} is not an internal link')
                continue
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_40.retrieve_content)(url) for url in urls)
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
                #document_list[i].set_published_at(content_list[i]["date_in_iso"])
                refined_document_list.append(document_list[i])
                self.add_success_count()
        return from_tuple_read(doc_list=document_list,err_url_list=err_urls)

    def crawling(self,is_proxy=False)->tuple[list[Document],str]:
        chrome_options=Options()
        #if PROXY is not None:
            #chrome_options.add_argument(f'--proxy-server=http://{PROXY}')
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument('--hedless')
        try:
            all_err_url:list[str]=[]
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
            driver.close()
            return all_doc,self.company_id
        except MaxErrorReached as e:
            raise(MaxErrorReached(all_err_url,self.company_id))