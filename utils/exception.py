class MaxErrorReached(Exception): 
    def __init__(self,urls:list[str]=None,cp_id:str=None):
        if urls is None and cp_id is None: 
            message=''
        else:
            message=f'Maximum error has reached for {cp_id}\n number of problematic url:{len(urls)}' 
            urls_message=''
            for url in urls: 
                urls_message=urls_message+f'\n{url}'
            message=message+urls_message
        super().__init__(message) 
        
        
