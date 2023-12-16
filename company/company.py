from datetime import date,datetime
import re 
import sqlite3

from utils.constant import COMPANIES_DB
from database_interface import get_company,get_index_company
class Company: 
    def __init__(self,h_code:str,a_code:str,zh_name:str,en_name:str,id:int|None=None): 
        
        """
        h_code format:4digit number with prefixing 0 and .HK 
        a_code format: 6digit number with prefixing 0 and .SH/.SZ
        """
        #hcode format:4digit number with prefixing 0 and .HK 
        self.__h_code=h_code  
        self.__a_code=a_code        
        self.__zh_name=zh_name
        self.__en_name=en_name  
        
        self.__id=id



    @property
    def h_code(self)->str: 
        return self.__h_code
    
    @property
    def a_code(self)->str:
        return self.__a_code

    @property
    def zh_name(self)->str:
        return self.__zh_name
           
    @property 
    def en_name(self)->str: 
        return self.__en_name

    @property
    def acode_yahoo_finance_format(self)->str:
        return self.__a_code.replace('SH','SS')
    
    @property
    def hcode_yahoo_finance_format(self)->str:
        return self.__h_code
    
    @property 
    def a_code_aastock_format(self)->str: 
        return self.__a_code[0:6]
    
    @property
    def h_code_aastock_format(self)->str: 
        return '0'+self.__h_code[0:4]
    
    #db
    @property
    def id(self):
        if self.__id is None: 
            raise AttributeError('id is not setted'+'/n'+self.to_dict())
        return self.__id
    
    #set function
    def set_id(self,id:int)->None:
         self.__id=id
    
    def get_digits_hcode(self)->str:
        pattern = r'[0123456789]+'
        match = re.search(pattern, self.__h_code)
        return match.group()
    
    def to_dict(self)->dict: 
        return {
            "zh_name":self.zh_name,
            "en_name":self.en_name, 
            "hcode":self.h_code,
            "acode":self.a_code,
            'id':self.__id
                }
    def to_tuple(self)->tuple:
        return(self.h_code,self.a_code,self.zh_name,self.en_name,self.__id)
    
class Keyword:
    def __init__(self,keyword:list,h_code:str,a_code:str,zh_name:str,en_name:str,id:int|None=None,company_id:int|None=None):
        self.__keyword=keyword
        self.__h_code=h_code
        self.__a_code=a_code
        self.__zh_name=zh_name
        self.__en_name=en_name
        
        self.__id=id
        self.__company_id=company_id        
    
    @property
    def keyword(self):
        return self.__keyword
    @property
    def h_code(self):
        return self.__h_code
    @property
    def a_code(self):
        return self.__a_code
    @property
    def zh_name(self):
        return self.__zh_name
    @property
    def en_name(self):
        return self.__en_name
    @property
    def keyword_str(self): 
        result=''
        for keyword in self.keyword:
            result=result+keyword+','
        return result[0:-1]
    
    #db
    @property
    def id(self):
        if self.__id is None: 
            raise AttributeError('id is not setted /n'+self.to_dict())
        return self.__id
    @property
    def company_id(self):
        if self.__company_id is None: 
            raise AttributeError('company_id is not setted /n'+self.to_dict())
        return self.__company_id
    
    #Set function
    def set_id(self,id:int)->None:
         self.__id=id
    def set_company_id(self,company_id:int)->None:
         self.__company_id=company_id
    
    
    def to_dict(self)->dict:
        return {
            'h_code':self.h_code,
            'a_code':self.a_code,
            'zh_name':self.zh_name,
            'en_name':self.en_name,
            'keyword':self.keyword_str,
            'id':self.__id,
            'company_id':self.__company_id
        } 
    def to_tuple(self)->tuple:
        return(self.keyword,self.h_code,self.a_code,self.zh_name,self.en_name,self.__id,self.__company_id)
