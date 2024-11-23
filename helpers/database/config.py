import psycopg2

class Database:
    postgres = None
    
    def __init__(self, db_name=None, db_user=None, db_password=None, db_host=None, db_port=None):
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        
    def setConfig(self, db_name, db_user, db_password, db_host, db_port):
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        
    def connect(self):
        try:
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
        
