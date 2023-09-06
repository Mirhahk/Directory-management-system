import os
import sqlite3
import pandas as pd
from flask import Flask, request, render_template, jsonify, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DB_NAME = 'SSGC.db'
TABLE_NAME = 'employees'
processing_data = False  # Flag to indicate if data is being processed


def load_data_to_database(file_path):
    global processing_data
    try:
        processing_data = True  # Set the flag to True during data processing
        clear_data()  # Clear the table before inserting new data

        df = pd.read_excel(file_path)

        column_mapping = {
            'NAME': 'Name',
            'DESIGNATION': 'Designation',
            'DEPARTMENT': 'Department',
            'PABX': 'PABX',
            'M/W': 'MW',
            'Direct Line': 'Direct line',
            'Fax Line': 'Fax line',
        }

        # Rename DataFrame columns to match database columns
        df.rename(columns=column_mapping, inplace=True)

        conn = sqlite3.connect(DB_NAME)
        df.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
        conn.close()
    except Exception as e:
        print("Error:", e)
    finally:
        processing_data = False  # Set the flag back to False after data processing is complete


# Add a function to clear the data in the table
def clear_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(f'DELETE FROM {TABLE_NAME}')
    conn.commit()

    cursor.close()
    conn.close()


# Call clear_data() before starting the Flask app
# clear_data()


@app.route('/', methods=['GET', 'POST'])
def index():
    global processing_data
    if request.method == 'POST':
        if processing_data:
            return render_template('index.html', error='Data is being processed. Please wait until it is completed.')

        if 'file' not in request.files:
            return render_template('index.html', error='No file part')

        file = request.files['file']
        if file.filename == '':
            return render_template('index.html', error='No selected file')

        if file and file.filename.endswith('.xlsx'):
            # Check if the file is already uploaded
            uploaded_files = session.get('uploaded_files', [])
            if file.filename in uploaded_files:
                return render_template('index.html', error='The file is already uploaded.')

            # Add the filename to the list of uploaded files in the session
            uploaded_files.append(file.filename)
            session['uploaded_files'] = uploaded_files

            # Delete the previous file if it exists
            if os.path.exists(file.filename):
                os.remove(file.filename)

            file.save(file.filename)
            load_data_to_database(file.filename)
            os.remove(file.filename)  # Delete the uploaded file after loading data
            return "File uploaded and data added to the database successfully!"
        else:
            return render_template('index.html', error='Invalid file format. Please upload a .xlsx file.')

    return render_template('index.html', error='')


def fetch_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, Name, Department, Designation FROM ' + TABLE_NAME)
    rows = cursor.fetchall()
    # Convert rows to a list of dictionaries
    column_names = [description[0] for description in cursor.description]
    data = [dict(zip(column_names, row)) for row in rows]
    cursor.close()
    conn.close()

    return data


@app.route('/GetData', methods=['GET'])
def get_data():
    data = fetch_data()
    return jsonify(data)


@app.route('/update', methods=['POST'])
def update():
    record_id = request.form['id']
    designation = request.form['designation']
    department = request.form['department']

    if designation and department:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Update the record in the database
        query = f"UPDATE {TABLE_NAME} SET Designation=?, Department=? WHERE id=?"
        cursor.execute(query, (designation, department, record_id))
        conn.commit()

        cursor.close()
        conn.close()

        return "Record updated successfully!"
    else:
        return "Designation and Department cannot be empty."


@app.route('/delete', methods=['POST'])
def delete():
    record_id = request.form['id']

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Delete the record from the database
    query = f"DELETE FROM {TABLE_NAME} WHERE id=?"
    cursor.execute(query, (record_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return "Record deleted successfully!"


@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    designation = request.form['designation']
    department = request.form['department']

    if name and designation and department:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Insert the record into the database
        query = f"INSERT INTO {TABLE_NAME} (Name, Designation, Department) VALUES (?, ?, ?)"
        cursor.execute(query, (name, designation, department))
        conn.commit()

        cursor.close()
        conn.close()

        return "Record added successfully!"
    else:
        return "Please enter all fields."


# Add the route handler for the "View" page
@app.route('/view', methods=['GET'])
def view():
    return render_template('view.html')


if __name__ == '__main__':
    app.run(debug=True)
