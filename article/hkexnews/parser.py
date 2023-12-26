#internal step 2
import re 
#import sys 
import time
#from class_my.companies_my import Company
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException,StaleElementReferenceException,ElementClickInterceptedException,NoSuchElementException, TimeoutException

from company.company import Company,Document
from utils.basic import convert_to_iso_hkexnews



# Define a method to get current record
def get_current_record(driver:WebDriver):
    wait = WebDriverWait(driver, timeout=20) # timeout can be adjusted
    element = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'component-loadmore-leftPart__container')))
    try:
        current_record = element.text
    except StaleElementReferenceException: 
        element=driver.find_element(By.CLASS_NAME,'component-loadmore-leftPart__container')
        current_record=element.text        
    pattern = r'Showing (\d+)'
    match = re.search(pattern,current_record)
    current_record = int(match.group(1))
    return current_record

def click_load_button(driver:WebDriver): 
    import time     
    # Click the first option
    WebDriverWait(driver, 10).until(
        EC.invisibility_of_element_located((By.ID, 'the_id_of_the_overlay_element'))
    )

    # Wait until the element to be clicked is clickable
    load_more_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'javascript:loadMore();')]"))
    )
    
    driver.execute_script("arguments[0].click();", load_more_button)
    
    time.sleep(0.5)


    
    
def _get_all_record(driver:WebDriver):
    total_record = driver.find_element(By.CLASS_NAME,'total-records').text 
    patten=r'Total records found: ([0123456789]+)'
    match = re.search(patten,total_record)
    total_record = int(match.group(1))

    ## Continue to click load button when current record != total record 
    current_record = get_current_record(driver)
    time.sleep(2)

    while current_record<total_record: 
        click_load_button(driver)
        try:
            current_record=get_current_record(driver)
        except UnexpectedAlertPresentException as e:
            driver.refresh()
        current_record=_get_all_record(driver) 
        
class ElementsWrapper:
    def __init__(self,webdriver:WebDriver,locator):
        self.webdriver=webdriver
        self.locator=locator
        self.elements=None

        self.locate_elements()
    
    def locate_elements(self)->list[WebElement]:
        self.elements=self.webdriver.find_elements(*self.locator)
    
    def from_elements_find_element(self,*locator,index:int)->WebElement: 
        try: 
            result=self.elements[index].find_element(*locator)
            return result
        except StaleElementReferenceException: 
            self.locate_elements()
            result=self.elements[index].find_element(*locator)



