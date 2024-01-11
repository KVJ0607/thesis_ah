from utils.basic import flatten_list_element
from company.company import *
from company.orm import Object2Relational,object2relational_ignore_commit
from utils.constant import COMPANIES_DB

def cal_car3_dual(db_path=COMPANIES_DB):
    car3_handler=Object2Relational(Car3,db_path)
    matching_obj=[]
    for cp_id in range(1,150):
        acar3_list:list[Car3]=car3_handler.fetch_some(('company_id=?',cp_id),('flag=?','a'),order_by='date')
        hcar3_list:list[Car3]=car3_handler.fetch_some(('company_id=?',cp_id),('flag=?','h'),order_by='date')
        acar3_dict = {acar3.date: acar3 for acar3 in acar3_list}
        for hcar3 in hcar3_list: 
            target_acar3=acar3_dict.get(hcar3.date,None)
            if target_acar3==None: 
                continue
            matching_obj.append(Car3Dual(target_acar3.id,hcar3.id,hcar3.date))
        object2relational_ignore_commit(matching_obj)
    return matching_obj
            

def cal_adjusted_daily_returns(db_path=COMPANIES_DB)->list[Return]: 
    pricing_handler=Object2Relational(Pricing)
    resulting_return:list[Return]=[]
    for company_id in range(1,150): 
        
        #flag=a 
        print(company_id)
        a_pricing_list:list[Pricing]=pricing_handler.fetch_some(('company_id=?',company_id),('flag=?','a'),order_by='date')
        h_pricing_list:list[Pricing]=pricing_handler.fetch_some(('company_id=?',company_id),('flag=?','h'),order_by='date')        
        last_c=a_pricing_list[0].adjusted_close
        listed_region=a_pricing_list[0].listed_region
        for i,a_pricing in enumerate(a_pricing_list[1:]): 
            today_c=a_pricing.adjusted_close
            adjusted_daily_return=(today_c-last_c)/last_c
            resulting_return.append(Return(date_=a_pricing.date,return_=adjusted_daily_return,type_='daily',flag='a',listed_region=listed_region,id=None,company_id=company_id,index_company_id=None,pricing_id=a_pricing.id))
            last_c=today_c
        
        #flag=h
        last_c=h_pricing_list[0].adjusted_close
        listed_region=h_pricing_list[0].listed_region        
        for i,h_pricing in enumerate(h_pricing_list[1:]): 
            today_c=h_pricing.adjusted_close
            adjusted_daily_return=(today_c-last_c)/last_c
            resulting_return.append(Return(date_=h_pricing.date,return_=adjusted_daily_return,type_='daily',flag='h',listed_region=listed_region,id=None,company_id=company_id,index_company_id=None,pricing_id=h_pricing.id))
            last_c=today_c
            
    for index_id in range(1,4): 
        pricing_list:list[Pricing]=pricing_handler.fetch_some(('index_company_id=?',index_id),order_by='date')
        last_c=pricing_list[0].adjusted_close
        listed_region=pricing_list[0].listed_region
        flag=pricing_list[0].flag
        
        for i,pricing_ in enumerate(pricing_list[1:]): 
            today_c=pricing_.adjusted_close
            adjusted_daily_return=(today_c-last_c)/last_c
            resulting_return.append(Return(date_=pricing_.date,return_=adjusted_daily_return,type_='daily',flag=flag,listed_region=listed_region,id=None,company_id=None,index_company_id=index_id,pricing_id=pricing_.id))
    print("The total length of return is: {}".format(len(resulting_return)))
    return resulting_return

def cal_adjusted_daily_returns_old(flatten_result=False,db_path=COMPANIES_DB)->list[Return]: 
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
        for pricing_of_one_flag in pricing_of_one_company:
            company_adjusted_daily_return=[]  
            for i,pricing_in_one_day in enumerate(pricing_of_one_flag):
                yesterday_adjusted_close=None                
                date_,open,high,low,close,adjusted_close,volume,flag,listed_region,pricing_id,company_id,index_company_id=pricing_in_one_day.to_tuple()
                if i==0: 
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
        for i,index_pricing_in_one_day in enumerate(index_pricing_in_one_company): 
            date_,open,high,low,close,adjusted_close,volume,flag,listed_region,pricing_id,company_id,index_company_id=index_pricing_in_one_day.to_tuple()
            if i==0: 
                yesterday_adjusted_close=adjusted_close
            else: 
                adjusted_daily_return=(adjusted_close-yesterday_adjusted_close)/yesterday_adjusted_close
                yesterday_adjusted_close=adjusted_close
                index_company_adjusted_daily_return.append(Return.from_tuple((date_,adjusted_daily_return,'adjusted_daily_return',flag,listed_region,company_id,index_company_id,pricing_id)))
        all_companies_adjusted_daily_return=all_companies_adjusted_daily_return+index_company_adjusted_daily_return
    if flatten_result: 
        flatten_list_element(all_companies_adjusted_daily_return,Return)
    return all_companies_adjusted_daily_return
            
