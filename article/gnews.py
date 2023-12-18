from datetime import date
import json 

import ssl
from urllib.parse import quote
from urllib.request import urlopen
from urllib.error import HTTPError
from http.client import InvalidURL

from utils.constant import GNEWS_KEYS
from company.company import *
from company.orm import Object2Relational,object2relational_commit

class GnewsRequest: 
    EndPoint_Template='https://gnews.io/api/v4/serarch?{}'
    def __init__(self,api_key):
        self.__api_key=api_key
        self.__q='None'
        self.__lang='Any'
        self.__country='Any'
        self.__max='10'
        self.__in='None'
        self.__nullable='description'
        self.__from='None'
        self.__to='None'
        self.__sortby='relevance'
        self.__page='1'
        self.__expand='content'
    
    def set_q(self,q:str)->None:
        """
        This parameter is mandatory.
        This parameter allows you to specify your search keywords to find the news articles you are looking for. The keywords will be used to return the most relevant articles. It is possible to use logical operators with keywords, see the section on [query syntax](https://gnews.io/docs/v4#query-syntax)

        """
        self.__q=q
    def set_lang(self,lang:str)->None:
        """
        This parameter allows you to specify the language of the news articles returned by the API. You have to set as value the 2 letters code of the language you want to filter.
        See the list of [supported languages](https://gnews.io/docs/v4#languages)
        """
        self.__lang=lang
    def set_country(self,country:str)->None:
        """
        This parameter allows you to specify the country where the news articles returned by the API were published, the contents of the articles are not necessarily related to the specified country. You have to set as value the 2 letters code of the country you want to filter.
        See the list of [supported countries](https://gnews.io/docs/v4#countries)
        """
        self.__country=country 
    def set_max(self,max:int|str)->None:
        """
        This parameter allows you to specify the number of news articles returned by the API. The minimum value of this parameter is 1 and the maximum value is 100. The value you can set depends on your subscription.
        See the [pricing] for more information(https://gnews.io/#pricing)
        """
        self.__max=str(max)
    def set_in(self,in_:str)->None:
        """
        This parameter allows you to choose in which attributes the keywords are searched. The attributes that can be set are title, description and content. It is possible to combine several attributes by separating them with a comma.
        e.g. title,description
        """
        self.__in=in_
    def set_nullable(self,nullable_:str)->None:
        """
        This parameter allows you to specify the attributes that you allow to return null values. The attributes that can be set are title, description and content. It is possible to combine several attributes by separating them with a comma.
        e.g. title,description
        """
        self.__nullable=nullable_
    def set_from(self,from_:str|date)->None:
        """
        This parameter allows you to filter the articles that have a publication date greater than or equal to the specified value. The date must respect the following format:
        YYYY-MM-DDThh:mm:ssTZD
        TZD = time zone designator, its value must always be Z (universal time)
        e.g. 2023-12-16T06:12:27Z
        """
        if type(from_)==date: 
            self.__from=from_.isoformat()
        else:
            self.__from=from_
    def set_to(self,to_:str|date)->None:
        """	
        This parameter allows you to filter the articles that have a publication date smaller than or equal to the specified value. The date must respect the following format:
        YYYY-MM-DDThh:mm:ssTZD
        TZD = time zone designator, its value must always be Z (universal time)
        e.g. 2023-12-16T06:12:27Z
        """
        if type(to_)==date: 
            self.__to=to_.isoformat()
        else:
            self.__to=to_
    def set_sortby(self,sortby_:str)->None:
        """
        This parameter allows you to choose with which type of sorting the articles should be returned. Two values are possible:
        publishedAt = sort by publication date, the articles with the most recent publication date are returned first
        relevance = sort by best match to keywords, the articles with the best match are returned first
        """
        self.__sortby=sortby_
    def set_page(self,page_:str|int)->None:
        """
        This parameter will only work if you have a paid subscription activated on your account.
        This parameter allows you to control the pagination of the results returned by the API. The paging behavior is closely related to the value of the max parameter. The first page is page 1, then you have to increment by 1 to go to the next page. Let's say that the value of the max parameter is 10, then the first page will contain the first 10 articles returned by the API (articles 1 to 10), page 2 will return the next 10 articles (articles 11 to 20), the behavior extends to page 3, 4, ...
        """
        self.__page=str(page_)
    def set_expand(self,expand_:str)->None:
        """
        This parameter will only work if you have a paid subscription activated on your account.
        This parameter allows you to return in addition to other data, the full content of the articles. To get the full content of the articles, the parameter must be set to content
        """
        self.__expand=expand_
    
        
    def to_endpoint(self)->str: 
        result_in_str=f'api_key={self.__api_key}&q={self.__q}&lang={self.__lang}&country={self.__country}&max={self.__max}&in={self.__in}&nullable{self.__nullable}&from={self.__from}&to={self.__to}&sortby={self.__sortby}&page={self.__page}&expand={self.__expand}'
        result =quote(result_in_str)
        return result
        
    def to_request(self)->str:     
        """Return the request url for the query. 
        This is the final url, not merely the endpoint. 

        Returns:
            str: final url for requests
        """
        return GnewsRequest.EndPoint_Template.format(self.to_endpoint())
