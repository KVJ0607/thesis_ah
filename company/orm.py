from typing import Callable
import sqlite3
from sqlite3 import Error
from company.company import *
from utils.constant import COMPANIES_DB
from utils.basic import create_nd_list,iterate_indexes,set_element_of_list_with_indexes,flatten_list_element
_COMPANY_LOOKUP={    
    'rational_representation':Company.rational_representation,
    'db_insert_col':Company.db_insert_col,
    'db_ignore_insert_col':Company.db_ignore_insert_col,
    'from_tuple':Company.from_tuple,
    'to_dict':Company.to_dict,
    'to_tuple':Company.to_tuple,
    'to_insert_para':Company.to_insert_para ,
    'table_reference_names_pair':Company.table_reference_names_pair
}

_COMPANY_MINING_LOOKUP={    
    'rational_representation':CompanyMining.rational_representation,
    'db_insert_col':CompanyMining.db_insert_col,
    'db_ignore_insert_col':CompanyMining.db_ignore_insert_col,
    'from_tuple':CompanyMining.from_tuple,
    'to_dict':CompanyMining.to_dict,
    'to_tuple':CompanyMining.to_tuple,
    'to_insert_para':CompanyMining.to_insert_para ,
    'table_reference_names_pair':CompanyMining.table_reference_names_pair
}
_INDEXCOMPANY_LOOKUP={    
    'rational_representation':IndexCompany.rational_representation,
    'db_insert_col':IndexCompany.db_insert_col,
    'db_ignore_insert_col':IndexCompany.db_ignore_insert_col,
    'from_tuple':IndexCompany.from_tuple,
    'to_dict':IndexCompany.to_dict,
    'to_tuple':IndexCompany.to_tuple,
    'to_insert_para':IndexCompany.to_insert_para,
    'table_reference_names_pair':IndexCompany.table_reference_names_pair  
}

_KEYWORD_LOOKUP={    
    'rational_representation':Keyword.rational_representation,
    'db_insert_col':Keyword.db_insert_col,
    'db_ignore_insert_col':Keyword.db_ignore_insert_col,
    'from_tuple':Keyword.from_tuple,
    'to_dict':Keyword.to_dict,
    'to_tuple':Keyword.to_tuple,
    'to_insert_para':Keyword.to_insert_para,
    'table_reference_names_pair':Keyword.table_reference_names_pair
}

_PRICING_LOOKUP={    
    'rational_representation':Pricing.rational_representation,
    'db_insert_col':Pricing.db_insert_col,
    'db_ignore_insert_col':Pricing.db_ignore_insert_col,
    'from_tuple':Pricing.from_tuple,
    'to_dict':Pricing.to_dict,
    'to_tuple':Pricing.to_tuple,
    'to_insert_para':Pricing.to_insert_para,
    'table_reference_names_pair':Pricing.table_reference_names_pair
}


_RETURN_LOOKUP={    
    'rational_representation':Return.rational_representation,
    'db_insert_col':Return.db_insert_col,
    'db_ignore_insert_col':Return.db_ignore_insert_col,
    'from_tuple':Return.from_tuple,
    'to_dict':Return.to_dict,
    'to_tuple':Return.to_tuple,
    'to_insert_para':Return.to_insert_para,
    'table_reference_names_pair':Return.table_reference_names_pair
    
}

_CAR3_LOOKUP={    
    'rational_representation':Car3.rational_representation,
    'db_insert_col':Car3.db_insert_col,
    'db_ignore_insert_col':Car3.db_ignore_insert_col,
    'from_tuple':Car3.from_tuple,
    'to_dict':Car3.to_dict,
    'to_tuple':Car3.to_tuple,
    'to_insert_para':Car3.to_insert_para,
    'table_reference_names_pair':Car3.table_reference_names_pair
}

_CAR3DUAL_LOOKUP={    
    'rational_representation':Car3Dual.rational_representation,
    'db_insert_col':Car3Dual.db_insert_col,
    'db_ignore_insert_col':Car3Dual.db_ignore_insert_col,
    'from_tuple':Car3Dual.from_tuple,
    'to_dict':Car3Dual.to_dict,
    'to_tuple':Car3Dual.to_tuple,
    'to_insert_para':Car3Dual.to_insert_para,
    'table_reference_names_pair':Car3Dual.table_reference_names_pair
}

