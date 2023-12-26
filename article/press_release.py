import re 
import time 

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException,StaleElementReferenceException,ElementClickInterceptedException,NoSuchElementException, TimeoutException,WebDriverException,InvalidArgumentException
from selenium.webdriver.common.keys import Keys


from joblib import Parallel, delayed

from bs4 import BeautifulSoup
from datetime import datetime

from crawling import PressRelease,driver_connect
from company.company import *
from article.mining import _extracting_an_document
class Cp_1(PressRelease): 
    def __init__(self):
        base_url='https://www.ftol.com.cn/'
        press_release_url='https://www.ftol.com.cn/main/yfzx/cjxw/cjyw/index.shtml'
        h_code='03678.hk'
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None
    
    @staticmethod
    def retrieve_content(press_release_url:str,url:str): 
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver2 = webdriver.Chrome(options=chrome_options)
        
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("invalidArguement ",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body div.Research_center_box div.early_box').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
        return target_ele
        
    
    def read_page(self,driver) -> list[Document]: 
        # Wait up to 10 seconds for the elements to become available
        re_three_element = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.nr > div.Re_three > ul'))
        )
        time.sleep(0.1)
        rows_element= re_three_element.find_elements(By.TAG_NAME,'li')
        document_list:list[Document]=[]          
        urls:list[str]=[]    
        for row in rows_element:
            span_element = row.find_element(By.TAG_NAME, 'span')
            date_in_iso=span_element.text            
            a_element = row.find_element(By.TAG_NAME, 'a')            
            href_value = a_element.get_attribute('href')
            urls.append(href_value)
            title=a_element.text
            document_list.append(Document(href_value,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_1.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            document_list[i].set_content(content_list[i])
        
        return document_list

    def get_current_page(self,driver:WebDriver)->int:
        current_page = driver.find_element(By.CSS_SELECTOR, 'div.Re_four > div.page_footer > a.fy').text
        return int(current_page)
    
    def get_total_page(self,driver:WebDriver)->int:
        #tot_page=driver.find_element(By.CSS_SELECTOR,'div.Re_four  div.page_footer  span#pageCount').text
        tot_page= driver.find_element(By.CSS_SELECTOR, '#pageCount').text
        return int(tot_page)
    
    def next_page(self,driver:WebDriver)->None:
        button=WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#next_page')))
        driver.execute_script("arguments[0].click();", button)
    
    def crawling(self)->list[Document]:
        #chrome_options = Options()
        #chrome_options.add_argument("--headless")        
        #driver = webdriver.Chrome(options=chrome_options)
        driver = webdriver.Chrome()
        max_attempts=5
        attempts=0
        while attempts<max_attempts: 
            try:
                driver.get(self.press_release_url)
                break
            except WebDriverException as e:
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
                
        #all rows under
        """
        <div class="nr">
			<div class="Re_three"></div>
			<div class="Re_four"></div>
		</div>
        """
        
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)

        all_doc:list[Document]=[]
        while current_page<=total_page: 
            page_doc=self.read_page(driver)
            all_doc=all_doc+page_doc
            if current_page<total_page:
                self.next_page(driver)
            current_page=current_page+1 
        driver.quit()
        return all_doc

class Cp_2(PressRelease):
    def __init__(self):
        base_url='http://www.zjshibao.com/tc/index.html'
        press_release_url='http://www.zjshibao.com/tc/tc_news/list-44.html'
        h_code='01057.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def retrieve_content(press_release_url:str,url:str): 
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver2 = webdriver.Chrome(options=chrome_options)        
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Arguement",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'#mm-0>div.nybody_box').text
        except NoSuchElementException:
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
        
        return target_ele
    
    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 1

    def read_page(self,driver:WebDriver)->list[Document]:
        ul_ele=driver.find_element(By.CSS_SELECTOR,'#mm-0>div.nybody_box>div.wrap>div.nybox_box>div.nybox_right>ul.nynews_box')
        li_ele=ul_ele.find_elements(By.CSS_SELECTOR,'li')
        document_list:list[Document]=[]
        urls:list[str]=[]
        for li_ in li_ele: 
            date_element = li_.find_element(By.CSS_SELECTOR, "div.time")
            date_in_iso = date_element.text
            
            title_element = li_.find_element(By.CSS_SELECTOR, "div.name.ovh")
            title = title_element.text
            
            a_element = li_.find_element(By.TAG_NAME, "a")
            url = a_element.get_attribute('href')
            urls.append(url)
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_2.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            document_list[i].set_content(content_list[i])
        return document_list    
            
    def next_page(self,driver:WebDriver)->None:
        pass

    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(driver)
                time.sleep(0.1)
            
            current_page=current_page+1
        driver.quit()
        return all_doc

class Cp_3(PressRelease):
    def __init__(self):
        base_url='https://www.jingchenggf.cn/'
        press_release_url='https://btic.cn/news-246.html'
        h_code='00187.hk'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        #class current
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body>div.wrap>div.page.flex>a.current'))).text
        return int(target_ele)
    
    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        page_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body>div.wrap>div.page.flex')))
        a_tags = page_div.find_elements(By.TAG_NAME, 'a')
        target_ele = a_tags[-2].text
        return int(target_ele)
    
    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.wrap').text
        except NoSuchElementException:
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
        
        return target_ele
        
    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body>div.wrap>ul.support_list')))
        rows=target_ele.find_elements(By.CSS_SELECTOR,'li')
        document_list:list[Document]=[]
        urls=[]
        for row_ in rows:
            a_tag = row_.find_element(By.TAG_NAME, 'a')
            date_in_iso = a_tag.find_element(By.TAG_NAME, 'span').text  
            url = a_tag.get_attribute('href')  
            title = a_tag.text.replace(date_in_iso, '').strip()
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_3.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            document_list[i].set_content(content_list[i])
        return document_list        
        
    
    

    def next_page(self,driver:WebDriver)->None:
        time.sleep(2)
        button=driver.find_elements(By.CSS_SELECTOR,'body>div.wrap>div.page.flex a')[-1]
        driver.execute_script("arguments[0].click();", button)

    def crawling(self)->list[Document]:
        # chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=1
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(driver)
                time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
            

class Cp_4(PressRelease):
    def __init__(self):
        base_url='http://www.fd-zj.com/'
        press_release_url='http://www.fd-zj.com/desktopmodules/ht/Big5/News/Index.aspx?LS=1'
        h_code='01349.hk'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    ##body>table>tbody>tr>td>table
    def get_current_page(self,driver:WebDriver)->int:
        return 1
        

    def get_total_page(self,driver:WebDriver)->int:
        return 6

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.XPATH,'/html/body/table/tbody/tr/td/table[2]/tbody/tr/td[1]/table/tbody/tr/td[2]/table/tbody/tr[3]/td[2]').text
        except NoSuchElementException:
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
        return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body>table>tbody>tr>td')))
        target_ele=target_ele.find_elements(By.TAG_NAME,'table')[1]
        target_ele=target_ele.find_element(By.CSS_SELECTOR,'tbody>tr').find_elements(By.TAG_NAME,'td')[1].find_element(By.CSS_SELECTOR,'table>tbody').find_elements(By.TAG_NAME,'tr')[1]
        target_ele=target_ele.find_elements(By.TAG_NAME,'td')[2]
        rows=target_ele.find_elements(By.CSS_SELECTOR,'li')
        document_list:list[Document]=[]
        urls=[]
        for row_ in rows:
            html_content = row_.get_attribute('outerHTML')
            # Parse the HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find the <a> tag
            a_tag = soup.find('a')

            # Extract the href attribute for the URL
            url = a_tag['href']

            # Make sure to create the absolute URL if the href is relative
            # This step assumes you know the base URL, which is typically the URL of the page
            # without the specific path. Here I'm using 'http://example.com' as a placeholder.
            base_url = 'http://example.com'
            full_url = base_url + url

            # Extract the title and date from the text
            # Assuming the date is always in yyyy-mm-dd format and at the end of the string
            text = a_tag.get_text(strip=True)
            date_str = text[-10:]
            title = text[:-10].strip()  # Remove the date from the end and any extra whitespace

            # Convert the date to ISO format (it already is in this case, but this is how you would do it)
            date_in_iso = datetime.strptime(date_str, '%Y-%m-%d').date().isoformat()

            document_list.append(Document(full_url,title,date_in_iso,self.press_release_url,None,self.company_id))
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_4.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            document_list[i].set_content(content_list[i])
        return document_list    
    

    def next_page(self,current_page:int,driver:WebDriver)->None:
        time.sleep(2)
        target_ele=driver.find_element(By.CSS_SELECTOR,'body > table > tbody > tr > td > table:nth-child(5) > tbody > tr > td:nth-child(2) > table > tbody > tr:nth-child(2) > td.word > table > tbody > tr > td')      
        next_page_link = target_ele.find_element(By.XPATH, f".//a[contains(@href, '{current_page + 1}')]")
        driver.execute_script("arguments[0].click();", next_page_link)


    def crawling(self)->list[Document]:
        # chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc

