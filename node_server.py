# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 16:28:26 2023

@author: hamza
"""

from hashlib import sha256
import json
import time

import os
import uuid
from werkzeug.utils import secure_filename

from flask import Flask, request, render_template
import requests

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0) :

        """Constructor for the 'Block' class.
        :param index: Unique ID of the block.
        :param transactions: List of transactions.
        :param timestamp: Time of generation of the block.
        :param previous hash: Hash or the previous block in the chain which this block part of.
        """
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
    def compute_hash(self) :
        """A function that return the hash of the block contents."""
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain: 
 #difficulty of our Proof of Work algorithm
    difficulty = 2
    def __init__(self):
        """Constructor of the 'Blockchain' class"""
        self.unconfirmed_transactions = []
        self.chain = []
    def create_genesis_block(self):
        """ A function to generate genesis block and appends it to the chain. The block has index 0, previous_hash as 0, and a valid hash"""
        genesis_block = Block(0, [], 0, "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)
        
    @property
    def last_block(self):
        return self.chain[-1]    
    
    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of latest block
          in the chain match.
        """
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True
    
    @staticmethod
    def proof_of_work(block): 
        """
        Function that tries different values of nonce to get a hash
        that satisfied our difficulty criteria
        """
        block.nonce = 0
        
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
            
        return computed_hash
    
    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)
        
    @classmethod
    def is_valid_proof(cls, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria
        """
        return(block_hash.startswith('0'* Blockchain.difficulty) and 
               block_hash == block.compute_hash())
        
    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "0"
        
        for block in chain: 
            block_hash = block.hash
            #remove the hash field to recompute the hash again
            #using 'compute hash' method.
            delattr(block, "hash")
            
            if not cls.is_valid_proof(block, block_hash) or \
                    previous_hash != block.pervious_hash:
                result =False
                break
            
            block.hash, previous_hash = block_hash, block_hash
        return result
    
    def mine(self):
        """ 
        this function serves as an interface to add the pending
        transactions to the the blockchain by adding them to the block
        and figuring out Proof of Work
        """
        if not self.unconfirmed_transactions:
            return False
        
        last_block = self.last_block
        
        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)
        proof = self.proof_of_work(new_block)
        if not self.is_valid_proof(new_block, proof):
            return False
        self.add_block(new_block, proof)
        self.unconfirmed_transactions = []
        
        return True
    
# Initialize flask application
app = Flask(__name__)

# the node's copy of blockchain
blockchain = Blockchain()
blockchain.create_genesis_block()

# the address to other participating members of the network
peers = set()

# endpoint to submit a new transaction. this will be used by
# our application to add new data (posts) to the blockchain

@app.route('/hello')
def hello():
    return "Hello World"

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    # tx_data = request.form
    # file = request.files['thumbnail']
    file = request.files.get('thumbnail')
    required_fields = ["author", "content", "title"]
    
    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 400
        
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            current_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(current_dir, 'static', unique_filename)
            file.save(image_path)
            tx_data['image_path'] = image_path
        else :
            tx_data['image_path'] = None
        # Add the image path to the transaction data
        # tx_data['image_path'] = image_path
        print("kontol")
        print(image_path)
        print("kontol")
        tx_data["timestamp"] = time.time()
        blockchain.add_new_transaction(tx_data)
        return "Success", 201
    # try:
    #     tx_data = request.form.to_dict()
    #     file = request.files.get('thumbnail')
    #     required_fields = ["author", "content", "title"]

    #     for field in required_fields:
    #         if field not in tx_data:
    #             print(f"Missing field: {field}")  # Debugging log
    #             return f"Invalid transaction data: missing {field}", 400

    #     if file and file.filename != '':
    #         filename = secure_filename(file.filename)
    #         unique_filename = str(uuid.uuid4()) + "_" + filename
    #         current_dir = os.path.dirname(os.path.abspath(__file__))
    #         image_path = os.path.join(current_dir, 'static', unique_filename)
    #         file.save(image_path)
    #         tx_data['image_path'] = image_path
    #     else:
    #         tx_data['image_path'] = None

    #     tx_data["timestamp"] = time.time()
    #     blockchain.add_new_transaction(tx_data)
    #     return "Success", 201

    # except Exception as e:
    #     print("An error occurred:", e)  # Log the error for debugging
    #     return str(e), 500
# endpoint to return the node's copy of the data
# our application will be using the endpoint to query
# all teh posts to display

@app.route('/chain', methods= ['GET'])
def get_chain():
    chain_data= []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),"chain": chain_data,"peers": list(peers)})
    
# endpoint to request the node to mine the unconfirmed
# transactions (if any). We'll be using to initiate
# a command to mine from our application itself
@app.route('/mine', methods= ["GET"]) 
def mine_unconfirmed_transactions():
    result= blockchain.mine()
    if not result :
       return "No transactions to mine"
    else:
       #making sure we have the longest chain before announcing to the network
       chain_length= len(blockchain.chain)
       consensus()
       if chain_length == len(blockchain.chain):
           #announce the recently mined block to the network
           announce_new_block(blockchain.last_block)
       return "Block #{} is mined.".format(blockchain.last_block.index) 
# endpoint to add new peers to the network
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node_address = request.get_json()['node_address']
    if not node_address:
        return "Invalid data", 400
    
    #Add the node to the peer list
    peers.add(node_address)
    
    #Return the consensus blockchain to the newly registered node
    #so that he can sync
    return get_chain()

@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    """
    Internally calls the 'register_node' endpoint to
    register current node with the node spcified in the 
    request, and sync the blockchain as well as peer data.
    """
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-type': "application/json"}

    #Make a request to register with remote node and obtain information
    response = requests.post(node_address + "/register_node",
                         data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        global blockchain
        global peers
        # update chain and peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        return "Registration successfuul", 200
    else:
        #if something goes wrong, pass it on to the API response
        return response.content, response.status_code


def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0:
            continue #skip genesis block
        block= Block(block_data["index"],
                     block_data["transactions"],
                     block_data["timestamp"],
                     block_data["previous_hash"],
                     block_data["nonce"])
        proof = block_data['hash']
        added = generated_blockchain.add_block(block, proof)
        if not added:
            raise Exception("the chain dump is tampered!")
        return generated_blockchain   

# endpoint to add a block mined by someone else to
#the node's chain. The block is first verified by the node
# and then added to the chain           
@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json() 
    block= Block(block_data["index"],
                 block_data["transactions"],
                 block_data["timestamp"],
                 block_data["previous_hash"],
                 block_data["nonce"])    
    
    proof = block_data['hash']
    added = blockchain.add_block(block, proof)
    
    if not added:
        return "The block was discarded by the node", 400
    
    return "Block added to the chain", 201

#endpoint to query unconfirmed transactions
@app.route('/pending_tx') #verify if it 
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)

def consensus():
    """
    Our naive consensus algorithm. if a longer valid chain is
    found, our chain is replaced with it.
    """
    global blockchain
    
    longest_chain = None
    current_len = len(blockchain.chain)
    
    for node in peers:
        responses = requests.get('{}chain'.format(node))
        length = responses.json()['length']
        chain = responses.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain
            
    if longest_chain:
        blockchain = longest_chain
        return True
    
    return False

def announce_new_block(block):
    """
    A function to announce to the network once a block has been mined.
    other nodes can simply verify the proof of work and add it to their respective chains
    """
    for peer in peers :
        url = "{}add_block".format(peer)
        headers = {'Content_Type': "application/json"}
        requests.post(url,
                      data= json.dumps(block.__dict__, sort_keys=True),
                      headers = headers)

    
    
#Uncomment this line if you want to specify the port number in the code
# if __name__ == '__main__':
# app.run(debug= True, port=8000)