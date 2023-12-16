
import requests
from pathlib import PosixPath
from datetime import datetime, date

from company.company import Article
#id	url	title	publish_at	api	content
class HKEXNEWS(Article):
    def __init__(self,url:str,title:str,publish_at:str|datetime,h_code:str,content=None,id=None):
        super().__init__(url,title,publish_at,'hkexnews',content)
        self.__h_code=h_code

    @property
    def url(self):
        return super().url 
    @property
    def title(self):
        return super().title 
    @property
    def published_at(self):
        return super().published_at 
    @property
    def api(self):
        return super().api 
    @property
    def h_code(self):
        return self.__h_code
    @property
    def content(self):
        return super().content   
    
    
class NewsOld:
    def __init__(self,company,time:str,doc:str,url_name:str,url:str): 
        self.__company:("Company")=company 
        self.__time=time
        self.__doc=doc
        self.__url_name=url_name
        self.__url=url
        self.__filename:PosixPath=None ##This file name does not include extension like "".csv"
 


        self.error_fit_minus_a3:float=None #OLD
        self.error_fit_minus_h3:float=None #OLD
        self.__h_error_estimate_minus_actual_in_statsmodel_estimate=None
        self.__h_error_estimate_minus_actual_in_statsmodel_estimate=None

        self.pre_listed_news:bool=False ##either a or h

    def __str__(self): 
        company_info = self.__company.ge_id()
        news_info = self.__time + " " + self.__doc + " " + self.__url_name + self.__url
        return company_info + news_info
    
    def __hash__(self):
        hcode_num=self.company.hcode.split('.')[0]
        new_dt=self.date_in_date_time
        new_dt_in_minute=new_dt.hour*60+new_dt.minute+new_dt.minute/60
        datetime_in_num=str(new_dt.year)+str(new_dt.month)+str(new_dt.day)+str(new_dt_in_minute)
        return float(hcode_num+datetime_in_num)
        
    def get_positive_score(self): 
        try: 
            return self.positive_score
        except(AttributeError): 
            print(self.company,self.filename)
    @property
    def company(self):
        try: 
            return self.__company
        except(AttributeError): 
            print(self.filename)
    @company.setter
    def company(self,company): 
        self.__company=company
    @property
    def time(self)->str:
        return self.__time
    @property
    def doc(self)->str:
        return self.__doc
    @property
    def url_name(self)->str:
        return self.__url_name
    @property
    def url(self)->str:
        return self.__url
    @property
    def filename(self)->PosixPath:
        return self.__filename
    @property
    def date_in_date_time(self)->datetime: 
        return self.__date_in_date_time
    @property
    def a_d1_date(self)->date:
        return self.__a_d1_date
    @property
    def a_d1_index(self)->int:
        return self.__a_d1_index
    @property
    def h_d1_date(self)->date:
        return self.__h_d1_date
    @property
    def h_d1_index(self)->int:
        return self.__h_d1_index
    
    @property
    def a3(self)->float:
        return self.__a3
    
    def set_a3(self,a3)->None:
        self.__a3=a3

    @property 
    def h3(self)->float:
        return self.__h3
    
    def set_h3(self,h3):
        self.__h3=h3

    def set_a_error_estimate_minus_actual_in_statsmodel_estimate(self,a_error)->None:
        self.__a_error_estimate_minus_actual_in_statsmodel_estimate=a_error
    @property
    def a_error_estimate_minus_actual_in_statsmodel_estimate(self)->float: 
        return self.__a_error_estimate_minus_actual_in_statsmodel_estimate

    def set_h_error_estimate_minus_actual_in_statsmodel_estimate(self,h_error)->None:
        self.__h_error_estimate_minus_actual_in_statsmodel_estimate=h_error
    @property
    def h_error_estimate_minus_actual_in_statsmodel_estimate(self)->float: 
        return self.__h_error_estimate_minus_actual_in_statsmodel_estimate



    ### D1 D2,....
    def set_pricing_D1_index(self):
        company=self.company
        a_date_list=company.a_pricing_history.date
        h_date_list=company.h_pricing_history.date
        a_index=0
        h_index=0
        a_d1=None 
        h_d1=None
        for a_pricing_date in a_date_list: 
            #a_date_time = date_to_datetime_stock(a_date)
            if a_pricing_date <=self.__date_in_date_time.date(): 
                a_index=a_index+1
            elif a_pricing_date >self.__date_in_date_time.date(): 
                a_d1=a_pricing_date   
                break         
        if a_index==0: 
            a_index=-1
            self.pre_listed_news=True
        for h_pricing_date in h_date_list: 
            #h_date_time = date_to_datetime_stock(h_date)
            if h_pricing_date <=self.__date_in_date_time.date(): 
                h_index=h_index+1
            elif h_pricing_date >self.__date_in_date_time.date(): 
                h_d1=h_pricing_date                
                break
        if h_index==0: 
            h_index=-1
            self.pre_listed_news=True
        self.__a_d1_index=a_index
        self.__h_d1_index=h_index
        self.__a_d1_date=a_d1
        self.__h_d1_date=h_d1
    
    #get dn_adjusted daily return 
    #get_a_dn_adjusted_daily_return
    def get_a_dn_adjusted_accumlated_return(self,nday:int=1)->float: 
        d1_index=self.a_d1_index
        if self.pre_listed_news==True or len(self.company.a_pricing_history.list)<=d1_index+nday-1: 
            return None
        if nday<1: 
            print("dn can't be smaller than 1")
            return None     
        new_close =self.company.a_pricing_history.list[d1_index+nday-1].adjusted_close
        old_close = self.company.a_pricing_history.list[d1_index-1].adjusted_close
        return (new_close-old_close)/old_close


    def get_a_dn_accumlated_return(self,nday:int=1)->float: 
        d1_index=self.a_d1_index
        if self.pre_listed_news==True or len(self.company.a_pricing_history.list)<=d1_index+nday-1: 
            return None
        if nday<1: 
            print("dn can't be smaller than 1")
            return None
        new_close =self.company.a_pricing_history.list[d1_index+nday-1].close
        old_close = self.company.a_pricing_history.list[d1_index-1].close
        return (new_close-old_close)/old_close


    
    def get_h_dn_adjusted_accumlated_return(self,nday:int=1)->float:
        d1_index=self.h_d1_index
        if self.pre_listed_news==True or len(self.company.h_pricing_history.list)<=d1_index+nday-1: 
            return None
        if nday<1: 
            print("dn can't be smaller than 1")
            return None 
    
        new_close =self.company.h_pricing_history.list[d1_index+nday-1].adjusted_close
        old_close = self.company.h_pricing_history.list[d1_index-1].adjusted_close
        return (new_close-old_close)/old_close
    
    def get_h_dn_accumlated_return(self,nday:int): 
        d1_index=self.h_d1_index
        if self.pre_listed_news==True:  
            print("This is pre-listed news")
            return None
        if len(self.company.h_pricing_history_list)<=d1_index+nday-1: 
            print("there is no Nd return data. out of bound")
            return None 
        if nday<1: 
            print("dn can't be smaller than 1")
            return None 
        new_close =self.company.h_pricing_history_list[d1_index+nday-1].close
        old_close = self.company.h_pricing_history_list[d1_index-1].close
        return (new_close-old_close)/old_close
      


    #set and get file name for downloading file
    def get_filename(self):
        return self.__filename
    
    def set_filename(self,name):
        self.__filename=name
    





    ### Downloading doc
    def download_news(self,index): 
        f_name = self.__url.split('/')[-1]
        ext_name = f_name.split('.')[-1]
        if ext_name == 'pdf': 
            self.download_news_pdf()
        elif ext_name == 'htm':
            self.download_news_htm()
        elif ext_name =='doc': 
            self.download_news_doc()
        elif ext_name=='html': 
            self.download_news_html()
        elif ext_name=='docx': 
            self.download_news_docx()
        elif ext_name=='xls':
            self.download_news_xls()
        elif ext_name=='rtf':
            self.download_news_rtf()
        else: 
            print("Error, the extension is {}".format(ext_name)+str(index))

    def download_news_pdf (self):
        if self.__filename == None: 
            print("This News has not been set a file name"+ self.get_company().get_id())
            return False
        response = requests.get(self.__url,timeout=80)
        with open(self.__filename+'.pdf','wb') as file: 
            file.write(response.content)
        return True
            
    def download_news_htm(self):
        if self.__filename == None: 
            print("This News has not been set a file name"+ self.get_company().get_id())
            return False
        response = requests.get(self.__url)
        with open(self.__filename +".htm",'w',encoding='utf-8') as file:
            file.write(response.text)
        return True

    def download_news_html(self):
        if self.__filename == None: 
            print("This News has not been set a file name"+ self.get_company().get_id())
            return False
        response = requests.get(self.__url)
        with open(self.__filename +".html",'w',encoding='utf-8') as file:
            file.write(response.text)
        return True
    def download_news_doc(self):
        if self.__filename == None: 
            print("This News has not been set a file name"+ self.get_company().get_id())
            return False
        response = requests.get(self.__url)
        with open(self.__filename +".doc",'wb') as file:
            file.write(response.content)
        return True
    def download_news_docx(self): 
        if self.__filename == None: 
            print("This News has not been set a file name"+ self.get_company().get_id())
            return False
        response = requests.get(self.__url)
        with open(self.__filename+'.docx','wb') as file:
            file.write(response.content)    
    def download_news_xls(self):
        if self.__filename == None: 
            print("This News has not been set a file name"+ self.get_company().get_id())
            return False
        response = requests.get(self.__url)
        with open(self.__filename+'.xls','wb') as file:
            file.write(response.content)  
    def download_news_rtf(self):
        if self.__filename == None: 
            print("This News has not been set a file name"+ self.get_company().get_id())
            return False
        response = requests.get(self.__url)
        with open(self.__filename+'.rtf', "wb") as f:
            f.write(response.content)

    
    ##### End of downloading doc
    #####
    ## set_state when pickle.load
    # def __setstate__(self,state):
    #     state.setdefault("date_in_date_time",None)
    #     self.__dict__.update(state)

