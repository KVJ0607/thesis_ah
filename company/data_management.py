from utils.constant import COMPANIES_DB
def init_db():
    import sqlite3
    conn = sqlite3.connect(COMPANIES_DB)    
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS company;''')
    c.execute('''DROP TABLE IF EXISTS keyword;''')
    c.execute('''
        CREATE TABLE company(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            h_code TEXT UNIQUE NOT NULL,
            a_code TEXT UNIQUE NOT NULL,
            zh_name TEXT, 
            en_name TEXT
        )'''
        )
    c.execute('''
            CREATE TABLE keyword(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                h_code TEXT,
                a_code TEXT, 
                zh_name TEXT,
                en_name TEXT,
                
                company_id INTEGER, 
                FOREIGN KEY (company_id) REFERENCES company (id)
                
              )
              ''')
    c.execute('''
            CREATE TABLE index_company(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flag TEXT NOT NULL, 
                listed_region TEXT NOT NULL,
                name TEXT,
                code TEXT,
            )
              ''')
    #date should be ISO8601 Strings
    c.execute('''
            CREATE TABLE pricing(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL, 
                open REAL, 
                high REAL, 
                low REAL,
                close REAL, 
                adjusted_close REAL NOT NULL, 
                volume REAL,
                flag TEXT NOT NULL, 
                lised_region TEXT NOT NULL,

                company_id INTEGER,
                index_company_id INTEGER,
                
                FOREIGN KEY(company_id) REFERENCES company (id),
                FOREIGN KEY(index_company_id) REFERENCES index_company(id)
              )
              ''')
    c.execute('''
              CREATE TABLE return(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT NOT NULL, 
                  return REAL NOT NULL, 
                  type TEXT NOT NULL, 
                  flag TEXT NOT NULL,
                  listed_region TEXT NOT NULL, 
                  
                  company_id INTERGER,
                  index_company_id INTEGER,
                  pricing_id INTERGER,
                  
                  FOREIGN KEY(company_id) REFERENCES company(id),
                  FOREIGN KEY(index_company_id) REFERENCES index_company(id),
                  FOREIGN KEY(pricing_id) REFERENCES pricing(id)
                  )
                ''')
    c.execute('''
              CREATE TABLE car3(
              id INTEGER PRIMARY KEY AUTOINCREMENT, 
              date TEXT NOT NULL, 
              car3 REAL NOT NULL, 
              flag TEXT NOT NULL, 
              
              company_id TEXT NOT NULL, 
              last_day_return_id TEXT,
              today_return_id TEXT,
              next_day_return_id TEXT,
              FOREIGN KEY(company_id) REFERENCES company(id),
              FOREIGN KEY(last_day_return_id) REFERENCES return(id),
              FOREIGN KEY(today_return_id) REFERENCES return(id),
              FOREIGN KEY(next_day_return_id) REFERENCES return(id)
              )
              ''')
    c.execute('''
            CREATE TABLE article(
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                url TEXT UNIQUE NOT NULL, 
                title TEXT,
                published_at TEXT,
                api TEXT, 
            )
              ''')
    c.execute('''
            CREATE TABLE tonescore(
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                article_id INTEGER NOT NULL,
                tonescore REAL, 
                positive_tonescore REAL, 
                negative_tonescore REAL, 
                url TEXT NOT NULL, 
                title TEXT NOT,
                published_at TEXT, 
                FOREIGN KEY(article_id) REFERENCES article(id)
            )
              ''')
    c.execute('''
            CREATE TABLE mention_in(
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                article_id INTEGER NOT NULL, 
                company_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                h_code TEXT NOT NULL, 
                FOREIGN KEY(article_id) REFERENCES article(id),
                FOREIGN KEY(company_id) REFERENCES company(id)
            )
              ''')
    c.execute('''
            CREATE TABLE affecting(
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                article_id INTEGER NOT NULL,
                return_id INTEGER,
                url TEXT NOT NULL,
                type TEXT NOT NULL,
                flag TEXT NOT NULL,
                listed_region,
                h_code TEXT NOT NULL,
                FOREIGN KEY(article_id) REFERENCES article(id),
                FOREIGN KEY(return_id) REFERENCES return(id)
            )
              ''')
    conn.commit()
    c.close()
    conn.close()