_ARTICLE_LOOKUP={    
    'rational_representation':Article.rational_representation,
    'db_insert_col':Article.db_insert_col,
    'db_ignore_insert_col':Article.db_ignore_insert_col,
    'from_tuple':Article.from_tuple,
    'to_dict':Article.to_dict,
    'to_tuple':Article.to_tuple,
    'to_insert_para':Article.to_insert_para,
    'table_reference_names_pair':Article.table_reference_names_pair
}

_QUERY_LOOKUP={    
    'rational_representation':Query.rational_representation,
    'db_insert_col':Query.db_insert_col,
    'db_ignore_insert_col':Query.db_ignore_insert_col,
    'from_tuple':Query.from_tuple,
    'to_dict':Query.to_dict,
    'to_tuple':Query.to_tuple,
    'to_insert_para':Query.to_insert_para,
    'table_reference_names_pair':Query.table_reference_names_pair
}
_DOCUMENT_LOOKUP={
    'rational_representation':Document.rational_representation,
    'db_insert_col':Document.db_insert_col,
    'db_ignore_insert_col':Document.db_ignore_insert_col,
    'from_tuple':Document.from_tuple,
    'to_dict':Document.to_dict,
    'to_tuple':Document.to_tuple,
    'to_insert_para':Document.to_insert_para,
    'table_reference_names_pair':Document.table_reference_names_pair
}
_TONESCORE_LOOKUP={    
    'rational_representation':Tonescore.rational_representation,
    'db_insert_col':Tonescore.db_insert_col,
    'db_ignore_insert_col':Tonescore.db_ignore_insert_col,
    'from_tuple':Tonescore.from_tuple,
    'to_dict':Tonescore.to_dict,
    'to_tuple':Tonescore.to_tuple,
    'to_insert_para':Tonescore.to_insert_para,
    'table_reference_names_pair':Tonescore.table_reference_names_pair
}
_TONESCOREMERGE_LOOKUP={    
    'rational_representation':TonescoreMerge.rational_representation,
    'db_insert_col':TonescoreMerge.db_insert_col,
    'db_ignore_insert_col':TonescoreMerge.db_ignore_insert_col,
    'from_tuple':TonescoreMerge.from_tuple,
    'to_dict':TonescoreMerge.to_dict,
    'to_tuple':TonescoreMerge.to_tuple,
    'to_insert_para':TonescoreMerge.to_insert_para,
    'table_reference_names_pair':TonescoreMerge.table_reference_names_pair
}
MENTIONIN_LOOKUP={    
    'rational_representation':MentionIn.rational_representation,
    'db_insert_col':MentionIn.db_insert_col,
    'db_ignore_insert_col':MentionIn.db_ignore_insert_col,
    'from_tuple':MentionIn.from_tuple,
    'to_dict':MentionIn.to_dict,
    'to_tuple':MentionIn.to_tuple,
    'to_insert_para':MentionIn.to_insert_para,
    'table_reference_names_pair':MentionIn.table_reference_names_pair
}
_AFFECTING_LOOKUP={    
    'rational_representation':Affecting.rational_representation,
    'db_insert_col':Affecting.db_insert_col,
    'db_ignore_insert_col':Affecting.db_ignore_insert_col,
    'from_tuple':Affecting.from_tuple,
    'to_dict':Affecting.to_dict,
    'to_tuple':Affecting.to_tuple,
    'to_insert_para':Affecting.to_insert_para,
    'table_reference_names_pair':Affecting.table_reference_names_pair
}
_CAUSING_LOOKUP={    
    'rational_representation':Causing.rational_representation,
    'db_insert_col':Causing.db_insert_col,
    'db_ignore_insert_col':Causing.db_ignore_insert_col,
    'from_tuple':Causing.from_tuple,
    'to_dict':Causing.to_dict,
    'to_tuple':Causing.to_tuple,
    'to_insert_para':Causing.to_insert_para,
    'table_reference_names_pair':Causing.table_reference_names_pair
}

