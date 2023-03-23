import pandas as pd
from flask import Flask, render_template, request
from flask import Flask, request, render_template, redirect
import requests
from bs4 import BeautifulSoup
import sqlite3
import os
from transformers import pipeline
from microsoftgraph.client import Client
from msal import ConfidentialClientApplication

app = Flask(__name__)

# Load the pre-trained model
classifier = pipeline("zero-shot-classification",
                      model="facebook/bart-large-mnli")

# Create a new SQLite database
conn = sqlite3.connect('documents.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS documents
             (document_id INTEGER PRIMARY KEY AUTOINCREMENT,
              document_name TEXT,
              category TEXT)''')
conn.commit()
conn.close()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    text = request.form.get('text')
    file = request.files.get('file')

    if file and file.filename:
        text = file.read().decode('utf-8')
    elif not text:
        return 'No text or file provided. Please go back and provide text or upload a file.'

    # Process text using zero-shot classification
    if text.startswith('http'):
        # If text is a website URL, parse the website
        website_url = text
        response = requests.get(website_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()

    # Define your categories here
    categories = ["technology", "sports",
                  "politics", "finance", "entertainment"]

    # Organize content into categories
    result = classifier(text, categories)
    category = result["labels"][0]

    # Store results in the database
    conn = sqlite3.connect('documents.db')
    c = conn.cursor()
    c.execute("INSERT INTO documents (document_name, category) VALUES (?, ?)",
              (file.filename, category))
    conn.commit()
    conn.close()

    # Upload to OneNote
    client_id = 'cd6'
    client_secret = '_CgcwC'
    tenant_id = 'b2578'
    authority = f'https://login.microsoftonline.com/{tenant_id}'
    scope = ['https://graph.microsoft.com/.default']

    app = ConfidentialClientApplication(client_id, client_secret, authority)
    result = app.acquire_token_for_client(scope)
    if "access_token" in result:
        access_token = result['access_token']
    else:
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))

    headers = {'Authorization': f'Bearer {access_token}'}
    notebook_id = 'YOUR_NOTEBOOK_ID'
    section_ids = ['SECTION_ID_0', 'SECTION_ID_1', 'SECTION_ID_2']

    # Create a new page in the specified section
    page_title = file.filename if file else "text_input"
    page_content = f'<html><head><title>{page_title}</title></head><body><p>{text}</p></body></html>'
    url = f'https://graph.microsoft.com/v1.0/me/onenote/notebooks/{notebook_id}/sections/{section_ids[category]}/pages'
    response = requests.post(url, headers={
                             'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/xhtml+xml'}, data=page_content)

    return 'File uploaded successfully!'


# The rest of the code remains the same


@app.route('/view_db', methods=['GET', 'POST'])
def view_db():
    conn = sqlite3.connect('data.db')
    df = pd.read_sql_query('SELECT * FROM data', conn)
    conn.close()

    if request.method == 'POST':
        # Get the edited row values
        row_id = request.form['row_id']
        new_values = {}
        for key in request.form.keys():
            if key != 'row_id':
                new_values[key] = request.form[key]

        # Update the database with the new values
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute(f"UPDATE data SET {','.join([f'{key} = ?' for key in new_values.keys()])} WHERE index = ?", tuple(
            new_values.values()) + (row_id,))
        conn.commit()
        conn.close()

        return redirect('/view_db')

    return render_template('view_db.html', table=df.to_html(index=False, classes='table table-bordered table-hover'))


@app.route('/upload_csv', methods=['GET', 'POST'])
def upload_csv():
    if request.method == 'POST':
        file = request.files['file']
        df = pd.read_csv(file)
        conn = sqlite3.connect('data.db')
        df.to_sql(name='data', con=conn)
        conn.close()
        return 'File uploaded successfully and converted to SQL database!'
    return render_template('upload_csv.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3636, debug=True)
