#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 28 12:17:23 2022

@author: canferakbulut
"""

import requests
import os
import json
import csv

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ.get("BEARER_TOKEN")


def create_urls(queries):
    # Specify the usernames that you want to lookup below
    # You can enter up to 100 comma-separated values.
    qs = ["q=" + queries[i] for i in range(0, len(queries))]
    pages = list(range(1, 50 + 1))
    # User fields are adjustable, options include:
    # created_at, description, entities, id, location, name,
    # pinned_tweet_id, profile_image_url, protected,
    # public_metrics, url, username, verified, and withheld
    urls = []
    for q in qs:
        for page in pages:
            url = "https://api.twitter.com/1.1/users/search.json?{}&page={}".format(q, page)
            urls.append(url)
    return urls


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2UserLookupPython"
    return r


def connect_to_endpoint(url):
    response = requests.request("GET", url, auth=bearer_oauth,)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    return response.json()

def abridge_dict(dic_list, keys):
    new_dic = []
    for dic in dic_list:
        entry = { key: dic[key] for key in keys }
        new_dic.append(entry)
    return new_dic

def dict_to_csv(dic_list, csv_name):
    keys = dic_list[0].keys()
    with open(csv_name, 'w', newline='') as out:
       dict_writer = csv.DictWriter(out, keys)
       dict_writer.writeheader()
       dict_writer.writerows(dic_list)
    

def main():
    urls = create_urls(["autism", "autistic", "aspergers", "aspie"])
    print("Status: URLs created")
    json_response_full = []
    for url in urls:
        json_response = connect_to_endpoint(url)
        json_response_full.extend(json_response)
    print("Status: Users retrieved")
    keys = ['id_str', 'name', 'screen_name', 'location', 'created_at', 'description']
    json_abridged = abridge_dict(json_response_full, keys)
    dict_to_csv(json_abridged, "charities_to_review.csv")


if __name__ == "__main__":
    main()