class IndexCompany: 
    def __init__(self,flag:str,listed_region:str,index_name:str,index_code:str,id:int|None=None):
        self.__flag=flag 
        self.__listed_region=listed_region
        self.__name=index_name
        self.__code=index_code
        
        self.__id=id
    
    @property
    def flag(self):
        return self.__flag
    @property
    def listed_region(self):
        return self.__listed_region
    @property
    def name(self):
        return self.__name
    @property
    def code(self):
        return self.__code
    
    #db 
    @property
    def id(self):
        if self.__id is None: 
            raise AttributeError('id is not setted' +'/n'+ self.to_dict())
        return self.__id
    
    #set function 
    def set_id(self,id:int)->None:
         self.__id=id
    
    def to_dict(self)->dict: 
        return {
            'flag':self.flag,
            'listed_region':self.listed_region,
            'name':self.name,
            'code':self.code,
            'id':self.__id
        }
    def to_tuple(self)->tuple: 
        return (self.flag,self.listed_region,self.name,self.code,self.__id)
class Pricing:
    """
    listed_region='sz'/'sh'/'hk'
    flag(a/h)
    #date should be ISO8601 Strings YY-MM-DD
    """
    def __init__(self,date_:str,open:float,high:float,low:float,close:float,adjusted_close:float,volume:float,flag:str,listed_region:str,id:int|None=None,company_id:int|None=None,index_company_id:int|None=None) :
        if type(date_)==str: 
            self.__date_=date_
        else: 
            raise(TypeError(f"date_ should be of type str, not {type(date_)}"))
        self.__open=float(open)
        self.__high=float(high)
        self.__low=float(low)
        self.__close=float(close)
        self.__adjusted_close=float(adjusted_close)
        self.__volume=float(volume)
        self.__flag=flag
        self.__listed_region=listed_region
        
        
        #db 
        self.__id=id 
        self.__company_id=company_id
        self.__index_company_id=index_company_id

    @property
    def date(self):
        return self.__date_
    @property
    def open(self):
        return self.__open
    @property
    def high(self):
        return self.__high
    @property
    def low(self):
        return self.__low
    @property
    def close(self):
        return self.__close
    @property
    def adjusted_close(self):
        return self.__adjusted_close
    @property
    def volume(self):
        return self.__volume
    @property
    def listed_region(self):
        return self.__listed_region
    @property
    def flag(self):
        return self.__flag

    #db
    @property
    def id(self):
        if self.__id is None: 
            raise AttributeError('id is not setted'+'/n'+self.to_dict())        
        return self.__id
    @property
    def company_id(self):
        if self.__company_id is None: 
            raise AttributeError('company_id is not setted'+'/n'+self.to_dict())        
        return self.__company_id
    @property
    def index_company_id(self):
        if self.__index_company_id is None: 
            raise AttributeError('index_company_id is not setted'+'/n'+self.to_dict())                
        return self.__index_company_id
    


    #Set function 
    def set_id(self,id:int)->None:
         self.__id=id
    def set_company_id(self,company_id:int)->None:
         self.__company_id=company_id
    def set_index_company_id(self,index_company_id:int)->None:
         self.__index_company_id=index_company_id
    
    
    

    def to_dict(self)->dict: 
        return{ 
            'date':self.date,
            'open':self.open,
            'high':self.high,
            'low':self.low,
            'close ':self.close,
            'adjusted_close':self.adjusted_close,
            'volume':self.volume,
            'listed_region':self.listed_region,
            'flag':self.flag,
            'id':self.__id,
            'company_id':self.__company_id,
            'index_company_id':self.__index_company_id
               }
    def to_tuple(self)->tuple:
        return(self.date,self.open,self.high,self.low,self.close,self.adjusted_close,self.volume,self.flag,self.listed_region,self.__id,self.__company_id,self.__index_company_id)
    
    def to_db_para(self)->tuple: 
        return (self.date,self.open,self.high,self.low,self.close,self.adjusted_close,self.volume,self.flag,self.listed_region,self.__company_id,self.__index_company_id)