_RELATIONAL_REPRESENTATION_LOOKUP={
    'company':_COMPANY_LOOKUP,
    'company_mining':_COMPANY_MINING_LOOKUP,
    'index_company':_INDEXCOMPANY_LOOKUP,
    'keyword':_KEYWORD_LOOKUP,
    'pricing':_PRICING_LOOKUP,
    'return':_RETURN_LOOKUP,
    'car3':_CAR3_LOOKUP, 
    'car3_dual':_CAR3DUAL_LOOKUP,
    'article':_ARTICLE_LOOKUP,
    'query':_QUERY_LOOKUP,
    'document':_DOCUMENT_LOOKUP,
    'tonescore':_TONESCORE_LOOKUP,
    'tonescore_merge':_TONESCOREMERGE_LOOKUP,
    'mention_in':MENTIONIN_LOOKUP,
    'affecting':_AFFECTING_LOOKUP,
    'causing':_CAUSING_LOOKUP
}

def get_obj_rr(obj)->str: 
    """get the relational representation of a python object

    Args:
        obj: the python object

    Returns:
        str: the relational representation 
    """
    if type(obj)==Company: return 'company'
    elif type(obj)==CompanyMining: return 'company_mining'
    elif type(obj)==IndexCompany: return 'index_company'
    elif type(obj)==Keyword: return 'keyword'
    elif type(obj)==Pricing: return 'pricing'
    elif type(obj)==Return: return 'return'
    elif type(obj)==Car3: return 'car3'
    elif type(obj)==Car3Dual: return 'car3_dual'
    elif type(obj)==Article: return 'article'
    elif type(obj)==Document: return 'document'
    elif type(obj)==Tonescore: return 'tonescore'
    elif type(obj)==TonescoreMerge: return 'tonescore_merge'
    elif type(obj)==MentionIn: return 'mention_in'
    elif type(obj)==Affecting: return 'affecting'
    elif type(obj)==Causing: return 'causing'
    else: 
        raise(TypeError(f'The type{type(obj)} is not supported'))

def get_class_rr(class_)->str: 
    """get the relational representation of a class

    Args:
        class_: the python class

    Returns:
        str: the relational representation
    """
    if class_==Company: return 'company'
    elif class_==CompanyMining: return 'company_mining'
    elif class_==IndexCompany: return 'index_company'
    elif class_==Keyword: return 'keyword'
    elif class_==Pricing: return 'pricing'
    elif class_==Return: return 'return'
    elif class_==Car3: return 'car3'
    elif class_==Article: return 'article'
    elif class_==Document: return 'document'
    elif class_==Tonescore: return 'tonescore'
    elif class_==TonescoreMerge: return 'tonescore_merge'
    elif class_==MentionIn: return 'mention_in'
    elif class_==Affecting: return 'affecting'
    elif class_==Causing: return 'causing'
    else: 
        raise(TypeError(f'The type{class_} is not supported'))    
    
def general_lookup(relational_represenatation:str,function_name:str): 
    class_lookup =_RELATIONAL_REPRESENTATION_LOOKUP.get(relational_represenatation,None)
    if class_lookup is None: 
        raise(ValueError(f'relational_representation doesnot have {relational_represenatation}'))
    result=class_lookup.get(function_name,None)
    if result is None:
        raise(ValueError(f'function_name doesnot have {function_name}'))
    return result

def general_lookup_with_undetermined_type(obj,function_name:str): 
    """It returns the corresponding function with that corresponding class of object 

    Args:
        obj (_type_): the object that need to call the function
        function_name (str): the function name 

    Returns:
        function: the function of that class of object
    """
    obj_rr= get_obj_rr(obj)
    return general_lookup(obj_rr,function_name)

def object2relational_insert_commit_old(objects,db_path=COMPANIES_DB)->None: 
    """insert object of varius type to sqlite database

    Args:
        objects: an iterable of object that to be commited to database
        db_path (COMPANIES_DB): sqlite3 database path
    """
    with sqlite3.connect(db_path) as con:
        c=con.cursor()
        
        for obj in objects: 
            insert_statement=general_lookup_with_undetermined_type(obj,'db_insert_col')()
            insert_value=general_lookup_with_undetermined_type(obj,'to_insert_para')(obj)
            c.execute(insert_statement,insert_value)
        con.commit()
def object2relational_insert_commit(objects, db_path=COMPANIES_DB) -> None:
    """Insert objects of various types to sqlite database.

    Args:
        objects: An iterable of objects to be committed to the database.
        db_path (COMPANIES_DB): Path to the sqlite3 database.
    """
    con = sqlite3.connect(db_path)  # Establish a new database connection
    c = con.cursor()  # Create a cursor from the connection
    try:
        for obj in objects:
            insert_statement = general_lookup_with_undetermined_type(obj, 'db_insert_col')()
            insert_value = general_lookup_with_undetermined_type(obj, 'to_insert_para')(obj)
            c.execute(insert_statement, insert_value)
        con.commit()  # Commit the transaction
    except sqlite3.Error as e:  # Catch any SQLite errors
        con.rollback()  # Rollback the transaction on error
        raise e  # Re-raise the exception to handle it outside
    finally:
        con.close()  # Close the connection whether or not an error occurred
        
    