###



####
class Gnews(Article):
    @classmethod 
    def keywords2query(keyword_list:list[str])->str: 
        """take a list of keywords and then turn it into a query

        Args:
            keyword_list (list[str]): the keyword list 

        Returns:
            str: a query in str
        """
        query_str=''
        if keyword_list[0] !='':
            if keyword_list[0].startswith('-'): 
                query_str='NOT "'+keyword_list[0][1:].strip()+'"'
            elif "AND" in keyword_list[0]:
                query_str=keyword_list[0].strip()
            else: 
                query_str='"'+keyword_list[0].strip()+'"'

        for i in range(len(keyword_list)-1): 
            if keyword_list[i+1] != '' : 
                if keyword_list[i+1].startswith('-'):
                    query_str=query_str+' AND NOT "'+keyword_list[i+1].strip()+'"'
                elif "AND" in keyword_list[i+1]:
                    query_str=query_str+' '+keyword_list[i+1].strip()
                else: 
                    query_str=query_str+ ' OR "'+keyword_list[i+1].strip()+'"'
        return query_str
        
    def __init__(self,url:str,title:str,published_at:datetime|str,api:str,query:str,content:str,source_name,source_url,id_:int|None=None):
        super().__init__(url,title,published_at,api,query,content,id_)
        self.__source_name=source_name
        self.__source_url=source_url
    
    @classmethod
    def from_dictionary(self,gnews_dictionary:dict[str,str]): 
        title=gnews_dictionary['title']
        url=gnews_dictionary['url']
        published_at=gnews_dictionary['publishedAt']
        api='gnews'
        content=gnews_dictionary['content']
        source_name=gnews_dictionary['source']['name']
        source_url=gnews_dictionary['source']['url']
        result=Gnews(url,title,published_at,api,None,content,source_name,source_url)
        """
        "title": "Google's Pixel 7 and 7 Pro’s design gets revealed even more with fresh crisp renders",
        "description": "Now we have a complete image of what the next Google flagship phones will look like. All that's left now is to welcome them during their October announcement!",
        "content": "Google’s highly anticipated upcoming Pixel 7 series is just around the corner, scheduled to be announced on October 6, 2022, at 10 am EDT during the Made by Google event. Well, not that there is any lack of images showing the two new Google phones, b... [1419 chars]",
        "url": "https://www.phonearena.com/news/google-pixel-7-and-pro-design-revealed-even-more-fresh-renders_id142800",
        "image": "https://m-cdn.phonearena.com/images/article/142800-wide-two_1200/Googles-Pixel-7-and-7-Pros-design-gets-revealed-even-more-with-fresh-crisp-renders.jpg",
        "publishedAt": "2022-09-28T08:14:24Z",
        "source": {
        "name": "PhoneArena",
        "url": "https://www.phonearena.com"
        """
    @classmethod
    def from_tuple(self,gnews_tuple:tuple)->'Article': 
        if len(gnews_tuple)==9:
            url_,title_,published_at_,api_,query,content_,source_name,source_url,id_=gnews_tuple
        elif len(gnews_tuple)==8:
            url_,title_,published_at_,api_,query,content_,source_name,source_url=gnews_tuple
            id_=None
        else: 
            raise(ValueError(f'gnews_tuple {gnews_tuple} should either have len of 9 or 8'))
        result=Gnews(url_,title_,published_at_,api_,query,content_,source_name,source_url,id_)
        return result
    
    @property
    def source_name(self):
        return self.__source_name
    @property
    def source_url(self):
        return self.__source_url

    def set_query(self,query_:str)->None:
        super().__query=query_
    
    def to_dict(self)->dict: 
        return{
            'url':self.url,
            'title':self.title,
            'published_at':self.published_at,
            'api':self.api,
            'query':self.query,
            'content':self.content,
            'source_name':self.source_name,
            'source_url':self.source_url,
            'id':self.__id
        }
        
    def to_tuple(self)->tuple:
        """
        url,title,published_at,api,query,content,source_name,source_url,id
        """
        return(self.url,self.title,self.published_at,self.api,self.query,self.content,self.source_name,self.source_url,self.__id)


    

