#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  5 10:52:00 2022

@author: canferakbulut
"""
import pandas as pd
import numpy as np
import random
import re
from string import punctuation, printable, digits
from nltk.stem import WordNetLemmatizer 
from nltk.corpus import stopwords
from nltk import bigrams
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics import cohen_kappa_score, classification_report
from imblearn.pipeline import Pipeline, make_pipeline
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split as tts, GridSearchCV
from imblearn.under_sampling import RandomUnderSampler
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import LinearSVC
from Doc2VecTransformer import Doc2VecTransformer
from sklearn.feature_selection import chi2
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm
from scipy import sparse
import time

#splitting corpus of user descriptions into two datasets
def samples_to_annotate(df, nsample = 30000, noverlap = 1000, seed = 42):
    random.seed(seed)
    nrows = df.shape[0]
    #random sample of n rows: coder 1
    r_id = random.sample(range(nrows), nsample)
    #creating overlapping values for intercoder reliability
    midpoint = round(len(r_id) / 2)
    coder1 = r_id[ : midpoint + noverlap]
    coder2 = r_id[midpoint: ]
    df1, df2 = df.iloc[coder1,:], df.iloc[coder2,:]
    return df1, df2

def remove_na(str_list):
    clean_list = ['{:.1f}'.format(float(x)) for x in str_list if str(x) != 'nan']
    return clean_list

def find_label(match, df):
    return df.loc[df['id'] == match, 'label'].iloc[0]

def percent_overlap(array1, array2):
    agree = [0 if x != y else 1 for x,y in zip(array1, array2)]
    return sum(agree)/len(agree)

def intercoder_reliability(df1, df2):
    id1, id2 = set(remove_na(df1['id'])), set(remove_na(df2['id']))
    match_ids = [int(float(x)) for x in list(set.intersection(id1, id2))]
    labels1, labels2 = [], []
    for match in match_ids:
        label1, label2 = find_label(match, df1), find_label(match, df2)
        labels1.append(label1)
        labels2.append(label2)
    kappa = cohen_kappa_score(labels1, labels2)
    overlap = percent_overlap(labels1, labels2)
    return kappa, overlap

def description_cleaning(text):
    stops = stopwords.words("english")
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
    text = text.lower()
    return text

def clean_dfs(path1, path2):
    cols = ['description', 'id', 'verified', 'username', 'name', 'label']
    df1, df2 = pd.read_csv(path1, usecols=cols), pd.read_csv(path2, usecols=cols)
    df = pd.concat([df1, df2])
    df.drop_duplicates(inplace=True, subset = ['id'])
    df['description'] = df['description'].map(description_cleaning)
    #remove NA descriptions
    df = df.loc[~(df['description'].replace(" ", "") == 'nan')]
    return df, intercoder_reliability(df1, df2)

def get_tts(df, pred = 'description', target = 'label'):
    data = df[[pred, target]].values
    X, y = data[:, 0], data[:, -1].astype('int')
    # label encode the target variable
    X_train, X_test, y_train, y_test = tts(X, y, stratify=y, random_state=0, test_size=0.33)
    return X_train, X_test, y_train, y_test
   
#passable into 'model_type': lg (logistic regression), mnb (multinomial),
# lsvm (linear support vector machine), rf (random forest)
def text_classifier(encoding_type, model_type):
    
    models = {
        'rf': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=0),
        'lsvm': LinearSVC(),
        'mnb': MultinomialNB(),
        'lg': LogisticRegression(max_iter=10000)
    }
    
    if encoding_type == 'tfidf':
        textclassifier = Pipeline([
            ('vect', CountVectorizer()), 
            ('tfidf', TfidfTransformer()),
            ('oversample', SMOTE()),
            ('undersample', RandomUnderSampler()),
            (model_type, models[model_type])])
        
    elif encoding_type == 'doc2vec':
        textclassifier = Pipeline([
            ('doc2vec', Doc2VecTransformer()),
            ('oversample', SMOTE()),
            ('undersample', RandomUnderSampler()),
            ('normalizing',MinMaxScaler()),
            (model_type, models[model_type])])
    
    else:
        raise Exception("invalid encoding type!")
           
    return textclassifier

    
def tune_hyperparameters(encoding_type, X_train, y_train):
    
    majority_count = np.bincount(y_train)[0]
    
    models = ['rf', 'lsvm', 'mnb', 'lg']
    
    cv_results = {encoding_type + '_' + model: {} for model in models}
    
    param_grid = {
        #20, 30, and 40 percent of majority class
        'oversample__sampling_strategy':[{1:round(majority_count * x), 2:round(majority_count * x)}
                                         for x in [0.4, 0.5, 0.6]],
        #undersample by 40, 60, and 80 percent
        'undersample__sampling_strategy':[{0:round(majority_count * x)} for x in [0.4, 0.6, 0.8]]
        }
    
    
    if encoding_type == "doc2vec":
        param_grid = {
            "doc2vec__vector_size": [30, 50],
            "doc2vec__epochs": [50], 
            "doc2vec__window": [3, 6, 8],
            "doc2vec__min_count": [10],
            "doc2vec__dm": [0, 1]
            } | param_grid
    
    for model in tqdm(models):
        name = encoding_type + '_' + model
        print("starting " + name)
        textclassifier = text_classifier(encoding_type, model)
        search = GridSearchCV(textclassifier, param_grid, verbose = 2)
        search.fit(X_train, y_train)
        cv_results[name]['parameters'] = search.best_params_
        cv_results[name]['scores'] = search.best_score_
        print("done with" + name)
    
    return cv_results

def evaluate_model(X_train, y_train, X_test, y_test, hyperparams_dict):
    keys = list(hyperparams_dict.keys())
    classification_reports = {key: {} for key in keys}
    for key in keys:
        embedding_type, model_type = key.split("_")
        textclassifier = text_classifier(embedding_type, model_type)
        textclassifier.set_params(**hyperparams_dict[key]['parameters'])
        textclassifier.fit(X_train, y_train)
        y_hat = textclassifier.predict(X_test)
        classification_reports[key] = classification_report(y_test, y_hat, output_dict=True)
        
    return classification_reports 

def main():
    df, intercoder_rel = clean_dfs(path1, path2)
    X_train, X_test, y_train, y_test = get_tts(df)
    embeddings = ["tfidf", "doc2vec"]
    best_hyperparams = {embedding: {} for embedding in embeddings}
    model_evals = {}
    for embedding in embeddings:
        best_hyperparams[embedding] = tune_hyperparameters(embedding, X_train, y_train)
        model_evals.update(evaluate_model(X_train, y_train, X_test, y_test, best_hyperparams[embedding]))
    
    return intercoder_rel, best_hyperparams, model_evals

if __name__ == "__main__":
    path1 = "/Users/canferakbulut/Documents/GitHub/TWITAUT/scraping/data/TWITAUT_Annotation_Spreadsheet.csv"   
    path2 = "/Users/canferakbulut/Documents/GitHub/TWITAUT/scraping/data/annotation_CA.csv"
    intercoder_rel, best_hyperparams, model_evals = main()

  
    
    
    

    
                          