class Return: 
    '''
    type: 'adjusted_daily_return'
    flag: 'a'/'h'
    listed_region: 'hk','sh','sz'
    '''
    @classmethod
    def db_insert_col(cls)->str:
        return 'date,return,type,flag,listed_region,company_id,index_company_id,pricing_id'
    def __init__(self,date_:str,return_:float,type_:str,flag:str,listed_region:str,id:int|None=None,company_id:int|None=None,index_company_id:int|None=None,pricing_id:int|None=None):
        #vital attribute
        if type(date_)==str: 
            self.__date_=date_
        else: 
            raise(TypeError(f"date_ should be of type str, not {type(date_)}"))
        self.__return_=return_
        self.__type_=type_
        
        #attribute from pricing 
        self.__flag=flag
        self.__listed_region=listed_region
        
        
        #db
        self.__id=id
        self.__company_id=company_id
        self.__index_company_id=index_company_id
        self.__pricing_id=pricing_id
        
    @property
    def date_(self):
        return self.__date_
    @property
    def return_(self):
        return self.__return_
    @property
    def type_(self):
        return self.__type_
    
    @property
    def flag(self):
        return self.__flag
    @property
    def listed_region(self):
        return self.__listed_region
    
    #db
    @property
    def id(self):
        if self.__id is None:
            raise AttributeError('id is not setted /n'+self.to_dict())
        return self.__id
    @property
    def company_id(self):
        if self.__company_id is None:
            raise AttributeError('company_id is not setted /n'+self.to_dict())
        return self.__company_id
    @property
    def index_company_id(self):
        if self.__index_company_id is None:
            raise AttributeError('index_company_id is not setted /n'+self.to_dict())
        return self.__index_company_id
    
    @property
    def pricing_id(self):
        if self.__pricing_id is None:
            raise AttributeError('pricing_id is not setted /n'+self.to_dict())
        return self.__pricing_id
    
    #Set function
    def set_id(self,id:int)->None:
         self.__id=id
    def set_company_id(self,company_id:int)->None:
         self.__company_id=company_id
    def set_index_company_id(self,index_company_id:int)->None:
         self.__index_company_id=index_company_id    
    def set_pricing_id(self,pricing_id:int)->None:
         self.__pricing_id=pricing_id
    
    def to_dict(self)->dict:
        return{
            'date':self.date_,
            'return':self.return_,
            'type':self.type_,
            
            'flag':self.flag,
            'listed_region':self.listed_region,
            
            'id':self.__id,
            'company_id':self.__company_id,
            'index_company_id':self.__index_company_id,
            'pricing_id':self.__pricing_id
            }
    def to_tuple(self)->tuple:
        """to tuple row-like form

        Returns:
            tuple: date_,return_,type_,flag,listed_region,id,company_id,index_company_id,pricing_id)
        """
        return(self.date_,self.return_,self.type_,self.flag,self.listed_region,self.__id,self.__company_id,self.__index_company_id,self.__pricing_id)
    
    def to_insert_para(self)->tuple:
        """?date_,?return_,?type_,?flag,?listed_region,?company_id,?index_company_id,?pricing_id

        Returns:
            tuple: (self.date_,self.return_,self.type_,self.flag,self.listed_region,self.__company_id,self.__index_company_id,self.__pricing_id)
        """
        return(self.date_,self.return_,self.type_,self.flag,self.listed_region,self.__company_id,self.__index_company_id,self.__pricing_id)
    