def object2relational_ignore_commit(objects,db_path=COMPANIES_DB)->None: 
    """insert or ignore object of varius type to sqlite database

    Args:
        objects: an iterable of object that to be commited to database
        db_path (COMPANIES_DB): sqlite3 database path
    """
    try: 
        con=sqlite3.connect(db_path)
        c=con.cursor()
        c.execute('BEGIN TRANSACTION;')
        for obj in objects: 
            insert_statement=general_lookup_with_undetermined_type(obj,'db_ignore_insert_col')()
            insert_value=general_lookup_with_undetermined_type(obj,'to_insert_para')(obj)
            c.execute(insert_statement,insert_value)        
        con.commit()
    except Error as e:
    # An error occurred, roll back the transaction
        con.rollback()
        print(e)
    finally:
        c.close()
        con.close()    
        

class Object2Relational: 
    
    """A handler for relational table. 
    
    require a corresponding object class that has the following function 
    1.rational_representation
    2.db_insert_col
    3.from_tuple
    4.table_reference_names_pair
    4.to_dict
    5.to_tuple
    6.to_insert_para    
    """
    def __init__(self,class_,db_path=COMPANIES_DB): 
        self.__class=class_
        self.__db_path=db_path
        self.__class_rr=get_class_rr(class_)
        self.__lookup_table=_RELATIONAL_REPRESENTATION_LOOKUP.get(self.__class_rr,None)
        if self.__lookup_table is None: 
            raise (ValueError(f"class {class_} is not supported"))

    
    @property
    def db_path(self):
        return self.__db_path
    
    def relational_representation(self)->str: 
        return get_class_rr(self.__class)
    
    def db_insert_col(self)->str: 
        """generate the snippet of sql for Insert row to db

        Returns:
            Documentstr: the str between INSERT and VALUES
        """
        return self.__lookup_table['db_insert_col'](self.__class)
    
    def from_tuple(self,tuple_:tuple): 
        """init the object with tuple input 

        Args:
            tuple_ (tuple): the init para

        Returns:
            _type_: the object instance 
        """
        return self.__lookup_table['from_tuple'](tuple_)
    
    def get_foreign_key_of_foreign_table(self,foreign_class)->list[tuple[str]]: 
        """get the pair of column that this class is linked by a col of a foreign class table 

        Args:
            foreign_class (_type_): the foreign class

        Returns:
            list[tuple[str]]: a list of all column pair (main_col,for_col)
        """
        foreign_rr=get_class_rr(foreign_class)
        result=general_lookup(foreign_rr,'table_reference_names_pair')(self.relational_representation())
        return result
    
    def to_dict(self,obj): 
        return self.__lookup_table['to_dict'](obj)
    
    def to_tuple(self,obj):
        return self.__lookup_table['to_tuple'](obj)
    
    def to_insert_para(self,obj)->tuple:
        """get the tuple of value to the parameter to execute insert sql

        Args:
            obj (_type_): _description_

        Returns:
            tuple: a tuple of value that need to insert a row
        """
        return self.__lookup_table['to_insert_para'](obj)

    def check_if_exist(self,unique_col:str,unique_val)->bool: 
        """check if if a row with value in col exists

        Example: 
            row_exists=handler.check_if_exist('title=?',title)
        Args:
            unique_col (str): the column requirenment
            unique_val (_type_): the value

        Returns:
            bool: True/False 
        
        """
        result=self.fetch_some((unique_col,unique_val))
        if len(result)==0: 
            return False
        else: 
            return True
        
    def check_if_exist_unique_tuples(self,unique_list:list[tuple])->bool: 
        """check if if a row with requirements in multiple column 

        Example: 
            row_exists=handler.check_if_exist([('title=?',title),('version>?',3)])
            
        Args:
            unique_list (list[tuple]): the list of requirement tuple; each element represent one column requirement

        Returns:
            bool: True/False
        """
        results=self.fetch_col_by_requirements(target_columns=['id'],column_value_pair=unique_list)
        if len(results)==0: 
            return False
        else: 
            return True
        
            
    
    def commit(self,row_obj)->None: 
        """commit one row to the database

        Args:
            obj (_type_): an python object to be commited
        """
        with sqlite3.connect(self.db_path) as con:
            
            c=con.cursor()
            sql=self.db_insert_col()
            para= (self.to_insert_para())
            c.execute(sql,para)
            con.commit()

    #plain fetch         
    def fetch_all(self)->list: 
        """ fetch all the objects in the database 
        
        Return: 
            list: a list of python object is returned
        """
        rr=self.relational_representation()
        
        with sqlite3.connect(self.db_path) as con:        
            c=con.cursor()
        
            sql_="""SELECT * 
                    FROM {}""".format(rr)
            fetched_results=c.execute(sql_).fetchall()
            object_results=[]
            for result_ in fetched_results: 
                object_results.append(self.from_tuple(result_))


        return object_results
    
    def fetch_some(self,*req_col_value_pair,order_by:str|None=None)->list: 
        """fetch all the objects that meets the requirement in the database
        
        Arg: 
            req_col_value_pair[list(tuple)]: a list of (col_name,col_value) tuples 
        
        Return: 
            list: a list of python objects is returned
        
        Example: 
        handler=fetch_some(('id>?',id),('h_code is not Null',None),order_by='id')
        """
        #connect to db
        with sqlite3.connect(self.db_path) as con:
            con=sqlite3.connect(self.db_path)
            c=con.cursor()
            
            #prepare the sql    
            rr=self.relational_representation()
            where_statement=''
            para=[]
            for col_value_pair in req_col_value_pair: 
                col_,val_=col_value_pair[0],col_value_pair[1]
                where_statement=where_statement+col_+' And '
                if val_ is not None:
                    para.append(val_)
            
            where_statement=where_statement[:-5]
            
            #the sql command and parameter
            if order_by is not None: 
                sql_="""
                    SELECT * 
                    FROM {}
                    WHERE {}
                    ORDER BY {};
                    """.format(rr,where_statement,order_by)
            else:
                sql_="""
                    SELECT * 
                    FROM {}
                    WHERE {};
                    """.format(rr,where_statement)
            #print(sql_)
            
            fetched_result=c.execute(sql_,para).fetchall()
            
            #parse the tuple into object 
            result_in_object=[]
            for result_ in fetched_result: 
                result_in_object.append(self.from_tuple(result_))
            
     
        return result_in_object
        
    
    def fetch_column_of_all(self,col_name:str)->list: 
        """fetch a column from all row 
        
        Return: 
        list: list of column value 
        """
        with sqlite3.connect(self.db_path) as con:
            #connect to db 
            
            c=con.cursor()
            
            #fetch all
            sql_="""
                    SELECT DISTINCT {}
                    FROM {} 
                    WHERE {} IS NOT NULL;
                    """.format(col_name,self.relational_representation(),col_name)
            result_fetched=c.execute(sql_).fetchall()
            
            #parse from tuple to str
            result_in_val=[ele[0] for ele in result_fetched]
            
            

        return result_in_val
    
    # def update_single_col(self,table_name,col_name,col_value,req_col,req_val): 
    #     con=sqlite3.connect(self.db_path)
    #     c=con.cursor()
    #     sql_update_query="""
    #         UPDATE {}
    #         SET {} = ?
    #         WHERE {} = ?;
    #     """.format(table_name,col_name,req_col)
    #     try:
    #         # Execute the SQL command with parameters
    #         c.execute(sql_update_query, (col_value, req_val))

    #         # Commit the changes to the database
    #         con.commit()

    #         # Check if any rows were updated
    #         if c.rowcount > 0:
    #             print(f"Updated {c.rowcount} row(s) in the table.")
    #         else:
    #             print("No rows were updated.")

    #     except sqlite3.Error as error:
    #         # Rollback in case of an error
    #         con.rollback()
    #         print("Failed to update rows in sqlite table", error)

    #     finally:
    #         # Close the cursor and connection to the database
    #         c.close()
    #         con.close()

    
    # def join_table_and_group_concat(self,foreign_class,foreign_col):
    #     """retreive a group concated values of a column in a foreign table; the main and foreign table have a 1-m relationship.
        
    #     Arg: 
    #         foreign_class
    #         foreign_col
    #     """        
    #     con=sqlite3.connect(self.db_path)
    #     c=con.cursor()
                
    #     key_sql=''
    #     foreign_keys=self.get_foreign_key_of_foreign_table(foreign_class)
    #     for key_pair in foreign_keys:
    #         main_key,for_key=key_pair 
    #         key_sql=key_sql+main_key+' = ' +get_class_rr(foreign_class)+'.'+for_key+' OR '        
    #     key_sql=key_sql[:-4]
        
    #     sql_="""SELECT id,GROUP_CONCAT({})
    #     FROM {}
    #     JOIN {} ON {}
    #     GROUP BY id""".format(foreign_col,self.relational_representation(),get_class_rr(foreign_class),key_sql)
        
    #     result=c.execute(sql_).fetchall()
    #     c.close()
    #     con.close()
    #     return result
        

        
    # def fetch_object_with_columns_values(self,*args,column_value_pair:dict={},order_column='id',flatten=False,db_path:str=COMPANIES_DB,)->list: 
    #     """fetch object in specified table grouped by sorting_column. 
    #     e.g get_nd_list_with_order('language','subject','published_year',column_value_pair={'on_sale=?':True},db_path=amazon_books.sqlite)
    #     This will return a 3-d list of books; result[i][j][k]=book in language[i],subject[j], published in year[k] and is currently on sale
    #     Args:
            
    #         column_value_par(dict)= key is the column(e.g. title=?) value is the parameter value(e.g.three little pigs) Defaults to{}
    #         order_column (str, optional): A single col to order by. Defaults to 'id.
    #         flatten (bool, optional): _description_. Defaults to False.
    #         db_path (str, optional): sqlite filename. Defaults to COMPANIES_DB.


    #     Returns:
    #         list: A list of n_d 

    #     """

    #     #define variable 
    #     table=self.relational_representation()
        
    #     #make connection 
    #     con=sqlite3.connect(db_path)
    #     c=con.cursor()
        
    #     #get domain_size by dimension
    #     dimension_list=list(args) #[i][j][k]
    #     args_length=len(dimension_list)
    #     domain_size_by_dimension=[] #size_i,size_j,size_k
    #     for dimension in dimension_list: 
    #         size_=c.execute(
    #             '''
    #             SELECT COUNT(DISTINCT {} )
    #             FROM {}
    #             WHERE {} IS NOT NULL 
    #             '''.format(dimension,table,dimension)
    #         ).fetchall()[0][0]
    #         domain_size_by_dimension.append(size_)
            
        
    #     #get a list of distinct value of each column
    #     domain_in_each_dimension=[]
    #     for di_ in dimension_list:
    #         domain_=c.execute(
    #             '''
    #             SELECT DISTINCT {}
    #             FROM {} 
    #             WHERE {} IS NOT NULL 
    #             '''.format(di_,table,di_)
    #         ).fetchall()
    #         domain_=tuple(ele[0] for ele in domain_)
    #         domain_in_each_dimension.append(domain_)
    #     #Get extra dimension for the req_col
    #     for i in range(len(column_value_pair)): 
    #         domain_size_by_dimension.append(1)   
    #     #Get a list of tuple containing the indexes [i][j][k]
    #     indexes_iterable=iterate_indexes(domain_size_by_dimension)
        
    #     #get a nd_list with 0 value placeholder
    #     result_nd_list=create_nd_list(domain_size_by_dimension,[])
         
    #     #Add the re_col in the domain_in_each_dimension
    #     for req_col,req_val in column_value_pair.items(): 
    #         new_di=req_val,
    #         dimension_list.append(req_col)
    #         domain_in_each_dimension.append(new_di)
            
    #     for indexes in indexes_iterable:         
    #         data=[]
    #         for i,index in enumerate(indexes): 
    #             data.append(domain_in_each_dimension[i][index])
    #         target_columns_data=''
    #         target_columns_data=target_columns_data[0:-1]        
    #         where_clause_1 = ' AND '.join(f"{col} = ?" for col in dimension_list[0:args_length])
    #         where_clause_2 = ' AND '.join(f"{col}" for col in dimension_list[args_length:])
    #         if args_length==0: 
    #             where_clause=where_clause_2
    #         elif len(dimension_list)==args_length and args_length!=0: 
    #             where_clause=where_clause_1
    #         elif len(dimension_list)==args_length: 
    #             where_clause='1=1'
    #         else: 
    #             where_clause=where_clause_1+' AND ' + where_clause_2
                  
            
    #         sql_=f'SELECT * FROM {table} WHERE {where_clause} ORDER BY {order_column}'
    #         parameter_=data
    #         c.execute(sql_, parameter_)
    #         sql_results = c.fetchall()
    #         results_in_object=[]
    #         class_init_fuc= general_lookup(table,'from_tuple')
    #         for sql_result in sql_results:
    #             results_in_object.append(class_init_fuc(sql_result))
    #         set_element_of_list_with_indexes(result_nd_list,indexes,results_in_object)
                            
    #     c.close()
    #     con.close()
    #     if flatten: 
    #         result_nd_list=flatten_list_element(result_nd_list,self.__class)
    #     return result_nd_list


    # def fetch_col_by_requirements(self,*args,target_columns:list[str]|tuple[str],column_value_pair:list[tuple]|None=None,order_column=None,db_path:str=COMPANIES_DB)->list: 
    #     """ get target_columns in a table grouped by sorting_column. 
    #     e.g get_nd_list_with_order('language','subject','published_year',target_columns=['author','sales'],column_value_pair=[('on_sales=?',True)]db_path=amazon_books.sqlite)
    #     This will return a 3-d list of two elements tuples; result[i][j][k]=(author_instance,sales_instance) where author_instance published a book in language[i] of subject[j], in year published_year[k] and is currently on sale

    #     Args:
    #         target_columns (list[str] | tuple[str]): tuple of column name to be selected
    #         table (str): table name 
    #         column_value_pair (list[tuple] | None, optional): a list of col_name,target_value tuple. Defaults to None.
    #         order_column (_type_, optional): A single col to order by. Defaults to None.
    #         db_path (str, optional): sqlite filename. Defaults to COMPANIES_DB.

    #     Returns:
    #         list: n_d list of tuple of col 
    #     """
    #     #define variable 
    #     table=self.relational_representation()
        
    #     con=sqlite3.connect(db_path)
    #     c=con.cursor()
        
    #     #get domain_size by dimension
    #     dimension_list=list(args) #[i][j][k]
    #     domain_size_by_dimension=[] #size_i,size_j,size_k
    #     for dimension in dimension_list: 
    #         size_=c.execute(
    #             '''
    #             SELECT COUNT(DISTINCT {} )
    #             FROM {} 
    #             '''.format(dimension,table)
    #         ).fetchall()[0][0]
    #         domain_size_by_dimension.append(size_)
        
    #     #get a nd_list with 0 value placeholder
    #     result_nd_list=create_nd_list(domain_size_by_dimension)
        
        
    #     #get a list of distinct value of each column
    #     domain_in_each_dimension=[]
    #     for di_ in dimension_list:
    #         domain_=c.execute(
    #             '''
    #             SELECT DISTINCT {}
    #             FROM {} 
    #             '''.format(di_,table)
    #         ).fetchall()
    #         domain_=tuple(ele[0] for ele in domain_)
    #         domain_in_each_dimension.append(domain_)
        
    #     #Get extra dimension for the req_col
    #     for i in range(len(column_value_pair)): 
    #         domain_size_by_dimension.append(1)        
    #     #Get a list of tuple containing the indexes [i][j][k]
    #     indexes_iterable=iterate_indexes(domain_size_by_dimension)     
        
    #     #Add the re_col in the domain_in_each_dimension
    #     for req_col,req_val in column_value_pair: 
    #         dimension_list.append(req_col)
    #         domain_in_each_dimension.append(tuple(req_val))
    #     for indexes in indexes_iterable:         
    #         data=[]
    #         for i in len(indexes): 
    #             data.append(domain_in_each_dimension[i][indexes[i]])
    #         target_columns_data=''
    #         for ele in target_columns: 
    #             target_columns_data=target_columns_data+ele+','
    #         target_columns_data=target_columns_data[0:-1]        
    #         where_clause = ' AND '.join(f"{col}" for col in dimension_list)        
            
    #         sql_=f'SELECT{target_columns} FROM {table} WHERE {where_clause} ORDER BY {order_column}'
    #         parameter_=data
    #         c.execute(sql_, parameter_)
    #         sql_results = c.fetchall()
    #         set_element_of_list_with_indexes(result_nd_list,indexes,sql_results)
                            
    #     c.close()
    #     con.close()
    #     return result_nd_list
        