class Cp_5(PressRelease):
    def __init__(self):
        base_url='https://www.shandongxinhuapharma.com/'
        press_release_url='https://www.shandongxinhuapharma.com/'
        h_code='00719.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def crawling(self)->list[Document]:
        return []
    
class Cp_6(PressRelease):
    def __init__(self):
        base_url='https://www.panda.cn/'
        press_release_url='https://www.panda.cn/qyxw/list_31.aspx'
        h_code='00553.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 112

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.XPATH,'/html/body/div[4]/div/div[2]/div[2]').text
        except NoSuchElementException:
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
        
        return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.XPATH,'/html/body/div[4]/div/div[2]/div[2]/ul')))  
        rows=target_ele.find_elements(By.TAG_NAME,'li')

        document_list:list[Document]=[]
        urls=[]
        for row_ in rows:
            title=row_.find_element(By.CSS_SELECTOR,'div.LiRight>h4>a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'div.LiRight>h4>span').text
            date_in_iso='20'+date_in_iso
            url=row_.find_element(By.CSS_SELECTOR,'div.LiRight>h4>a').get_attribute('href')
            urls.append(url)
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        
        
        content_list = Parallel(n_jobs=-1)(delayed(Cp_6.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            document_list[i].set_content(content_list[i])
        return document_list    
            

    def next_page(self,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        button=wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[4]/div/div[2]/div[2]/div/a[8]')))
        driver.execute_script("arguments[0].click();", button)
        

    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc

class Cp_7(PressRelease):
    def __init__(self):
        base_url='https://www.group.citic/'
        press_release_url='https://www.group.citic/html/medias/media_news/'
        h_code='06066.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robots.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div[4]/div/div/div/div/ul')))
        current_page=target_ele.find_element(By.CSS_SELECTOR,'li.on.fl>a').text
        return int(current_page)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div[4]/div/div/div/div/ul')))
        tot_page=target_ele.find_elements(By.TAG_NAME,'li')[-4].text
        return int(tot_page)

    @staticmethod
    def retrieve_content(url:str)->tuple[str,str]:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        with webdriver.Chrome(options=chrome_options) as driver:
            try:
                driver_connect(driver,url)
                target_ele=driver.find_element(By.CSS_SELECTOR,'#wrapper > div.media_center.content-wrap > div').text
                date_in_iso=driver.find_element(By.CSS_SELECTOR,'#wrapper > div.media_center.content-wrap > div > div > p').text
                return date_in_iso, target_ele
            except Exception as e:
                print(f"Error retrieving content from {url}: {e}")
                return '',''
                

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#wrapper > div.zxparty_news.media-news-list > div > div > div > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        document_list:list[Document]=[]
        urls=[]
        for row_ in rows:
            time.sleep(0.2)
            url=row_.find_element(By.CSS_SELECTOR,'div.con>div.title>a').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'div.con>div.title>a').get_attribute('title')
            urls.append(url)
            document_list.append(Document(url,title,None,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_7.retrieve_content)(url) for url in urls)
        for i in range(len(content_list)): 
            document_list[i].set_content(content_list[i][1])
            document_list[i].set_published_at(content_list[i][0])
        return document_list    

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#input')))
        page_input.clear()
        page_input.send_keys(str(cur_page + 1) + Keys.ENTER)
        page_div = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#wrapper > div.zxparty_news.media-news-list > div > div > div > div > ul > li.fl.pageB > input[type=button]')))
        driver.execute_script("arguments[0].click();", page_div)

    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=11
        current_page=1
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc

class Cp_8(PressRelease):
    def __init__(self):
        base_url='https://www.ccnew.com.hk/'
        press_release_url='https://www.ccnew.com.hk/tc/company/cctrend'
        h_code='01375.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#pager > ul'))).find_element(By.CSS_SELECTOR,'a.current').text
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#pager > ul'))).find_elements(By.TAG_NAME,'li')[-2].text
        return int(target_ele)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'#asset > div.left > div.movement').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
        return target_ele
        

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#aboutcc > div.left > div.aboutccin > table > tbody')))
        rows=target_ele.find_elements(By.TAG_NAME,'tr')
        document_list:list[Document]=[]
        urls=[]
        for row_ in rows:
            date_in_iso=row_.find_element(By.TAG_NAME,'td').text
            url=row_.find_element(By.CSS_SELECTOR, "td:nth-child(2)>a").get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR, "td:nth-child(2)>a").text
            urls.append(url)
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        
        content_list = Parallel(n_jobs=-1)(delayed(Cp_8.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            document_list[i].set_content(content_list[i])
        return document_list    

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#pager > ul'))).find_element(By.CSS_SELECTOR,'li.next > a')
        driver.execute_script("arguments[0].click();", target_ele)

    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=5
        current_page=1
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
        
class Cp_9(PressRelease):
    
    def __init__(self):
        base_url='https://www.zhglb.com/'
        press_release_url='https://www.zhglb.com/news/1/'
        h_code='01108.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=https://www.zhglb.com/robots.txt

            
        
    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#c_static_001-16886996617940 > div > div > div.e_loop-24.s_list.response-transition > div > div.p_page > div')))
        target_ele=target_ele.find_element(By.CSS_SELECTOR,'a.current').text
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#c_static_001-16886996617940 > div > div > div.e_loop-24.s_list.response-transition > div > div.p_page > div > a:nth-child(7)'))).text
        return int(target_ele)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#c_static_001-16886996617940 > div > div > div.e_loop-24.s_list.response-transition > div > div.p_page > div a.page_next')))
        driver.execute_script("arguments[0].click();", page_div)
        
        
    
    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return '',''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'#js_content > section:nth-child(1) > section > section').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
        return target_ele
        

    def read_page(self,driver:WebDriver,page:int)->list[Document]:
        wait = WebDriverWait(driver, 3)    
                      ##c_static_001-16886996617940 > div > div > div.e_loop-24.s_list > div > div.p_list > div:nth-child(1) > div > div.cbox-25-1.p_item > p
                      ###c_static_001-16886996617940 > div > div > div.e_loop-24.s_list > div > div.p_list > div:nth-child(1) > div > div.cbox-25-1.p_item > p > a
                      ###c_static_001-16886996617940 > div > div > div.e_loop-24.s_list.response-transition > div > div.p_list > div:nth-child(1) > div > div.cbox-25-1.p_item > p > a
        css_selector='div.p_list'
        rows=wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
        rows=rows.find_elements(By.CSS_SELECTOR,'div')
        for row in rows: 
            print(row.get_attribute('outerHTML'))
        document_list:list[Document]=[]
        urls=[]
        for i in range(len(rows)): 
            time.sleep(3)
            
            try_element=driver.find_element(By.CSS_SELECTOR,f'div.p_list > div:nth-child{i+1}')
            print(f'try_element succuess:{i}')
            try_element2=driver.find_element(By.CSS_SELECTOR,f'div.p_list > div:nth-child{i+1} > div')
            print(f'try_element2 succuess:{i}')
            print(try_element2.get_attribute('outerHTML'))
            a_element=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,f'div.p_list > div:nth-child({i+1}) > div > div:nth-child(2)> p > a')))
            url = a_element.get_attribute('href')
            title = a_element.text
            date_in_iso=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,f'div.p_list > div:nth-child({i+1}) > div > div:nth-child(3)>p'))).text
            urls.append(url)
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_9.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            document_list[i].set_content(content_list[i])
        return document_list  

        


    def crawling(self)->list[Document]:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome(options=chrome_options)
        max_attempts=5
        attempts=0
        while attempts<max_attempts: 
            try:
                driver.get(self.press_release_url)
                break
            except WebDriverException as e:
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        total_page=23
        current_page=1
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver,current_page)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
        