class Car3: 
    @classmethod
    def db_insert_col(cls)->str: 
        return 'date,car3,flag,company_id,last_day_return_id,today_return_id,next_day_return_id'
    def __init__(self,date:str,car3:str,flag:str,id:int|None=None,company_id:int|None=None,last_day_return_id:int|None=None,today_return_id:int|None=None,next_day_return_id:int|None=None):
        self.__date=date
        self.__car3=car3 
        self.__flag=flag
        self.__id=id 
        self.__company_id=company_id
        self.__last_day_return_id=last_day_return_id
        self.__today_return_id=today_return_id
        self.__next_day_return_id=next_day_return_id
    
    @property
    def date(self):
        return self.__date
    @property
    def car3(self):
        return self.__car3
    @property
    def flag(self):
        return self.__flag
    
    #db
    @property
    def id(self):
        if self.__id is None: 
            raise AttributeError('id is not setted'+'/n'+self.to_dict())
        return self.__id    
    @property
    def company_id(self):
        return self.__company_id
    @property
    def last_day_return_id(self):
        if self.__last_day_return_id is None: 
            raise AttributeError("last_day_return_id is not setted"+'/n'+self.to_dict())
        return self.__last_day_return_id
    @property
    def today_return_id(self):
        if self.__today_return_id is None: 
            raise AttributeError("today_return_id is not setted"+'/n'+self.to_dict())
        return self.__today_return_id
    @property
    def next_day_return_id(self):
        if self.__next_day_return_id is None: 
            raise AttributeError("next_day_return_id is not setted"+'/n'+self.to_dict())
        return self.__next_day_return_id

    #set function
    def set_id(self,id:int)->None:
        self.__id=id
    def set_company_id(self,company_id:int)->None:
        self.__company_id=company_id
    
    def set_last_day_return_id(self,last_day_return_id:int)->None:
        self.__last_day_return_id=last_day_return_id
    def set_today_return_id(self,today_return_id:int)->None:
        self.__today_return_id=today_return_id
    def set_next_day_return_id(self,next_day_return_id:int)->None:
        self.__next_day_return_id=next_day_return_id
    def to_dict(self)->dict: 
        return{
             'date':self.date,
             'car3':self.car3,
             'flag':self.flag,
             
             'id':self.__id, 
             'company_id':self.__company_id,
             'last_day_return_id':self.__last_day_return_id,
             'today_return_id':self.__today_return_id,
             'next_day_return_id':self.__next_day_return_id
               }
    def to_tuple(self)->tuple: 
        return (self.date,self.car3,self.flag,self.__id,self.__company_id,self.__last_day_return_id,self.__today_return_id,self.__next_day_return_id)
    
    def to_insert_para(self)->tuple: 
        """'?date,?car3,?flag,?company_id,?last_day_return_id,?today_return_id,?next_day_return_id'

        Returns:
            tuple:(self.date,self.car3,self.flag,self.__company_id,self.__last_day_return_id,self.__today_return_id,self.__next_day_return_id)
        """
        return (self.date,self.car3,self.flag,self.__company_id,self.__last_day_return_id,self.__today_return_id,self.__next_day_return_id)
class Article:
    def __init__(self,url:str,title:str,published_at:datetime|str,api:str,content:str,id:int|None=None):
        self.__url=url 
        self.__title=title
        if type(published_at)==datetime:
            self.__published_at=published_at.isoformat()
        elif type(published_at)==str:
            self.__published_at=published_at
        else:
            raise(TypeError("published_at should be of type datetime, not{}".format(type(published_at))))
        self.__api=api
        self.__content=content        
        #db 
        self.__id=id
    
    @property
    def url(self):
        return self.__url
    @property
    def title(self):
        return self.__title
    @property
    def published_at(self):
        return self.__published_at
    @property
    def api(self):
        return self.__api
    @property
    def content(self):
        return self.__content
    #db 
    @property
    def id(self):
        if self.__id is None: 
            raise AttributeError("id is not setted /n"+self.to_dict())
        return self.__id
    
    #set function
    def set_id(self,id:int)->None:
         self.__id=id
    
    def to_dict(self)->dict: 
        return{
            'url':self.url,
            'title':self.title,
            'published_at':self.published_at,
            'api':self.api,
            'content':self.content,
            'id':self.__id
        }
    def to_tuple(self)->tuple:
        return(self.url,self.title,self.published_at,self.api,self.__content,self.__id)
    
