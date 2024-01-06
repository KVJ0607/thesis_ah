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
FLAT_MAX_PAGE=100