class Cp_10(PressRelease):
    def __init__(self):
        base_url='http://ssc.sinopec.com/'
        press_release_url='http://ssc.sinopec.com/sosc/news/com_news/'
        h_code='01033.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#pagingIndex > span > b'))).text
        page=target_ele.split('/')[0]
        return int(page)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#pagingIndex > span > b'))).text
        page=target_ele.split('/')[1]
        return int(page)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#pager_p > a:nth-child(3)")))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'#DeltaPlaceHolderMain > div.container > div.lfnews-content').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
        return target_ele
        
        

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#ctl00_SPWebPartManager1_g_1fb3ae84_62ae_490e_b183_5811a82d92d7 > div.w_newslistpage_box > div > div.w_newslistpage_body > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        document_list:list[Document]=[]
        urls=[]
        for row_ in rows:
            title=row_.find_element(By.CSS_SELECTOR,'span.title>a').text
            url=row_.find_element(By.CSS_SELECTOR,'span.title>a').get_attribute('href')
            urls.append(url)
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'span.date>').text
            date_in_iso = date_in_iso.replace('年', '-').replace('月', '-').replace('日', '').split('-')
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_10.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            document_list[i].set_content(content_list[i])
        return document_list  


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=12
        current_page=1
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
        
class Cp_11(PressRelease):
    def __init__(self):
        base_url='https://www.fmsh.com/'
        press_release_url='https://www.cansinotech.com.cn/html/1//179/180/list-2.html'
        h_code='01385.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.inmain.clearfix > div > div.page')))
        target_ele=target_ele.find_element(By.CSS_SELECTOR,'a.cpb').text
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        last_page = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.inmain.clearfix > div > div.page > a:nth-child(12)'))).get_attribute('href')
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.get(last_page)
        target_ele=self.get_current_page(driver2)
        driver2.quit()
        return target_ele

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.inmain.clearfix > div > div.page > a:nth-child(11)')))
        driver.execute_script("arguments[0].click();", page_div)
        
    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.inmain.clearfix > div').text
        driver2.quit()
        return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#newslist')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        document_list:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('title')
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'span').text
            date_in_iso=date_in_iso.replace('.','-')
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_11.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            document_list[i].set_content(content_list[i])
        return document_list  


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc

class Cp_12(PressRelease):
    def __init__(self):
        base_url='https://www.dongjiang.com.cn/'
        press_release_url='https://www.dongjiang.com.cn/main/media/djxw/index.shtml'
        h_code='00895.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#newsPage > div.yema>div.yema-k'))).text
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#newsPage > div.yema>span:last-of-type > a:nth-of-type(2)'))).get_attribute('href')
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.get(target_ele)
        tot_page=self.get_current_page(driver2)
        driver2.quit()
        
        return tot_page

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#newsPage > div.yema > span:nth-child(8) > a:nth-child(1)')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''

        target_ele=driver2.find_element(By.CSS_SELECTOR,'#nr > div > table').text
        driver2.quit()
        return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#newsPage > div.news > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        document_list:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'span').text
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_12.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            document_list[i].set_content(content_list[i])
        return document_list  


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
        
class Cp_13(PressRelease):
    def __init__(self):
        base_url='https://www.cansinotech.com.cn/'
        press_release_url='https://www.cansinotech.com.cn/html/1//179/180/index.html'
        h_code='06185.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None
    def extract_number(text):
        # Use a regular expression to find numbers within parentheses
        matches = re.search(r'\((\d+)\)', text)
        if matches:
            # Return the first group of digits found
            return matches.group(1)
        else:
            # If no digits are found within parentheses, return None or raise an error
            return None
    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.main > div.ms-content-main-page > a.ms-content-main-page-current'))).text 
        cur_page=self.extract_number(target_ele)
        
        return int(cur_page)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.main > div.ms-content-main-page > a.ms-content-main-page-last'))).get_attribute('href')
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.get(target_ele)
        page_=self.get_current_page(driver2)
        driver2.quit()
        return page_

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.main > div.ms-content-main-page > a.ms-content-main-page-next')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try: 
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.main > div.News.animation1').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
        return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.main > div.Trends.animation1 > div > div > div.Tab-content.Tab-content_current > div > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        document_list:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'div.title > a').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'div.title > a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'div.date').text
            date_in_iso=date_in_iso.strip().strip('"').strip()
            document_list.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_13.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            document_list[i].set_content(content_list[i])
        return document_list  


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_14(PressRelease):
    def __init__(self):
        base_url='https://www.glsc.com.cn/'
        press_release_url='https://www.glsc.com.cn/subsite/ir/#/detail/announce/A/zh-CN'
        h_code='01456.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#app > div.app-container > div > div.detail-content > div.router-view-container > div > div.pagination-container > div > ul')))
        target_ele=target_ele.find_element(By.CSS_SELECTOR,'li.active')
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#app > div.app-container > div > div.detail-content > div.router-view-container > div > div.pagination-container > div > ul > li:nth-child(8)')))
        return int(target_ele)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#app > div.app-container > div > div.detail-content > div.router-view-container > div > div.pagination-container > div > button.btn-next')))
        driver.execute_script("arguments[0].click();", page_div)
        
    def retrieve_content(self,url:str,temp_doc:Document)->str:
        txt=_extracting_an_document(temp_doc)
        return txt 

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#app > div.app-container > div > div.detail-content > div.router-view-container > div > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        temp_doc_list=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'div>span.item-left-date').text.replace('.','-')
            temp_doc=Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id)
            temp_doc_list.append(temp_doc)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            
        content_list = Parallel(n_jobs=-1)(delayed(self.retrieve_content)(self.press_release_url,url) for url in temp_doc_list)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc  

    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
        
        
        
        
        
class Cp_15(PressRelease):
    def __init__(self):
        base_url='http://www.clypg.com.cn/'
        press_release_url='http://www.clypg.com.cn/lydlww/gsyw/list.shtml'
        h_code='00916.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None 

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 1

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        pass 

    def retrieve_content(press_release_url:str,url:str)->tuple[str,str]:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return '',''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return '',''

        try:
            date_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.wra.w1200 > div.fr.ml30.mt30.w900 > div > div > div > div.source > div.sdiv.fl > span > publishtime').text
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.wra.w1200 > div.fr.ml30.mt30.w900 > div > div').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
        return date_ele,target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.wra.w1200 > div.fr.ml30.mt30.w900 > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'p>a').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'p>b>a:nth-child(2)')
            tot_doc.append(Document(url,title,None,self.press_release_url,None,None,self.company_id))
        
        content_list = Parallel(n_jobs=-1)(delayed(Cp_15.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i][1])
            tot_doc[i].set_published_at(content_list[0])
        return tot_doc


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc

class Cp_16(PressRelease):
    def __init__(self):
        base_url='https://sh.yofc.com/'
        press_release_url='https://sh.yofc.com/list/220.html'
        h_code='06869.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.mm-page > div.inner_cont > div > div > div.list_newspic2page > div.page > a.on'))).text 
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.mm-page > div.inner_cont > div > div > div.list_newspic2page > div.page > a:nth-child(5)'))).text
        return int(target_ele)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.mm-page > div.inner_cont > div > div > div.list_newspic2page > div.page > a.next')))
        driver.execute_script("arguments[0].click();", page_div)

    def retrieve_content(press_release_url:str,url:str)->tuple[str,str]:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return '',''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return '',''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.mm-page > div.inner_cont > div > div > div.cont_infoleft > div > div.post_article').text
            date_in_iso=driver2.find_element(By.CSS_SELECTOR,'body > div.mm-page > div.inner_cont > div > div > div.cont_infoleft > div > div.post_article > div.article_header > div > ul > li.li1 > span').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
            date_in_iso=''
        finally:
            driver2.quit()
            return date_in_iso,target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.mm-page > div.inner_cont > div > div > div.list_newspic2page > div.list_newspic2')))
        rows=target_ele.find_elements(By.TAG_NAME,'dl')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'a>dt>div>h3').text            
            tot_doc.append(Document(url,title,self.press_release_url,None,self.company_id))
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_16.retrieve_content)(self.press_release_url,url) for url in urls) 
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i][1])
            tot_doc[i].set_published_at(content_list[i][0])
        return tot_doc 


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
        