def cal_abnormal_returns()->list[Return]:
    #abnormal return = adr = adr_index
    return_handler=Object2Relational(Return)
    index_cp_handler=Object2Relational(IndexCompany)
    sz_:IndexCompany=index_cp_handler.fetch_some(('code=?','szse'))[0]
    hk_:IndexCompany=index_cp_handler.fetch_some(('code=?','hsce'))[0]
    sh_:IndexCompany=index_cp_handler.fetch_some(('code=?','sse'))[0]
    sz_id=sz_.id
    hk_id=hk_.id
    sh_id=sh_.id
    sz_returns:list[Return]=return_handler.fetch_some(('type=?','daily'),('index_company_id=?',sz_id),order_by='date')
    hk_returns:list[Return]=return_handler.fetch_some(('type=?','daily'),('index_company_id=?',hk_id),order_by='date')
    sh_returns:list[Return]=return_handler.fetch_some(('type=?','daily'),('index_company_id=?',sh_id),order_by='date')
    
    sz_return_dict={sz_return.date_ : sz_return.return_ for sz_return in sz_returns}  
    hk_return_dict={hk_return.date_ : hk_return.return_ for hk_return in hk_returns}  
    sh_return_dict={sh_return.date_ : sh_return.return_ for sh_return in sh_returns}   
    
    resulting_ab_list:list[Return]=[]  
    type_='abnormal'               
    for company_id in range(1,150):
        #a 
        company_returns:list[Return]=return_handler.fetch_some(('company_id=?',company_id),('type=?','daily'),order_by='date')
        for cp_return in company_returns: 
            index_return =None
            if cp_return.listed_region=='sz': 
                index_return=sz_return_dict.get(cp_return.date_) 
            elif cp_return.listed_region=='hk': 
                index_return=hk_return_dict.get(cp_return.date_)
            elif cp_return.listed_region=='sh': 
                index_return=sh_return_dict.get(cp_return.date_)
            else: 
                mes_="The database about daily return is problematic, exist listed_region ={}".format(cp_return.listed_region)
                raise(ValueError(mes_))           
            if index_return==None: 
                print('for cp_id {} and date{}, there is no corrsponding index return'.format(company_id,cp_return.date_))
                continue 
            ab_return=cp_return.return_-index_return
            date_=cp_return.date_
            flag_=cp_return.flag
            listed_region=cp_return.listed_region
            pricing_id=cp_return.pricing_id
            resulting_ab_list.append(Return(date_,ab_return,type_,flag_,listed_region,None,company_id,None,pricing_id))
    print("Number of {} abnormal return is generated".format(len(resulting_ab_list)))
    return resulting_ab_list
       
       
                    


def cal_abnormal_returns_old(flatten_result=False,db_path=COMPANIES_DB)->list[list[Return]]: 
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
    all_return_in_class_by_company=return_handler.fetch_object_with_columns_values('company_id','flag',column_value_pair={'type=?':'adjusted_daily_return'},order_column='date')
    all_return_in_class_by_index_company=return_handler.fetch_object_with_columns_values('index_company_id',column_value_pair={'type=?':'adjusted_daily_return'},order_column='date')
                
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

def cal_car3s_old(flatten_result=False,db_path=COMPANIES_DB)->list[list[list[Car3]]]: 
    """calculate and return all the car3 for corrsponding return date in the db

    Args:
        db_path (_type_, optional): sqlite3 filename. Defaults to COMPANIES_DB.

    Returns:
        list[list[list[Car3]]]: car3 of flag of company; result[i][0][j] corrsponding to abnormal returns of company i in the h/a market and the jth record by date. 
    """
    #define a handler 
    return_handler=Object2Relational(Return,db_path)
    
    col_val_pair=[('type = ?','abnormal_return = ?')]
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
                
                    
                
