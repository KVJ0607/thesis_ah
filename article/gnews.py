from datetime import date
import json 

import ssl
from urllib.request import urlopen
from urllib.error import HTTPError
from http.client import InvalidURL

from company.company import *
class GnewsRequest: 
    EndPoint_Template='https://gnews.io/api/v4/serarch?{}'
    def __init__(self,api_key):
        self.__api_key=api_key
        self.__q='None'
        self.__lang='Any'
        self.__country='Any'
        self.__max='10'
        self.__in='None'
        self.__nullable='None'
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
        return f'api_key={self.__api_key}&q={self.__q}&lang={self.__lang}&country={self.__country}&max={self.__max}&in={self.__in}&nullable{self.__nullable}&from={self.__from}&to={self.__to}&sortby={self.__sortby}&page={self.__page}&expand={self.__expand}'
        
    def to_request(self)->str:     
        """Return the request url for the query. 
        This is the final url, not merely the endpoint. 

        Returns:
            str: final url for requests
        """
        return GnewsRequest.EndPoint_Template.format(self.to_endpoint())

class Gnews(Article):
    @classmethod
    def db_insert_col(cls)->str: 
        return 'url,title,publish_at,api,content'
        
    def __init__(self,url:str,title:str,published_at:datetime|str,description:str,content:str,source_name:str,id:int|None=None): 
        super().__init__(url,title,published_at,'gnews',content,id)
        self.__description=description
        self.__source_name=source_name
    
    @classmethod
    def from_dict(cls,data): 
        return cls(data['url'],data['title'],data['publishedAt'],data['description'],data['content'],data['source']['name'])
    
    @property
    def url(self): 
        return super().url
    @property
    def title(self):
        return super().title
    @property
    def published_at(self):
        return super().published_at()
    @property
    def api(self):
        return super().api
    @property
    def content(self): 
        return super().content
        
    def to_tuple(self)->tuple: 
        return(self.url,self.title,self.published_at,self.api,self.content,self.id)
    def to_insert_para(self)->tuple: 
        """
        (?url,?title,?publish_at,?api,?content)
        """
        return(self.url,self.title,self.published_at,self.api,self.content)
    

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
                    article_in_gnews=Gnews.from_dict(articles_in_json[i])
                    article_list_of_gnews.append(article_in_gnews)
                result=result+article_list_of_gnews
        except(HTTPError,InvalidURL): 
            print(gnews_request.__q)
            raise(ValueError("END"))
    return result

    