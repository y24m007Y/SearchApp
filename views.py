from flask import render_template, url_for, request, redirect, session, g
from SearchApp import app
from QiitaSearch import BM25, VecSearch, RankFusion, search_dict, TagComb
import numpy as np
import colorsys

app.secret_key = 'your_secret_key'

def sort_tags(taglist):
    taglist = list(set(taglist))
    sort_index = np.argsort([g.tagdb.getCount(tag)[0] for tag in taglist])[::-1]
    taglist = [taglist[i] for i in sort_index]
    return taglist

def connect_tagdb():
    if "tagdb" not in g:
        g.tagdb = search_dict.tagDB()
        g.tagdb.connect_database()
        
def make_color(tag):
    count = g.tagdb.getCount(tag)
    hue = 1/count[0]
    rgb = colorsys.hsv_to_rgb(hue, 1, 1)
    return '#%02x%02x%02x' % (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

def init_session():
    if session.get('init') is None:
        session['init'] = True
        session.pop('query', None)
        session.pop('results', None)
        session.pop('template-tags', None)
        session.pop('add_tags', None)
        session.pop('taglist', None)

@app.after_request
def close_tagdb(response):
    db = getattr(g, "tagdb", None)
    if db is not None:
        db.close_database()
    return response

@app.route('/')
def create_app():
    session.clear()
    init_session()
    return render_template('index.html')

@app.route('/reset')
def reset_session():
    session.clear()
    init_session()
    return render_template("/reset.html")

@app.route('/search_page', methods=['POST', 'GET'])
def search_page():
    connect_tagdb()
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
        session['query'] = query
        session['results'] = results
        return redirect(url_for('result_page'))
    else:
            if session.get('template-tags') is None:
                top_10_tags = g.tagdb.getTaglist(top_n=10, sorted=True)
                session['template-tags'] = list(top_10_tags)
                print(top_10_tags)
                session['taglist'] = session.get('template-tags')
            else:
                if session.get('add_tags') is not None:
                    tmp = session.pop('taglist', None)
                    tmp.extend(session.get('add_tags'))
                    session['taglist'] = sort_tags(tmp)
            return render_template('/search_page.html', tags=session.get('taglist'))

@app.route('/result_page', methods=['POST', 'GET'])
def result_page():
    connect_tagdb()
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
        taglist = sort_tags(taglist)
        return render_template('/result_page.html', query=query, results=results, taglist=taglist)

@app.route('/tag_links', methods=["POST", 'GET'])
def tag_links():
    connect_tagdb()
    tag_comb = TagComb.tagcomb()
    tagnet_list = session.get('taglist')
    tagnet_list = sort_tags([tag for tag in tagnet_list if tag in tag_comb.bool_table.tags.to_list()])
    if request.method=="POST":
        core_tag = request.form['tag']
        tag_network = tag_comb.simulate(core_tag).to_numpy()
        nodes = [{'data': {'id': tag, 'color': make_color(tag), 'count':g.tagdb.getCount(tag)[0]}} for tag in tag_network]
        edges = [{'data': {'source': core_tag, 'target': tag_network[i], 'width': len(tag_network)-i}} for i in range(len(tag_network)) if tag_network[i] != core_tag]
        return render_template('/tag_links.html', taglist=tagnet_list, nodes=nodes, edges=edges)
    else:
        return  render_template('/tag_links.html', taglist=tagnet_list, nodes=[], edges=[])
