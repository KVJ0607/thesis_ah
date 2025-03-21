from datetime import datetime
from datetime import date as c_date
import re 
from collections import Counter

from utils.basic import is_iso_format
from utils.constant import COMPANIES_DB
from master_dictionary.master_dictionary import MasterDictionary

class Company: 
    REFERENCE_TABLE={}
    
    @classmethod
    def rational_representation(cls)->str:
        return 'company'
    
    @classmethod 
    def attribute_in_col_string(cls)->str:
        return 'company(h_code,a_code,zh_name,en_name)'
    
    @classmethod
    def db_insert_col(cls) ->str:
        """generate the sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        return """INSERT INTO company(h_code,a_code,zh_name,en_name)
                VALUES(?,?,?,?)
                """        
    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        return """INSERT OR IGNORE INTO company(h_code,a_code,zh_name,en_name)
                VALUES(?,?,?,?)
                """ 
    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
        return result 
    
    @classmethod
    def reformat_h_code(cls,h_code:str): 
        partition=h_code.split('.')
        if len(partition)==1: 
            h_code=h_code+'.hk'
        numeric_code=h_code.split('.')[0]
        if len(numeric_code)==4: 
            h_code='0'+h_code
        return h_code.lower()
    
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
        
    @classmethod
    def from_tuple(cls,cp_tuple)->'Company':
        if len(cp_tuple)==5 :
            h_code,a_code,zh_name,en_name,id_=cp_tuple
        elif len(cp_tuple)==4: 
            h_code,a_code,zh_name,en_name=cp_tuple
            id_=None
            
        result=Company(h_code,a_code,zh_name,en_name,id_)
        return result        

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
            raise AttributeError('id is not setted')
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
        """
        result[tuple]:h_code,a_code,zh_name,en_name,id
        """
        return(self.h_code,self.a_code,self.zh_name,self.en_name,self.__id)
    
    def to_insert_para(self)->tuple: 
        """?h_code,?a_code,?zh_name,?en_name

        Returns:
            tuple: (self.h_code,self.a_code,self.zh_name,self.en_name)
        """
        return (self.h_code,self.a_code,self.zh_name,self.en_name)

class CompanyMining:
    REFERENCE_TABLE={
        'company':[('id','company_id')]
    }
    @classmethod
    def rational_representation(cls)->str: 
        return 'company_mining'   

    @classmethod 
    def attribute_in_col_string(cls)->str:
        pass
    
    @classmethod
    def db_insert_col(cls)->str: 
        """generate the sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        return """INSERT INTO company_mining(document_flag,gnews_flag,company_id)
                VALUES(?,?,?)
                """  
                
    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        return """INSERT OR IGNORE INTO company_mining(document_flag,gnews_flag,company_id)
                VALUES(?,?,?)
                """ 
    
    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f"the main table{main_table_rr} is not linked to {cls}"))
        return result 
        
    def __init__(self,document_flag:int=0,gnews_flag:int=0,id:int|None=None,company_id:int|None=None): 
        self.__document_flag=document_flag 
        self.__gnews_flag=gnews_flag
        self.__id=id 
        self.__company_id=company_id
    
    @classmethod
    def from_tuple(cls,*tuple)->'CompanyMining':
        col=list(*tuple)
        if len(col)==4: 
            document_flag,gnews_flag,id_,company_id=col[0],col[1],col[2],col[3]
        elif len(col)==3: 
            document_flag,gnews_flag,company_id=col[0],col[1],col[2]
            id_=None
        result=CompanyMining(document_flag,gnews_flag,id_,company_id)
        return result
    
    @property
    def document_flag(self):
        return self.__document_flag
    @property
    def gnews_flag(self):
        return self.__gnews_flag
    @property
    def id(self):
        if self.__id==None: 
            raise(AttributeError('self.__id is not setted'))
        return self.__id
    @property
    def company_id(self):
        if self.__company_id==None:
            raise(AttributeError('self.__company_id is not setted'))
        return self.__company_id
    
    def set_id(self,id_:int): 
        self.__id=id_
        
    def set_company_id(self,company_id:int): 
        self.__company_id=company_id
    
    def to_dict(self)->dict: 
        return {
            "document_flag":self.document_flag,
            "gnews_flag":self.gnews_flag, 
            "id":self.__id,
            "company_id":self.__company_id,
        }
        
    def to_tuple(self)->tuple:
        """
        result[tuple]:document_flag,gnews_flag,id,company_id
        """
        return(self.document_flag,self.gnews_flag,self.__id,self.__company_id)
    
    def to_insert_para(self)->tuple: 
        """?document_flag,?gnews_flag,?company_id

        Returns:
            tuple: (self.document_flag,self.gnews_flag,self.__company_id)
        """
        return (self.document_flag,self.gnews_flag,self.__company_id)
class Keyword:
    REFERENCE_TABLE={
        'company':[('id','company_id')]
    }
    
    @classmethod
    def rational_representation(cls)->str:
        return 'keyword'

    @classmethod 
    def attribute_in_col_string(cls)->str:
        pass
    
    @classmethod
    def db_insert_col(cls)->str: 
        """generate the sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        sql="""INSERT INTO keyword(keyword,company_id)
                VALUES(?,?)"""
        return sql
    
    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        sql="""INSERT OR IGNORE INTO keyword(keyword,company_id)
                VALUES(?,?)"""
        return sql
    
    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
        return result 
        
    def __init__(self,keyword:str,id:int|None=None,company_id:int|None=None):
        self.__keyword=keyword        
        self.__id=id
        self.__company_id=company_id       
    
    @classmethod
    def from_tuple(cls,keyword_tuple:tuple)->'Keyword':
        if len(keyword_tuple)==3: 
            keyword,id_,company_id=keyword_tuple
            
        elif len(keyword_tuple)==2:
            keyword,company_id=keyword_tuple
            id_=None
        else: 
            raise(ValueError(f"keyword tuple {keyword_tuple} should either have length of 3 or 2"))
        result=Keyword(keyword,id_,company_id)
        return result
        
    
    @property
    def keyword(self):
        return self.__keyword
    @property
    def keyword(self):
        return self.__keyword
    
    
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
            'keyword':self.keyword,
            'id':self.__id,
            'company_id':self.__company_id
        } 
    def to_tuple(self)->tuple:
        """
        return: (keyword,id,company_id)
        """
        return(self.keyword,self.__id,self.__company_id)
    
    def to_insert_para(self)->tuple: 
        """ ?keyword,?company_id)

        Returns:
            tuple: (keyword,company_id)
        """
        return (self.keyword,self.company_id)
    
class IndexCompany: 
    REFERENCE_TABLE={}
    
    @classmethod
    def rational_representation(cls)->str:
        return 'index_company'    

    @classmethod 
    def attribute_in_col_string(cls)->str:
        pass
    
    @classmethod
    def db_insert_col(cls)->str: 
        """generate the sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        sql="""INSERT INTO index_company(flag,listed_region,name,code)
                VALUES(?,?,?,?)"""
        return sql

    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        sql="""INSERT OR IGNORE INTO index_company(flag,listed_region,name,code)
                VALUES(?,?,?,?)"""
        return sql
    
    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
        return result 
        
    def __init__(self,flag:str,listed_region:str,name:str,code:str,id:int|None=None):
        self.__flag=flag 
        self.__listed_region=listed_region 
        self.__name=name
        self.__code=code #hsce,sse,szse
        
        self.__id=id
        
    @classmethod
    def from_tuple(cls,cp_tuple:tuple)->'IndexCompany':
        if len(cp_tuple)==5: 
            flag_,listed_region,name_,code_,id_=cp_tuple
        elif len(cp_tuple)==4: 
            flag_,listed_region,name_,code_=cp_tuple
            id_=None
        result=IndexCompany(flag_,listed_region,name_,code_,id_)
        return result
    
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
        """
        return (flag,listed_region,name,code,id)
        """
        return (self.flag,self.listed_region,self.name,self.code,self.__id)
    
    def to_insert_para(self)->tuple: 
        """ ?flag,?listed_region,?name,?code)

        Returns:
            tuple: (flag,listed_region,name,code)
        """
        return (self.flag,self.listed_region,self.name,self.code)
    
