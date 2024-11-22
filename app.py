from flask import Flask, render_template, request, redirect, session
import psycopg2

app = Flask(__name__)

@app.route('/')
def index():
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
    
    try:
        postgres = psycopg2.connect(database=database_name, user=username, password=password, host='localhost', port='5432')
    except Exception as e:
        errorMsg = str(e).split(':')[-1].strip()
            
        return redirect(f'/?error=Connection failed: {errorMsg}')
    
    return render_template('database.html')

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run(debug=True)