# Program 4
# CSS 436
# Author: Yasmine Subbagh
# Date: 2/23

from flask import Flask, request, jsonify, url_for, redirect, render_template
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import requests
import boto3
import json

app = Flask(__name__)
# setup aws stuff
s3 = boto3.client('s3')
dynamo = boto3.resource('dynamodb')
table = dynamo.Table('prog4-data')

# load page
@app.route("/")
def home():
    return render_template("index.html")

# load data from sites
@app.route("/load-data", methods=["POST"])
def loadData():
    # urls to retrieve from 
    awsUrl = 'https://s3-us-west-2.amazonaws.com/css490/input.txt'
    azureUrl = 'https://css490.blob.core.windows.net/lab4/input.txt'

    # bucket creds
    bucket_name = 'program4'
    aws_key = 'awsInput.txt'
    azure_key = 'azureInput.txt'

    # get files
    #aws first
    try:
        #download
        response = requests.get(awsUrl)
        #upload
        s3.put_object(Bucket=bucket_name, Key=aws_key, Body=response.content)
    except Exception as e:
        return jsonify({"message": "Could not upload file from AWS."})

    #azure next
    try:
        #download
        response = requests.get(azureUrl)
        #upload
        s3.put_object(Bucket=bucket_name, Key=azure_key, Body=response.content)
    except Exception as e:
        return jsonify({"message": "Could not upload file from Azure."})

    #parse the data from the files
    return parse(aws_key, azure_key)

# parse the data and put it into the database
def parse(awsFile, azureFile):
    aws_data = parseFile(awsFile)
    azure_data = parseFile(azureFile)

    if aws_data and azure_data:
        return jsonify({"message": "Data uploaded to database successfully."})
    else:
       return jsonify({"message": "Data uploaded failed."})

#helper function for parse()
def parseFile(file_path):
    bucket_name = 'program4'

    # get file
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_path)
        data = response['Body'].read().decode('utf-8')
    except Exception as e:
        return False

    # parse
    parsed_data = parse_data(data)
    if parsed_data:
        upload = upload_to_table(parsed_data)

    return upload

# helper function for parse
def parse_data(data):
    parsed_data = []
    lines = data.split('\n')
    # upload by line
    for line in lines:
        if line.strip():
            record = {}
            parts = line.split('\t') # if there are tabs, like azure file
            if len(parts) == 1:
                parts = line.split()
            name = parts.pop(0)
            record['name'] = name
            for part in parts:
                key_val = part.split('=')
                if len(key_val) == 2:
                    key, value = key_val
                    record[key] = value
            parsed_data.append(record)
    return parsed_data

#helper function for parse
def upload_to_table(data):
    for item in data:
        #check if item exists
        response = table.get_item(Key={'name': item['name']})
        if 'Item' not in response:
            # insert, it doesnt already exist
            try:
                table.put_item(Item=item)
            except Exception as e:
                return False
    return True

# clear data from table
@app.route("/clear-data", methods=["POST"])  
def clearData():
    return jsonify({"message": "Data cleared successfully"})

# query for user from table
@app.route("/query", methods=["POST", "GET"])  
def query():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    return jsonify({"message": "No results found."})

# intiazliation 
if __name__ == '__main__':
    app.run(debug=True)