class Pricing:
    """
    listed_region='sz'/'sh'/'hk'
    flag(a/h)
    #date should be ISO8601 Strings YY-MM-DD
    """
    REFERENCE_TABLE={
        'company':[('id','company_id')],
        'index_company':[('id','index_company_id')]
    }
    
    @classmethod
    def rational_representation(cls)->str:
        return 'pricing'  

    @classmethod 
    def attribute_in_col_string(cls)->str:
        pass
    
    @classmethod
    def db_insert_col(cls)->str: 
        """generate the sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        sql="""INSERT INTO pricing(date,open,high,low,close,adjusted_close,volume,flag,listed_region,company_id,index_company_id)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)"""                
        return sql

    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        sql="""INSERT OR IGNORE INTO pricing(date,open,high,low,close,adjusted_close,volume,flag,listed_region,company_id,index_company_id)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)"""                
        return sql
    
    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
        return result 
      
    def __init__(self,date_:str,open:float,high:float,low:float,close:float,adjusted_close:float,volume:float,flag:str,listed_region:str,id:int|None=None,company_id:int|None=None,index_company_id:int|None=None) :
        if type(date_)==str: 
            self.__date_=date_
        else: 
            raise(TypeError(f"date_ should be of type str, not {type(date_)}"))
        self.__open=float(open)
        self.__high=float(high)
        self.__low=float(low)
        self.__close=float(close)
        if adjusted_close is not None:
            self.__adjusted_close=float(adjusted_close)
        else: 
            self.__adjusted_close=None
            
        self.__volume=float(volume)
        self.__flag=flag #a,h
        self.__listed_region=listed_region ##sh,sz,hk
            
        #db 
        self.__id=id 
        self.__company_id=company_id
        self.__index_company_id=index_company_id
    
    @classmethod
    def from_tuple(self,pricing_tuple:tuple)->'Pricing': 
        if len(pricing_tuple)==12: 
            date_,open_,high_,low_,close_,adjusted_close_,volume_,flag_,listed_region_,id_,company_id_,index_company_id_=pricing_tuple
        elif len(pricing_tuple)==11: 
            date_,open_,high_,low_,close_,adjusted_close_,volume_,flag_,listed_region_,company_id_,index_company_id_=pricing_tuple
            id_=None
        else:
            raise(ValueError(f"length of pricing_tuple {pricing_tuple}should be either 11 or 12 "))
        result=Pricing(date_,open_,high_,low_,close_,adjusted_close_,volume_,flag_,listed_region_,id_,company_id_,index_company_id_)
        return result 
    
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
            mes='company_id is not setted'
            raise AttributeError(mes)        
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
        """
        return[tuple]: (date,open,high,low,close,adjusted_close,volume,flag,listed_region,id,company_id,index_company_id)
        """
        return(self.date,self.open,self.high,self.low,self.close,self.adjusted_close,self.volume,self.flag,self.listed_region,self.__id,self.__company_id,self.__index_company_id)
    
    def to_insert_para(self)->tuple: 
        """
        ?date,?open,?high,?low,?close,?adjusted_close,?volume,?flag,?listed_region,?company_id,?index_company_id
        
        return[tuple]: (self.date,self.open,self.high,self.low,self.close,self.adjusted_close,self.volume,self.flag,self.listed_region,self.__company_id,self.__index_company_id)
        """
        return (self.date,self.open,self.high,self.low,self.close,self.adjusted_close,self.volume,self.flag,self.listed_region,self.__company_id,self.__index_company_id)
class Return: 
    '''
    type: 'adjusted_daily_return'
    flag: 'a'/'h'
    listed_region: 'hk','sh','sz'
    '''
    REFERENCE_TABLE={
        'company':[('id','company_id')],
        'index_company':[('id','index_company_id')],
        'pricing':[('id','pricing_id')]
    }
    
    @classmethod
    def rational_representation(cls)->str:
        return 'return'    

    @classmethod 
    def attribute_in_col_string(cls)->str:
        pass
    
    @classmethod
    def db_insert_col(cls)->str:
        """generate the sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        sql="""INSERT INTO return(date,return,type,flag,listed_region,company_id,index_company_id,pricing_id)
                VALUES(?,?,?,?,?,?,?,?)"""
        return sql 

    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        sql="""INSERT OR IGNORE INTO return(date,return,type,flag,listed_region,company_id,index_company_id,pricing_id)
                VALUES(?,?,?,?,?,?,?,?)"""
        return sql 
    
    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
        return result 
        
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
    
    @classmethod
    def from_tuple(self,return_tuple:tuple)->'Return': 
        if len(return_tuple)==9: 
            date,return_,type,flag,listed_region,id_,company_id,index_company_id,pricing_id=return_tuple
        elif len(return_tuple)==8: 
            date,return_,type,flag,listed_region,company_id,index_company_id,pricing_id=return_tuple
            id_=None
        else: 
            raise(ValueError(f'return_tuple {return_tuple} should either have length 8 or 9'))
        result=Return(date,return_,type,flag,listed_region,id_,company_id,index_company_id,pricing_id)
        return result
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
    REFERENCE_TABLE={
        'company':[('company_id')],
        'return': [('id','last_day_return_id'),('id','today_return_id'),('id','next_day_return_id')]
    }
    @classmethod
    def rational_representation(cls)->str:
        return 'car3'     

    @classmethod 
    def attribute_in_col_string(cls)->str:
        pass
    
    @classmethod
    def db_insert_col(cls)->str: 
        """generate the snippet of sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        sql="""INSERT INTO car3(date,car3,flag,company_id,last_day_return_id,today_return_id,next_day_return_id)
                VALUES(?,?,?,?,?,?,?)"""        
        return sql

    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        sql="""INSERT OR IGNORE INTO car3(date,car3,flag,company_id,last_day_return_id,today_return_id,next_day_return_id)
                VALUES(?,?,?,?,?,?,?,?)"""        
        return sql
    
    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
        return result 
    
    def __init__(self,date:str,car3:str,flag:str,id:int|None=None,company_id:int|None=None,last_day_return_id:int|None=None,today_return_id:int|None=None,next_day_return_id:int|None=None):
        self.__date=date
        self.__car3=car3 
        self.__flag=flag
        self.__id=id 
        self.__company_id=company_id
        self.__last_day_return_id=last_day_return_id
        self.__today_return_id=today_return_id
        self.__next_day_return_id=next_day_return_id
    
    @classmethod
    def from_tuple(self,car3_tuple:tuple)->'Car3': 
        if len(car3_tuple)==8: 
            date_,car3_,flag_,id_,company_id,ldr_id,tr_id,ndr_id=car3_tuple
        elif len(car3_tuple)==7: 
            date_,car3_,flag_,company_id,ldr_id,tr_id,ndr_id=car3_tuple
            id_=None
        else: 
            raise(ValueError(f'car3_tuple {car3_tuple} should either have len 7 or 8'))
        result=Car3(date_,car3_,flag_,id_,company_id,ldr_id,tr_id,ndr_id)
        return result
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
        """
        return[tuple]: (date,car3,flag,id,company_id,last_day_return_id,today_return_id,next_day_return_id)
        """
        return (self.date,self.car3,self.flag,self.__id,self.__company_id,self.__last_day_return_id,self.__today_return_id,self.__next_day_return_id)
    
    def to_insert_para(self)->tuple: 
        """'?date,?car3,?flag,?company_id,?last_day_return_id,?today_return_id,?next_day_return_id

        Returns:
            tuple:(self.date,self.car3,self.flag,self.__company_id,self.__last_day_return_id,self.__today_return_id,self.__next_day_return_id)
        """
        return (self.date,self.car3,self.flag,self.__company_id,self.__last_day_return_id,self.__today_return_id,self.__next_day_return_id)
    

class Car3Dual:
    REFERENCE_TABLE={
        'car3':[('id','acar3_id'),('id','hcar3_id')]
    }
    def rational_representation(cls)->str:
        return 'car3_dual'     

    @classmethod 
    def attribute_in_col_string(cls)->str:
        pass

    @classmethod
    def db_insert_col(cls)->str: 
        """generate the snippet of sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        sql="""INSERT INTO car3_dual(acar3_id,hcar3_id,date)
                VALUES(?,?,?)"""        
        return sql

    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        sql="""INSERT OR IGNORE INTO car3_dual(acar3_id,hcar3_id,date)
                VALUES(?,?,?)"""                       
        return sql
    
    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
        return result 
        
    def __init__(self,acar3_id:int,hcar3_id:int,date:str|datetime|c_date,id_=None): 
        if type(acar3_id) != int or type(hcar3_id) != int: 
            mes_="acar3_id {} or hcar3_id {} is not of type int".format(acar3_id,hcar3_id)
            raise(TypeError(mes_))
        if type(date)!= str and type(date)!=datetime and type(date)!=c_date:
            mes_="date {} is not the right type".format(date)
            raise(TypeError(mes_))
        self.__acar3_id=acar3_id
        self.__hcar3_id=hcar3_id
        self.__date=date
        self.__id=id_

    @classmethod
    def from_tuple(self,car3dual_tuple:tuple)->'Car3Dual': 
        if len(car3dual_tuple)==4: 
            acar3_id,hcar3_id,date,id_=car3dual_tuple
        elif len(car3dual_tuple)==3: 
            acar3_id,hcar3_id,date=car3dual_tuple
            id_=None
        else: 
            raise(ValueError(f'car3dual_tuple {car3dual_tuple} should either have len 3 or 4'))
        result=Car3Dual(acar3_id,hcar3_id,date,id_)
        return result
    
    @property
    def acar3_id(self):
        if self.__acar3_id is None: 
            mes_='acar3_id is not setted'+'/n'+self.to_dict()
            raise AttributeError(mes_)               
        return self.__acar3_id
    
    @property
    def hcar3_id(self):
        if self.__hcar3_id is None: 
            mes_='hcar3_id is not setted'+'/n'+self.to_dict()
            raise AttributeError(mes_)        
        return self.__hcar3_id
    
    @property
    def date(self):
        return self.__date
    @property
    def id(self):
        if self.__id is None: 
            mes_='id is not setted'+'/n'+self.to_dict()
            raise AttributeError(mes_)        
        return self.__id
    
    def set_acar3_id(self,acar3_id_:int)->None:
        self.__acar3_id=acar3_id_
    
    def set_hcar3_id(self,hcar3_id_:int)->None:
        self.__hcar3_id=hcar3_id_
    
    def set_date(self,date_:str|datetime|c_date)->None:        
        if type(date_)==datetime or type(date_)==c_date:
            self.__date=date_.isoformat()
        elif type(date_)==str:
            self.__date=date_
        else:
            print("Warning in set_date: date should be of type datetime, not{}".format(type(date_)))
            print(f"url{self.url}")
            self.__date=None
                    
    
    def set_id(self,id_:int )->None:
        self.__id=id_
    
    def to_dict(self)->dict: 
        return{
            'acar3_id':self.__acar3_id,
            'hcar3_id':self.__hcar3_id,
            'date':self.date,
            'id':self.__id, 
        }
    def to_tuple(self)->tuple: 
        """
        return[tuple]: (acar3_id,hcar3_id,date,id)
        """
        return (self.__acar3_id,self.__hcar3_id,self.date,self.__id)
    
    def to_insert_para(self)->tuple: 
        """'?date,?car3,?flag,?company_id,?last_day_return_id,?today_return_id,?next_day_return_id

        Returns:
            tuple:(acar3_id,hcar3_id,date)
        """
        return (self.__acar3_id,self.__hcar3_id,self.date)
    
    
