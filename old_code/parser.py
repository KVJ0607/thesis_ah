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
    wait = WebDriverWait(driver, 4)
    first_option = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="autocomplete-list-0"]/div[1]/div[1]/table/tbody/tr[1]/td[1]/span')))
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
    time.sleep(2)
    

    while current_record <total_record: 
        click_load_button(driver)
        if current_record < 1000:    
            time.sleep(1)
        else:
            time.sleep(2)             
        current_record = get_current_record(driver)

            
    time.sleep(2)
    rows = driver.find_elements(By.TAG_NAME,"tr")
    rows = rows[1:-1]
    document_list = []
    for row in rows:  
        time_ele =  row.find_element(By.CLASS_NAME,'release-time').text
        #doc_ele =  row.find_element(By.CLASS_NAME,'headline').text
        url_title = row.find_element(By.CLASS_NAME,'doc-link').text        
        ###
        url = row.find_element(By.CLASS_NAME,'doc-link').find_element(By.TAG_NAME,'a').get_attribute("href")
        document_list.append(Document(url,url_title,time_ele,company.h_code,None,None,company.id))
    time.sleep(2)
    # Remember to close the driver
    driver.quit()
    return document_list 


