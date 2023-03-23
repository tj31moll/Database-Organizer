from flask import Flask, request, render_template
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import onenote
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
    client_id = os.environ.get('ONENOTE_CLIENT_ID')
    client_secret = os.environ.get('ONENOTE_CLIENT_SECRET')
    tenant_id = os.environ.get('ONENOTE_TENANT_ID')
    onenote_client = onenote.OneNote(client_id, client_secret, tenant_id)
    notebook_id = os.environ.get('ONENOTE_NOTEBOOK_ID')
    section_id = os.environ.get(f'ONENOTE_SECTION_ID_{category}')

    # Create a new page in the specified section
    page_title = file.filename
    page_content = f'<html><body><p>{text.decode("utf-8")}</p></body></html>'
    onenote_client.create_page(page_title, page_content, notebook_id, section_id)

    return 'File uploaded successfully!'

if __name__ == '__main__':
    app.run(debug=True)
