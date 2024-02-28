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


# ---intiazliation----
if __name__ == '__main__':
    application.run()