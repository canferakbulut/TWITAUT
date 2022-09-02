#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 18:16:08 2022

@author: canferakbulut
"""
import requests
import os
import json
import pandas as pd
from time import sleep

os.chdir("/Users/canferakbulut/Documents/GitHub/TWITAUT/scraping/data")
df = pd.read_csv("ac_user_descriptions_220712.csv", usecols = ["id"])
user_ids = df['id'].to_list()

# To set your environment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ.get("BEARER_TOKEN")

def create_url(user_id):
    url = "https://api.twitter.com/2/users/{}/following".format(user_id)
    return url

def get_params(user_fields = ["username", "id"],
               max_results = 1000):
    user_fields = ','.join(user_fields)
    params = {"user.fields": user_fields, "max_results": max_results}
    return params


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FollowingLookupPython"
    return r


def connect_to_endpoint(url, params):
        try: 
            response = requests.request("GET", url, auth=bearer_oauth, params=params)
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
    params = get_params()

    json_response_full = {}
    
    for user_id in user_ids:
        
        url = create_url(user_id)
        json_response_full[user_id] = []
        
        pagination_flag = True
        token_flag = False     
        
        while pagination_flag:
            sleep(1)
            if token_flag:
                params['pagination_token'] = next_token[0]
            
            success = False
            attempts = 0
            
            while not success and attempts <= 2:
                success, json_response = connect_to_endpoint(url, params)
                attempts += 1
        
        #checks if 'data' field is empty; if not, appends to full results
        
            if success:
                try:
                    json_response_full[user_id].extend(json_response['data'])
                except KeyError:
                    pass
                    
                token_flag, next_token = next_page(json_response)
                
            if not token_flag:
                pagination_flag = False
                    
    return json_response_full


if __name__ == "__main__":
    y = main()