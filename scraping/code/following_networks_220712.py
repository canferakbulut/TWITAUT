#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 13:48:57 2022

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

os.chdir("/Users/canferakbulut/Documents/GitHub/TWITAUT/scraping/data")
df = pd.read_csv("ac_user_descriptions_220712.csv", usecols = ["id"])
user_ids = df['id'].to_list()

def get_url(user_id):
    user_id = str(user_id)
    base_url = "https://api.twitter.com/1.1/followers/ids.json?"
    url = base_url + "&user_id=" + user_id + "&count=200"
    return url
    

def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FollowingLookupPython"
    return r


def connect_to_endpoint(url):    
        try: 
            response = requests.request("GET", url, auth=bearer_oauth)
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
            elif response.status_code in (431, 500, 502, 503, 504):
                print("Servers down... waiting 10 minutes.")
                sleep(600)
                return False, response.json()
            else:
                return False, response.json()

def next_page(json_response):
    next_cursor = "placeholder"
    
    if json_response['next_cursor'] == 0:
        token_flag = False
    else:
        token_flag = True
        next_cursor = json_response['next_cursor_str']
    
    return token_flag, next_cursor
    
def main():

    json_response_full = {}
    
    for user_id in user_ids:
        
        url = get_url(user_id)
        json_response_full[user_id] = []
        
        pagination_flag = True
        token_flag = False     
        
        while pagination_flag:
            sleep(1)
            if token_flag:
                url = url + "&cursor=" + next_cursor
            
            success = False
            attempts = 0
            
            while not success and attempts <= 2:
                success, json_response = connect_to_endpoint(url)
                attempts += 1
        
        #checks if 'data' field is empty; if not, appends to full results
        
            if success:
                try:
                    json_response_full[user_id].extend(json_response['ids'])
                except KeyError:
                    pass
                    
                token_flag, next_cursor = next_page(json_response)
                
            if not token_flag:
                pagination_flag = False
                    
    return json_response_full

def dict_to_df(dic):
    keys = dic.keys()
    list_of_dfs = []
    for key in keys:
        print(key, len(dic[key]))
        if len(dic[key]) != 0:
            df = pd.DataFrame(dic[key])
            df['origin_id'] = [key] * df.shape[0]
            list_of_dfs.append(df)
    return pd.concat(list_of_dfs)
    
if __name__ == "__main__":
    y = main()