def get_hkexnews_var3(company:Company)->list[Document]: 
    print('start get_hkexnews {}'.format(company.id))
    URL = 'https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=en'
    base_url='https://www1.hkexnews.hk'
    hcode_key = company.get_digits_hcode()
    #chrome_options = Options()
    #chrome_options.add_argument("--headless")
    #driver = webdriver.Chrome(options=chrome_options)
    driver = webdriver.Chrome()
    driver.get(URL)

    ## send input 
    input_field = driver.find_element(By.ID, 'searchStockCode')
    input_field.send_keys(hcode_key)

    #click the combobox 
    combobox = driver.find_element(By.ID, 'searchStockCode')
    combobox.click()

    # Wait for the dropdown options to become visible
    wait = WebDriverWait(driver, 10)
    first_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="autocomplete-list-0"]/div[1]/div[1]/table/tbody/tr[1]/td[1]/span')))
    first_option.click()
    search_button = driver.find_element(By.CLASS_NAME, 'filter__btn-applyFilters-js')
    # Click the first option
    search_button.click()


    # get total record 
    total_record = driver.find_element(By.CLASS_NAME,'total-records').text 
    patten=r'Total records found: ([0123456789]+)'
    match = re.search(patten,total_record)
    total_record = int(match.group(1))
    print(f'total_record: {total_record}')
    ## Continue to click load button when current record != total record 
    current_record = get_current_record(driver)
    
    
    reject_button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID,'onetrust-reject-all-handler')))
    driver.execute_script("arguments[0].click();", reject_button)
    time.sleep(1)
    
    records = []
    last_processed_index = 0  # Keep track of the last index processed
    
    while current_record < total_record:
        # Wait for the rows to be loaded
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr"))
        )

        # Get the current number of records
        current_record = get_current_record(driver)

        # Iterate over new rows since the last processed index
        for index in range(last_processed_index, current_record):      
            try:  
            # Find the elements for time, url text, and the href attribute
                time.sleep(0.5)
                row = driver.find_elements(By.CSS_SELECTOR, "tbody tr")[index]
                time_ele_text = row.find_element(By.CSS_SELECTOR, 'td.release-time').text
                time_ele_in_iso=convert_to_iso_hkexnews(time_ele_text)
                
                doc_link = row.find_element(By.CSS_SELECTOR,'div.doc-link a')
                url = doc_link.get_attribute('href')
                title = doc_link.text

                # Append the data to the records list
                records.append(Document(url,title,time_ele_in_iso,"HKEXNEWS",None,None,company.id))
                print(f'row{index}, {title} {time_ele_in_iso} \n {url}')
            except Exception as e:
                print(f"Error occurred at row number: {index + 1}")
                raise e  # This will re-raise the last exception

        # Update the last processed index to the current record count
        last_processed_index = current_record

        # Check if there are more records to load
        if current_record < total_record:
            click_load_button(driver)
            # Optionally, wait for the new rows to load
            WebDriverWait(driver, 10).until(
                lambda d: get_current_record(driver) > last_processed_index
            )


    time.sleep(2)
    # Remember to close the driver
    driver.quit()
    return records 



















def get_hkexnews_old2(company:Company)->list[Document]: 
    print('start get_hkexnews {}'.format(company.id))
    URL = 'https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=en'
    hcode_key = company.get_digits_hcode()
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(URL)

    ## send input 
    input_field = driver.find_element(By.ID, 'searchStockCode')
    input_field.send_keys(hcode_key)

    #click the combobox 
    combobox = driver.find_element(By.ID, 'searchStockCode')
    combobox.click()

    # Wait for the dropdown options to become visible
    wait = WebDriverWait(driver, 10)
    first_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="autocomplete-list-0"]/div[1]/div[1]/table/tbody/tr[1]/td[1]/span')))
    first_option.click()
    search_button = driver.find_element(By.CLASS_NAME, 'filter__btn-applyFilters-js')
    # Click the first option
    search_button.click()


    # get total record 
    total_record = driver.find_element(By.CLASS_NAME,'total-records').text 
    patten=r'Total records found: ([0123456789]+)'
    match = re.search(patten,total_record)
    total_record = int(match.group(1))
    print(f'total_record: {total_record}')
    ## Continue to click load button when current record != total record 
    current_record = get_current_record(driver)
    
    
    reject_button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID,'onetrust-reject-all-handler')))
    driver.execute_script("arguments[0].click();", reject_button)
    time.sleep(1)
    

    while current_record<total_record: 
        click_load_button(driver)
        time.sleep(2)
        try:
            current_record=get_current_record(driver)
        except UnexpectedAlertPresentException as e:
            driver.refresh()
            time.sleep(2)    
            current_record=get_current_record(driver) 
            print(f'loaded to current_record{current_record}')
            
    time.sleep(2)
    #Number of rows under tbody 

    
    
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
    number_of_rows=len(rows)
    document_list = []

    for index in range(number_of_rows): 
        time_ele_text=driver.find_elements(By.CSS_SELECTOR, "tbody tr")[index].find_element(By.CSS_SELECTOR,'td.release-time').text
        url_ele_text=driver.find_elements(By.CSS_SELECTOR, "tbody tr")[index].find_element(By.CSS_SELECTOR,"td.doc-link").text
        url=driver.find_elements(By.CSS_SELECTOR, "tbody tr")[index].find_element(By.CSS_SELECTOR,"td.doc-link").find_element(By.TAG_NAME,'a').get_attribute('href')
        time_ele_in_iso=convert_to_iso_hkexnews(time_ele_text)
        document_list.append(Document(url,url_ele_text,time_ele_in_iso,company.h_code,None,None,company.id))
        print(f'For row {index}: {time_ele_in_iso}, {url_ele_text}, \n {url}')


    time.sleep(2)
    # Remember to close the driver
    driver.quit()
    return document_list 