def single_gnew_request(gnews_request:GnewsRequest,number_of_page=1)->list[Gnews]: 
    result:list[Gnews]=[]
    for page_num in number_of_page: 
        gnews_request.set_page(page_num)
        request_url=gnews_request.to_request()
        context = ssl._create_unverified_context()        
        try:
            with urlopen(request_url,context=context) as response:
                data = json.loads(response.read().decode("utf-8"))
                articles_in_json = data["articles"]
                total_art=data["totalArticles"]
                article_list_of_gnews:list[Gnews]=[]
                for i in range(total_art):
                    article_in_gnews=Gnews.from_dictionary(articles_in_json[i])
                    article_list_of_gnews.append(article_in_gnews)
                result=result+article_list_of_gnews
        except(HTTPError,InvalidURL): 
            print(gnews_request.__q)
            raise(ValueError("END"))
    return result

def request_with_keyword(db_path=COMPANIES_DB)->None: 
    """request with Gnews API for all company's keywords and commit it to database

    Args:
        db_path (_type_, optional): the sqlite3 database filename. Defaults to COMPANIES_DB.
    """
    
    company_handler=Object2Relational(Company,db_path)
    article_handler=Object2Relational(Article)
    mention_in_handler=Object2Relational(MentionIn)
    query_handler=Object2Relational(Query)
    cp_keywords_list_by_cp=company_handler.join_table_and_group_concat(Keyword,'keyword')
    
    for cp_data in cp_keywords_list_by_cp: 
        company_id,keywords=cp_data
        query=Gnews.keywords2query(keywords)
        g_request=GnewsRequest(api_key=GNEWS_KEYS)
        g_request.set_q(query)
        g_request.set_max(100)
        gnews_results=single_gnew_request(g_request)
        for gnews_result in gnews_results: 
            gnews_result.set_query(query)
            article_exist=article_handler.check_if_exist('url',gnews_result.url)
            if not article_exist: 
                article_handler.commit(gnews_result)
            article_id=article_handler.fetch_some(['url',gnews_result.url])[0].id
            query_exist=query_handler.check_if_exist_unique_tuples([('query',query),('article_id',article_id)])
            if not query_exist: 
                query_object=Query(query,None,article_id)
                query_handler.commit(query_object)
            mention_exist=mention_in_handler.check_if_exist_unique_tuples([('article_id',article_id),('company_id',company_id)])
            if not mention_exist: 
                h_code=company_handler.fetch_some([('id',company_id)])[0].id
                mi_object=MentionIn(gnews_result.url,h_code,None,article_id,company_id)
                mention_in_handler.commit(mi_object)

        
        

def request_with_keyword_old(is_commit=False,db_path=COMPANIES_DB)->dict[str,list[Gnews]]: 
    """request with Gnews API for all company's keywords

    Args:
        db_path (_type_, optional): the sqlite3 database filename. Defaults to COMPANIES_DB.

    Returns:
        dict[str,list[Gnews]]: dictionary of company_id to its list of Gnews 
    """
    company_handler=Object2Relational(Company,db_path)
    cp_keywords_list_by_cp=company_handler.join_table_and_group_concat(Keyword,'keyword')
    cp_gnews_results:dict[str,list[Gnews]]={}
    for cp_data in cp_keywords_list_by_cp: 
        company_id,keywords=cp_data
        query=Gnews.keywords2query(keywords)
        g_request=GnewsRequest(api_key=GNEWS_KEYS)
        g_request.set_q(query)
        g_request.set_max(100)
        gnews_results=single_gnew_request(g_request)
        for gnew_result in gnews_results: 
            gnew_result.set_query(query)
        cp_gnews_results[str(company_id)]=gnews_results
        
    #To commit the result to db
    if is_commit: 
        #Define handlers
        article_handler=Object2Relational(Article)
        mention_in_handler=Object2Relational(MentionIn)
        
        
        #loop though all company
        for cp_id,gnews in cp_gnews_results.items(): 
            #loop though all news in a company
            for one_gnews in gnews: 
                article_exist=article_handler.check_if_exist('url',one_gnews.url)
                if not article_exist: 
                    article_handler.commit(one_gnews)
                    
                    #url,h_code,,article_id,company_id
                    url=one_gnews.url
                    h_code=company_handler.fetch_some([('id',cp_id)])[0].h_code
                    article_id=article_handler.fetch_some([('url',url)])[0].id
                    mi_object=MentionIn(url,h_code,None,article_id,cp_id)
                    mention_exist=mention_in_handler.check_if_exist_unique_tuples([('article_id',article_id),('company_id',cp_id)])
                    if not mention_exist: 
                        mention_in_handler.commit(mi_object)
                    
    return cp_gnews_results


        
        