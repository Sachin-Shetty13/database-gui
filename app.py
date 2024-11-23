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
    
    try:
        cursor = database.getCursor()
        
        cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
        resultColumns = cursor.fetchall()
        
        cursor.execute(f"SELECT * FROM {table}")
        resultRows = cursor.fetchall()
    
    except Exception as e:
        database.postgres.rollback()
        return jsonify(error=': '.join(str(e).replace('\n', ' ').split(':')))
    
    finally:
        cursor.close()
    
    cursor.close()
    return jsonify(rows=resultRows, columns=[column[0] for column in resultColumns], columnTypes=[column[1] for column in resultColumns])

@app.route('/addItem', methods=['POST'])
def addItem():
    table = request.args.get('table')
    data = request.json
    
    try:
        cursor = database.getCursor()
        cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
        resultColumns = cursor.fetchall()
        
        columns = [column[0] for column in resultColumns]
        
        cursor.execute(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['%s' for _ in data])})", data)
        database.postgres.commit()
        
        cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
        resultColumns = cursor.fetchall()
        
        cursor.execute(f"SELECT * FROM {table}")
        resultRows = cursor.fetchall()
    except Exception as e:
        database.postgres.rollback()
        return jsonify(error=': '.join(str(e).replace('\n', ' ').split(':')))
    finally:
        cursor.close()
    
    cursor.close()
    return jsonify(rows=resultRows, columns=[column[0] for column in resultColumns], columnTypes=[column[1] for column in resultColumns])

@app.route('/updateItem', methods=['POST'])
def updateItem():
    table = request.args.get('table')
    data = request.json
    
    print(data, table)
    
    try:
        cursor = database.getCursor()
        cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
        resultColumns = cursor.fetchall()
        
        columns = [column[0] for column in resultColumns]
        cursor.execute(f"UPDATE {table} SET {', '.join([f'{column} = %s' for column in columns])} WHERE id = %s", (*data['values'], data['id']))
        database.postgres.commit()
    except Exception as e:
        database.postgres.rollback()
        cursor.close()
        return jsonify(error=': '.join(str(e).replace('\n', ' ').split(':')))
    
    cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
    resultColumns = cursor.fetchall()
    
    cursor.execute(f"SELECT * FROM {table}")
    resultRows = cursor.fetchall()
    
    cursor.close()
    return jsonify(rows=resultRows, columns=[column[0] for column in resultColumns], columnTypes=[column[1] for column in resultColumns])

@app.route('/deleteItem', methods=['POST'])
def deleteItem():
    table = request.args.get('table')
    data = request.json
    
    
    try:
        cursor = database.getCursor()
        cursor.execute(f"DELETE FROM {table} WHERE id = %s", (data['id'],))
        database.postgres.commit()
        
        cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
        resultColumns = cursor.fetchall()
        
        cursor.execute(f"SELECT * FROM {table}")
        resultRows = cursor.fetchall()
    except Exception as e:
        database.postgres.rollback()
        return jsonify(error=': '.join(str(e).replace('\n', ' ').split(':')))
    finally:
        cursor.close()
        
    return jsonify(rows=resultRows, columns=[column[0] for column in resultColumns], columnTypes=[column[1] for column in resultColumns])

@app.route('/createTable', methods=['POST'])
def createTable():
    data = request.json
    table_name = data['table_name']
    columns = data['columns']
    
    if not table_name or not columns:
        return jsonify(error='Please fill in all fields')
    
    table_name = table_name.replace(' ', '_').lower()
    
    column_list = [f"id SERIAL PRIMARY KEY"] + [f"{column['name'].replace(' ', '_').lower()} {column['type']}" for column in columns]
    print(f"CREATE TABLE {table_name} ({', '.join(column_list)})")
    
    try:
        cursor = database.getCursor()
        cursor.execute(f"CREATE TABLE {table_name} ({', '.join(column_list)})")
        database.postgres.commit()
        
        cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")
        resultColumns = cursor.fetchall()
        
        cursor.execute(f"SELECT * FROM {table_name}")
        resultRows = cursor.fetchall()
    except Exception as e:
        database.postgres.rollback()
        cursor.close()
        return jsonify(error=': '.join(str(e).replace('\n', ' ').split(':')))
    finally:
        cursor.close()
        
    return jsonify(rows=resultRows, columns=[column[0] for column in resultColumns], columnTypes=[column[1] for column in resultColumns])

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run(debug=True)