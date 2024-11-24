import psycopg2
import os

class Database:
    postgres = None
    
    def __init__(self, db_name=None):
        self.db_name = db_name
        self.db_user = os.environ.get('DB_USER')
        self.db_password = os.environ.get('DB_PASSWORD')
        self.db_host = os.environ.get('DB_HOST')
        self.db_port = os.environ.get('DB_PORT')
        
    def setConfig(self, db_name):
        self.db_name = db_name
        
    def connect(self):
        try:
            print(self.db_name, self.db_user, self.db_password, self.db_host, self.db_port)
            self.postgres = psycopg2.connect(database=self.db_name, user=self.db_user, password=self.db_password, host=self.db_host, port=self.db_port)
        except Exception as e:
            errorMsg = str(e).split(':')[-1].strip()
            raise Exception(f'Connection failed: {errorMsg}')
        
    def getCursor(self):
        if self.postgres is None:
            self.connect()
            
        return self.postgres.cursor()
    
    def close(self):
        self.postgres.close()
        