class Article:
    REFERENCE_TABLE={}
    @classmethod
    def rational_representation(cls)->str:
        return 'article'    

    @classmethod 
    def attribute_in_col_string(cls)->str:
        pass
    
    @classmethod
    def db_insert_col(cls)->str: 
        """generate the sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        sql="""INSERT INTO article(url,title,published_at,api,content)
                VALUES(?,?,?,?,?)"""
        return sql

    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        sql="""INSERT OR IGNORE INTO article(url,title,published_at,api,content)
                VALUES(?,?,?,?,?)"""    
        return sql
    
    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
        return result 
        
    def __init__(self,url:str,title:str,published_at:datetime|str,api:str,content:str,id:int|None=None):
        self.__url=url 
        self.__title=title
        if type(published_at)==datetime:
            self.__published_at=published_at.isoformat()
        elif type(published_at)==str:
            self.__published_at=published_at
        elif published_at==None: 
            self.__published_at=None
        else:
            raise(TypeError("published_at should be of type datetime, not{}".format(type(published_at))))
        self.__api=api
        self.__content=content        
        #db 
        self.__id=id
    
    @classmethod
    def from_tuple(self,article_tuple:tuple)->'Article': 
        if len(article_tuple)==7:
            url_,title_,published_at_,api_,content_,id_=article_tuple
        elif len(article_tuple)==6:
            url_,title_,published_at_,api_,content_=article_tuple
            id_=None
        else: 
            raise(ValueError(f'article_tuple {article_tuple} should either have len of 7 or 6'))
        result=Article(url_,title_,published_at_,api_,content_,id_)
        return result
    
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
        """
        url,title,published_at,api,content,id
        """
        return(self.url,self.title,self.published_at,self.api,self.content,self.__id)
    
    def to_insert_para(self)->tuple:
        """
        ?url,?title,?published_at,?api,?query,?content
        return[tuple]: (self.url,self.title,self.published_at,self.api,self.query,self.content)
        """
        return (self.url,self.title,self.published_at,self.api,self.content)
    
    def get_tonescore(self)->'Tonescore': 
        from master_dictionary.master_dictionary import MasterDictionary,load_masterdictionary,ToneNertral
        master_dict=load_masterdictionary('data/master_dictionary/Loughran-McDonald_MasterDictionary_1993-2021.csv',)
        content=self.content
        
        counter = Counter()
        tone_score=0
        positive_tonescore=0 
        negative_tonescore=0 
        words_text=content.split()
        counter.update(words_text)
        
        for word,word_count in counter.items(): 
            word=word.upper()
            result=master_dict.get(word,ToneNertral)
            positive_flag=int(result.positive)
            negative_flag=int(result.negative)
            strong_modal_flag=int(result.strong_modal)
            weak_modal_flag=int(result.weak_modal)
            if positive_flag>0 and strong_modal_flag>0:
                positive_tonescore=positive_tonescore+2*word_count
            elif positive_flag>0 and weak_modal_flag>0: 
                positive_tonescore=positive_tonescore+0.5*word_count
            elif positive_flag>0: 
                positive_tonescore=positive_tonescore+1*word_count
            elif negative_flag>0 and strong_modal_flag>0: 
                negative_tonescore=negative_tonescore+2*word_count
            elif negative_flag>0 and weak_modal_flag>0: 
                negative_tonescore=negative_tonescore+0.5 *word_count
            elif negative_flag>0: 
                negative_tonescore=negative_tonescore+1*word_count
        tone_score=positive_tonescore-negative_tonescore
        result=Tonescore(tone_score,positive_tonescore,negative_tonescore,self.url,self.title,self.published_at,self.api,None,self.id,None)
        return result
            

class Query:
    REFERENCE_TABLE={}
    @classmethod
    def rational_representation(cls)->str:
        return 'query'    

    @classmethod 
    def attribute_in_col_string(cls)->str:
        pass
    
    @classmethod
    def db_insert_col(cls)->str: 
        """generate the sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        sql="""INSERT INTO query(query,article_id)
                VALUES(?,?)"""
        return sql 

    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        sql="""INSERT OR IGNORE INTO query(query,article_id)
                VALUES(?,?)"""
        return sql 
    
    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
        return result 
        
    def __init__(self,query:str,id_:int|None=None, article_id:int|None=None): 
        self.__query=query
        self.__id=id_
        self.__article_id=article_id
    @classmethod        
    def from_tuple(cls,query_tuple:tuple)->'Query':
        if len(query_tuple)==3:
            query,id_,article_id_=query_tuple
        elif len(query_tuple)==2:
            query,article_id_
            id_=None
        else: 
            raise(ValueError(f'article_tuple {query_tuple} should either have len of 7 or 6'))
        result=Query(query,id_,article_id_)
        return result
    @property
    def query(self):
        return self.__query
    @property
    def id(self):
        return self.__id
    @property
    def article_id(self):
        return self.__article_id

    def to_dict(self)->dict: 
        return{
            'query':self.query, 
            'id':self.__id,
            'article_id':self.__article_id
        }
        
    def to_tuple(self)->tuple:
        """
        query,id,article_id
        """
        return self.query,self.__id,self.__article_id
    
    def to_insert_para(self)->tuple:
        """
        ?query,?article_id
        return[tuple]: (self.query,self.article_id)
        """
        return (self.query,self.article_id)
    
