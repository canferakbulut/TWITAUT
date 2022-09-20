#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  2 12:46:45 2022

@author: canferakbulut
"""
import pandas as pd
import numpy as np
from itertools import product
from gensim.models import Word2Vec
import re
from string import punctuation, printable, digits
from nltk.stem import WordNetLemmatizer 
from nltk.corpus import stopwords
from scipy.spatial.distance import cosine
from gensim.utils import RULE_DISCARD, RULE_KEEP
from tqdm import tqdm
import glob
import os

def csv(path):
    df = pd.read_csv(path, lineterminator = "\n", usecols = ['text'])
    return df.text.to_list()

def read_corpora(root, files): #takes input of: root directory (str), files (dict)
    corpus_dict = {}
    corpus_dict['aut'], corpus_dict['par'], corpus_dict['ac'], corpus_dict['asag'] = csv(root + files['aut']), \
                                                                                     csv(root + files['par']), \
                                                                                     csv(root + files['ac']), \
                                                                                     csv(root + files['asag']) 
    baseline_tweets = csv(root + files['baseline'])
    return corpus_dict, baseline_tweets
                                                                    

def cleaning(text, stops = stopwords.words("english")):
    text = str(text)
    #remove url links
    text = re.sub(r'http\S+', ' ', text)
    #remove @ words
    text = re.sub(r'@\w+', ' ', text)
    #remove stopwords
    text = ' '.join([word for word in text.split() if word not in stops])
    #remove punct
    text = text.translate(str.maketrans({char:' ' for char in punctuation}))
    #remove numbers
    text = text.translate(str.maketrans({char:' ' for char in digits}))
    #remove non-ascii characters
    text = ''.join(filter(lambda x: x in printable, text))
    #lemmatize words
    lemmatizer = WordNetLemmatizer()
    text = ' '.join([lemmatizer.lemmatize(x) for x in text.split()])
    text = text.strip("\n")
    text = text.lower()
    text = text.split() #iterable tweets
    return text

def tweet_cleaning(tweets):
    tweets = [cleaning(tweet) for tweet in tweets]
    return tweets

def make_params():
    raw_params = [[100, 300, 500], #vector_size
        [5, 8], # window
        [30, 50], # min_count
        [0, 1], #training algorithm: skipgram vs cbow
        [0, 1] #output layer: softmax vs negative sampling
        ]
    products = [list(x) for x in list(product(*raw_params))]
    for x in products:
        if x[4] == 0: 
            x.append(10) #add negative sampling rate if output layer = negative sampling
    param_names = ['vector_size', 'window', 'min_count', 'sg', 'hs', 'negative']
    params_dic = [{param_name: i for (param_name, i) in zip(param_names, product)} for product in products]
    return params_dic
    
def train_baselines(params, baseline_tweets, save = True):
    model_dic = {}
    baseline_tweets = tweet_cleaning(baseline_tweets)
    for param in tqdm(params):
        name = 'vs-' + str(param['vector_size']) + '_w-' + \
                str(param['window']) + '_mc-' + str(param['min_count']) + \
                '_sg-' + str(param['sg']) + '_hs-' + str(param['hs'])
        print("working on {} model training".format(name))
        if len(param) == 6:
            model = Word2Vec(sentences = baseline_tweets, 
                         vector_size = param['vector_size'],
                         window = param['window'], 
                         min_count= param['min_count'],
                         sg = param['sg'],
                         hs = param['hs'],
                         negative = param['negative'],
                         workers = 4)
        elif len(param) == 5:
            model = Word2Vec(sentences = baseline_tweets, 
                         vector_size = param['vector_size'],
                         window = param['window'], 
                         min_count= param['min_count'],
                         sg = param['sg'],
                         hs = param['hs'],

                         workers=4)
        else:
            raise ValueError("uh oh! unexpected param length in word2vec initialization")
        
        model.build_vocab(baseline_tweets)
        model.train(baseline_tweets, epochs = model.epochs, total_examples = model.corpus_count)
        model_dic[name] = model
        
        if save:
            model.save(name + '.model')
        
        print("finished with {} model training".format(name))
            
    return model_dic

    
#can pass in model_dic or list of model names 
#if model names already have .model extension, i.e. if read in through listdir or glob
#set extension = False
def update_training(full_corpus, model_dic, extension = True):
    print("start of cleaning")
    clean_corpus = {x: tweet_cleaning(full_corpus[x]) for x in full_corpus}
    print("finished cleaning!")
    updates = {x: {y: None for y in clean_corpus} for x in model_dic}
    
    if extension:
        model_names = [x + ".model" for x in model_dic]
    else:
        model_names = [x for x in model_dic]
        
    for model_name in tqdm(model_names):
        for corpus_name in clean_corpus:
            corpus = clean_corpus[corpus_name]
            model = Word2Vec.load(model_name)
            model.build_vocab(corpus, update = True)
            model.train(corpus, epochs = model.epochs, total_examples = len(corpus))
            updates[model_name][corpus_name] = model.wv
    return updates

def from_name(pattern, name):
    name = re.sub(".model", "", name)
    return int(re.search(pattern, name).group(1))

def cosine_similarity_df(updates):
    cos_sim = []
    orgs = ['ac', 'asag']
    indvs = ['aut', 'par']
    param_names = ['vector_size', 'window', 'min_count', 'sg', 'hs']
    patterns = ['^vs-(.*?)_', '_w-(.*?)_', '_mc-(.*?)_', '_sg-(.*?)_', '_hs-(.*?)$']
    
    for model_name in updates:
        vectors = updates[model_name]
        words = [set(vectors[corpus_name].index_to_key) for corpus_name in vectors]
        words_in_common = list(set.intersection(*words))
        
        for word in words_in_common:
            for org in orgs:
                for indv in indvs:
                    result_dic = {param_name: from_name(pattern,model_name) for (param_name,pattern) 
                                  in zip(param_names,patterns)} | {'specification': model_name}
                    
                    result_dic['word'] = word
                    result_dic['org'] = org
                    result_dic['indv'] = indv
                    result_dic['cos_sim'] = 1 - cosine(vectors[org][word], vectors[indv][word])
                    cos_sim.append(result_dic)

    return pd.DataFrame(cos_sim)
          
def main():
    corpus_dic, baseline_tweets = read_corpora(root, files)
    print(1)
    params = make_params()
    print(2)
    model_dic = train_baselines(params, baseline_tweets)
    print(3)    
    updates = update_training(corpus_dic, model_dic)
    print(4)
    cos_sim_df = cosine_similarity_df(updates)
    print(5)
    return cos_sim_df

if __name__ == "__main__":
    root = "/Users/canferakbulut/Documents/GitHub/TWITAUT/data/corpora/"
    files = {'aut': 'final_aut_corp.csv',
             'par': 'final_parent_corp.csv' ,
             'ac': 'ac_tweets_220730.csv',
             'asag': 'asag_tweets_220730.csv',
             'baseline': 'final_baseline_corp.csv'}
    corpus_dic, baseline_tweets = read_corpora(root, files)
    os.chdir("/Users/canferakbulut/Documents/GitHub/TWITAUT/analysis/models")
    model_dic = glob.glob("*.model")
    updates = update_training(corpus_dic, model_dic, extension = False)
    cos_sim_df = cosine_similarity_df(updates)
    #cos_sim_df = main()
  
z = []
for x in corpus_dic.keys():
    z.append(sample(corpus_dic[x],1))
    
    
    
