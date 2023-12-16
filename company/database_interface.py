import sqlite3
import itertools
from utils.constant import COMPANIES_DB
from company.company import Return
from utils.basic import create_nd_list,iterate_indexes,set_element_of_list_with_indexes
# interface between db and object of my classes


##Company related
def get_company(a_code:str='',h_code:str='',warning=True,db_path:str=COMPANIES_DB)->tuple[str]: 
    """matching a_code and h_code from the database and returning a tuple of result
    returning (h_code,a_code,zh_name,en_name,id)

    Args:
        a_code (str, optional): a_code of the target company Defaults to ''.
        h_code (str, optional): h_code of the target company. Defaults to ''.
        warning (bool, optional): flag of raising error when None is return. Defaults to True.
        db_path (str, optional): sqlite database file. Defaults to COMPANIES_DB.

    Returns:
        tuple[str]: _description_
    """
    con=sqlite3.connect(db_path)
    c=con.cursor()
    if a_code !='': 
        data={"a_code":a_code}
        resulting_cp=c.execute('''
                  SELECT h_code,a_code,zh_name,en_name,id
                  FROM company 
                  WHERE a_code=:a_code
                  ''',data).fetchall()
    elif h_code!='': 
        data={'h_code':h_code}
        resulting_cp=c.execute('''
                               SELECT h_code,a_code,zh_name,en_name,id
                               FROM company
                               WEHRE h_code=:h_code
                               ''').fetchall()
    else: 
        raise(ValueError('a_code and h_code arguement cannot be both empty'))
    c.close()
    con.close()
    if warning and len(resulting_cp==0):
        raise(ValueError(f'The{a_code}{h_code} is not found in the database')) 
        
    return resulting_cp[0]

def get_all_company_id(db_path:str=COMPANIES_DB)->list[tuple]: 
    """get all distinct company_id 
    Args:
        db_path (str, optional): sqlite3 database file. Defaults to COMPANIES_DB.

    Returns:
        list[tuple]: tuple:(company_id)
    """
    con=sqlite3.connect(db_path)
    c=con.cursor()
    
    result=c.execute('''
              SELECT DISTINCT id
              FROM company
              ''').fetchall()
    c.close()
    con.close()
    return result

# index_company_related
def get_index_company(code:str,warning=True,db_path=COMPANIES_DB)->tuple:
    """fetching index_company from database with matching code

    Args:
        code (str): the matching code
        warning (bool, optional): flag to raise error if the return type is None . Defaults to True.
        db_path (_type_, optional): _description_. Defaults to COMPANIES_DB.

    Returns:
        tuple: (flag,listed_region,name,code,id)
    """
    con=sqlite3.connect(db_path)
    c=con.cursor()
    data={'code':code}
    result=c.execute('''
                    SELECT flag,listed_region,name,code ,id
                    FROM index_company
                    WHERE code=:code                    
                    ''',data).fetchall()
    c.close()
    con.close() 
    if warning and len(result)==0: 
        raise(ValueError(f'The code{code} has no matching result in the database'))
    return result[0]

def get_all_index_company_id(db_path:str=COMPANIES_DB)->list[tuple]: 
    """get all distinct index_company_id 

    Args:
        db_path (str, optional): sqlite3 database file. Defaults to COMPANIES_DB.

    Returns:
        list[tuple]: tuple:(index_company_id)
    """
    con=sqlite3.connect(db_path)
    c=con.cursor()
    
    result=c.execute('''
              SELECT DISTINCT id
              FROM index_company
              ''').fetchall()
    c.close()
    con.close()
    return result