def cal_car3s()->list[Car3]:
    # for all abnormal return, there is prob one car3
    return_handler=Object2Relational(Return)
    
    result_car3:list[Car3]=[]
    for company_id in range(1,150): 
        #a 
        flag_='a'
        a_ab_returns:list[Return]=return_handler.fetch_some(('company_id=?',company_id),('flag=?',flag_),('type=?','abnormal'),order_by='date')
        
        #init the return and id 
        for i, abnormal_return in enumerate(a_ab_returns):
            if i==0 or i==len(a_ab_returns)-1: 
                continue
            date_=abnormal_return.date_
            car3_=a_ab_returns[i-1].return_+a_ab_returns[i].return_+a_ab_returns[i+1].return_
            last_id=a_ab_returns[i-1].id
            today_id=a_ab_returns[i].id
            next_id=a_ab_returns[i+1].id
            result_car3.append(Car3(date_,car3_,flag_,None,company_id,last_id,today_id,next_id))
        #a 
        flag_='h'
        h_ab_returns:list[Return]=return_handler.fetch_some(('company_id=?',company_id),('flag=?',flag_),('type=?','abnormal'),order_by='date')
        
        #init the return and id 
        for i, ab_return_ in enumerate(h_ab_returns):
            if i==0 or i==len(h_ab_returns)-1: 
                continue
            date_=ab_return_.date_
            car3_=h_ab_returns[i-1].return_+h_ab_returns[i].return_+h_ab_returns[i+1].return_
            last_id=h_ab_returns[i-1].id
            today_id=h_ab_returns[i].id
            next_id=h_ab_returns[i+1].id
            result_car3.append(Car3(date_,car3_,flag_,None,company_id,last_id,today_id,next_id))            
    return result_car3
    
    
    
def check_dup(): 
    return_handler=Object2Relational(Return)
    
    result_car3:list[Car3]=[]
    for company_id in range(1,150): 
        #a 
        flag='a'
        a_ab_returns:list[Return]=return_handler.fetch_some(('company_id=?',company_id),('flag=?',flag),('type=?','daily'),order_by='date')
        
        #init the return and id 

        
        for i,a_ab_re in enumerate(a_ab_returns[2:-1]): 
            try:
                if a_ab_re.date_[2:-1][i]==a_ab_returns[2:-1][i-1].date_:
                    print('a,id={}, date={}'.format(company_id,a_ab_re.date_))
            except: 
                continue
            
        #a 
        flag='h'
        a_ab_returns:list[Return]=return_handler.fetch_some(('company_id=?',company_id),('flag=?',flag),('type=?','daily'),order_by='date')
        
    
        
        for i,a_ab_re in enumerate(a_ab_returns[2:-1]): 
            try:
                if a_ab_re.date_[2:-1][i]==a_ab_returns[2:-1][i-1].date_:
                    print('h,id={}, date={}'.format(company_id,a_ab_re.date_))
            except:
                continue
    return result_car3
        
def check_dup2():
    return_handler=Object2Relational(Return)
    pricing_handler=Object2Relational(Pricing)
    cp_handler=Object2Relational(Company)
    result_car3:list[Car3]=[]
    for company_id in range(1,150): 
        h_code=cp_handler.fetch_some(('id=?',company_id))[0].h_code
        #
        #a 
        flag='a'
        a_ab_returns:list[Pricing]=pricing_handler.fetch_some(('company_id=?',company_id),('flag=?',flag),order_by='date')
        
        #init the return and id 

        date_ab=a_ab_returns[1].date
        for i,a_ab_re in enumerate(a_ab_returns[2:-1]): 
            if a_ab_re.date==a_ab_returns[2:-1][i-1]:
                print('a, id={} h_code={}, date={}'.format(company_id,h_code,a_ab_re.date))
            date_ab=a_ab_re.date
            
        #h 
        flag='h'
        a_ab_returns:list[Pricing]=pricing_handler.fetch_some(('company_id=?',company_id),('flag=?',flag),order_by='date')
        
    
        for i,a_ab_re in enumerate(a_ab_returns[2:-1]): 
            if a_ab_re.date==a_ab_returns[2:-1][i-1].date:
                print('a, id={} h_code={}, date={}'.format(company_id,h_code,a_ab_re.date))
                  
    return result_car3    