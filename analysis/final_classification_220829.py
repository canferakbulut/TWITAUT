#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 17:23:32 2022

@author: canferakbulut
"""
import pandas as pd
import numpy as np
from training_selfidentification_labels_220705 import text_classifier, description_cleaning, best_hyperparams
from bisect import bisect_left

def read_annotation_data(path):
    df = pd.read_csv(path)
    data = df[['description', 'label']].values
    X, y = data[:, 0], data[:, -1].astype('int')
    majority_count = max(np.bincount(y))
    return X, y, majority_count, annotation_df

def id_list(full_list):
    clean = []
    for x in full_list:
        try:
            clean.append(str(int(float(x))))
        except (KeyError, ValueError) as e: 
            pass
    return list(set(clean))

def get_org_tweet_ids(charity_path, sa_path):
    charity_tweets = pd.read_csv(charity_path,
                             lineterminator = "\n")
    sa_tweets = pd.read_csv(sa_path,
                        lineterminator = "\n")
    
    org_ids = id_list(charity_tweets.author_id.to_list() + 
                      sa_tweets.author_id.to_list())
    
    return org_ids

def get_full_users(path, org_ids):
    full_users = pd.read_csv(path,
                         lineterminator = "\n")
    full_users.drop_duplicates(inplace=True, subset = ['id'])
    clean_users = full_users.loc[~(full_users['id'].isin(org_ids))]
    clean_users['description'] = clean_users['description'].map(description_cleaning)
        
    return clean_users

def as_U(x):
    try:
        x = x.astype('U')
    except AttributeError:
        x = np.array(x).astype('U')
     
    return x

# embedding and model must be manually specified from model eval results
def train_and_predict(X, y, X_predict, embedding, model, best_hyperparams):
    X, y, X_predict = as_U(X), as_U(y), as_U(X_predict)
    hyperparams = best_hyperparams[embedding][embedding + "_" + model]
    tc = text_classifier(embedding, model)
    tc.set_params(**hyperparams)
    tc.fit(X, y)
    y_hat = tc.predict(X_predict)
    return y_hat

def clean_predictions(predictions, annotation_df, users_df):
    annotation_df.id = [int(x) for x in df.id.to_list()]
    for i in range(len(predictions)):
        if users_df.id.iloc[i] in annotation_df.id:
            try:
                actual = annotation_df.loc[annotation_df.id == users_df.id.iloc[i], 'label'].values[0]
                predictions[i] = actual
            except IndexError:
                pass
    
    return predictions

def binary_search(alist, item):
    i = bisect_left(alist, item)
    if i != len(alist) and alist[i] == item:
        return i
    else:
        raise ValueError

def read_and_clean_indiv_tweets(path, org_ids):
    tweets_df = pd.read_csv(path,
                          lineterminator = "\n")
    ftweets_df = full_tweets.loc[~(full_tweets['author_id'].isin(org_ids))]
    return tweets_df

def add_predictions(users_df, tweets_df):
    labels = list(set(users_df.label))
    users_by_group = {x: sorted(users_df.loc[users_df.label == x, 'id'].to_list()) for x in labels}

    author_labels = []
    for author_id in full_tweets.author_id:
        attempts = 0
        for i in labels:
            try:
                binary_search(users_by_group[i], author_id)
                author_labels.append(int(i))
                break
            except ValueError:
                pass
        
            if attempts == 2:
                author_labels.append(999)
        
            attempts += 1
    
    return author_labels
             
def main(paths):
    X, y, majority_count, annotation_df = read_annotation_data(paths['annotation_path'])
    org_ids = get_org_tweet_ids(paths['charity_path'], paths['sa_path'])
    users_df = get_full_users(paths['users_path'], org_ids)
    predictions = train_and_predict(X, y, X_predict, embedding, model, 
                                    best_hyperparams)       
    predictions = clean_predictions(predictions, annotation_df, users_df)
    tweets_df = read_and_clean_indiv_tweets(path['tweets_path'], org_ids)
    tweets_df.author_labels = add_predictions(users_df, tweets_df)
    return tweets_df
    
if __name__ == "__main__":
    main_path = "x/"
    path_files = ['a', 'b', 'c', 'd', 'e', 'f']
    path_names = ['annotation_path', 'charity_path', 'sa_path', 'users_path', 'tweets_path']
    paths = {path_name: main_path + path_file for path_name, 
             path_file in zip(path_names, path_files)}
    labeled_tweets_df = main(paths)
    
    
    
    
            
            
            
    






            
            
        
    

