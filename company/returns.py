import sqlite3

from utils.basic import flatten_list_element
from company.company import *
from company.database_interface import get_return_by_company,get_return_by_index_company,get_nd_list_with_columns_values

def cal_adjusted_daily_returns(flatten_result=False,db_path=COMPANIES_DB)->list[tuple]: 
    """calculate adjusted_daily_return from a database

    Args:
        db_path (_type_, optional): sqlite3 database file. Defaults to COMPANIES_DB.

    Returns:
        list[tuple]: each tuple represent one adjusted daily return entity and for each tuple:(date,return,type,flag,listed_region,company_id,index_company_id,pricing_id)
    """
    con=sqlite3.connect(db_path)
    c=con.cursor()
    
    #get all distinct company_id from the company
    all_company_id=c.execute('''
                          SELECT DISTINCT id
                          FROM company 
                          WHERE id IS NOT NULL
                          ''').fetchall()
    
    
    #get all distinct flag from the pricing 
    all_flag=c.execute('''
                       SELECT DISTINCT flag 
                       FROM pricing 
                       WHERE flag IS NOT NULL
                       ''').fetchall()
    
    #un-tuple the data
    all_company_id=tuple(ele[0] for ele in all_company_id)
    all_flag=tuple(ele[0] for ele in all_flag)
    all_pricing_by_company=[]
    
    for index_i in all_company_id: 
        pricing_given_company_id=list()
        for index_j in all_flag:         
            pricing_element=c.execute('''
                                      SELECT date,adjusted_close,flag,listed_region,company_id,index_company_id,id
                                      FROM pricing
                                      WHERE company_id=?
                                      AND flag=?
                                      ORDER BY date
                                    ''',(index_i,index_j)).fetchall()
            
            pricing_given_company_id.append(pricing_element)
        all_pricing_by_company.append(tuple(pricing_given_company_id))
            
        
    #calculate daily return by company by date
    all_companies_adjusted_daily_return=[]

    for pricing_of_one_company in all_pricing_by_company: 
        company_adjusted_daily_return=[]        
        yesterday_adjusted_close=None
        for pricing_in_one_day in pricing_of_one_company:
            date_,adjusted_close,flag,listed_region,company_id,index_company_id,pricing_id=pricing_in_one_day
            if len(company_adjusted_daily_return)==0: 
                yesterday_adjusted_close=adjusted_close
            else: 
                adjusted_daily_return=(adjusted_close-yesterday_adjusted_close)/yesterday_adjusted_close
                yesterday_adjusted_close=adjusted_close
                company_adjusted_daily_return.append((date_,adjusted_daily_return,'adjusted_daily_return',flag,listed_region,company_id,index_company_id,pricing_id))
        
        all_companies_adjusted_daily_return=all_companies_adjusted_daily_return+company_adjusted_daily_return

        

    #get all distinct codes of index_company
    all_index_company_id=c.execute('''
                        SELECT index_company_id 
                        FROM pricing 
                        WHERE index_company_id IS NOT NULL
                        ''').fetchall()
    #get all pricing data by code of index_company
    all_index_pricing_by_company=[]
    for index_company_id in all_index_company_id: 
        pricing_given_index_company_id=c.execute('''
                  SELECT date,adjusted_close,flag,listed_region,company_id,index_company_id,id
                  FROM pricing
                  WHERE index_company_id=?index_company_id
                  ORDER BY date
                  ''',index_company_id
                  ).fetchall()
        all_index_pricing_by_company.append(pricing_given_index_company_id)
    #calculate all returns by index_company and by date 
    for index_pricing_in_one_company in all_index_pricing_by_company: 
        index_company_adjusted_daily_return=[]
        yesterday_adjusted_close=None
        for index_pricing_in_one_day in index_pricing_in_one_company: 
            date_,adjusted_close,flag,listed_region,company_id,index_company_id,pricing_id=index_pricing_in_one_day
            if len(index_company_adjusted_daily_return)==0: 
                yesterday_adjusted_close=adjusted_close
            else: 
                adjusted_daily_return=(adjusted_close-yesterday_adjusted_close)/yesterday_adjusted_close
                yesterday_adjusted_close=adjusted_close
                index_company_adjusted_daily_return.append((date_,adjusted_daily_return,'adjusted_daily_return',flag,listed_region,company_id,index_company_id,pricing_id))
        all_companies_adjusted_daily_return=all_companies_adjusted_daily_return+index_company_adjusted_daily_return
    #closing connection 
    c.close()
    con.close()
    
    if flatten_result: 
        flatten_list_element(all_companies_adjusted_daily_return,Return)
    return all_companies_adjusted_daily_return
            

