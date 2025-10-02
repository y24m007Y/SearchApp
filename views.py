from flask import render_template, url_for, request, redirect, session
from SearchApp import app
from QiitaSearch import BM25, VecSearch, RankFusion, search_dict
import itertools

app.secret_key = 'your_secret_key'

@app.route('/')
def create_app():
    return render_template('index.html')

@app.route('/search_page', methods=['POST', 'GET'])
def search_page():
    if request.method=="POST":
        query = request.form['query']
        argorithm = request.form['argoritm']
        tags = request.form.getlist('tag')
        if argorithm=="0":
            engin = BM25.bm25()
        elif argorithm=="1":
            engin = VecSearch.vec_search()
        elif argorithm=="2":
            engin = RankFusion.RRF()
        else:
            print("適切なフォームが送信されていません")
            return
        results = engin.search(query, tags)
        print(tags)
        session['query'] = query
        session['results'] = results
        return redirect(url_for('result_page'))
    else:
        if session:
            session.pop("query", None)
            session.pop("results", None)
        else:
            tagdb = search_dict.tagDB()
            tagdb.connect_database()
            top10_tags = tagdb.getTaglist(top_n=10, sorted=True)
            session["template-tags"] = top10_tags
            tagdb.close_database()
            del tagdb
        return render_template('/search_page.html', tags=session.get('template-tags'))

@app.route('/result_page/', methods=['POST', 'GET'])
def result_page():
    if request.method=="POST":
        #####
        print("hello")
    else:
        query = session.get('query')
        results = session.get('results')
        tmp = [result['tags'] for result in results]
        taglist = []
        for tags in tmp:
            taglist.extend(tags)
        taglist = set(taglist)
        return render_template('/result_page.html', query=query, results=results, taglist=list(taglist))

@app.route('/tag_links')
def tag_links():
    return        
