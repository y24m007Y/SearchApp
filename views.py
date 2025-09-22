from flask import render_template, url_for, request
from SearchApp import app
from Searcher import BM25, VecSearch, RankFusion, searcher

@app.route('/')
def create_app():
    return render_template('index.html')

@app.route('/search_page', methods=['GET', 'POST'])
def search_page():
    if request.method == "POST":
        query = request.form['query']
        argorithm = request.form['argoritm']
        if argorithm=="0":
            engin = BM25.bm25()
        elif argorithm=="1":
            engin = VecSearch.vec_search()
        elif argorithm=="2":
            engin = RankFusion.RRF()
        else:
            print("適切なフォームが送信されていません")
            return
        results = engin.search(query)
        return render_template('/result_page.html', query=query, results=results)
    else:
        return render_template('/search_page.html')

"""
@app.route('/hello/')
@app.route('/hello/<name>')
def hello_world(name=None):
    return render_template('hello.html', name=name)
"""