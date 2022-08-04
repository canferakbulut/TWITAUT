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
from string import punctuation, printable
from nltk.stem import WordNetLemmatizer 
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics import cohen_kappa_score, classification_report
from imblearn.pipeline import Pipeline, make_pipeline
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split as tts
from imblearn.under_sampling import RandomUnderSampler
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
import gensim
import gensim.downloader as gensim_api

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
    df1.drop_duplicates(inplace=True, subset = ['id'])
    df2.drop_duplicates(inplace=True, subset = ['id'])
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
    text = str(text)
    #remove url links
    text = re.sub(r'http\S+', '', text)
    #remove @ words
    text = re.sub(r'@\w+', '', text)
    #remove punct
    text = text.translate(str.maketrans('', '', punctuation))
    #remove non-ascii characters
    text = ''.join(filter(lambda x: x in printable, text))
    #lemmatize words
    lemmatizer = WordNetLemmatizer()
    text = ' '.join([lemmatizer.lemmatize(x) for x in text.split()])
    text = text.lower()
    return text


#passable into 'model_type': lg (logistic regression), mnb (multinomial),
# lsvm (linear support vector machine), rf (random forest)
def text_classifier(model_type):

    models = {
        'rf': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=0),
        'lsvm': LinearSVC(),
        'mnb': MultinomialNB(),
        'lg': LogisticRegression(random_state=0)
    }
    
    textclassifier = Pipeline([
        ('vect', CountVectorizer()),
        ('tfidf', TfidfTransformer()),
        ('oversample', SMOTE(sampling_strategy = {1:400, 2:200})),
        ('undersample', RandomUnderSampler(sampling_strategy = {0:300})),
        (model_type, models[model_type])])
    
    return textclassifier
 
def evaluate_model(textclassifier, df):
    data = df[['description', 'label']].values
    # split into input and output elements
    X, y = data[:, 0], data[:, -1].astype('int')
    # label encode the target variable
    X_train, X_test, y_train, y_test = tts(X, y, stratify=y, random_state=0)
    textclassifier.fit(X_train, y_train) 
    y_hat = textclassifier.predict(X_test)
    return classification_report(y_test, y_hat)

def main():
    pass


if __name__ == "__main__":
    df1 = pd.read_csv("/Users/canferakbulut/Documents/GitHub/TWITAUT/scraping/data/TWITAUT_Annotation_Spreadsheet.csv")   
    df1 = df1.rename(columns = {'label (0 = NA, 1 = autistic, 2 = parent of autistic child)': 'label'})
    df2 = pd.read_csv("/Users/canferakbulut/Documents/GitHub/TWITAUT/scraping/data/annotation_CA.csv")
    df2 = df2.rename(columns = {'scoring': 'label'})
    cols = ['description', 'id', 'verified', 'username', 'name', 'label']
    df1, df2 = df1[cols], df2[cols]
    print(intercoder_reliability(df1, df2))
    df = pd.concat([df1, df2])
    df.drop_duplicates(inplace=True, subset = ['id'])
    df['description'] = df['description'].map(description_cleaning)
    textclassifier = text_classifier('lsvm')
    print(evaluate_model(textclassifier, df))
    
    

    
                          