class Cp_17(PressRelease):
    def __init__(self):
        base_url='https://www.e-chinalife.com/'
        press_release_url='https://www.e-chinalife.com/xwzx/'
        h_code='02628.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=

    # #secondPage_xwzx_132012_page
    # span.current linenum43
    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#secondPage_xwzx_132012_page>span.current'))).text
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        #wait = WebDriverWait(driver, 15)
        #target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'')))
        return 129

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#secondPage_xwzx_132012_page>a.nextpage')))
        driver.execute_script("arguments[0].click();", page_div)
        
    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div > div.mainpage > div > div.doubleR > div').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele


    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#secondPage_xwzx_132012 > div > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a.a_left').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'a_left').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'span.a_right').text
            content=self.retrieve_content(url)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,content,None,self.company_id))

        content_list = Parallel(n_jobs=-1)(delayed(Cp_17.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc

    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_18(PressRelease):
    def __init__(self):
        base_url='http://www.ebscn.com/'
        press_release_url='http://www.ebscn.com/inverstorRelations/dqgg/hggg/'
        h_code='06178.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#main_inverstorRelations_dqgg_hggg_index > div > div.content > div.con_detail > div > div.left_content.fl > div > div.pageBar > a.act')))
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        return 57

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#next_page')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def extract_iso_datetime(text):
        # Use regular expression to find the datetime pattern in the text
        match = re.search(r'时间：(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', text)
        if match:
            # Extract the matching group which contains the datetime string
            datetime_str = match.group(1)
            # Parse the datetime string into a datetime object
            datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            # Return the datetime in ISO 8601 format
            return datetime_obj.isoformat()
        else:
            # If no datetime pattern is found, return None or raise an error
            return None
        
    def retrieve_content(press_release_url:str,url:str)->tuple[str,str]:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return '',''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return '',''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.section > div > div.article_detail > div > div > div.left.fl.no_border > div.words')
            target_url=target_ele.find_element(By.CSS_SELECTOR,'a').get_attribute('href')

            date_in_iso=driver2.find_element(By.CSS_SELECTOR,'body > div.section > div > div.article_detail > div > div > div.left.fl.no_border > div.top > p').text
            date_in_iso=Cp_18.extract_iso_datetime(date_in_iso)
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return date_in_iso,target_ele
        

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#main_inverstorRelations_dqgg_hggg_index > div > div.content > div.con_detail > div > div.left_content.fl > div > div.bk_child > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        temp_doc_list=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'a').text
            date_in_iso,target_url=self.retrieve_content(url)
            temp_doc=Document(target_url,title,date_in_iso,self.press_release_url,None,None,self.company_id)
            temp_doc_list.append(temp_doc)
            content=_extracting_an_document(temp_doc)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,content,None,self.company_id))
            
        content_list = Parallel(n_jobs=-1)(delayed(_extracting_an_document)(doc) for doc in temp_doc_list)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc

    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_19(PressRelease):
    def __init__(self):
        base_url='https://www.suntien.com/'
        press_release_url='https://www.suntien.com/info.php?id=105&en=c'
        h_code='00956.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=https://www.suntien.com/robots.txt

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#right > div.nycontent.wow.fadeInRight.animated > div.small_nycontent > p > span >a.focus'))).text
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#right > div.nycontent.wow.fadeInRight.animated > div.small_nycontent > p > a:nth-child(4)'))).get_attribute('href')
        return self.get_current_page(target_ele)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#right > div.nycontent.wow.fadeInRight.animated > div.small_nycontent > p > a:nth-child(4)')))
        driver.execute_script("arguments[0].click();", page_div)
        
    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'').text
            
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#right > div.nycontent.wow.fadeInRight.animated > div.small_nycontent > div.nylisttt')))
        ##right > div.nycontent.wow.fadeInRight.animated > div.small_nycontent > div.nylisttt
        ##right > div.nycontent.wow.fadeInRight.animated > div.small_nycontent > div.nylisttt > li:nth-child(1) > div > span
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        temp_doc_list=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,' div > a.awz').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,' div > a.awz').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,' div > span').text
            date_in_iso=date_in_iso.replace('[','').replace(']','')
            temp_doc= Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id)
            temp_doc_list.append(temp_doc)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(self.retrieve_content)(self.press_release_url,url) for url in temp_doc_list)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
        
class Cp_20(PressRelease):
    def __init__(self):
        base_url='https://zlgj.chinalco.com.cn/'
        press_release_url='https://zlgj.chinalco.com.cn/xwzx/gsyw/'
        h_code='02068.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None 
    
    #body > div.content.container > div.conRight > p > span 
    #body > div.content.container > div.conRight > p > span
    #body > div.content.container > div.conRight > p > a:nth-child(11)
    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.content.container > div.conRight > p > span'))).text
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.content.container > div.conRight > p > a:nth-child(11)'))).get_attribute('href')
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.get(target_ele)
        page_=self.get_current_page(driver2)
        driver2.close()
        return page_

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.content.container > div.conRight > p > a:nth-child(10)')))
        driver.execute_script("arguments[0].click();", page_div)
        
    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.content.container').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele


    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.content.container > div.conRight > div > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'span.mhide').text
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            
        content_list = Parallel(n_jobs=-1)(delayed(Cp_20.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc

    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_21(PressRelease):
    def __init__(self):
        base_url='www.first-tractor.com.cn'
        press_release_url='http://www.first-tractor.com.cn/xwzx/gsxw/'
        h_code='00038.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.w1170.con.clearfix > div.sidebarR > div.serve_list > div')))
        target_ele=target_ele.find_element(By.XPATH,"//p[@style='color:#f00;']").text
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.w1170.con.clearfix > div.sidebarR > div.serve_list > div > p:nth-child(10) > a'))).text
        return int(target_ele)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.w1170.con.clearfix > div.sidebarR > div.serve_list > div > p:nth-child(11) > a')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.w1170.con.clearfix > div.sidebarR > div.compon_particulars.subcompon3').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.w1170.con.clearfix > div.sidebarR > div.serve_list > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'p').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'a').text
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_21.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc

    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
        
class Cp_22(PressRelease):
    def __init__(self):
        base_url='https://www.hepalink.com/'
        press_release_url='https://www.hepalink.com/News/index.aspx'
        h_code='09989.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None
        
    #body > div.Main-box.padd.clearfix.news-back > div > div.Page002623 > div > span > em
    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.Main-box.padd.clearfix.news-back > div > div.Page002623 > div > span > em > a.a_cur'))).text
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        return 10

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.Main-box.padd.clearfix.news-back > div > div.Page002623 > div > span > a.a_next')))
        driver.execute_script("arguments[0].click();", page_div)
        
    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.Main-box.padd.clearfix > div > div').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def convert_to_iso(date_str):
        # Split the string by the space to separate 'MM-DD' and 'YYYY'
        parts = date_str.split(' ')
        
        # Check if we have two parts and the first part contains the expected '-'
        if len(parts) == 2 and '-' in parts[0]:
            mm_dd, yyyy = parts[0], parts[1]
            # Construct the ISO date string
            iso_date = f"{yyyy}-{mm_dd}"
            return iso_date
        else:
            raise ValueError("Date string format is incorrect, expected 'MM-DD YYYY'")
        
    def read_page(self,driver:WebDriver)->list[Document]:
        WebDriverWait
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.Main-box.padd.clearfix.news-back > div > div.news-list.padd.clearfix > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'a>div>h2').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'a>div>time').text
            date_in_iso=self.convert_to_iso(date_in_iso)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_22.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc

    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
        