class Tonescore:
    def __init__(self,tonescore:float,positive_score:float,negative_score:float,url:str,title:str,published_at:datetime,api:str,id:int|None=None,article_id:int|None=None):        
        self.__tonescore=tonescore
        self.__positive_score=positive_score
        self.__negative_score=negative_score
        self.__url=url 
        self.__title=title
        if type(published_at)==datetime:
            self.__published_at=published_at
        else: 
            raise(TypeError("published_at should be of type datetime, not{}".format(type(published_at))))
        self.__api=api
        
        #db 
        self.__id=id
        self.__article_id=article_id

    
    @property
    def tonescore(self):
        return self.__tonescore
    @property
    def positive_score(self):
        return self.__positive_score
    @property
    def negative_score(self):
        return self.__negative_score
    @property
    def url(self):
        return self.__url
    @property
    def title(self):
        return self.__title
    @property
    def published_at(self):
        return self.__published_at
    @property
    def api(self):
        return self.__api

    #db 
    @property
    def id(self):
        if self.__id is None: 
            raise AttributeError("id is not setted /n"+self.to_dict())
        return self.__id    
    @property
    def article_id(self):
        if self.__article_id is None: 
            raise AttributeError("article_id is not setted /n"+self.to_dict())
        return self.__article_id    
    
    #set function 
    def set_id(self,id:int)->None:
        self.__id=id
    def set_article_id(self,article_id:int): 
        self.__article_id=article_id
                    
    def to_dict(self)->dict: 
        return {
            'tonescore':self.tonescore,
            'positive_tonescore':self.positive_score,
            'negative_tonescore':self.negative_score,
            'url':self.url, 
            'title':self.title,
            'published_at':self.published_at,
            'api':self.api,
            'id':self.__id,
            'article_id':self.__article_id,
                }

class MetionIn:
    def __init__(self,url:str,h_code:str,id:int|None=None,article_id:int|None=None,company_id:int|None=None):        
        self.__url=url
        self.__h_code=h_code
        
        self.__id=id
        self.__article_id=article_id
        self.__company_id=company_id
        
    @property
    def url(self):
        return self.__url
    @property
    def h_code(self):
        return self.__h_code
    
    #db
    @property
    def id(self):
        if self.__id is None: 
            raise AttributeError('id is not setted'+'/n'+self.to_dict())        
        return self.__id
    @property
    def article_id(self):
        if self.__id is None: 
            raise AttributeError('article_id is not setted'+'/n'+self.to_dict())        
        return self.__article_id
    @property
    def company_id(self):
        if self.__id is None: 
            raise AttributeError('company_id is not setted'+'/n'+self.to_dict())        
        return self.__company_id
    
    #set function
    def set_id(self,id:int)->None:
         self.__id=id
    def set_article_id(self,article_id:int)->None:
         self.__article_id=article_id
    def set_company_id(self,company_id:int)->None:
         self.__company_id=company_id
    
    def to_dict(self)->dict: 
        return {
            'url':self.url,
            'h_code':self.h_code,
            
            'id':self.__id,
            'article_id':self.__article_id,
            'company_id':self.__company_id
        }
    def to_tuple(self)->tuple:
        return(self.url,self.h_code,self.__id,self.__article_id,self.__company_id)
    

class Affecting:
    def __init__(self,url:str,type_:str,flag:str,listed_region:str,h_code:str,id:int|None=None,article_id:int|None=None,return_id:int|None=None): 
        self.__url=url
        self.__type_=type_
        self.__flag=flag         
        self.__listed_region=listed_region
        self.__h_code=h_code
        
        self.__id=id
        self.__article_id=article_id
        self.__return_id=return_id

    @property
    def url(self):
        return self.__url

    @property
    def type_(self): 
        return self.__type_
    @property
    def flag(self):
        return self.__flag
    @property
    def listed_region(self):
        return self.__listed_region
        
    @property
    def h_code(self):
        return self.__h_code

    #db
    @property
    def id(self):
        if self.__id is None: 
            raise AttributeError('id is not setted'+'/n'+self.to_dict())
        return self.__id
    @property
    def article_id(self):
        if self.__id is None: 
            raise AttributeError('article_id is not setted'+'/n'+self.to_dict())
        return self.__article_id
    @property
    def return_id(self):
        if self.__id is None: 
            raise AttributeError('return_id is not setted'+'/n'+self.to_dict())
        return self.__return_id
    
    #set function 
    def set_id(self,id:int)->None:
         self.__id=id
    def set_article_id(self,article_id:int)->None:
         self.__article_id=article_id
    def set_return_id(self,return_id:int)->None:
         self.__return_id=return_id
    
    def to_dict(self)->dict: 
        return{
            'url':self.url,
            'type':self.type_,
            'flag':self.flag,
            'listed_region':self.listed_region,
            'h_code':self.h_code,
            
            'id':self.__id,
            'article_id':self.__article_id,
            'return_id':self.__return_id
        }
    def to_tuple(self)->tuple: 
        return (self.url,self.type_,self.flag,self.listed_region,self.h_code,self.__id,self.__article_id,self.__return_id)
    
