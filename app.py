from flask import Flask, render_template, request, redirect, session, jsonify
import psycopg2
from helpers.database.config import Database

app = Flask(__name__)
database = Database()

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
def databaseFunc():
    database_name = session.get('database_name')
    username = session.get('username')
    password = session.get('password')
    
    if not database_name or not username or not password:
        return redirect('/?error=Please connect to a database first')
    
    try:
        database.setConfig(database_name, username, password, 'localhost', 5432)
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
        
    cursor.close()
    
    return render_template('database.html', database_name=database_name, tables=tables)

@app.route('/disconnect', methods=['GET'])
def disconnect():
    session.clear()
    return redirect('/')


@app.route('/getTableData', methods=['GET'])
def getTableData():
    table = request.args.get('table')
    cursor = database.getCursor()
    
    cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
    resultColumns = cursor.fetchall()
    
    cursor.execute(f"SELECT * FROM {table}")
    resultRows = cursor.fetchall()
    
    cursor.close()
    return jsonify(rows=resultRows, columns=[column[0] for column in resultColumns])

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run(debug=True)