class Cp_23(PressRelease):
    def __init__(self):
        base_url='http://www.swhygh.com/'
        press_release_url='http://www.swhygh.com/zxzx/zxlist.jsp?classid=0001000200030001'
        h_code='06806.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    ##rewin_fenye > table > tbody > tr
    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#rewin_fenye > table > tbody > tr >')))
        target_ele=target_ele.find_element(By.XPATH,"//*[contains(@style, 'color:#C00') and contains(@style, 'font-weight:bold')]").text
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#rewin_fenye > table > tbody > tr > td:nth-child(8) > a'))).get_attribute('href')
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.get(target_ele)
        page=self.get_current_page(driver2)
        
        driver2.quit()
        
        return page

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#rewin_fenye > table > tbody > tr > td:nth-child(7) > a')))
        driver.execute_script("arguments[0].click();", page_div)
        
    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.information > div.m_2 > div.m_n').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#ul_list')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'a').text 
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'span').text
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_23.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_24(PressRelease):
    def __init__(self):
        base_url='https://www.china-galaxy.com.cn/#page1'
        press_release_url='https://www.china-galaxy.com.cn/index.php?m=content&c=index&a=lists&catid=14'
        h_code='06881.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.nybox.gynybox.aos-init.aos-animate > div.qydt-box.aos-init.aos-animate > div.ym.aos-init.aos-animate > p.on > a'))).text
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        return 4

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.nybox.gynybox.aos-init.aos-animate > div.qydt-box.aos-init.aos-animate > div.ym.aos-init.aos-animate > p:nth-child(6) > a')))
        driver.execute_script("arguments[0].click();", page_div)
        
    @staticmethod
    def to_iso_format(dt_str):
        # Assuming the irrelevant part is always two digits and a period at the end
        # Modify the slicing as necessary to accommodate different patterns
        clean_str = dt_str[:-3]

        # Parse the datetime string to a datetime object
        dt_obj = datetime.strptime(clean_str, "%Y-%m-%d %H:%M")

        # Convert the datetime object to an ISO 8601 formatted string
        iso_format = dt_obj.isoformat()

        return iso_format
    
    def retrieve_content(press_release_url:str,url:str)->tuple[str,str]:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return '',''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return '',''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.xwxq.aos-init.aos-animate').text
            date_in_iso=driver2.find_element(By.CSS_SELECTOR,'body > div.xwxq.aos-init.aos-animate > div.xwxq-top > p')
            date_in_iso=Cp_24.to_iso_format(date_in_iso)
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.nybox.gynybox.aos-init.aos-animate > div.qydt-box.aos-init.aos-animate > div.qydt-box-con')))
        rows=target_ele.find_elements(By.TAG_NAME,'div')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'a >h5').text
            tot_doc.append(Document(url,title,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_24.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i][1])
            tot_doc[i].set_published_at(content_list[i][0])
        return tot_doc


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_25(PressRelease):
    def __init__(self):
        base_url='https://www.gwm.com.cn/'
        press_release_url='https://www.gwm.com.cn/company.html'
        h_code='02333.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=https://www.gwm.com.cn/robots.txt

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#layui-laypage-1>span.layui-laypage-curr'))).text
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#layui-laypage-1 > a.layui-laypage-last'))).text
        return int(target_ele)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#layui-laypage-1 > a.layui-laypage-next')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.news_content').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > main > div.news_bottom_bg > div > div.news_list > div > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('data-title')
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('data-time')
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_25.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc   


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_26(PressRelease):
    def __init__(self):
        base_url='https://www.dynagreen.com.cn/'
        press_release_url='https://www.dynagreen.com.cn/newsList_19_page1.html'
        h_code='01330.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=https://www.dynagreen.com.cn/robots.txt

    #body > div.wrap-layer > div > div.in-right.in-right2 > div.page-wrap.ft18 > div
    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.wrap-layer > div > div.in-right.in-right2 > div.page-wrap.ft18 > div > ul > li.cr'))).text 
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.wrap-layer > div > div.in-right.in-right2 > div.page-wrap.ft18 > div > ul > li:nth-child(9)'))).get_attribute('href')
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.get(target_ele)
        page_=self.get_current_page(driver2)
        driver2.close()
        return page_

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.wrap-layer > div > div.in-right.in-right2 > div.page-wrap.ft18 > div > ul > li.next > a')))
        driver.execute_script("arguments[0].click();", page_div)

    def retrieve_content(press_release_url:str,url:str)->tuple[str,str]:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return '',''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return '',''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.wrap-layer > div > div.in-right.in-right2 > div.newsInfo').text
            date_=driver2.find_element(By.CSS_SELECTOR,'body > div.wrap-layer > div > div.in-right.in-right2 > div.newsInfo > div.source.ft16 > ul > li').text
            pattern = r'\d{4}-\d{2}-\d{2}'
            date_in_iso = re.search(pattern, date_).group()
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return date_in_iso,target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.wrap-layer > div > div.in-right.in-right2 > div.mod-news-5')))
        rows=target_ele.find_elements(By.TAG_NAME,'div')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('title')
            tot_doc.append(Document(url,title,None,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_26.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i][1])
            tot_doc[i].set_published_at(content_list[i][0])
        return tot_doc  


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_27(PressRelease):
    def __init__(self):
        base_url='http://spc.sinopec.com/'
        press_release_url='http://spc.sinopec.com/spc/news/news_report/'
        h_code='00338.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#pagingIndex > span > b'))).text
        target_ele=target_ele[0]
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#pagingIndex > span > b'))).text
        target_ele=target_ele[-1]
        return int(target_ele)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#pager_p > a:nth-child(3)')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'#DeltaPlaceHolderMain > div.container > div.lfnews-content').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#ctl00_SPWebPartManager1_g_9bcf6e15_e0de_4d64_8db9_15227dcb295e > div.w_newslistpage_box > div > div.w_newslistpage_body > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'span.date').text
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_27.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_28(PressRelease):
    def __init__(self):
        base_url='https://www.cicc.com/'
        press_release_url='https://www.cicc.com/news/list_104_311_1.html'
        h_code='03908.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#Pagination > div.jump > span'))).text
        target_ele=target_ele.split('/')[0]
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#Pagination > div.jump > span'))).text
        target_ele=target_ele.split('/')[1]
        return int(target_ele)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#Pagination > div.page > a.next')))
        driver.execute_script("arguments[0].click();", page_div)
        
    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.page-box.responsibility-page.charity-detail-page > div > div.main-content').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.page-box.news-page.news-list-page > div > div.main-content > div.ui-article-list')))
        rows=target_ele.find_elements(By.TAG_NAME,'div')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'p.time').text
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_28.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_29(PressRelease):
    def __init__(self):
        base_url='https://development.coscoshipping.com/'
        press_release_url='https://development.coscoshipping.com/col/col1555/index.html'
        h_code='02866.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#layui-laypage-1 > span.layui-laypage-curr'))).text
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#layui-laypage-1 > a.layui-laypage-last'))).get_attribute('data-page')
        return int(target_ele)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#layui-laypage-1 > a.layui-laypage-next')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'#c > tbody').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#文章正文 > div.page-content')))
        rows=target_ele.find_elements(By.TAG_NAME,'table')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            urls.append(url)
            title=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('title')
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'td.bt_time').text
            date_in_iso=date_in_iso.replace('[','').replace(']','')
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_29.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_30(PressRelease):
    def __init__(self):
        base_url='https://www.andre.com.cn/'
        press_release_url='https://www.andre.com.cn/index.php?m=content&c=index&a=lists&catid=14'
        h_code='02218.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=https://www.andre.com.cn/robots.txt

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 5

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.page-main.main > div > div > div.pm-r > div.pages.Ybox > ul > li:nth-child(7) > a')))
        driver.execute_script("arguments[0].click();", page_div)
        
    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.page-main.main > div > div > div.pm-r > div.Ybox.content.show > div > div.content-main').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.page-main.main > div > div > div.pm-r > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'a').text
            day=row_.find_element(By.CSS_SELECTOR,'div.day').text
            month=row_.find_element(By.CSS_SELECTOR,'month').text
            pattern=r'\b\d{1,2}[A-Za-z]+'
            day_ = re.search(pattern, day).group(0)
            month_=month[5:7]
            year_=month[0:4]
            date_in_iso=year_+'-'+month_+'-'+day_
            urls.append(url)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_30.retrieve_content)(self.press_release_url,url) for url in urls)    
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_31(PressRelease):
    def __init__(self):
        base_url='https://www.smics.com/'
        press_release_url='https://www.smics.com/tc/site/news'
        h_code='00981.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=https://www.smics.com/robots.txt

    ##neirong > div.container.clearfix > div.news_left
    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 1

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#neirong > div.container.clearfix > div.news_left > ul > li.load_more')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'#company_con > div.new_read.page_cell > div.container.clearfix > div.content').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#neirong > div.container.clearfix > div.news_left > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        urls=[]
        for index,row_ in enumerate(rows):
            if 'show' not in show_flag: 
                while 'show' not in show_flag: 
                    self.next_page(driver=driver)
                    row_=driver.find_element(By.CSS_SELECTOR,'#neirong > div.container.clearfix > div.news_left > ul').find_elements('li')[index]
                    show_flag=row_.get_attribute('class')
            show_flag=row_.get_attribute('class')
            row_.find_element('a')
            wait2=WebDriverWait(row_,10)
            page_div=wait2.until(EC.element_to_be_clickable((By.TAG_NAME, 'a')))
            driver.execute_script("arguments[0].click();", page_div)
            subrows=driver.find_element(By.CSS_SELECTOR,'#neirong > div.container.clearfix > div.news_right > table > tbody')
            subrows=subrows.find_elements(By.CSS_SELECTOR,'tr')
            for sub_row in subrows: 
                date_in_iso= sub_row.find_element(By.CSS_SELECTOR,'td.date').text
                title = sub_row.find_element(By.CSS_SELECTOR,'p.t').text 
                url = sub_row.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
                urls.append(url)
                tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_31.retrieve_content)(self.press_release_url,url) for url in urls)
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc
                    


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        all_doc=self.read_page(driver)
        driver.quit()
        return all_doc
    
