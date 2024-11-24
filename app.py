from flask import render_template, request, redirect, session, jsonify
from helpers.database.config import Database
from create_app import create_app

app = create_app()
database = Database()

@app.route('/')
def index():
    database_name = session.get('database_name')
    
    if database_name:
        return redirect('/database')
    
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect():
    database_name = request.form.get('connection_string')
    
    if not database_name:
        return redirect('/?error=Please fill in all fields')
    
    session['database_name'] = database_name.replace(' ', '_').lower()
    return redirect('/database')

@app.route('/createDatabase', methods=['POST'])
def createDatabase():
    database_name = request.form.get('connection_string')
    
    if not database_name:
        return redirect('/?error=Please fill in all fields')
    
    database_name = database_name.replace(' ', '_').lower()
    cursor = None
    
    try:
        database.setConfig('admin_n27v')
        database.connect()
        database.postgres.autocommit = True
        
        cursor = database.getCursor()
        cursor.execute(f"CREATE DATABASE {database_name}")
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {database_name} TO admin")
    except Exception as e:
        error = ': '.join(str(e).replace('\n', ' ').split(':'))
        return redirect(f'/?error={error}')
    finally:
        if cursor:
            cursor.close()
    
    session['database_name'] = database_name
    
    return redirect('/database')
   
@app.route('/database')
def databaseFunc():
    database_name = session.get('database_name')
    
    if not database_name:
        return redirect('/?error=Please connect to a database first')
    
    try:
        database.setConfig(database_name)
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
        
        cursor.execute(f"Select * FROM {table} LIMIT 0")
        colnames = [desc[0] for desc in cursor.description]
        
        finalColumns = []
        for column in colnames:
            for col in resultColumns:
                if col[0] == column:
                    finalColumns.append((col[0], col[1]))
                    break
        
        cursor.execute(f"SELECT * FROM {table}")
        resultRows = cursor.fetchall()
    
    except Exception as e:
        database.postgres.rollback()
        return jsonify(error=': '.join(str(e).replace('\n', ' ').split(':')))
    
    finally:
        cursor.close()
        
    cursor.close()
    return jsonify(rows=resultRows, columns=[column[0] for column in finalColumns], columnTypes=[column[1] for column in finalColumns])

@app.route('/addItem', methods=['POST'])
def addItem():
    table = request.args.get('table')
    data = request.json
    
    try:
        cursor = database.getCursor()
        cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
        resultColumns = cursor.fetchall()
        
        columns = [column[0] for column in resultColumns]
        
        cursor.execute(f"Select * FROM {table} LIMIT 0")
        colnames = [desc[0] for desc in cursor.description]
        
        finalColumns = []
        for column in colnames:
            for col in resultColumns:
                if col[0] == column:
                    finalColumns.append((col[0], col[1]))
                    break
        
        cursor.execute(f"INSERT INTO {table} ({', '.join(colnames)}) VALUES ({', '.join(['%s' for _ in data])})", data)
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
    return jsonify(rows=resultRows, columns=[column[0] for column in finalColumns], columnTypes=[column[1] for column in finalColumns])

@app.route('/updateItem', methods=['POST'])
def updateItem():
    table = request.args.get('table')
    data = request.json
    
    try:
        cursor = database.getCursor()
        cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
        resultColumns = cursor.fetchall()
        
        columns = [column[0] for column in resultColumns]
        
        cursor.execute(f"Select * FROM {table} LIMIT 0")
        colnames = [desc[0] for desc in cursor.description]
        
        finalColumns = []
        for column in colnames:
            for col in resultColumns:
                if col[0] == column:
                    finalColumns.append((col[0], col[1]))
                    break
        
        cursor.execute(f"UPDATE {table} SET {', '.join([f'{column} = %s' for column in colnames])} WHERE id = %s", (*data['values'], data['id']))
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
    return jsonify(rows=resultRows, columns=[column[0] for column in finalColumns], columnTypes=[column[1] for column in finalColumns])

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
        
        cursor.execute(f"Select * FROM {table} LIMIT 0")
        colnames = [desc[0] for desc in cursor.description]
        
        finalColumns = []
        for column in colnames:
            for col in resultColumns:
                if col[0] == column:
                    finalColumns.append((col[0], col[1]))
                    break
        
        cursor.execute(f"SELECT * FROM {table}")
        resultRows = cursor.fetchall()
    except Exception as e:
        database.postgres.rollback()
        return jsonify(error=': '.join(str(e).replace('\n', ' ').split(':')))
    finally:
        cursor.close()
        
    return jsonify(rows=resultRows, columns=[column[0] for column in finalColumns], columnTypes=[column[1] for column in finalColumns])

@app.route('/createTable', methods=['POST'])
def createTable():
    data = request.json
    table_name = data['table_name'].replace(' ', '_').lower()
    columns = data['columns']
    
    if not table_name or not columns:
        return jsonify(error='Please fill in all fields')
    
    table_name = table_name.replace(' ', '_').lower()
    
    column_list = [f"id SERIAL PRIMARY KEY"] + [f"{column['name'].replace(' ', '_').lower()} {column['type']}" for column in columns]
    
    try:
        cursor = database.getCursor()
        cursor.execute(f"CREATE TABLE {table_name} ({', '.join(column_list)})")
        database.postgres.commit()
        
        cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")
        resultColumns = cursor.fetchall()
        
        cursor.execute(f"Select * FROM {table_name} LIMIT 0")
        colnames = [desc[0] for desc in cursor.description]
        
        finalColumns = []
        for column in colnames:
            for col in resultColumns:
                if col[0] == column:
                    finalColumns.append((col[0], col[1]))
                    break
        
        cursor.execute(f"SELECT * FROM {table_name}")
        resultRows = cursor.fetchall()
    except Exception as e:
        database.postgres.rollback()
        cursor.close()
        return jsonify(error=': '.join(str(e).replace('\n', ' ').split(':')))
    finally:
        cursor.close()
        
    return jsonify(rows=resultRows, columns=[column[0] for column in finalColumns], columnTypes=[column[1] for column in finalColumns])

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run()