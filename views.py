from flask import render_template, url_for, request, redirect, session, g, jsonify, Blueprint
import numpy as np
import colorsys
from openai import OpenAI
import os, sys
import re
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
import datetime
import time
import inspect
from collections import defaultdict

#記事検索モジュールのパスを指定
sys.path.append("QiitaSearch")

from QiitaSearch import BM25, VecSearch, RankFusion, search_dict, TagComb, logsys

#環境情報の取得
load_dotenv()
#apikeyの設定
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    api_key = os.getenv('OPENAI_KEY')

#タグ説明
explainer = OpenAI(api_key=api_key)

from flask import Blueprint
bp = Blueprint("main_bp", __name__)

def connect_articledb():
    if "articledb" not in g:
        g.articledb = search_dict.articleDB()

def connect_tagdb():
    if "tagdb" not in g:
        g.tagdb = search_dict.tagDB()

def connect_logdb():
    if "logdb" not in g:
        g.logdb = logsys.logDB()

def text_summarizer(text):
    res = explainer.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content":"あなたは情報技術文書の要約専門のアシスタントです"},
            {"role":"user", "content": f"次の文章の要約を100文字以内で作ってください。また、見出しは初心者でも理解できるような内容で1つのみ出力してください{text}"}]
            )
    return res.choices[0].message.content

def article_summarize(article_ids):
    splitters = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="gpt-4o-mini",
        chunk_size=1500,
        chunk_overlap=50
    )
    bodies = dict(g.articledb.getbody(article_ids, isid=True))
    split_body_heads = [splitters.split_text(bodies[key]) for key in article_ids]
    results = [text_summarizer(split_body_head[0]) for split_body_head in split_body_heads]
    return results

def tag_explainer(tag):
    res = explainer.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system", "content":"あなたは情報通信技術の専門家です"},
            {"role":"user", "content":f"次の単語について初心者でも理解できるように100文字程度で簡単に説明してください。{tag}"}
        ]
    )
    return res.choices[0].message.content

