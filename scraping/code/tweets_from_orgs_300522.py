#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 30 15:38:37 2022

@author: canferakbulut
"""
import requests
import os
import json
import pandas as pd
from time import sleep

# To set your environment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ.get("BEARER_TOKEN")

# Optional params: start_time,end_time,since_id,until_id,max_results,next_token,
# expansions,tweet.fields,media.fields,poll.fields,place.fields,user.fields

#start_time is creation of account, end time is scrape time
def create_queries(ids, start_time, 
                   tweet_fields = ["id", "text", "author_id", "created_at"],
                   max_results = 100):
    author_ids = ['(from:' + ids[i] + ') -is:retweet' for i in range(0, len(ids))]
    tweet_fields = ','.join(tweet_fields)
    qs = []
    for author_id, date in zip(author_ids, start_time):
        q = {'query': author_id, 'start_time': date, 
             'tweet.fields': tweet_fields, 'max_results': 100}
        qs.append(q)
    return qs
        
def bearer_oauth(r):
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FullArchiveSearchPython"
    return r


def connect_to_endpoint(params):
    search_url = "https://api.twitter.com/2/tweets/search/all"
    try:
        response = requests.request("GET", search_url, auth=bearer_oauth, params=params)
    except (MaxRetryError, gaierror, ConnectionError, NewConnectionError) as error: 
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(error).__name__, error.args)
        print(message)
        return False, []
    else:
        print(response.status_code)
        if response.status_code == 200:
            return True, response.json()
        elif response.status_code == 429:
            print("Too many requests: waiting 15 minutes...")
            sleep(900)
            return False, response.json()
        elif response.status_code in (401, 403, 404):
            print("Page not found, skipping...")
            return False, response.json()
        elif response.status_code in (500, 502, 503, 504):
            print("Servers down... waiting 10 minutes.")
            sleep(600)
            return False, response.json()
        else:
            return False, response.json()


def next_page(json_response):
    next_token = []
    
    try:
        json_response['meta']['next_token']
    except KeyError:
        return False, next_token
    else:
        next_token.append(json_response['meta']['next_token'])
        return True, next_token    
    

def main():
    queries = create_queries(ids, start_time)
    json_response_full = []
    for query in queries:
        pagination_flag = True
        token_flag = False   
        while pagination_flag:
            sleep(1)
            if token_flag:
                query['next_token'] = next_token[0]
           
            attempts = 0
            success = False
            
            while not success and attempts <= 3:
                success, json_response = connect_to_endpoint(query)
                attempts += 1
       
       #checks if 'data' field is empty; if not, appends to full results
       
            if success:
                try: 
                    json_response_full.extend(json_response['data'])
                except KeyError:
                    pass
                finally:
                    token_flag, next_token = next_page(json_response)

            else:
                token_flag = False
               
            if not token_flag:
                pagination_flag = False
                    
    return json_response_full
                
                
if __name__ == "__main__":
    df = pd.read_csv("/Users/canferakbulut/Documents/GitHub/TWITAUT/scraping/data/ac_user_descriptions_220712.csv")
    ids = df['username'].to_list()
    start_time = df['created_at'].to_list()
    json_response_full = main()
    
    

        