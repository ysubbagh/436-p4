# Program 4
# CSS 436
# Author: Yasmine Subbagh
# Date: 2/23

from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import requests

app = Flask(__name__)

@app.route('/api/data', methods=['POST'])
def processData():
    # get data
    data = request.json

    # process
    result = {'message': 'Data recieved successfully', 'data': data}

    return jsonify(result)

# get data from the files
def getData():
    awsUrl = "https://css490.blob.core.windows.net/lab4/input.txt"
    azureUrl = "https://css490.blob.core.windows.net/lab4/input.txt"

    outputFile = "input.txt"

    AWSresponse = requests.get(awsUrl)
    azureResponse = requests.get(azureUrl)

    if AWSresponse.status_code == 200 and azureResponse.status_code == 200:
        with open(outputFile, 'wb') as f:
            f.write(AWSresponse.content)
            f.write(azureResponse.content)
        print("File donwloaded succesfully")
    else:
        print("Failed to download files")

if __name__ == '__main__':
    app.run(debug=True)
