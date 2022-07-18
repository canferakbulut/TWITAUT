#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 16:39:43 2022

@author: canferakbulut
"""
import requests
import os
import json
from time import sleep
from datetime import datetime, timedelta
from random import randrange
import pandas as pd


# To set your environment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ.get("BEARER_TOKEN")

# Optional params: start_time,end_time,since_id,until_id,max_results,next_token,
# expansions,tweet.fields,media.fields,poll.fields,place.fields,user.fields

def get_keywords(path):
    with open(path) as f:
        content = f.readlines()
    keywords = [content[i].strip() for i in range(0, len(content))]
    return keywords

def get_random_time(start, end):
    dtformat = '%Y-%m-%dT%H:%M:%SZ'
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    rand_second = randrange(int_delta)
    rand_start = start + timedelta(seconds=rand_second)
    ## returns endtime: 24 hrs later
    rand_end= rand_start + timedelta(hours = 24)
    return rand_start.strftime(dtformat), rand_end.strftime(dtformat) 

def create_queries(number_of_dates, keywords, base_year, range_of_years,
                   max_results = 100,
                   existing_start_times = [],
                   tweet_fields = ["id", "text", "author_id", "created_at"]):
    query = " OR ".join(keywords) + " -is:retweet lang:en"
    tweet_fields = ','.join(tweet_fields)
    list_of_dates = [datetime(base_year + years, 1, 1) for years in range(range_of_years)]
    qs = []
    start_time_dump = existing_start_times
    for date in list_of_dates:
        for i in range(number_of_dates):
            lower_date, upper_date = date, datetime(date.year + 1, 1, 1)
            start_time, end_time = get_random_time(lower_date, upper_date)
            while start_time in start_time_dump:
                start_time, end_time = get_random_time(lower_date, upper_date)
            start_time_dump.append(start_time)
            q = {'query': query, 'start_time': start_time, 'end_time': end_time,
                 'max_results': max_results, 'tweet.fields': tweet_fields}
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
    queries = create_queries(number_of_dates, keywords, lower_date, upper_date)
    json_response_full = []
    for query in queries:
        pagination_flag = True
        token_flag = False     
        while pagination_flag:
            sleep(1)
            if token_flag:
                query['next_token'] = next_token[0]
            
            success = False
            attempts = 0
            while not success and attempts <= 2:
                success, json_response = connect_to_endpoint(query)
                attempts += 1
        
        #checks if 'data' field is empty; if not, appends to full results
        
            if success:
                json_response_full.extend(json_response['data'])
                token_flag, next_token = next_page(json_response)
                
            if not token_flag:
                pagination_flag = False
       
                    
    return json_response_full
                
                
if __name__ == "__main__":
    main()
    