#return related
def get_return_by_company(type_:str,db_path=COMPANIES_DB)->list[list[Return]]: 
    all_company_id=get_all_company_id(db_path)
    #Connect to db
    con=sqlite3.connect(db_path)
    c=con.cursor()
    all_return_in_tuple_by_company=[]
    check_flag=c.execute('''
                         SELECT company_id 
                         FROM return 
                         WHERE type=? 
                         ''',(type_)).fetchall()
    if len(check_flag)==0:
        raise(ValueError('The return type {} has no matching result in db'.format(type_)))
    for company_id in all_company_id: 
        company_return_in_tuple=c.execute('''
                  SELECT date,return,type,flag,listed_region,id,company_id,index_company_id,pricing_id 
                  FROM return 
                  WHERE company_id = ? 
                  AND type = ?
                  ORDER BY date 
                  ''',(company_id[0],type_)).fetchall()
        all_return_in_tuple_by_company.append(company_return_in_tuple)
    all_return_in_class_by_company:list[list[Return]]=[]
    for company_return_in_tuple in all_return_in_tuple_by_company:
        company_return_in_class:list[Return]=[] 
        for return_in_tuple in company_return_in_tuple: 
            company_return_in_class.append(Return(*return_in_tuple))
        all_return_in_class_by_company.append(company_return_in_class)
    return all_return_in_class_by_company

def get_return_by_index_company(type_:str,db_path=COMPANIES_DB)->list[list[Return]]: 
    """get the target type of return for all index companies

    Args:
        type_ (str): the type of return specified in database
        db_path (_type_, optional): sqplite3 database path. Defaults to COMPANIES_DB.

    Returns:
        list[list[Return]]: list[Return] represent Return of one index_company
        
    """
    all_index_company_id=get_all_index_company_id(db_path)
    #Connect to db
    con=sqlite3.connect(db_path)
    c=con.cursor()

    check_flag=c.execute('''
                         SELECT company_id 
                         FROM return 
                         WHERE type=? 
                         ''',(type_)).fetchall()
    if len(check_flag)==0:
        raise(ValueError('The return type {} has no matching result in db'.format(type_)))
    
    all_return_in_tuple_by_index_company:list[list[tuple]]=[]
    for index_company_id in all_index_company_id: 
        company_return_in_tuple=c.execute('''
                  SELECT date,return,type,flag,listed_region,id,company_id,index_company_id,pricing_id 
                  FROM return 
                  WHERE index_company_id = ? 
                  AND type = ?
                  ORDER BY date 
                  ''',(index_company_id[0],type_)).fetchall()
        all_return_in_tuple_by_index_company.append(company_return_in_tuple)
    all_return_in_class_by_index_company:list[list[Return]]=[]
    for index_company_return_in_tuple in all_return_in_tuple_by_index_company:
        index_company_return_in_class:list[Return]=[] 
        for return_in_tuple in index_company_return_in_tuple: 
            index_company_return_in_class.append(Return(*return_in_tuple))
        all_return_in_class_by_index_company.append(index_company_return_in_class)
    return all_return_in_class_by_index_company



##INDEX: get nd-list in order