def cal_abnormal_returns(flatten_result=False,db_path=COMPANIES_DB)->list[list[Return]]: 
    """calculate abnormal returns from database

    Args:
        db_path (_type_, optional): sqlite3 database file. Defaults to COMPANIES_DB.

    Returns:
        list[list[tuple]]: each tuple represent one abnormal return entity and for each tuple:(date,return,type,flag,listed_region,id,company_id,index_company_id,pricing_id)
        each list of tuple represent all abnormal return in one company 
    """
    result:list[list[tuple]]=[]

    all_return_in_class_by_company=get_return_by_company('adjusted_daily_return')
    all_return_in_class_by_index_company=get_return_by_index_company('adjusted_daily_return')
    
    def _get_index_return_by_date_listed_region(date_:str,listed_region:str,all_return_in_class_by_index_company:list[list[Return]])->float: 
        for index_return_of_one_index in all_return_in_class_by_index_company: 
            index_listed_region=index_return_of_one_index[0].listed_region            
            if index_listed_region==listed_region: 
                for index_return in index_return_of_one_index: 
                    if  index_return.date_==date_: 
                        return index_return.return_
                
    #hsce sse szse
    for all_company_return_in_class in all_return_in_class_by_company: 
        company_abnormal_return:list[tuple]=[]
        for return_in_class in all_company_return_in_class: 
            return_tuple=return_in_class.to_tuple()
            date_,return_,type_,flag,listed_region,id,company_id,index_company_id,pricing_id=return_tuple
            index_return=_get_index_return_by_date_listed_region(date_,listed_region,type_,all_return_in_class_by_index_company)
            ab_return=return_-index_return
            return_obj=Return(date_,ab_return,'abnormal_return',flag,listed_region,company_id=company_id,index_company_id=index_company_id,pricing_id=pricing_id)
            company_abnormal_return.append(return_obj)
        result.append(company_abnormal_return)   
        if flatten_result: 
            flatten_list_element(result,Return)
    return result

def cal_car3s(flatten_result=False,db_path=COMPANIES_DB)->list[list[list[Car3]]]: 
    """calculate and return all the car3 for corrsponding return date in the db

    Args:
        db_path (_type_, optional): sqlite3 filename. Defaults to COMPANIES_DB.

    Returns:
        list[list[list[Car3]]]: car3 of flag of company; result[i][0][j] corrsponding to abnormal returns of company i in the h/a market and the jth record by date. 
    """
    #So car3 is basically one date and three returns info 
    #so we first get all "today return"
    #In order to create a tuple of car3, we need date,car3,flag,cp_id,ld_return_id,td_id,nd_id
    dimension_list=['company_id','flag']
    col_val_pair=('type','abnormal_return')
    target_col=['date','return','flag','id','company_id']
    ab_return=get_nd_list_with_columns_values(dimension_list,target_columns=target_col,table='return',column_value_pair=col_val_pair,order_column='date',db_path=db_path)  
    result_list=[]
    for company_d in ab_return: 
        result_list_by_cp=[]
        for flag_d in company_d: 
            result_list_by_flag=[]
            for i in range(len(flag_d)-1): 
                date_,return_,flag_,id_,company_id_=flag_d[i]
                next_date_,next_return_,next_flag_,next_id_,next_company_id=flag_d[i+1]
                if i==0: 
                    last_id=id_
                    last_return=return_
                car3=last_return+return_+next_return_
                result_list_by_flag.append(Car3(date_,car3,flag_,company_id=company_d,last_day_return_id=last_id,today_return_id=id_,next_day_return_id=next_id_))
                last_id=id_
                last_return=return_
            result_list_by_cp.append(result_list_by_flag)
        result_list.append(result_list_by_cp)
    if flatten_result: 
        flatten_list_element(result_list,Car3)
    return result_list
                
                    
                
# Commit result to db 
def commit_returns(returns:list[Return],db_path:COMPANIES_DB)->None:
    """commit returns to sqlite database
    Args:
        returns (list[Return]): list of tuple, each tuple representing one returns:(date,return,type,flag,listed_region,company_id,index_company_id,pricing_id) 
        db_path (COMPANIES_DB): sqlite3 database path
    """
    con=sqlite3.connect(db_path)
    c=con.cursor()
    for return_ in returns: 
        sql_=f"""
        INSERT INTO return({Return.db_insert_col()})
        VALUES(?date_,?return_,?type_,?flag,?listed_region,?company_id,?index_company_id,?pricing_id)
        """            
        data=return_.to_insert_para()
        c.execute(sql_,data)
    con.commit()
    c.close()
    con.close()
    
    

def commit_car3s(returns:list[Car3],db_path=COMPANIES_DB)->None:
    con=sqlite3.connect(db_path)
    c=con.cursor()
    for ele in returns: 
        sql_=f'''
        INSERT INTO car3({Car3.db_insert_col()})
        VALUES(?date,?car3,?flag,?company_id,?last_day_return_id,?today_return_id,?next_day_return_id)
        '''
        data=ele.to_insert_para()
        c.execute(sql_,data)
    con.commit()
    c.close()
    con.close()