# commit list to database
def index_companies2db(index_companies:list[tuple],db_path=COMPANIES_DB)->None: 
    """commit index_companies to database 
    Args:
        index_companies (list[tuple]): each tuple represent one index_company entity, (flag,listed_region,name,code)
        db_path (_type_, optional): sqlite3 database file path. Defaults to COMPANIES_DB.
    """
    con=sqlite3.connect(db_path)
    c=con.cursor()
    for index_company in index_companies: 

        c.execute('''
                  INSERT INTO index_company(flag,listed_region,name,code)
                  VALUES(?flag,?listed_region,?name,?code)
                  ''',index_company
                  )
    con.commit()
    
    c.close()
    con.close()
    
def companies2db(companies:list[tuple],db_path=COMPANIES_DB)->None: 
    """commit companies to database 
    Args:
        companies (list[tuple]): each tuple represent one company entity, (h_code,a_code,zh_name,en_name)
        db_path (_type_, optional): sqlite3 database file path. Defaults to COMPANIES_DB.
    """
    con=sqlite3.connect(db_path)
    c=con.cursor()
    for company in companies: 
        c.execute('''INSERT INTO company(h_code,a_code,zh_name,en_name) VALUES(?h_code,?a_code,?zh_name,?en_name)''',company)
    con.commit()
    c.close()
    con.close()
    
def keywords2db(keywords:list[tuple],db_path=COMPANIES_DB)->None:
    """commit keywords to database
    Args:
        keywords (list[tuple]): each tuple represent one keword weak entity, (keyword,h_code,a_code,zh_name,en_name)
        db_path (_type_, optional): sqlite3 database file path. Defaults to COMPANIES_DB.
    """
    con=sqlite3.connect(db_path)
    c=con.cursor()
    for keyword in keywords: 
        company_attri=keyword[1:]
        company_id=c.execute('''
                             SELECT company_id 
                             FROM company 
                             WHERE hcode=?hcode,a_code=?a_code,zh_name=?zh_name,en_name=?en_name
                             ''',company_attri).fetchall()[0][0]
        data=list(keyword).append(company_id)
        c.execute('''
                  INSERT INTO keyword(keywords,h_code,a_code,zh_name,en_name,company_id)
                  VALUES(?keywords,?h_code,?a_code,?zh_name,?en_name,company_id                  
                  ''',data)
    con.commit()
    c.close()
    con.close()
        



def pricing2db(pricing_list:list[tuple],db_path=COMPANIES_DB): 
    """commit pricings to database

    Args:
        pricing_list (list[tuple]): each tuple represent one pricing weak entity, (date,open,high,low,close,adjusted_close,volume,flag,listed_region,company_id,index_company_id)
        db_path (_type_, optional): sqlite3 database file path. Defaults to COMPANIES_DB.
    """
    con=sqlite3.connect(db_path)
    c=con.cursor()
    
    for pricing in pricing_list: 
        c.execute('''
                  INSERT INTO TABLE pricing(date,open,high,low,close,adjusted_close,volume,flag,listed_region,company_id,index_company_id)
                  VALUES(?date,?open,?high,?low,?close,?adjusted_close,?volume,?flag,?listed_region,?company_id,?index_company_id)
                  ''',pricing) 
    con.commit()
    c.close()
    con.close()
    
    
    
