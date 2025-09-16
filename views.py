from flask import render_template
from webapp import app
from Searcher import BM25, VecSearch, searcher

model = searcher.searcher()
#bm25 = BM25.bm25()
#vec_model = VecSearch.vec_search()

@app.route('/')
def create_app():
    return "Hello, World!"

@app.route('/result_page')
def result_page():
    query = "python"
    result_data = model.search(query, top_n=20)
    return render_template('result_page.html', query=query, results=result_data)

@app.route('/hello/')
@app.route('/hello/<name>')
def hello_world(name=None):
    return render_template('hello.html', name=name)