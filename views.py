from flask import render_template, url_for, request, redirect, session, g, jsonify
from SearchApp import app
from .QiitaSearch import BM25, VecSearch, RankFusion, search_dict, TagComb
import numpy as np
import colorsys
import asyncio
from openai import AsyncOpenAI, OpenAI
import os, sys
import re
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter

#環境情報の取得
load_dotenv()
#apikeyの設定
api_key = os.getenv("OPENAI_API_KEY")

app.secret_key = 'your_secret_key'
text_generator = AsyncOpenAI()
explainer = OpenAI()

def sort_tags(taglist):
    sort_index = np.argsort([g.tagdb.getCount(tag)[0] for tag in taglist])[::-1]
    taglist = [taglist[i] for i in sort_index]
    return taglist

def connect_articledb():
    if "articledb" not in g:
        g.articledb = search_dict.articleDB()
        g.articledb.connect_database()

def connect_tagdb():
    if "tagdb" not in g:
        g.tagdb = search_dict.tagDB()
        g.tagdb.connect_database()

async def text_summarizer(text):
    res = await text_generator.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content":"あなたは情報技術文書の要約専門のアシスタントです"},
            {"role":"user", "content": f"次の文章の要約を100文字以内で作ってください。また、見出しは初心者でも理解できるような内容で1つのみ出力してください{text}"}]
            )
    return res.choices[0].message.content

async def article_summarize(article_ids):
    splitters = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="gpt-4o-mini",
        chunk_size=1500,
        chunk_overlap=50
    )
    bodies = [g.articledb.getbody(article_id)[0] for article_id in article_ids]
    split_body_head = [splitters.split_text(body)[0] for body in bodies]
    tasks = [text_summarizer(text) for text in split_body_head]
    results = await asyncio.gather(*tasks)
    return results

def tag_explainer(tag):
    res = explainer.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system", "content":"あなたは情報技術に関するスペシャリストです"},
            {"role":"user", "content":f"次の単語について初心者でも理解できるように100文字程度で簡単に説明してください。{tag}"}
        ]
    )
    return res.choices[0].message.content

def make_color(tag):
    count = g.tagdb.getCount(tag)
    hue = 1/count[0]
    rgb = colorsys.hsv_to_rgb(hue, 1, 1)
    return '#%02x%02x%02x' % (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

def init_session():
    if session.get('init') is None:
        session['init'] = True
        session.pop('taglist', None)

@app.after_request
def close_db(response):
    tagdb = getattr(g, "tagdb", None)
    articledb = getattr(g, "articledb", None)
    if tagdb is not None:
        tagdb.close_database()
    if articledb is not None:
        articledb.close_database()
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
        session['article_id'] = results
        return redirect(url_for('result_page'))
    else:
            """
            if session.get('template-tags') is None:
                top_10_tags = g.tagdb.getTaglist(top_n=10, sorted=True)
                session['template-tags'] = list(top_10_tags)
                print(top_10_tags)
                session['taglist'] = session.get('template-tags')
            else:
            """
            if session.get('add_tags') is not None:
                tmp = session.get('taglist')
                if tmp is None:
                    tmp = session.pop('add_tags', None)
                else:
                    tmp.extend(session.pop('add_tags', None))
                    tmp = list(set(tmp))
                session['taglist'] = sort_tags(tmp)
            return render_template('/search_page.html', tags=session.get('taglist'))

@app.route('/result_page', methods=['POST', 'GET'])
def result_page():
    connect_tagdb()
    connect_articledb()
    if request.method=="POST":
        #print(request.form.getlist('add_tags'))
        session['add_tags'] = request.form.getlist('add_tags')
        return redirect(url_for('search_page'))
    else:
        query = session.pop('query', None)
        article_ids = session.pop('article_id', None)
        results = [{"title":g.articledb.getTitle(article_id)[0],"url":g.articledb.getURL(article_id)[0], "tags":[tag[0] for tag in g.articledb.getTags(article_id)]} for article_id in article_ids]
        taglist = []
        #print(results)
        #pxys = {tag: taglist.count(tag)/len(results) for tag in taglist} #検索結果上位N件に特定のタグが含まれている記事の出現確率
        #comb = TagComb.tagcomb()
        headings = asyncio.run(article_summarize(article_ids=article_ids))
        headings = [re.sub(r"[#\n\u3000\s\t]+", "", heading) for heading in headings]
        for i in range(len(article_ids)):
            results[i]['heading'] = headings[i]
            taglist.extend(results[i]['tags'])
        taglist = list(set(taglist))
        taglist = sort_tags(taglist)
        #pxs = comb.Px(taglist)
        #score = {tag: pxys[tag]*pxs[tag] if tag in pxs.keys() else 0 for tag in taglist} 
        #score = dict(sorted(score.items(), key=lambda x:x[1], reverse=True)) #特定のタグが付与された記事の出現確率と検索結果上位N件に出現する記事の出現確率のPMI
        #taglist = list(score.keys())[:5]
        return render_template('/result_page.html', query=query, results=results, taglist=taglist[:10])

@app.route('/tag_links', methods=["POST", 'GET'])
def tag_links():
    connect_tagdb()
    tag_comb = TagComb.tagcomb()
    tagnet_list = session.get('taglist')
    tagnet_list = sort_tags([tag for tag in tagnet_list if tag in tag_comb.bool_table.tags.to_list()])
    if request.method=="POST":
        core_tag = request.form['tag']
        session['core_tag'] = core_tag
        tag_network = tag_comb.simulate(core_tag).to_numpy()
        nodes = [{'data': {'id': tag, 'color': make_color(tag), 'count':g.tagdb.getCount(tag)[0]}} for tag in tag_network]
        edges = [{'data': {'source': core_tag, 'target': tag_network[i], 'width': len(tag_network)-i}} for i in range(len(tag_network)) if tag_network[i] != core_tag]
        return render_template('/tag_links.html', taglist=tagnet_list, nodes=nodes, edges=edges)
    else:
        return  render_template('/tag_links.html', taglist=tagnet_list, nodes=[], edges=[])
    
@app.route('/tag_explain', methods=["POST"])
def tag_explain():
    data = request.get_json()
    tag = data['word']
    explain = tag_explainer(tag)
    explain = re.sub(r'[#\n\u3000\t]+', "", explain)
    print(explain)
    return jsonify({'status':'ok', 'explain':explain})