# read from source
def read_and_commit_companies_from_csv(filename:str,db_path=COMPANIES_DB)->None: 
    """read companies info from csv and commit it to database
    Args:
        filename (str): the csv filename
        db_path (_type_, optional): sqlite3 database file path. Defaults to COMPANIES_DB.
    """
    import csv
    result_company=[]
    result_keyword=[]
    with open(filename,'r') as f: 
        reader=csv.reader(f)
        reader.__next__()
        for row in reader: 
            en_name,h_code,a_code,zh_name,keywords=row[0],row[1],row[2],row[3],row[4:]
            result_company.append((h_code,a_code,zh_name,en_name))
            result_keyword.append((keywords,h_code,a_code,zh_name,en_name))
    companies2db(result_company,db_path)
    keywords2db(result_keyword,db_path)
            

def read_and_commit_index_company_from_csv(filename:str,db_path=COMPANIES_DB)->None:
    """read index_company information from csv file and commit it to database
        expect a csv file with column name:flag,listed_region,name,code
        e.g. H,HK,HANG SENG CHINA ENTERPRISES IND,HSCE
             A,SH,SSE Composite Index,SSE
    Args:
        filename (str): The filename of the csv file
        db_path (_type_, optional): sqlite3 database file path. Defaults to COMPANIES_DB.

    """
    import csv 
    result_indexcompany=[]
    with open(filename,'r') as f: 
        reader=csv.reader(f)
        reader.__next__()
        for row in reader: 
            flag,listed_region,name,code=row[0].lower(),row[1].lower(),row[2].lower(),row[3].lower()
            result_indexcompany.append((flag,listed_region,name,code))
    index_companies2db(result_indexcompany,db_path)


def read_and_commit_pricing_from_a_directory(foldername:str,db_path=COMPANIES_DB)->None: 
    """read shock pricing data from a folder and commit it to databases
    expecting a csv file with column of order Date,Open,High,Low,Close,Adj Close,Volume
    expecting with pricing data from company having filename =a_code.csv|h_code.csv
    expecting with pricing data from index_company having filename= index_%code%.csv, where %code% is the code of the index_company
    Args:
        foldername (str): The folder path where all subfolders contain the csv files
        db_path (_type_, optional): sqlite3 database file path. Defaults to COMPANIES_DB.

    """
    import os
    import glob
    import pandas as pd
    csv_files = [file for file in glob.glob(os.path.join(foldername, '**/*.csv'), recursive=True)]
    #csv_files=[file for file in os.listdir(foldername) if file.endswith('.csv')]
    all_pricing=[]
    con=sqlite3.connect(db_path)
    c=con.cursor()
    
    for csv_file in csv_files: 
        file_path=os.path.join(foldername,csv_file)
        data_=pd.read_csv(file_path)
        #Get h_code/a_code information from filename
        listed_region=csv_file[-6:-4]

        if csv_file.startswith('index_'): 
            index_code=csv_file.split('.csv')[0][6:]
            resulting_row=[None,None,None,None]
            index_resulting_row=get_index_company(code=index_code)
        elif listed_region.upper()=='HK': 
            flag='h'
            h_code=csv_file[0:-6]
            resulting_row=get_company(h_code=h_code,warning=True)
            index_resulting_row=(None,None,None,None)
        elif listed_region.upper()=='SZ' or listed_region.upper()=='SH':             
            flag='a'
            a_code=csv_file[0:-6]
            resulting_row=get_company(a_code=a_code,warning=True)
            index_resulting_row=(None,None,None,None)
        else: 
            raise(ValueError(f'The folderpath{foldername} contain csv with wrong filename {csv_file}'))
        
        flag,listed_region,index_name,index_code,index_company_id =index_resulting_row
        h_code,a_code,zh_name,en_name,company_id=resulting_row
        
        for index_i,row in data_.iterrows():             
            all_pricing.append((row.iloc[0],row.iloc[1],row.iloc[2],row.iloc[3],row.iloc[4],row.iloc[5],row.iloc[6],flag,listed_region,company_id,index_company_id))
        
    pricing2db(all_pricing)
    c.close()
    con.close()
    return all_pricing 

    
