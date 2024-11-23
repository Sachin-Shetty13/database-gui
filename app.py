from flask import Flask, render_template, request, redirect, session
import psycopg2
from helpers.database.config import Database

app = Flask(__name__)

@app.route('/')
def index():
    database_name = session.get('database_name')
    username = session.get('username')
    password = session.get('password')
    
    if database_name and username and password:
        return redirect('/database')
    
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect():
    database_name = request.form.get('connection_string')
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not database_name or not username or not password:
        return redirect('/?error=Please fill in all fields')
    
    session['database_name'] = database_name
    session['username'] = username
    session['password'] = password
    return redirect('/database')
   
@app.route('/database')
def database():
    database_name = session.get('database_name')
    username = session.get('username')
    password = session.get('password')
    
    if not database_name or not username or not password:
        return redirect('/?error=Please connect to a database first')
    
    database_name = "medicause"
    
    try:
        database = Database(db_name=database_name, db_user=username, db_password=password)
        database.connect()
    except Exception as e:
        session.clear()
        return redirect(f'/?error={str(e)}')
    
    cursor = database.getCursor()
    cursor.execute("SELECT table_name FROM %s.tables WHERE table_schema='public'" % "information_schema")
    resultTables = cursor.fetchall()
    tables = []
    
    for table in resultTables:
        tables.append(table[0])
    
    return render_template('database.html', database_name=database_name, tables=tables)

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run(debug=True)