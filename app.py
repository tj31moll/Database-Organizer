from flask import Flask, request, render_template
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import onenote
import requests
from bs4 import BeautifulSoup
import sqlite3
import os

app = Flask(__name__)

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
    file = request.files['file']
    text = file.read()

    # Process text using AI/ML algorithms
    # Organize content into categories
    if text.decode('utf-8').startswith('http'):
        # If text is a website URL, parse the website
        website_url = text.decode('utf-8')
        response = requests.get(website_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform([text.decode('utf-8')])
    kmeans = KMeans(n_clusters=3, random_state=0).fit(X)
    category = kmeans.predict(X)[0]

    # Store results in the database
    conn = sqlite3.connect('documents.db')
    c = conn.cursor()
    c.execute("INSERT INTO documents (document_name, category) VALUES (?, ?)",
              (file.filename, category))
    conn.commit()
    conn.close()

    # Upload to OneNote
    client_id = 'YOUR_CLIENT_ID'
    client_secret = 'YOUR_CLIENT_SECRET'
    tenant_id = 'YOUR_TENANT_ID'
    onenote_client = onenote.OneNote(client_id, client_secret, tenant_id)
    notebook_id = 'YOUR_NOTEBOOK_ID'
    section_ids = ['SECTION_ID_0', 'SECTION_ID_1', 'SECTION_ID_2']

    # Create a new page in the specified section
    page_title = file.filename
    page_content = f'<html><body><p>{text.decode("utf-8")}</p></body></html>'
    onenote_client.create_page(page_title, page_content, notebook_id, section_ids[category])

    return 'File uploaded successfully!'

from flask import Flask, render_template, request
import pandas as pd
import sqlite3

app = Flask(__name__)

@app.route('/view_db')
def view_db():
    conn = sqlite3.connect('data.db')
    df = pd.read_sql_query('SELECT * FROM data', conn)
    conn.close()
    return render_template('view_db.html', table=df.to_html(index=False))

 from flask import Flask, render_template, request
import pandas as pd
import sqlite3

app = Flask(__name__)

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
    app.run(debug=True)
