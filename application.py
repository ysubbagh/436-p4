# Program 4
# CSS 436
# Author: Yasmine Subbagh
# Date: 2/25/23

from flask import Flask, request, jsonify, url_for, redirect, render_template
import requests
import boto3
import time
from boto3.dynamodb.conditions import Key

# ---vars---
application = Flask(__name__)
MAX_RETRY = 3

# setup aws stuff
s3 = boto3.client('s3')
dynamo = boto3.resource('dynamodb')
table = dynamo.Table('prog4')



# ---load page---
@application.route("/")
def home():
    return render_template("index.html")



# ---load data from sites---
@application.route("/load-data", methods=["POST"])
def loadData():
    # urls to retrieve from 
    awsUrl = 'https://s3-us-west-2.amazonaws.com/css490/input.txt'
    azureUrl = 'https://css490.blob.core.windows.net/lab4/input.txt'

    # bucket creds
    bucket_name = 'program4'
    aws_key = 'awsInput.txt'
    azure_key = 'azureInput.txt'

    # get files with retry logic
    retry = 0
    delay = 2

    #aws first
    while retry < MAX_RETRY:
        try:
            #download
            response = requests.get(awsUrl)
            #upload
            s3.put_object(Bucket=bucket_name, Key=aws_key, Body=response.content)
            break
        except Exception as e:
            retry += 1
            if retry == MAX_RETRY:
                return jsonify({"message": "Could not upload file from AWS."})
            #backoff delay
            time.sleep(delay)
            delay *= 2

    #azure next
    retry = 0
    delay = 2
    while retry < MAX_RETRY:
        try:
            #download
            response = requests.get(azureUrl)
            #upload
            s3.put_object(Bucket=bucket_name, Key=azure_key, Body=response.content)
            break
        except Exception as e:
            retry += 1
            if retry == MAX_RETRY:
                return jsonify({"message": "Could not upload file from Azure."})
            #backoff delay
            time.sleep(delay)
            delay *= 2

    #parse the data from the files
    return parse(aws_key, azure_key)

# parse the data and put it into the database
def parse(awsFile, azureFile):
    aws_data = parseFile(awsFile)
    azure_data = parseFile(azureFile)

    if aws_data and azure_data:
        return jsonify({"message": "Data uploaded to database successfully."})
    else:
       return jsonify({"message": "Data uploaded failed, some entries may have still been uploaded. "})

#helper function for parse(), does each file
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

# helper function for parse, do the actual parsing
def parse_data(data):
    parsed_data = []
    lines = data.split('\n')
    # upload by line
    for line in lines:
        if line.strip():
            record = {}
            parts = line.split()  # Split by whitespace
            first_name = parts[0]
            last_name = parts[1]
            record['first_name'] = first_name
            record['last_name'] = last_name
            for part in parts[2:]:  # Iterate over attributes starting from the third word
                key_val = part.split('=')
                if len(key_val) == 2:
                    key, value = key_val
                    record[key] = value
            parsed_data.append(record)
    return parsed_data

#helper function for parse, upload the parsed data into the table
def upload_to_table(data):
    items_failed = 0
    for item in data:
        # Check if 'first_name' and 'last_name' attributes exist and are not empty
        if 'first_name' in item and 'last_name' in item and item['first_name'] and item['last_name']:
            formatted_first_name = item['first_name'].capitalize()
            formatted_last_name = item['last_name'].capitalize()
            full_name = f"{formatted_first_name} {formatted_last_name}"

            # Check if item exists in the table
            response = table.get_item(Key={'name': full_name})
            if 'Item' not in response:
                # Insert item into the table if it doesn't already exist
                retry = 0
                delay = 2
                while retry < MAX_RETRY:
                    try:
                        item['name'] = full_name
                        table.put_item(Item=item)
                        break
                    except Exception as e:
                        retry += 1
                        if retry == MAX_RETRY:
                            items_failed += 1
                            break # still try to add other items
                        #back off delay
                        time.sleep(delay)
                        delay *= 2
        else:
            # Skip inserting item if either first_name or last_name attribute is missing or empty
            continue
    
    if items_failed > 0:
        return False
    
    return True


# ---clear data from table---
@application.route("/clear-data", methods=["POST"])  
def clearData():
    if deleteFiles() and emptyTable():
        return jsonify({"message": "Data cleared successfully."})

    return jsonify({"message": "Data not successfully cleared."})

# helper function for clear, deleted the s3 files
def deleteFiles():
    # bucket creds
    bucket_name = 'program4'
    aws_key = 'awsInput.txt'
    azure_key = 'azureInput.txt'

    #delete aws
    retry = 0
    delay = 2
    while retry < MAX_RETRY:
        try:
            s3.delete_object(Bucket=bucket_name, Key=aws_key)
            break
        except Exception as e:
            retry += 1
            if retry == MAX_RETRY:
                return False
            #backoff delay
            time.sleep(delay)
            delay *= 2

    #delete azure 
    retry = 0
    delay = 2
    while retry < MAX_RETRY:
        try:
            s3.delete_object(Bucket=bucket_name, Key=azure_key)
            break
        except Exception as e:
            retry += 1
            if retry == MAX_RETRY:
                return False
            #backoff delay
            time.sleep(delay)
            delay *= 2
        
    return True

# helper function for clear, empties out the table
def emptyTable():
    retry = 0
    delay = 2
    while retry < MAX_RETRY:
        try: 
            #get all items in table
            response = table.scan()
            # delete items in the table
            for item in response['Items']:
                table.delete_item(Key={'name': item['name']})
            return True
        except Exception as e:
            retry += 1
            if retry == MAX_RETRY:
                return False
            #backoff delay
            time.sleep(delay)
            delay *= 2


# ---query for user from table---
@application.route("/query", methods=["POST"])  
def query():
    #get user data
    data = request.json
    first_name = data.get("first_name")
    last_name =  data.get("last_name")

    #check query request
    if first_name is None and last_name is None:
        return jsonify({"message": "Query request invalid."})
    
   # Capitalize the first letter of first and last names
    first_name = first_name.capitalize() if first_name else None
    last_name = last_name.capitalize() if last_name else None

    # do the querying
    retry = 0
    delay = 2

    results = []
    while retry < MAX_RETRY:
        try:
            response = table.scan()
            for item in response['Items']:
                if first_name is not None and last_name is not None: #first and last name was given
                    if first_name in item['name'] and last_name in item['name']:
                        formatted_item = ' '.join([f"{key}={value}" for key, value in item.items() if key not in ['first_name', 'last_name']])
                        results.append(f"{item['name']} {formatted_item}")
                elif first_name is None: # only last name was given
                    if last_name in item['name'] and not item['name'].startswith(last_name):
                        formatted_item = ' '.join([f"{key}={value}" for key, value in item.items() if key not in ['first_name', 'last_name']])
                        results.append(f"{item['name']} {formatted_item}")
                elif last_name is None: # only first name is given
                    if item['name'].startswith(first_name):
                        formatted_item = ' '.join([f"{key}={value}" for key, value in item.items() if key not in ['first_name', 'last_name']])
                        results.append(f"{item['name']} {formatted_item}")
            break
        except Exception as e:
            retry += 1
            if retry == MAX_RETRY:
                return jsonify({"message": "Error executing query."}) 
            time.sleep(delay)
            delay *= 2

    #return results or lack of
    if results:
        #format
        results.sort(key=lambda x: x.split(' ')[0])
        formatted_results = '\n'.join(results)
        return jsonify({"message": formatted_results})
    else:
        return jsonify({"message": "No results found."})


# ---intiazliation----
if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000)