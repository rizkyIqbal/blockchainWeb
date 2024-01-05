#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 13 16:17:09 2023

@author: danghuy
"""
import datetime
import json
import requests
from flask import render_template, redirect, request

import os
import uuid
from werkzeug.utils import secure_filename

from app import app

#the node our application interacts

CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

posts = []

def fetch_posts():
    """
    Function to fetch the chain from a block chain node

    """
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            print("DEBUG blcok+ ----------")
            print(block)
            
            for tx in block["transactions"]:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)
            
        global posts
        posts = sorted(content, key = lambda k: k['timestamp'],
                           reverse=True)
            
@app.route('/')
def index():
    fetch_posts()
    return render_template('index.html', 
                           title = 'Gaming News : Get The Latest News About Gaming!',
                            posts = posts,
                            node_address = CONNECTED_NODE_ADDRESS,
                            readable_time=timestamp_to_string)
    
@app.route('/create')
def create():
    return render_template('create.html', 
                           title = 'Gaming News : Get The Latest News About Gaming!',
                            posts = posts,
                            node_address = CONNECTED_NODE_ADDRESS,
                            readable_time=timestamp_to_string)

@app.route('/verify')
def verify():
    return render_template('verify.html', 
                           title = 'Gaming News : Get The Latest News About Gaming!',
                            posts = posts,
                            node_address = CONNECTED_NODE_ADDRESS,
                            readable_time=timestamp_to_string)

@app.route('/submit', methods = ['POST'])
def submit_textarea():
    """ 
    Endpoint to create a new transaction via our application
    """
    title = request.form["title"]
    post_content = request.form["content"]
    author = request.form["author"]
    file = request.files["thumbnail"]
    
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + "_" + filename
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, 'static', unique_filename)
        file.save(image_path)
        thumbnail = unique_filename  
    else:
        thumbnail = None
    post_object = {
            'title': title,
            'author': author,
            'content': post_content,
            'thumbnail': thumbnail
    }

# Submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)
    
    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content_type':'application.json'})
    
    # data = {key: str(value) for key, value in post_object.items()}
    # if file:
    #     data['thumbnail'] = file

    # new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)
    # requests.post(new_tx_address, files=data)
    return redirect('/')


def timestamp_to_string(epoc_time):
    return datetime.datetime.fromtimestamp(epoc_time).strftime('H:%M')