class Document:
    REFERENCE_TABLE={
        'company':[('id','company_id')]
    }
    @classmethod
    def rational_representation(cls)->str:
        return 'document'    

    @classmethod 
    def attribute_in_col_string(cls)->str:
        pass
    
    @classmethod
    def db_insert_col(cls)->str: 
        """generate the sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        sql="""INSERT INTO document(url,title,published_at,source,content,company_id)
                VALUES(?,?,?,?,?,?)"""
        return sql 

    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        sql="""INSERT OR IGNORE INTO document(url,title,published_at,source,content,company_id)
                VALUES(?,?,?,?,?,?)"""
        return sql 

    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
        return result 
        
    def __init__(self,url:str,title:str,published_at:datetime|str,source:str,content:str,id:int|None=None,company_id:int|None=None):
        self.__url=url 
        self.__title=title
        
        if type(published_at)==datetime and published_at is not None:
            self.__published_at=published_at.isoformat()
        elif type(published_at)==str and is_iso_format(published_at) and published_at is not None:            
            self.__published_at=published_at
        elif published_at is None:
            self.__published_at=None
        else:
            message=f"published_at should be string or in isoformat,not {published_at}"
            print(message)
            raise(ValueError(message))
            #self.__published_at=published_at
          
        self.__source=source
        if type(content)==str or content==None: 
            self.__content=content         
        else: 
            message_="content should be of type str not {}".format(type(content))
            raise(TypeError(message_)) 
        #db 
        self.__id=id
        self.__company_id=company_id
    @classmethod
    def from_url(self,url:str)->'Document':
        return Document(url,None,None,None,None,None,None)
        
    @classmethod
    def from_tuple(self,article_tuple:tuple)->'Document': 
        if len(article_tuple)==7:
            url_,title_,published_at_,api_,content_,id_,company_id_=article_tuple
        elif len(article_tuple)==6:
            url_,title_,published_at_,api_,content_,company_id_=article_tuple
            id_=None
        else: 
            raise(ValueError(f'document_tuple {article_tuple} should either have len of 5 or 6'))
        result=Document(url_,title_,published_at_,api_,content_,id_,company_id_)
        return result
    
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
    def source(self):
        return self.__source
    @property
    def content(self):
        return self.__content
    #db 
    @property
    def id(self):
        if self.__id is None: 
            raise AttributeError("id is not setted /n"+self.to_dict())
        return self.__id
    
    @property
    def company_id(self):
        if self.__company_id is None: 
            raise AttributeError("company_id is not setted /n"+str(self.to_dict()))
        return self.__company_id
    
    #set function
    def set_id(self,id:int)->None:
         self.__id=id
    def set_company_id(self,company_id_:int)->None:
        self.__company_id=company_id_
    def set_content(self,content:str)->None:
        self.__content=content
    def set_published_at(self,published_at)->None: 
        if type(published_at)==datetime:
            self.__published_at=published_at.isoformat()
        elif type(published_at)==str:
            self.__published_at=published_at
        else:
            print("Warning in set_published_at: published_at should be of type datetime, not{}".format(type(published_at)))
            print(f"url{self.url}")
            self.__published_at=None
        
    def set_url(self,url:str)->None: 
        self.__url=url
    
    def to_dict(self)->dict: 
        return{
            'url':self.url,
            'title':self.title,
            'published_at':self.published_at,
            'source':self.source,
            'content':self.content,
            'id':self.__id,
            'company_id':self.__company_id
        }
    def to_tuple(self)->tuple:
        """
        url,title,published_at,source,content,id,company_id
        """
        return(self.url,self.title,self.published_at,self.source,self.__content,self.__id,self.__company_id)
    
    def to_insert_para(self)->tuple:
        """
        ?url,?title,?published_at,?source,?content,?company_id
        return[tuple]: (self.url,self.title,self.published_at,self.source,self.content,self.company_id)
        """
        
        return (self.url,self.title,self.published_at,self.source,self.content,self.company_id)

    def get_tonescore(self)->'Tonescore': 
        from master_dictionary.master_dictionary import MasterDictionary,load_masterdictionary,ToneNertral
        master_dict=load_masterdictionary('data/master_dictionary/Loughran-McDonald_MasterDictionary_1993-2021.csv',)
        content=self.content
        
        counter = Counter()
        tone_score=0
        positive_tonescore=0 
        negative_tonescore=0 
        words_text=content.split()
        counter.update(words_text)
        
        for word,word_count in counter.items(): 
            word=word.upper()
            result=master_dict.get(word,ToneNertral)
            positive_flag=int(result.positive)
            negative_flag=int(result.negative)
            strong_modal_flag=int(result.strong_modal)
            weak_modal_flag=int(result.weak_modal)
            if positive_flag>0 and strong_modal_flag>0:
                positive_tonescore=positive_tonescore+2*word_count
            elif positive_flag>0 and weak_modal_flag>0: 
                positive_tonescore=positive_tonescore+0.5*word_count
            elif positive_flag>0: 
                positive_tonescore=positive_tonescore+1*word_count
            elif negative_flag>0 and strong_modal_flag>0: 
                negative_tonescore=negative_tonescore+2*word_count
            elif negative_flag>0 and weak_modal_flag>0: 
                negative_tonescore=negative_tonescore+0.5 *word_count
            elif negative_flag>0: 
                negative_tonescore=negative_tonescore+1*word_count
        tone_score=positive_tonescore-negative_tonescore
        result=Tonescore(tone_score,positive_tonescore,negative_tonescore,self.url,self.title,self.published_at,None,None,None,self.id)
        return result
class Tonescore: 
    REFERENCE_TABLE={
        'document':[('id','document_id')],
        'company':[('id','company_id')]     
    }
    
    @classmethod
    def rational_representation(cls)->str:
        return 'tonescore'    

    @classmethod 
    def attribute_in_col_string(cls)->str:
        pass
    
    @classmethod
    def db_insert_col(cls)->str: 
        """generate the sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        sql="""INSERT INTO tonescore(tonescore,positive_tonescore,negative_tonescore,document_id,company_id,is_hkex)
                VALUES(?,?,?,?,?,?)"""
        return sql

    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        sql="""INSERT OR IGNORE INTO tonescore(tonescore,positive_tonescore,negative_tonescore,document_id,company_id,is_hkex')
                VALUES(?,?,?,?,?,?)"""        
        return sql
    
    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
        return result    
    
    def __init__(self,tonescore:float,positive_tonescore:float,negative_tonescore:float,id:int|None=None,document_id:int|None=None,company_id:int|None=None,is_hkex:int=0):        
        self.__tonescore=tonescore
        self.__positive_tonescore=positive_tonescore
        self.__negative_tonescore=negative_tonescore                                
        #db 
        self.__id=id        
        self.__document_id=document_id
        self.__company_id=company_id
        if type(is_hkex)!=int:
            raise(TypeError())
        self.__is_hkex=is_hkex
    @classmethod
    def from_tuple(self,tonescore_tuple:tuple)->'Tonescore': 
        if len(tonescore_tuple)==7: 
            tonescore_,positive_tonescore_,negative_tonescore_,id_,document_id_,company_id,is_hkex=tonescore_tuple
        elif len(tonescore_tuple)==6: 
            tonescore_,positive_tonescore_,negative_tonescore_,document_id_,company_id,is_hkex=tonescore_tuple
            id_=None
        else: 
            raise(ValueError(f'tonescore_tuple {tonescore_tuple} should either have len of 7 or 6'))
        result=Tonescore(tonescore_,positive_tonescore_,negative_tonescore_,id_,document_id_,company_id,is_hkex)
        return result
         
    @property
    def tonescore(self):
        return self.__tonescore
    @property
    def positive_tonescore(self):
        return self.__positive_tonescore
    @property
    def negative_tonescore(self):
        return self.__negative_tonescore

    #db 
    @property
    def id(self):
        if self.__id is None: 
            mes_="id is not setted /n"+self.to_dict()
            raise AttributeError(mes_)
        return self.__id    
  
    @property
    def document_id(self):
        if self.__document_id is None: 
            mes_="document_id is not setted /n"+self.to_dict()
            raise AttributeError(mes_)        
        return self.__document_id
    
    @property
    def company_id(self):
        if self.__company_id is None: 
            mes_="company_id is not setted /n"+self.to_dict()
            raise AttributeError(mes_)        
        return self.__company_id

    @property
    def is_hkex(self):
        return self.__is_hkex
    
   
    #set function 
    def set_id(self,id:int)->None:
        self.__id=id
    def set_document_id(self,document_id_:int)->None:
        self.__document_id=document_id_
    def set_company_id(self,company_id:int): 
        self.__company_id=company_id    
    
    def to_dict(self)->dict: 
        return {
            'tonescore':self.tonescore,
            'positive_tonescore':self.positive_tonescore,
            'negative_tonescore':self.negative_tonescore,
            'id':self.__id,
            'document_id':self.__document_id,
            'company_id':self.__company_id,
            'is_hkex':self.is_hkex
        }
        
    def to_tuple(self)->tuple: 
        """
        return (tonescore,positive_tonescore,negative_tonescore,id,document_id,company_id,is_hkex)
        """
        return (self.tonescore,self.positive_tonescore,self.negative_tonescore,self.__id,self.__document_id,self.__company_id,self.is_hkex)
    def to_insert_para(self)->tuple: 
        """
        ?tonescore,?positive_tonescore,?negative_tonescore,?document_id,?company_id
        return[tuple]: tonescore,positive_tonescore,negative_tonescore,document_id,company_id
        """
        return (self.tonescore,self.positive_tonescore,self.negative_tonescore,self.__document_id,self.__company_id,self.is_hkex)

