from flask import render_template, url_for, request, redirect, session
from SearchApp import app
from QiitaSearch import BM25, VecSearch, RankFusion, search_dict, TagComb
import itertools

app.secret_key = 'your_secret_key'
tag_comb = TagComb.tagcomb()

@app.before_request
def init_session():
    if session.get('init') is None:
        session['init'] = True
        session.pop('query', None)
        session.pop('results', None)
        session.pop('template-tags', None)
        session.pop('add_tags', None)
        session.pop('taglist', None)

@app.route('/')
def create_app():
    init_session()
    return render_template('index.html')

@app.route('/reset')
def reset_session():
    session.clear()
    init_session()
    return render_template("/reset.html")

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
            if session.get('template-tags') is None:
                tagdb = search_dict.tagDB()
                top_10_tags = tagdb.getTaglist(top_n=10, sorted=True)
                session['template-tags'] = list(top_10_tags)
                tagdb.close_database()
                session['taglist'] = session.get('template-tags')
            else:
                if session.get('add_tags') is not None:
                    tmp = session.pop('taglist', None)
                    tmp.extend(session.get('add_tags'))
                    session['taglist'] = list(set(tmp))
            return render_template('/search_page.html', tags=session.get('taglist'))

@app.route('/result_page', methods=['POST', 'GET'])
def result_page():
    if request.method=="POST":
        print(request.form.getlist('add_tags'))
        session['add_tags'] = request.form.getlist('add_tags')
        return redirect(url_for('search_page'))
    else:
        query = session.get('query')
        results = session.get('results')
        tmp = [result['tags'] for result in results]
        taglist = []
        for tags in tmp:
            taglist.extend(tags)
        taglist = set(taglist)
        return render_template('/result_page.html', query=query, results=results, taglist=list(taglist))

@app.route('/tag_links', methods=["POST", 'GET'])
def tag_links():
    tagnet_list = session.get('taglist')
    print(tagnet_list, tag_comb.bool_table.tags)
    tagnet_list = [tag for tag in tagnet_list if tag in tag_comb.bool_table.tags.to_list()]
    if request.method=="POST":
        core_tag = request.form['tag']
        #tagcomb = TagComb.tagcomb()
        tag_network = tag_comb.simulate(core_tag).to_numpy()
        print(tag_network)
        #nodes = [{'data': {'id':tag_network[i]}}  for i in range(len(tag_network))]
        #edges = {'data': {'source':core_tag, 'target':tag_network[i], 'width':len(tag_network)-i} for i in range(len(tag_network))}
        nodes = [{'data': {'id': tag_network[i]}} for i in range(len(tag_network))]
        edges = [{'data': {'source': core_tag, 'target': tag_network[i], 'width': len(tag_network)-i}} for i in range(len(tag_network)) if tag_network[i] != core_tag]
        print(nodes, edges)
        return render_template('/tag_links.html', taglist=tagnet_list, nodes=nodes, edges=edges)
    else:
        return  render_template('/tag_links.html', taglist=tagnet_list, nodes=[], edges=[])