class Cp_32(PressRelease):
    def __init__(self):
        base_url='https://www.gac.com.cn/'
        press_release_url='https://www.gac.com.cn/cn/news'
        h_code='02238.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#__layout > div > div.news > div.page > div.success-box > div.footer > div > div > div > ul > li.active'))).text
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#__layout > div > div.news > div.page > div.success-box > div.footer > div > div > div > ul > li:nth-child(6)'))).text
        return int(target_ele)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#__layout > div > div.news > div.page > div.success-box > div.footer > div > div > div > button.btn-next')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'#__layout > div > div:nth-child(2) > div:nth-child(1) > div.container > div.article').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#__layout > div > div.news > div.page > div.success-box > div.body > div > div > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'img').get_attribute('alt')
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'div.time').text
            urls.append(url)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_32.retrieve_content)(self.press_release_url,url) for url in urls)
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_33(PressRelease):
    def __init__(self):
        base_url='https://bbmg-umb.azurewebsites.net/'
        press_release_url=''
        h_code='02009.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page_a(self,driver:WebDriver)->int:
        return 10
    
    def get_total_page_h(self,driver:WebDriver)->int:
        return 17

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#PagesContainer > table > tbody > tr > td:nth-child(3) > a')))
        driver.execute_script("arguments[0].click();", page_div)
        
    def retrieve_content(self,driver:WebDriver,url_ele:WebElement,doc:Document)->tuple[str,str]:
        first_window_handle = driver.current_window_handle
        
        driver.execute_script("arguments[0].click();", url_ele)
        
        new_window_handle=None
        for handle in driver.window_handles: 
            if handle != first_window_handle: 
                new_window_handle = handle
        driver.switch_to(new_window_handle)
        current_url = driver.current_url
        temp_doc=Document(current_url,doc.title,doc.published_at,self.base_url,None,None,self.company_id)
        content=_extracting_an_document(temp_doc)
        driver.close()
        driver.switch_to.window(first_window_handle)
        return current_url,content

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#PressReleases')))
        rows=target_ele.find_elements(By.TAG_NAME,'div')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url_ele=row_.find_element(By.CSS_SELECTOR,'a image')
            title=row_.find_element(By.CSS_SELECTOR,'a.PressRelease-NewsTitle').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'span.PressRelease-NewsDate').text
            #2023年8月24日
            date_in_iso=date_in_iso.replace('年','-').replace('月','-').replace('日','-')
            urls.append(url_ele)
            tot_doc.append(Document(None,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_33.retrieve_content)(self.press_release_url,url) for url in urls)
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i][1])
            tot_doc[i].set_url(content_list[i][0])
        return tot_doc

    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        
        # crawl a 
        
        wait=WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.internal-page-content.announcements-and-circulars > div > div > div:nth-child(2) > div > div > div > div > div > div.stock-header > ul > li.active > a')))
        driver.execute_script("arguments[0].click();", page_div)
        total_page=self.get_total_page_a(driver)
        current_page=1
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
            
        #crawl h 
        page_div2=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.internal-page-content.announcements-and-circulars > div > div > div:nth-child(2) > div > div > div > div > div > div.stock-header > ul > li:nth-child(2) > a')))
        driver.execute_script("arguments[0].click();", page_div2)
        total_page=self.get_total_page_h(driver)
        current_page=1
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc

class Cp_34(PressRelease):
    def __init__(self):
        base_url='https://comec.cssc.net.cn/'
        press_release_url=''
        h_code='00317.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'')))
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'')))
        return int(target_ele)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'')
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'')
            urls.append(url)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_34.retrieve_content)(self.press_release_url,url) for url in urls)
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_35(PressRelease):
    def __init__(self):
        base_url='https://www.shanghai-electric.com/'
        press_release_url='https://www.shanghai-electric.com/listed/xwzx/rdzx/'
        h_code='02727.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 108

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#u-columnbg > div > nav > div > ul > li.page_next > a')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'#u-columnbg > div > div.news-detail.clearfix').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#u-columnbg > div > div.news-list.news-list-hotinfo > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        urls=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'span').text
            urls.append(url)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
        content_list = Parallel(n_jobs=-1)(delayed(Cp_35.retrieve_content)(self.press_release_url,url) for url in urls)
        for i in range(len(content_list)): 
            tot_doc[i].set_content(content_list[i])
        return tot_doc


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_36(PressRelease):
    def __init__(self):
        base_url='https://www.3healthcare.com/'
        press_release_url='https://www.3healthcare.com/news.html    '
        h_code='06826.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=https://www.3healthcare.com/robots.txt

    def get_current_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#about > div > div > div > div.main_col > div > div.pager > span.current'))).text
        return int(target_ele)

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#about > div > div > div > div.main_col > div > div.pager > a:nth-child(8)'))).get_attribute('href')
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.get(target_ele)
        page_=self.get_current_page(driver2)
        driver2.close()
        return page_

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#about > div > div > div > div.main_col > div > div.pager > a:nth-child(7)')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'#about > div > div > div > div.main_col > div > div.about_content_news').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#about > div > div > div > div.main_col > div > div.about_content_news > div > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'span.showtime').text
            content=self.retrieve_content(url)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,content,None,self.company_id))


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_37(PressRelease):
    def __init__(self):
        base_url='https://www.beijingns.com.cn/'
        press_release_url='https://www.beijingns.com.cn/invest/'
        h_code="00588.HK".lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 142 

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#ajaxpage > div > div > a.next')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.main > div.wrap > div').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#ajaxlist')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'h3 a').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'h3 a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'div.news_time').text.replace('.','-')
            content=self.retrieve_content(url)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,content,None,self.company_id))


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_38(PressRelease):
    def __init__(self):
        base_url='https://www.ceec.net.cn/'
        press_release_url='https://www.ceec.net.cn/col/col11016/index.html'
        h_code='03996.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 69

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#\34 10804 > table > tbody > tr > td > table > tbody > tr > td:nth-child(4) > a')))
        driver.execute_script("arguments[0].click();", page_div)

    def retrieve_content(press_release_url:str,url:str)->tuple[str,str]:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return '',''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return '',''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'#body > div.wzy > div.wz_sakb.content > div.wz_article.atcl-viedo').text
            time_ele=driver2.find_element(By.CSS_SELECTOR,'#body > div.wzy > div.wz_sakb.content > ul > li.fl.time').text
            date_pattern = r'\b\d{4}-\d{2}-\d{2}\b'
            date_in_iso = re.match(date_pattern, time_ele).group()
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()        
            return date_in_iso,target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#\34 10804 > div > div > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'a').text
            date_in_iso,content=self.retrieve_content(url)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,content,None,self.company_id))


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_39(PressRelease):
    def __init__(self):
        base_url='https://www.dzug.cn/'
        press_release_url='https://www.dzug.cn/Article/235_1570,1600'
        h_code='01635.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 15

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#aspnetForm > div.bodyer.type2 > div.width1132 > div.width877.fr > div > div.paging > a.next')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > form > div.bodyer.type2 > div.width1132 > div.width877.fr > div > div.cbd').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#aspnetForm > div.bodyer.type2 > div.width1132 > div.width877.fr > div > div.bd > dl')))
        rows=target_ele.find_elements(By.TAG_NAME,'d')
        tot_doc:list[Document]=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'span').text.replace('.','-')
            content=self.retrieve_content(url)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,content,None,self.company_id))


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_40(PressRelease):
    def __init__(self):
        base_url='https://www.goldwind.com/cn/'
        press_release_url='https://www.goldwind.com/cn/news/focus/'
        h_code='02208.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 2

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#list > div.pagination > ul > li.item-next > a')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'#__layout > div > div:nth-child(2) > div:nth-child(2) > div').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#list > div.news > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'div > h3').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'div > label')
            content=self.retrieve_content(url)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,content,None,self.company_id))


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc

class Cp_41(PressRelease):
    def __init__(self):
        base_url='https://www.dfzq.com.cn/'
        press_release_url='https://www.dfzq.com.cn/osoa/views/main/investorrelations/circulars/index.shtml'
        h_code='03958.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 130
    ##PagesContainer > table > tbody > tr
    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        element=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#PagesContainer > table > tbody > tr')))
        children = element.find_elements(By.XPATH, ".//*")
        
        flag=False
        for child in children: 
            tagname=child.tag_name
            if flag: 
                driver.execute_script("arguments[0].click();", child)
            if tagname=='span': 
                flag=True
            
            
        
        
    ##PagesContainer > table > tbody > tr > td:nth-child(2) > a:nth-child(3)
    def retrieve_content(self,url_ele:WebElement,driver:WebDriver)->tuple[str,str]:
        current_handler=driver.current_window_handle
        driver.execute_script("arguments[0].click();", url_ele)
        new_handler=None
        for handler in driver.window_handles: 
            if handler != current_handler: 
                new_handler=handler
        driver.switch_to(new_handler)
        current_url=driver.current_url
        temp_doc=Document(current_url,None,None,None,None,None,self.company_id)
        content=_extracting_an_document(temp_doc)
        driver.close()
        driver.switch_to.window(current_handler)
        return current_url,content

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#PressReleases')))
        rows=target_ele.find_elements(By.TAG_NAME,'div')
        tot_doc:list[Document]=[]
        for row_ in rows:
            ##PressRelease_0 > div.NoChange-NewsColumn.ColumnLayoutColumn > div > div.PressRelease-Attachment > div > a > img
            url_ele=row_.find_element(By.CSS_SELECTOR,'img')
            title=row_.find_element(By.CSS_SELECTOR,'a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'span.PressRelease-NewsDate').text.replace('年','-').replace('月','-').replace('日','-')
            url,content=self.retrieve_content(url_ele)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,content,None,self.company_id))


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        wait=WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#YearPeriodsContainer > a:nth-child(6')))
        driver.execute_script("arguments[0].click();", page_div)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_42(PressRelease):
    def __init__(self):
        base_url='https://www.portqhd.com/'
        press_release_url='https://www.portqhd.com/c/media_corporate.php'
        h_code='03369.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=https://www.portqhd.com/robots.txt

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,year:int)->int:
        if year==2023 or 2017: 
            return 3
        elif year ==2022 or year==2021 or year ==2020 or year==2019 or year==2018 or year==2016: 
            return 1
        else: 
            return 1 
        
    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_content(self,driver:WebDriver,url_ele:WebElement)->tuple[str,str]: 
        current_handle=driver.current_window_handle
        driver.execute_script("arguments[0].click();", url_ele)
        new_handle=None
        all_handles=driver.window_handles
        for handle in all_handles: 
            if handle!=current_handle: 
                new_handle=handle
        driver.switch_to(new_handle)
        current_url=driver.current_url
        content=_extracting_an_document(Document(current_url,None,None,None,None,None,self.company_id))
        driver.close()
        driver.switch_to(current_handle)
        return current_url,content
            
    def loop_and_read(self,year_no:int,driver:WebDriver)->list[Document]:        
        result_document:list[Document]=[]
        wait=WebDriverWait(driver, 15)
        parent_ele=driver.find_element(By.CSS_SELECTOR, 'body > div.outer_box > div.page_content > div.page_right > div > div.page_main > div.ir_year')
        parent_wait=WebDriverWait(parent_ele,10)
        ul_eles=parent_ele.find_elements(By.CSS_SELECTOR,'ul')
        ul_eles=parent_wait.until(EC.visibility_of_all_elements_located(By.CSS_SELECTOR,'ul'))
        display_index=-1
        target_index=-1
        for index_,li_ele in enumerate(ul_eles): 
            if li_ele.get_attribute('style')=='display: block;':
                display_index=index_
            year_lists:list[int]=[]
            li_eles=li_ele.find_elements(By.CSS_SELECTOR,'li')
            for li_ele in li_eles: 
                year_int=int(li_ele.text.strip('.'))
                year_lists.append(year_int)            
            if year_no in year_lists:
                target_index=index_
        
        #Get the target_ul to shown: 
        if display_index==target_index: 
            pass    
        elif display_index<target_index: 
            while display_index<target_index: 
                page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#next_a')))
                driver.execute_script("arguments[0].click();", page_div)
                ul_eles=parent_wait.until(EC.visibility_of_all_elements_located(By.CSS_SELECTOR,'ul'))
                for index_,li_ele in enumerate(ul_eles): 
                    if li_ele.get_attribute('style')=='display: block;':
                        display_index=index_
        else: 
            while display_index>target_index: 
                page_div2=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#previous_a')))
                driver.execute_script("arguments[0].click();", page_div2)
                ul_eles=parent_wait.until(EC.visibility_of_all_elements_located(By.CSS_SELECTOR,'ul'))
                for index_,li_ele in enumerate(ul_eles): 
                    if li_ele.get_attribute('style')=='display: block;':
                        display_index=index_

        #click this li year element 
        ul_eles=parent_wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR,'ul')))
        for index_,li_ele in enumerate(ul_eles): 
            if li_ele.get_attribute('style')=='display: block;':
                display_index=index_
            li_eles=li_ele.find_elements(By.CSS_SELECTOR,'li')
            for li_ele in li_eles: 
                year_int=int(li_ele.text.strip('.'))
                year_lists.append(year_int)            
                if year_int ==year_no:
                    driver.execute_script("arguments[0].click();", li_ele)
        
        # read that page
        tot_page=self.get_total_page(year_no)
        cur_page=1
        while cur_page <= tot_page: 
            page_articles=wait.until(EC.visibility_of((By.CSS_SELECTOR,'body > div.outer_box > div.page_content > div.page_right > div > div.page_main > div.ir_list > ul')))
            li_eles= page_articles.find_elements(By.CSS_SELECTOR,'li')
            for li_ele in li_eles: 
                url_ele=li_ele.find_element(By.CSS_SELECTOR,'div.page_an_down > a')
                url,content= self.read_content(driver,url_ele)
                date_in_iso=li_ele.find_element(By.CSS_SELECTOR,'div.page_an_date > span').text
                title=li_ele.find_element(By.CSS_SELECTOR,'div.page_an_title > a').text
                result_document.append(Document(url,title,date_in_iso,self.base_url,content,None,self.company_id))
        return result_document
                
    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.outer_box > div.page_content > div.page_right > div > div.page_main > div.ir_year')))
        years_ele = target_ele.find_elements('li')
        tot_doc:list[Document]=[]
        for year_row in years_ele: 
            year=int(year_row.text.strip('.'))
            temp_doc=self.loop_and_read(year,driver)
            tot_doc=tot_doc+temp_doc

                
    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        
        all_doc:list[Document]=self.read_page(driver)
        driver.quit()
        return all_doc
        