def get_nd_list_with_columns_values(*args,target_columns:list[str]|tuple[str],table:str,column_value_pair:list[tuple]|None=None,order_column=None,db_path:str=COMPANIES_DB)->list: 
    """ get target_columns in a table grouped by sorting_column. 
    e.g get_nd_list_with_order('language','subject','published_year',target_columns=(author,sales),table=books,column_value_pair=[(on_sales,True)]db_path=amazon_books.sqlite)
    This will return a 3-d list of two elements tuples; result[i][j][k]=(author_instance,sales_instance) where author_instance published a book in language[i] of subject[j], in year published_year[k] and is currently on sale

    Args:
        target_columns (list[str] | tuple[str]): tuple of column name to be selected
        table (str): table name 
        column_value_pair (list[tuple] | None, optional): a list of col_name,target_value tuple. Defaults to None.
        order_column (_type_, optional): A single col to order by. Defaults to None.
        db_path (str, optional): sqlite filename. Defaults to COMPANIES_DB.

    Returns:
        list: A need of n_d 
    """
    
    con=sqlite3.connect(db_path)
    c=con.cursor()
    
    
    #get domain_size by dimension
    dimension_list=list(args) #[i][j][k]
    domain_size_by_dimension=[] #size_i,size_j,size_k
    for dimension in dimension_list: 
        size_=c.execute('''
                        SELECT COUNT(DISTINCT ? )
                        FROM ? 
                        ''',(dimension,table)).fetchall()[0][0]
        domain_size_by_dimension.append(size_)
    
    #get a nd_list with 0 value placeholder
    result_nd_list=create_nd_list(domain_size_by_dimension)
    
    
    #get a list of distinct value of each column
    domain_in_each_dimension=[]
    for di_ in dimension_list:
        domain_=c.execute('''
                          SELECT DISTICT ?
                          FROM ? 
                          ''',(di_,table)).fetchall()
        domain_=tuple(ele[0] for ele in domain_)
        domain_in_each_dimension.append(domain_)
    
    #Get extra dimension for the req_col
    for i in range(len(column_value_pair)): 
        domain_size_by_dimension.append(1)        
    #Get a list of tuple containing the indexes [i][j][k]
    indexes_iterable=iterate_indexes(domain_size_by_dimension)     
    
    #Add the re_col in the domain_in_each_dimension
    for req_col,req_val in column_value_pair: 
        dimension_list.append(req_col)
        domain_in_each_dimension.append(tuple(req_val))
    for indexes in indexes_iterable:         
        data=[]
        for i in len(indexes): 
            data.append(domain_in_each_dimension[i][indexes[i]])
        target_columns_data=''
        for ele in target_columns: 
            target_columns_data=target_columns_data+ele+','
        target_columns_data=target_columns_data[0:-1]        
        where_clause = ' AND '.join(f"{col} = ?" for col in dimension_list)        
        
        sql_=f'SELECT{target_columns} FROM {table} WHERE {where_clause} ORDER BY {order_column}'
        parameter_=data
        c.execute(sql_, parameter_)
        sql_results = c.fetchall()
        set_element_of_list_with_indexes(result_nd_list,indexes,sql_results)
                         
    c.close()
    con.close()
    return result_nd_list
    










def get_nd_list_with_columns_values_old(*args,target_columns:list[str]|tuple[str],table:str,order_column=None,db_path:str=COMPANIES_DB)->list: 
    """get target_columns in a table grouped by sorting_column. 
    e.g get_nd_list_with_order('language','subject','published_year',target_columns=(author,sales),table=books,db_path=amazon_books.sqlite)
    This will return a 3-d list of two elements tuples; result[i][j][k]=(author_instance,sales_instance) where author_instance published a book in language[i] of subject[j] and in year published_year[k]
    """
    
    con=sqlite3.connect(db_path)
    c=con.cursor()
    
    
    #get domain_size by dimension
    dimension_list=list(args) #[i][j][k]
    domain_size_by_dimension=[] #size_i,size_j,size_k
    for dimension in dimension_list: 
        size_=c.execute('''
                        SELECT COUNT(DISTINCT ? )
                        FROM ? 
                        ''',(dimension,table)).fetchall()[0][0]
        domain_size_by_dimension.append(size_)
    
    #get a nd_list with 0 value placeholder
    result_nd_list=create_nd_list(domain_size_by_dimension)
    
    
    #get a list of distinct value of each column
    domain_in_each_dimension=[]
    for di_ in dimension_list:
        domain_=c.execute('''
                          SELECT DISTICT ?
                          FROM ? 
                          ''',(di_,table)).fetchall()
        domain_=tuple(ele[0] for ele in domain_)
        domain_in_each_dimension.append(domain_)
    
    
    
    #Get a list of tuple containing the indexes [i][j][k]
    indexes_iterable=iterate_indexes(domain_size_by_dimension) 
    for indexes in indexes_iterable:         
        data=[]
        for i in len(indexes): 
            data.append(domain_in_each_dimension[i][indexes[i]])
        target_columns_data=''
        for ele in target_columns: 
            target_columns_data=target_columns_data+ele+','
        target_columns_data=target_columns_data[0:-1]        
        where_clause = ' AND '.join(f"{col} = ?" for col in dimension_list)        
        
        sql_=f'SELECT{target_columns} FROM {table} WHERE {where_clause} ORDER BY {order_column}'
        parameter_=data
        c.execute(sql_, parameter_)
        sql_results = c.fetchall()
        set_element_of_list_with_indexes(result_nd_list,indexes,sql_results)
                         
    c.close()
    con.close()
    return result_nd_list
    