def make_color(count):
    hue = 1/count
    rgb = colorsys.hsv_to_rgb(hue, 1, 1)
    return '#%02x%02x%02x' % (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

def init_session():
    if session.get('init') is None:
        session['init'] = True
        session.pop('taglist', None)

@bp.after_request
def close_db(response):
    tagdb = getattr(g, "tagdb", None)
    articledb = getattr(g, "articledb", None)
    if tagdb is not None:
        tagdb.close_database()
    if articledb is not None:
        articledb.close_database()
    return response

@bp.route('/', endpoint='home')
def Startbp():
    session.clear()
    init_session()
    return render_template('/index.html')

@bp.route('/reset', endpoint='reset')
def reset_session():
    session.clear()
    init_session()
    return render_template("/reset.html")

@bp.route('/search_page', methods=['POST', 'GET'], endpoint='search_page')
def search_page():
    connect_tagdb()
    popup = session.pop("popup", None)
    if request.method=="POST":
        connect_logdb()
        start = time.time()
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
        session['article_id'] = results
        session['query_tags'] = tags
        session['search_count'] = session.get('search_count', 0) + 1
        g.logdb.search_time_log(date=datetime.datetime.now(), type=engin.__class__.__name__, exectime=time.time()-start)
        return redirect(url_for('main_bp.result_page'))
    else:
            """
            if session.get('template-tags') is None:
                top_10_tags = g.tagdb.getTaglist(top_n=10, sorted=True)
                session['template-tags'] = list(top_10_tags)
                print(top_10_tags)
                session['taglist'] = session.get('template-tags')
            """
            if session.get('add_tags') is not None:
                tmp = session.get('taglist')
                if tmp is None:
                    tmp = session.pop('add_tags', None)
                else:
                    tmp.extend(session.pop('add_tags', None))
                    tmp = list(set(tmp))
                session['taglist'] = tmp
            return render_template('/search_page.html', popup=popup, tags=session.get('taglist'))

@bp.route('/result_page', methods=['POST', 'GET'], endpoint='result_page')
def result_page():
    connect_tagdb()
    connect_articledb()
    if request.method=="POST":        
        session['add_tags'] = request.form.getlist('add_tags')
        session['popup'] = "タグリストにタグを追加しました!"
        return redirect(url_for('main_bp.search_page'))
    else:
        connect_logdb()
        start = time.time()
        query = session.pop('query', None)
        article_ids = session.pop('article_id', None)
        titles = dict(g.articledb.getTitle(article_ids, isid=True))
        urls =dict(g.articledb.getURL(article_ids, isid=True))
        tags = g.articledb.getTags(article_ids)
        results = [{"title":titles[article_id],"url":urls[article_id], "tags":tags[article_id]} for article_id in article_ids]
        headings = article_summarize(article_ids)
        headings = [re.sub(r"[#\n\u3000\s\t]+", "", heading) for heading in headings]
        result_taglist = defaultdict(int)
        for i in range(len(article_ids)):
            results[i]['heading'] = headings[i]
            for tag in results[i]['tags']:
                result_taglist[tag] += 1
        result_taglist = sorted(result_taglist.items(), key=lambda x: x[1], reverse=True)
        result_taglist = [key for key, value in result_taglist]
        g.logdb.result_page_log(date=datetime.datetime.now(), exectime=time.time()-start, query=query, result_id=article_ids)
        return render_template('/result_page.html', query=query, results=results, taglist=result_taglist[:10])

@bp.route('/tag_links', methods=["POST", 'GET'], endpoint='tag_links')
def tag_links():
    connect_tagdb()
    tag_comb = TagComb.tagcomb()
    tagnet_list = session.get('taglist')
    popup = session.pop('popup', None)
    tagnet_list = tag_comb.check_tag(tagnet_list)
    if request.method=="POST":
        core_tag = request.form['tag']
        session['core_tag'] = core_tag
        tag_network = tag_comb.simulate(core_tag)
        counts = dict(g.tagdb.getCount(tag_network, isname=True))
        nodes = [{'data': {'id': tag, 'color': make_color(counts[tag]), 'count':counts[tag]}} for tag in tag_network]
        edges = [{'data': {'source': core_tag, 'target': tag_network[i], 'width': len(tag_network)-i}} for i in range(len(tag_network)) if tag_network[i] != core_tag]
        return render_template('/tag_links.html', popup=popup, taglist=tagnet_list, nodes=nodes, edges=edges)
    else:
        return  render_template('/tag_links.html', popup=popup, taglist=tagnet_list, nodes=[], edges=[])

@bp.route('/remove_tag', methods=["POST", "GET"], endpoint='remove_tag')
def remove_tag():
    if request.method == "POST":
        target = request.form.getlist('remove_tag')
        taglist = session.get('taglist')
        taglist = [tag for tag in taglist if tag not in target]
        session['taglist'] = taglist
        popup = f"taglistから{" ".join(target)}を削除しました。"
        return render_template("/search_page.html", popup=popup, tags=session.get("taglist"))
    else:
        return render_template("/remove_tags.html", tags=session.get("taglist"))
    
@bp.route('/tag_explain', methods=["POST"], endpoint='tag_explain')
def tag_explain():
    data = request.get_json()
    tag = data['word']
    explain = tag_explainer(tag)
    explain = re.sub(r'[#\n\u3000\t]+', "", explain)
    return jsonify({'status':'ok', 'explain':explain})

@bp.route('/add_tag', methods=["POST"], endpoint='add_tag')
def add_tag():
    data = request.form['click_tag']
    tmp = session.get('taglist')
    print(data, "hello")
    if tmp is None:
        tmp = data
    else:
        tmp.append(data)
        tmp = list(set(tmp))
    session['popup'] = "タグリストにタグを追加しました!"
    return redirect(url_for('main_bp.tag_links'))

@bp.route('/click_url', methods=["POST"], endpoint='click_url')
def click_url():
    connect_logdb()
    data = request.get_json()
    id = session.get('user_id')
    title = data['title']
    rank = data['rank']
    date = datetime.datetime.now()
    query = data['query']
    tags = session.get('query_tags')
    count = session.get('search_count')
    g.logdb.click_url_log(user_id=id, search_query=query, tags=tags, date=date, rank=rank, title=title, search_count=count)
    return jsonify({"status":"ok"})

@bp.route('/start_page', methods=["POST"], endpoint='start_page')
def start_page():
    session['user_id'] = request.form['id']
    return render_template('/search_page.html', popup=None, tags=None)