class Cp_43(PressRelease):
    def __init__(self):
        base_url='http://www.zzbank.cn/'
        press_release_url='http://www.zzbank.cn/inversrtor_relations/ggth/agu/2023/'
        h_code='06196.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'')))
        return int(target_ele)


    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,target_year:int,driver:WebDriver)->list[Document]:
        tot_doc:list[Document]=[]
        wait = WebDriverWait(driver, 15)
        year_list = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#business > div.main_tab')))
        years_row=year_list.find_elements(By.CSS_SELECTOR,'a')
        for year_row in years_row: 
            if target_year == int(year_row.text.strip()):
                driver.execute_script("arguments[0].click();", year_row)
        
        news_parent = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#business > div.row > div > ul')))
        rows=news_parent.find_elements(By.TAG_NAME,'li')
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'a span').text
            content=_extracting_an_document(Document(url,title,date_in_iso,self.press_release_url,None,None,self.company_id))
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,content,None,self.company_id))

    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        all_years_a=[2023,2022,2021,2020,2019,2018]
        
        #a news 
        page_div=WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.container > div.main_wrap > div > div.side_bar > ul:nth-child(2) > li:nth-child(2) > a')))
        driver.execute_script("arguments[0].click();", page_div)
        tot_doc:list[Document]=[]
        for year_a in all_years_a: 
            tot_doc=tot_doc+self.read_page(year_a,driver)
            
            
        all_years_h=list(range(2016,2023+1))
        #h news 
        page_div2=WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.container > div.main_wrap > div > div.side_bar > ul:nth-child(2) > li:nth-child(3) > a')))
        driver.execute_script("arguments[0].click();", page_div2)
        for year_h in all_years_h: 
            tot_doc=tot_doc+self.read_page(year_h,driver)
    
        driver.quit()
        return tot_doc
    
class Cp_44(PressRelease):
    def __init__(self):
        base_url='http://www.liaoningport.com/'
        press_release_url='http://www.liaoningport.com/rdzx/index.jhtml'
        h_code='02880.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 36

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.about > div > div.about_right > article > div').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.about > div > div.about_right > article > div')))
        rows=target_ele.find_elements(By.TAG_NAME,'div')
        tot_doc:list[Document]=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'div.date').text
            content=self.retrieve_content(url)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,content,None,self.company_id))


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc

class Cp_45(PressRelease):
    def __init__(self):
        base_url='https://www.huahonggrace.com/'
        press_release_url='https://www.huahonggrace.com/c/news_press.php'
        h_code='01347.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=https://www.huahonggrace.com/robots.txt

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'')))
        return int(target_ele)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'')))
        driver.execute_script("arguments[0].click();", page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        txt_result=_extracting_an_document(Document(url,None,None,press_release_url,None,None,None))
        driver2.quit()
        return txt_result

    def read_page(self,url:str)->list[Document]:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver2, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div > div.container > div.cont_right > div > div.inner_cont_ann > ul')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'div.date').text.replace(' ','').replace('.','-')
            content=self.retrieve_content(url)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,content,None,self.company_id))
        driver2.close()


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        all_doc:list[Document]=[]
        all_years=driver.find_element(By.CSS_SELECTOR,'body  div div.year_list').find_elements(By.CSS_SELECTOR,'a')
        for year in all_years: 
            year_url=year.get_attribute('href')
            all_doc=all_doc+self.read_page(year_url)
        
        driver.quit()
        return all_doc


class Cp_46(PressRelease):
    def __init__(self):
        base_url='https://www.ccccltd.cn/'
        press_release_url='https://www.ccccltd.cn/news/gsyw/'
        h_code='01800.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=None 

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 100

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        page_template=self.press_release_url+"index_{}.html".format(cur_page+1)
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'')))
        driver.execute_script('arguments[0].click();', page_div)
        driver.get(page_template)
        
    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'body > div.maxcontainer.main-con-bg > dl > dt > div').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.maxcontainer.main-con-bg > dl > dd > dl > dd > div')))
        rows=target_ele.find_elements(By.TAG_NAME,'dl')
        tot_doc:list[Document]=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'dt.fl_pc a').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'dt.fl_pc a').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'dd.fr_pc').text
            content=self.retrieve_content(url)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,content,None,self.company_id))


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                if "net::ERR_CONNECTION_RESET" in str(e):
                    attempts += 1
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else: 
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_47(PressRelease):
    def __init__(self):
        base_url=''
        press_release_url=''
        h_code='00991.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'')))
        return int(target_ele)

    def next_page(self,cur_page:int,driver:WebDriver)->None:
        wait = WebDriverWait(driver, 15)
        page_div=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'')))
        driver.execute_script('arguments[0].click();', page_div)

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'')
            content=self.retrieve_content(url)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,content,None,self.company_id))


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                    print(f"Attempt {attempts} of {max_attempts} failed with error: {e}")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else:
                    raise(e)
        
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
class Cp_48(PressRelease):
    def __init__(self):
        base_url='http://www.mcc.com.cn/'
        press_release_url='http://www.mcc.com.cn/xwzx_7388/lddt/'
        h_code='01618.HK'.lower()
        super().__init__(base_url,press_release_url,h_code)
        #robot.txt=

    def get_current_page(self,driver:WebDriver)->int:
        return 1

    def get_total_page(self,driver:WebDriver)->int:
        return 25
    #href="index_22.html"
    def next_page(self,cur_page:int,driver:WebDriver)->None:
        template='index_{}.html'.format(cur_page+1)
        page_url=self.press_release_url+template
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        driver2.get(page_url)
        driver2.quit()  

    @staticmethod
    def retrieve_content(press_release_url:str,url:str)->str:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver2 = webdriver.Chrome(options=chrome_options)
        try:
            driver_connect(driver2,url)
        except TimeoutException: 
            driver2.close()
            return ''
        except InvalidArgumentException:
            print("Invalid Argument",url)
            try:
                driver_connect(driver2,press_release_url+url)
            except InvalidArgumentException: 
                driver2.close()
                return ''
        try:
            target_ele=driver2.find_element(By.CSS_SELECTOR,'').text
        except NoSuchElementException: 
            print(press_release_url, " ", url)
            target_ele=''
        finally:
            driver2.quit()
            return target_ele

    def read_page(self,driver:WebDriver)->list[Document]:
        wait = WebDriverWait(driver, 15)
        target_ele = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '')))
        rows=target_ele.find_elements(By.TAG_NAME,'li')
        tot_doc:list[Document]=[]
        for row_ in rows:
            url=row_.find_element(By.CSS_SELECTOR,'').get_attribute('href')
            title=row_.find_element(By.CSS_SELECTOR,'').text
            date_in_iso=row_.find_element(By.CSS_SELECTOR,'')
            content=self.retrieve_content(url)
            tot_doc.append(Document(url,title,date_in_iso,self.press_release_url,content,None,self.company_id))


    def crawling(self)->list[Document]:
        #chrome_options = Options()
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
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else:
                    raise(e)
        time.sleep(0.1)
        total_page=self.get_total_page(driver)
        current_page=self.get_current_page(driver)
        all_doc:list[Document]=[]
        while(current_page<=total_page):
            temp_doc=self.read_page(driver)
            all_doc=all_doc+temp_doc
            if(current_page<total_page):
                self.next_page(current_page,driver)
            time.sleep(0.1)
            current_page=current_page+1
        driver.quit()
        return all_doc
    
    