def get_hkexnews_old(company:Company)->list[Document]: 
    URL = 'https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=en'
    hcode_key = company.get_digits_hcode()
    driver = webdriver.Chrome()
    driver.get(URL)

    ## send input 
    input_field = driver.find_element(By.ID, 'searchStockCode')
    input_field.send_keys(hcode_key)

    #click the combobox 
    combobox = driver.find_element(By.ID, 'searchStockCode')
    combobox.click()

    # Wait for the dropdown options to become visible
    wait = WebDriverWait(driver, 10)
    first_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="autocomplete-list-0"]/div[1]/div[1]/table/tbody/tr[1]/td[1]/span')))
    first_option.click()
    search_button = driver.find_element(By.CLASS_NAME, 'filter__btn-applyFilters-js')
    # Click the first option
    search_button.click()


    # get total record 
    total_record = driver.find_element(By.CLASS_NAME,'total-records').text 
    patten=r'Total records found: ([0123456789]+)'
    match = re.search(patten,total_record)
    total_record = int(match.group(1))

    ## Continue to click load button when current record != total record 
    current_record = get_current_record(driver)
    
    reject_button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID,'onetrust-reject-all-handler')))
    reject_button.click()
    time.sleep(1)
    

    while current_record<total_record: 
        click_load_button(driver)
        time.sleep(2)
        try:
            current_record=get_current_record(driver)
        except UnexpectedAlertPresentException as e:
            driver.refresh()
            time.sleep(2)    
            current_record=get_current_record(driver) 
            
    time.sleep(2)
    #rows_wrapper= ElementsWrapper(driver,(By.TAG_NAME,'tr'))
    #rows =rows_wrapper.elements
    
    
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
    document_list = []

    for index,row in enumerate(rows):
        try:
            time_ele=row.find_element(By.CLASS_NAME,'release-time').text
        except StaleElementReferenceException: 
            rows=driver.find_elements(By.CSS_SELECTOR,"tbody tr")
            time_ele=rows[index].find_element(By.CLASS_NAME,'release-time').text
        try:  
            url_ele=row.find_element(By.CLASS_NAME,'doc-link').text
        except StaleElementReferenceException: 
            rows=driver.find_elements(By.CSS_SELECTOR,"tbody tr")
            url_ele=rows[index].find_element(By.CLASS_NAME,'doc-link').text
            
        try:
            url=row.find_element(By.CLASS_NAME,'doc-link').find_element(By.TAG_NAME,'a').get_attribute('href')
        except StaleElementReferenceException: 
            try: 
                url_a_ele= row.find_element(By.CLASS_NAME,'doc-link').find_element(By.TAG_NAME,'a')
            except StaleElementReferenceException:
                try:
                    url_doc_link=row.find_element(By.CLASS_NAME,'doc-link')
                except StaleElementReferenceException:
                    rows=driver.find_elements(By.TAG_NAME,'tr')
                    row=rows[index]
                    url_doc_link=row.find_element(By.CLASS_NAME,'doc-link')
                url_a_ele=url_doc_link.find_element(By.TAG_NAME,'a')
            url=url_a_ele.get_attribute("href")
            
        document_list.append(Document(url,url_ele,time_ele,company.h_code,None,None,company.id))


    time.sleep(2)
    # Remember to close the driver
    driver.quit()
    return document_list 






