from utils.constant import COMPANIES_DB

def init_db():
    import sqlite3
    conn = sqlite3.connect(COMPANIES_DB)    
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS company;''')
    c.execute('''DROP TABLE IF EXISTS keyword;''')
    #h_code	a_code	zh_name	en_name	id
    c.execute(
        '''
        CREATE TABLE company(
            h_code TEXT UNIQUE NOT NULL,
            a_code TEXT UNIQUE NOT NULL,
            zh_name TEXT, 
            en_name TEXT,
            id INTEGER PRIMARY KEY AUTOINCREMENT
        )
        '''
    )
    c.execute (
        '''
        CREATE TABLE company_mining(
            document_flag INTEGER NOT NULL DEFAULT 0,
            gnews_flag INTEGER NOT NULL DEFAULT 0,  
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER
        )
        ''' 
    )
    
    c.execute(
        '''    
        CREATE TABLE keyword(
            keyword TEXT,
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER, 
            FOREIGN KEY (company_id) REFERENCES company (id)
            )
        '''
    )
    c.execute(
        '''
        CREATE TABLE index_company(
            flag TEXT NOT NULL, 
            listed_region TEXT NOT NULL,
            name TEXT,
            code TEXT,
            id INTEGER PRIMARY KEY AUTOINCREMENT
        )
        '''
    )
    #date should be ISO8601 Strings
    c.execute(
        '''
        CREATE TABLE pricing(        
            date TEXT NOT NULL, 
            open REAL, 
            high REAL, 
            low REAL,
            close REAL, 
            adjusted_close REAL NOT NULL, 
            volume REAL,
            flag TEXT, 
            listed_region TEXT,
            
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            index_company_id INTEGER,
            UNIQUE(company_id,index_company_id,flag,date)
            FOREIGN KEY(company_id) REFERENCES company (id),
            FOREIGN KEY(index_company_id) REFERENCES index_company(id)
        )
        '''
    )
    c.execute(
        '''
        CREATE TABLE return(
            date TEXT NOT NULL, 
            return REAL NOT NULL, 
            type TEXT NOT NULL, 
            flag TEXT NOT NULL,
            listed_region TEXT NOT NULL, 
            
            id INTEGER PRIMARY KEY AUTOINCREMENT,  
            company_id INTERGER,
            index_company_id INTEGER,
            pricing_id INTERGER,
            
            UNIQUE(company_id, index_company_id,flag,type,date)
            FOREIGN KEY(company_id) REFERENCES company(id),
            FOREIGN KEY(index_company_id) REFERENCES index_company(id),
            FOREIGN KEY(pricing_id) REFERENCES pricing(id)
        )
        '''
    )
    c.execute(
        '''
        CREATE TABLE car3(
            date TEXT NOT NULL, 
            car3 REAL NOT NULL, 
            flag TEXT NOT NULL, 
          
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            company_id TEXT NOT NULL, 
            last_day_return_id TEXT,
            today_return_id TEXT,
            next_day_return_id TEXT,
            
            UNIQUE(company_id, flag,date)
            FOREIGN KEY(company_id) REFERENCES company(id),
            FOREIGN KEY(last_day_return_id) REFERENCES return(id),
            FOREIGN KEY(today_return_id) REFERENCES return(id),
            FOREIGN KEY(next_day_return_id) REFERENCES return(id)
            )
        '''
    )

    c.execute(
        '''
        CREATE TABLE car3_dual(
            acar3_id NOT NULL
            hcar3_id NOT NULL
            date TEXT NOT NULL, 

          
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            UNIQUE(acar3_id,hcar3_id),
            FOREIGN KEY(acar3_id) REFERENCES car3(id)
            FOREIGN KEY(hcar3_id) REFERENCES car3(id)
            )
        '''
    )
    
    c.execute(
        '''
        CREATE TABLE article(
            url TEXT UNIQUE NOT NULL, 
            title TEXT,
            published_at TEXT,
            api TEXT, 
            content TEXT,
            id INTEGER PRIMARY KEY AUTOINCREMENT
        )
        '''
    )
    c.execute(
        '''
        CREATE TABLE query(
            query TEXT NOT NULL,
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            article_id INTEGER, 
            FOREIGN KEY(article_id) REFERENCES article(id)
        )
        '''
    )
    c.execute(
        '''
        CREATE TABLE document(
            url TEXT NOT NULL,
            title TEXT,
            published_at TEXT,
            source TEXT, 
            content TEXT,
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            company_id INTEGER,
            UNIQUE(url,company_id),
            FOREIGN KEY(company_id) REFERENCES company(id)
        )
        '''
    )
    c.execute(
        '''
        CREATE TABLE tonescore(
            tonescore REAL, 
            positive_tonescore REAL, 
            negative_tonescore REAL,                                     
            id INTEGER PRIMARY KEY AUTOINCREMENT,         
            document_id INTEGER NOT NULL,
            company_id INTEGER,            
            FOREIGN KEY(document_id) REFERENCES document(id),
            FOREIGN KEY(company_id) REFERENCES company(id)
        )
        '''
    )
    c.execute(
        '''
        CREATE TABLE tonescore_merge(
            tonescore REAL, 
            positive_tonescore REAL, 
            negative_tonescore REAL,       
            date TEXT NOT NULL,                              
            id INTEGER PRIMARY KEY AUTOINCREMENT,         
            company_id INTEGER,            
            FOREIGN KEY(company_id) REFERENCES company(id)
        )
        '''
    )
    
    c.execute(
        '''
        CREATE TABLE mention_in(
            url TEXT NOT NULL,
            h_code TEXT NOT NULL, 
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            article_id INTEGER NOT NULL, 
            company_id INTEGER NOT NULL,
            UNIQUE(article_id, company_id)
            FOREIGN KEY(article_id) REFERENCES article(id),
            FOREIGN KEY(company_id) REFERENCES company(id)
        )
        '''
    )
    c.execute(
        '''
        CREATE TABLE affecting(
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            article_id INTEGER NOT NULL,
            car3_id INTEGER,
            return_id INTEGER,
            company_id INTEGER,
            UNIQUE(article_id, car3_id,return_id)
            FOREIGN KEY(article_id) REFERENCES article(id),
            FOREIGN KEY(car3_id)  REFERENCES car3(id),
            FOREIGN KEY(return_id) REFERENCES return(id),
            FOREIGN KEY(company_id) REFERENCES company(id)
        )
        '''
    )
    c.execute(
        '''
        CREATE TABLE causing(
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            document_id INTEGER NOT NULL,
            car3_id INTEGER,
            return_id INTEGER,
            company_id INTEGER,
            UNIQUE(document_id, car3_id,return_id)
            FOREIGN KEY(document_id) REFERENCES document(id),
            FOREIGN KEY(car3_id)  REFERENCES car3(id),
            FOREIGN KEY(return_id) REFERENCES return(id),
            FOREIGN KEY(company_id) REFERENCES company(id)                
        )
        '''
    )
    conn.commit()
    c.close()
    conn.close()

