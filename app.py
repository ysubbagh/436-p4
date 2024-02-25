# Program 4
# CSS 436
# Author: Yasmine Subbagh
# Date: 2/23

from flask import Flask, request, jsonify, url_for, redirect, render_template
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import requests
import boto3

app = Flask(__name__)

# load page
@app.route("/")
def home():
    return render_template("index.html")

# load data from sites
@app.route("/load-data", methods=["POST"])
def loadData():
    return jsonify({"message": "Data loaded successfully"})

# clear data from table
@app.route("/clear-data", methods=["POST"])  
def clearData():
    return jsonify({"message": "Data cleared successfully"})

# query for user from table
@app.route("/query", methods=["POST", "GET"])  
def query():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    return jsonify("No results found.")

# intiazliation 
if __name__ == '__main__':
    app.run(debug=True)