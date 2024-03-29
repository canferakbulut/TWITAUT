#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 18:52:23 2022

@author: canferakbulut
"""

from requests_oauthlib import OAuth1Session
import os
import json
from time import sleep, time
import pandas as pd
import numpy as np
from math import ceil
from tqdm import tqdm

consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")

# To set your environment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
# bearer_token = os.environ.get("BEARER_TOKEN")

def chunker(seq, size):
    return list(seq[pos:pos + size] for pos in range(0, len(seq), size))

## pass in usernames as users
def create_queries(users,  
                   user_fields = ["username", "name", "id", "created_at", "description", "verified"]):
    user_slices = chunker(users, 100)
    user_fields = ','.join(user_fields)
    qs = []
    for chunk in user_slices:
        string_chunk = [str(x) for x in chunk]
        query = ','.join(string_chunk)
        q = {'ids': query, 'user.fields': user_fields}
        qs.append(q)
    return qs


# In your terminal please set your environment variables by running the following lines of code.
# export 'CONSUMER_KEY'='<your_consumer_key>'
# export 'CONSUMER_SECRET'='<your_consumer_secret>'

consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")

# Get request token
def get_request_token(consumer_key, consumer_secret):
    request_token_url = "https://api.twitter.com/oauth/request_token"
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
    except ValueError:
       print(
        "There may have been an issue with the consumer_key or consumer_secret you entered."
        )

    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")
    print("Got OAuth token: %s" % resource_owner_key)
    return resource_owner_key, resource_owner_secret, oauth

# # Get authorization
def get_authorization(oauth):
    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    print("Please go here and authorize: %s" % authorization_url)
    verifier = input("Paste the PIN here: ")
    return verifier

# Get the access token
def get_access_token(consumer_key, consumer_secret, 
                     resource_owner_key, resource_owner_secret, 
                     verifier):
    access_token_url = "https://api.twitter.com/oauth/access_token"
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
       resource_owner_key=resource_owner_key,
       resource_owner_secret=resource_owner_secret,
    verifier=verifier,
    )
    oauth_tokens = oauth.fetch_access_token(access_token_url)
    access_token = oauth_tokens["oauth_token"]
    access_token_secret = oauth_tokens["oauth_token_secret"]
    return access_token, access_token_secret

# Make the request
def make_request(queries, consumer_key, consumer_secret, access_token, access_token_secret):
    oauth = OAuth1Session(
    consumer_key,
    client_secret=consumer_secret,
    resource_owner_key=access_token,
    resource_owner_secret=access_token_secret,
    )
    try:
        response = oauth.get("https://api.twitter.com/2/users", params=queries)
    except Exception as error: 
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(error).__name__, error.args)
        print(message)
        return False, []
    else:
        if response.status_code != 200:
            print(response.status_code)
        if response.status_code == 200:
            return True, response.json()
        elif response.status_code == 429:
            wait = ceil(float(response.headers['x-rate-limit-reset']) - time())
            print("Too many requests: waiting {minute} minutes...".format(minute = ceil(wait/60)))
            sleep(wait)
            return False, response.json()
        elif response.status_code in (401, 403, 404):
            print("Page not found, skipping...")
            return False, response.json()
        elif response.status_code in (500, 502, 503, 504):
            print("Servers down... waiting a minute.")
            sleep(60)
            return False, response.json()
        else:
            return False, response.json()
        
def main():
    queries = create_queries(users)
    resource_owner_key, resource_owner_secret, oauth = get_request_token(consumer_key, consumer_secret)
    verifier = get_authorization(oauth)
    access_token, access_token_secret = get_access_token(consumer_key, consumer_secret, 
                                                         resource_owner_key, resource_owner_secret,
                                                         verifier)
    json_response_full = []
    for query in tqdm(queries):
        
        attempts = 0
        success = False
        while not success and attempts <= 3:
            success, response = make_request(query, consumer_key, consumer_secret, access_token, 
                                             access_token_secret)
            attempts += 1
        
        if success:
            try: 
                json_response_full.extend(response['data'])
            except KeyError:
                print("Experiencing a key error! Moving on...")
    
    os.system('say "your code is done running!"')
    return json_response_full
        
if __name__ == "__main__":
   user_df = pd.read_csv("/Users/canferakbulut/Documents/GitHub/TWITAUT/scraping/data/TweetsSoFar_220816.csv",
                       lineterminator = "\n", dtype = {'author_id':'int'}, usecols = ['author_id'])
   users = user_df.author_id.to_list()
   json_response_full = main()


        
