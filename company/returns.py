from utils.basic import flatten_list_element
from company.company import *
from company.orm import Object2Relational

def cal_adjusted_daily_returns(flatten_result=False,db_path=COMPANIES_DB)->list[Return]: 
    """calculate adjusted_daily_return from a database

    Args:
        db_path (_type_, optional): sqlite3 database file. Defaults to COMPANIES_DB.

    Returns:
        list[tuple]: each tuple represent one adjusted daily return entity and for each tuple:(date,return,type,flag,listed_region,company_id,index_company_id,pricing_id)
    """
    #define handler 
    pricing_handler=Object2Relational(Pricing)

    #get all pricing by company_id
    all_pricing_by_company=pricing_handler.fetch_object_with_columns_values('company_id','flag',order_column='date',db_path=db_path)
    all_index_pricing_by_company=pricing_handler.fetch_object_with_columns_values('index_company_id',order_column='date',db_path=db_path)
        
    #calculate daily return by company by date
    all_companies_adjusted_daily_return=[]
    
    for pricing_of_one_company in all_pricing_by_company: 
        company_adjusted_daily_return=[]        
        yesterday_adjusted_close=None
        for pricing_in_one_day in pricing_of_one_company:
            date_,open,high,low,close,adjusted_close,volume,flag,listed_region,pricing_id,company_id,index_company_id=pricing_in_one_day.to_tuple()
            if len(company_adjusted_daily_return)==0: 
                yesterday_adjusted_close=adjusted_close
            else: 
                adjusted_daily_return=(adjusted_close-yesterday_adjusted_close)/yesterday_adjusted_close
                yesterday_adjusted_close=adjusted_close
                company_adjusted_daily_return.append(Return.from_tuple((date_,adjusted_daily_return,'adjusted_daily_return',flag,listed_region,company_id,index_company_id,pricing_id)))
        
        all_companies_adjusted_daily_return=all_companies_adjusted_daily_return+company_adjusted_daily_return

        
    #calculate all returns by index_company and by date 
    for index_pricing_in_one_company in all_index_pricing_by_company: 
        index_company_adjusted_daily_return=[]
        yesterday_adjusted_close=None
        for index_pricing_in_one_day in index_pricing_in_one_company: 
            date_,open,high,low,close,adjusted_close,volume,flag,listed_region,pricing_id,company_id,index_company_id=pricing_in_one_day.to_tuple()
            if len(index_company_adjusted_daily_return)==0: 
                yesterday_adjusted_close=adjusted_close
            else: 
                adjusted_daily_return=(adjusted_close-yesterday_adjusted_close)/yesterday_adjusted_close
                yesterday_adjusted_close=adjusted_close
                index_company_adjusted_daily_return.append(Return.from_tuple((date_,adjusted_daily_return,'adjusted_daily_return',flag,listed_region,company_id,index_company_id,pricing_id)))
        all_companies_adjusted_daily_return=all_companies_adjusted_daily_return+index_company_adjusted_daily_return
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
    def _get_index_return_by_date_listed_region(date_:str,listed_region:str,all_return_in_class_by_index_company:list[list[Return]])->float: 
        for index_return_of_one_index in all_return_in_class_by_index_company: 
            index_listed_region=index_return_of_one_index[0].listed_region            
            if index_listed_region==listed_region: 
                for index_return in index_return_of_one_index: 
                    if  index_return.date_==date_: 
                        return index_return.return_
                    
    result:list[list[tuple]]=[]
    return_handler=Object2Relational(Return,db_path)
    all_return_in_class_by_company=return_handler.fetch_object_with_columns_values('company_id','flag',column_value_pair=[('type','adjusted_daily_return')],order_column='date')
    all_return_in_class_by_index_company=return_handler.fetch_object_with_columns_values('index_company_id',column_value_pair=[('type','adjusted_daily_return')],order_column='date')
                
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
    #define a handler 
    return_handler=Object2Relational(Return,db_path)
    
    col_val_pair=[('type','abnormal_return')]
    target_col=['date','return','flag','id','company_id']
    ab_return=return_handler.fetch_col_by_requirements('company_id','flag',target_columns=target_col,column_value_pair=col_val_pair,order_column='date')
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
                
                    
                
    
    