class TonescoreMerge:
    """
    tonescore_merge					
    tonescore	positive_tonescore	negative_tonescore	date	id	company_id is_hkex
    """

    REFERENCE_TABLE={
        'company':[('id','company_id')]        
    }
    
    @classmethod
    def rational_representation(cls)->str:
        return 'tonescore_merge'    

    @classmethod 
    def attribute_in_col_string(cls)->str:
        pass
    
    @classmethod
    def db_insert_col(cls)->str: 
        """generate the sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        sql="""INSERT INTO tonescore_merge(tonescore,positive_tonescore,negative_tonescore,date,company_id,is_hkex)
                VALUES(?,?,?,?,?,?)"""
        return sql

    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        sql="""INSERT OR IGNORE INTO tonescore_merge(tonescore,positive_tonescore,negative_tonescore,date,company_id,is_hkex')
                VALUES(?,?,?,?,?,?)"""        
        return sql
    
    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
        return result    
    
    def __init__(self,tonescore:float,positive_tonescore:float,negative_tonescore:float,date_:str|datetime|c_date,id:int|None=None,company_id:int|None=None,is_hkex:int=None):        
        self.__tonescore=tonescore
        self.__positive_tonescore=positive_tonescore
        self.__negative_tonescore=negative_tonescore                                
        self.__date=date_
        #db 
        self.__id=id        
        self.__company_id=company_id
        self.__is_hkex=is_hkex
        
    @classmethod
    def from_tuple(self,tonescore_tuple:tuple)->'Tonescore': 
        if len(tonescore_tuple)==7: 
            tonescore_,positive_tonescore_,negative_tonescore_,date_,id_,company_id,is_hkex=tonescore_tuple
        elif len(tonescore_tuple)==6: 
            tonescore_,positive_tonescore_,negative_tonescore_,date_,company_id,is_hkex=tonescore_tuple
            id_=None
        else: 
            raise(ValueError(f'tonescoremerge_tuple {tonescore_tuple} should either have len of 6 or 7'))
        result=TonescoreMerge(tonescore_,positive_tonescore_,negative_tonescore_,date_,id_,company_id,is_hkex)
        return result
         
    @property
    def tonescore(self):
        return self.__tonescore
    
    @property
    def positive_tonescore(self):
        return self.__positive_tonescore
    @property
    def negative_tonescore(self):
        return self.__negative_tonescore
    @property
    def date(self):
        return self.__date
    

    #db 
    @property
    def id(self):
        if self.__id is None: 
            mes_="id is not setted /n"+self.to_dict()
            raise AttributeError(mes_)
        return self.__id    

    
    @property
    def company_id(self):
        if self.__company_id is None: 
            mes_="company_id is not setted /n"+self.to_dict()
            raise AttributeError(mes_)        
        return self.__company_id

    @property
    def is_hkex(self):
        return self.__is_hkex
    
   
    #set function 
    def set_id(self,id:int)->None:
        self.__id=id
    def set_company_id(self,company_id:int): 
        self.__company_id=company_id    
    
    def to_dict(self)->dict: 
        return {
            'tonescore':self.tonescore,
            'positive_tonescore':self.positive_tonescore,
            'negative_tonescore':self.negative_tonescore,
            'date':self.date,
            'id':self.__id,
            'company_id':self.__company_id,
            'is_hkex':self.is_hkex
        }
        
    def to_tuple(self)->tuple: 
        """
        return (tonescore,positive_tonescore,negative_tonescore,date,id,company_id,is_hkex)
        """
        return (self.tonescore,self.positive_tonescore,self.negative_tonescore,self.date,self.__id,self.__company_id)
    def to_insert_para(self)->tuple: 
        """
        ?tonescore,?positive_tonescore,?negative_tonescore,?document_id,?company_id,?is_hkex
        return[tuple]: tonescore,positive_tonescore,negative_tonescore,date,company_id,is_hkex
        """
        return (self.tonescore,self.positive_tonescore,self.negative_tonescore,self.date,self.__company_id,self.is_hkex)


# class Tonescore_old:
#     REFERENCE_TABLE={
#         'article':[('id','article_id')],
#         'document':[('id','document')]
#     }
#     @classmethod
#     def rational_representation(cls)->str:
#         return 'tonescore'    

#     @classmethod 
#     def attribute_in_col_string(cls)->str:
#         pass
    
#     @classmethod
#     def db_insert_col(cls)->str: 
#         """generate the sql for Insert row to db

#         Returns:
#             str: The sql_ with ? place holder for insert row 
#         """
#         sql="""INSERT INTO tonescore(tonescore,positive_tonescore,negative_tonescore,url,title,published_at,api,article_id,document_id')
#                 VALUES(?,?,?,?,?,?,?,?,?)"""
#         return sql

#     @classmethod
#     def db_ignore_insert_col(cls)->str:
#         """generate the sql for insert or ingore row to db 
        
#         Returns: 
#             str: The sql_ with ? place holder for insert or ignore row 
#         """
#         sql="""INSERT OR IGNORE INTO tonescore(tonescore,positive_tonescore,negative_tonescore,url,title,published_at,api,article_id,document_id')
#                 VALUES(?,?,?,?,?,?,?,?,?)"""
#         return sql
    
#     @classmethod
#     def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
#         result=cls.REFERENCE_TABLE.get(main_table_rr,None)
#         if result==None: 
#             raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
#         return result 
        
#     def __init__(self,tonescore:float,positive_tonescore:float,negative_tonescore:float,url:str,title:str,published_at:datetime,api:str,id:int|None=None,article_id:int|None=None,document_id:int|None=None):        
#         self.__tonescore=tonescore
#         self.__positive_tonescore=positive_tonescore
#         self.__negative_tonescore=negative_tonescore
#         self.__url=url 
#         self.__title=title
#         if type(published_at)==datetime:
#             self.__published_at=published_at
#         else: 
#             raise(TypeError("published_at should be of type datetime, not{}".format(type(published_at))))
#         self.__api=api
        
#         #db 
#         self.__id=id
#         self.__article_id=article_id
#         self.__document_id=document_id

#     @classmethod
#     def from_tuple(self,tonescore_tuple:tuple)->'Tonescore': 
#         if len(tonescore_tuple)==10: 
#             tonescore_,positive_tonescore_,negative_tonescore_,url_,title_,published_at_6,api_7,id_,article_id_,document_id_=tonescore_tuple
#         elif len(tonescore_tuple)==9: 
#             tonescore_,positive_tonescore_,negative_tonescore_,url_,title_,published_at_6,api_7,article_id_,document_id_=tonescore_tuple
#             id_=None
#         else: 
#             raise(ValueError(f'tonescore_tuple {tonescore_tuple} should either have len of 9 or 8'))
#         result=Tonescore(tonescore_,positive_tonescore_,negative_tonescore_,url_,title_,published_at_6,api_7,id_,article_id_,document_id_)
#         return result
    
#     @property
#     def tonescore(self):
#         return self.__tonescore
#     @property
#     def positive_tonescore(self):
#         return self.__positive_tonescore
#     @property
#     def negative_tonescore(self):
#         return self.__negative_tonescore
#     @property
#     def url(self):
#         return self.__url
#     @property
#     def title(self):
#         return self.__title
#     @property
#     def published_at(self):
#         return self.__published_at
#     @property
#     def api(self):
#         return self.__api

#     #db 
#     @property
#     def id(self):
#         if self.__id is None: 
#             raise AttributeError("id is not setted /n"+self.to_dict())
#         return self.__id    
#     @property
#     def article_id(self):
#         if self.__article_id is None: 
#             raise AttributeError("article_id is not setted /n"+self.to_dict())
#         return self.__article_id    
#     @property
#     def document_id(self):
#         if self.__document_id is None: 
#             raise AttributeError("document_id is not setted /n"+self.to_dict())        
#         return self.__document_id
    
#     #set function 
#     def set_id(self,id:int)->None:
#         self.__id=id
#     def set_article_id(self,article_id:int): 
#         self.__article_id=article_id
#     def set_document_id(self,document_id_:int)->None:
#         self.__document_id=document_id_
    
    
#     def to_dict(self)->dict: 
#         return {
#             'tonescore':self.tonescore,
#             'positive_tonescore':self.positive_tonescore,
#             'negative_tonescore':self.negative_tonescore,
#             'url':self.url, 
#             'title':self.title,
#             'published_at':self.published_at,
#             'api':self.api,
#             'id':self.__id,
#             'article_id':self.__article_id,
#             'document_id':self.__document_id
#                 }
#     def to_tuple(self)->tuple: 
#         """
#         return (tonescore,positive_tonescore,negative_tonescore,url,title,published_at,id,article_id,document_id)
#         """
#         return (self.tonescore,self.positive_tonescore,self.negative_tonescore,self.url,self.title,self.published_at,self.__id,self.__article_id,self.__document_id)
#     def to_insert_para(self)->tuple: 
#         """
#         ?tonescore,?positive_tonescore,?negative_tonescore,?url,?title,?published_at,?article_id,?document_id
#         return[tuple]: tonescore,positive_tonescore,negative_tonescore,url,title,published_at,article_id,document_id
#         """
#         return (self.tonescore,self.positive_tonescore,self.negative_tonescore,self.url,self.title,self.published_at,self.__article_id,self.__document_id)

class MentionIn:
    REFERENCE_TABLE={
        'article':[('id','article_id')],
        'company':[('id','company_id')]
    }
    @classmethod
    def rational_representation(cls)->str:
        return 'mention_in'    
    
    @classmethod 
    def attribute_in_col_string(cls)->str:
        pass

    @classmethod
    def db_insert_col(cls)->str: 
        """generate the sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        sql="""INSERT INTO mention_in(url,h_code,article_id,company_id)
                VALUES(?,?,?,?)"""
        return sql

    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        sql="""INSERT OR IGNORE INTO mention_in(url,h_code,article_id,company_id)
                VALUES(?,?,?,?)"""
        return sql
    
    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
        return result 
        
    def __init__(self,url:str,h_code:str,id:int|None=None,article_id:int|None=None,company_id:int|None=None):        
        self.__url=url
        self.__h_code=h_code
        
        self.__id=id
        self.__article_id=article_id
        self.__company_id=company_id
    
    @classmethod
    def from_tuple(self,mentionin_tuple:tuple)->'MentionIn': 
        if len(mentionin_tuple)==5: 
            url_,h_code_,id_,article_id_,company_id_=mentionin_tuple
        elif len(mentionin_tuple)==4: 
            url_,h_code_,article_id_,company_id_=mentionin_tuple
            id_=None
        else: 
            raise(ValueError(f'mentionin_tuple {mentionin_tuple} should either have len of 4 or 5'))
        
        result=MentionIn(url_,h_code_,id_,article_id_,company_id_)
        return result
    
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
        """
        return[tuple]: (self.url,self.h_code,self.__id,self.__article_id,self.__company_id)
        """
        return(self.url,self.h_code,self.__id,self.__article_id,self.__company_id)
    
    def to_insert_para(self)->tuple: 
        """
        ?url,?h_code,?article_id,?company_id
        return[tuple]: (self.url,self.h_code,self.__article_id,self.__company_id)
        """
        return(self.url,self.h_code,self.__article_id,self.__company_id)
    
class Affecting:
    REFERENCE_TABLE={
        'article':[('id','article_id')],
        'car3':[('id','car3_id')],
        'return':[('id','return_id')],
        'company':[('id','company_id')]
    }
    @classmethod
    def rational_representation(cls)->str:
        return 'affecting'    

    @classmethod 
    def attribute_in_col_string(cls)->str:
        pass
    
    @classmethod
    def db_insert_col(cls)->str: 
        """generate the sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        sql="""INSERT INTO affecting(article_id,car3_id,return_id,company_id)
                VALUES(?,?,?,?)"""
        return sql

    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        sql="""INSERT OR IGNORE INTO affecting(article_id,car3_id,return_id,company_id)
                VALUES(?,?,?,?)"""
        return sql
    
    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
        return result 
        
    def __init__(self,id:int|None=None,article_id:int|None=None,car3_id:int|None=None,return_id:int|None=None,company_id:int|None=None): 
        self.__id=id
        self.__article_id=article_id
        self.__car3_id=car3_id
        self.__return_id=return_id
        self.__company_id=company_id

    @classmethod
    def from_tuple(self,affecting_tuple:tuple)->'Affecting': 
        if len(affecting_tuple)==5: 
            id_,article_id_,car3_id_,return_id_,company_id_=affecting_tuple
        elif len(affecting_tuple)==4: 
            article_id_,car3_id_,return_id_,company_id_=affecting_tuple
            id_=None 
        else: 
            raise(ValueError(f'affecting_tuple {affecting_tuple} should have len of either 5 or 4'))    
        result=Affecting(id_,article_id_,car3_id_,return_id_,company_id_)
        return result
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
    def car3_id (self):
        return self.__car3_id   
    @property
    def return_id(self):
        if self.__id is None: 
            raise AttributeError('return_id is not setted'+'/n'+self.to_dict())
        return self.__return_id
    @property
    def company_id(self):
        return self.__company_id
    
    
    #set function 
    def set_id(self,id:int)->None:
         self.__id=id
    def set_article_id(self,article_id:int)->None:
         self.__article_id=article_id
    def set_return_id(self,return_id:int)->None:
         self.__return_id=return_id
    
    def to_dict(self)->dict: 
        return{
            'id':self.__id,
            'article_id':self.__article_id,
            'car3_id':self.__car3_id,
            'return_id':self.__return_id,
            'company_id':self.__company_id
        }
    def to_tuple(self)->tuple: 
        """
        return[tuple]: (self.__id,self.__article_id,self.__car3_id,self.__return_id,self.__company_id)
        """
        return (self.__id,self.__article_id,self.__car3_id,self.__return_id,self.__company_id)
    
    def to_insert_para(self)->tuple: 
        """
        ?article_id,?car3_id,?return_id,?company_id
        return[tuple]: (article_id,car3_id,return_id,company_id)
        """
        return (self.__article_id,self.__car3_id,self.__return_id,self.__company_id)


    
class Causing:
    REFERENCE_TABLE={
        'document':[('id','document_id')],
        'car3':[('id','car3_id')],
        'return':[('id','return_id')],
        'company':[('id','company_id')]
    }
    @classmethod
    def rational_representation(cls)->str:
        return 'causing'    

    @classmethod 
    def attribute_in_col_string(cls)->str:
        pass
    
    @classmethod
    def db_insert_col(cls)->str: 
        """generate the sql for Insert row to db

        Returns:
            str: The sql_ with ? place holder for insert row 
        """
        sql="""INSERT INTO causing(document_id,car3_id,return_id,company_id)
                VALUES (?,?,?,?)"""
        return sql 

    @classmethod
    def db_ignore_insert_col(cls)->str:
        """generate the sql for insert or ingore row to db 
        
        Returns: 
            str: The sql_ with ? place holder for insert or ignore row 
        """
        sql="""INSERT OR IGNORE INTO causing(document_id,car3_id,return_id,company_id)
                VALUES (?,?,?,?)"""
        return sql 
    
    @classmethod
    def table_reference_names_pair(cls,main_table_rr:str)->list[tuple]: 
        result=cls.REFERENCE_TABLE.get(main_table_rr,None)
        if result==None: 
            raise(ValueError(f'the main table{main_table_rr} is not linked to {cls}'))
        return result 
        
    def __init__(self,id:int|None=None,document_id:int|None=None,car3_id:int|None=None,return_id:int|None=None,company_id:int|None=None): 
        self.__id=id
        self.__document_id=document_id
        self.__car3_id=car3_id
        self.__return_id=return_id
        self.__company_id=company_id

    @classmethod
    def from_tuple(self,affecting_tuple:tuple)->'Affecting': 
        if len(affecting_tuple)==5: 
            id_,document_id_,car3_id_,return_id_,company_id_=affecting_tuple
        elif len(affecting_tuple)==4: 
            document_id_,car3_id_,return_id_,company_id_=affecting_tuple
            id_=None 
        else: 
            raise(ValueError(f'affecting_tuple {affecting_tuple} should have len of either 5 or 4'))    
        result=Affecting(id_,document_id_,car3_id_,return_id_,company_id_)
        return result
    #db
    @property
    def id(self):
        if self.__id is None: 
            raise AttributeError('id is not setted'+'/n'+self.to_dict())
        return self.__id
    @property
    def document_id(self):
        if self.__id is None: 
            raise AttributeError('article_id is not setted'+'/n'+self.to_dict())
        return self.__document_id
    @property
    def car3_id (self):
        return self.__car3_id   
    @property
    def return_id(self):
        if self.__id is None: 
            raise AttributeError('return_id is not setted'+'/n'+self.to_dict())
        return self.__return_id
    
    @property
    def company_id(self):
        return self.__company_id
    
    
    #set function 
    def set_id(self,id:int)->None:
         self.__id=id
    def set_document_id(self,document_id:int)->None:
         self.__document_id=document_id
    def set_return_id(self,return_id:int)->None:
         self.__return_id=return_id
    
    def to_dict(self)->dict: 
        return{
            'id':self.__id,
            'document_id':self.__document_id,
            'car3_id':self.__car3_id,
            'return_id':self.__return_id,
            'company_id':self.__company_id
        }
    def to_tuple(self)->tuple: 
        """
        return[tuple]: (self.__id,self.__document_id,self.__car3_id,self.__return_id,self.__company_id)
        """
        return (self.__id,self.__document_id,self.__car3_id,self.__return_id,self.__company_id)
    
    def to_insert_para(self)->tuple: 
        """
        ?document_id,?car3_id,?return_id,?company_id
        return[tuple]: (document_id,car3_id,return_id,company_id)
        """
        return (self.__document_id,self.__car3_id,self.__return_id,self.__company_id)


    
