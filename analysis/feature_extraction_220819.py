#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 19 20:18:29 2022

@author: canferakbulut
"""
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from imblearn.pipeline import Pipeline, make_pipeline
from imblearn.over_sampling import SMOTE
import numpy as np
from scipy import sparse
from sklearn.feature_selection import chi2
from nltk import bigrams

def feature_extraction(df, n_top_features):
    tfidf = TfidfVectorizer(sublinear_tf=True, norm='l2', encoding='latin-1', ngram_range=(1, 2))
    features = tfidf.fit_transform(df.description.astype('U')).toarray()
    labels = df.label
    unique_labels = list(set(labels))
    feature_dic = {label: {'unigrams':[], 'bigrams':[]} for label in unique_labels}
    for label in unique_labels:
        features_chi2 = chi2(features, labels == label)
        indices = np.argsort(features_chi2[0])
        feature_names = np.array(tfidf.get_feature_names_out())[indices]
        feature_dic[label]['unigrams'] = [v for v in feature_names if len(v.split(' ')) == 1][-n_top_features:]
        feature_dic[label]['bigrams'] = [v for v in feature_names if len(v.split(' ')) == 2][-n_top_features:]
    return feature_dic

def create_ratio_feature(df, feature_dic):
    labels = [1, 2]
    counts = {x: [] for x in labels}
    for desc in df.description.to_list():
        uni = desc.split()
        bi = [" ".join(x) for x in list(bigrams(desc.split()))]
        for label in labels:
            count = sum([1 if x == y else 0 for x in uni for y in feature_dic[label]['unigrams']]) + \
                    sum([1 if x == y else 0 for x in bi for y in feature_dic[label]['bigrams']])
            counts[label].append(count)
    
    return counts

def feature_classification(df):
    feature_dic = feature_extraction(df, 20)
    counts = create_ratio_feature(df, feature_dic)
    X = sparse.csr_matrix((np.array([counts[1], counts[2]])).reshape(-1,2))
    y = (df['label'].values).astype('int')
    X_train, X_test, y_train, y_test = tts(X, y, stratify=y, random_state=0, test_size=0.33)
    pipe = Pipeline([
        ('oversample', SMOTE()),
        ('undersample', RandomUnderSampler()),
        ('mnb', MultinomialNB())])
    pipe.fit(X_train, y_train)
    y_hat = pipe.predict(X_test)
    print(classification_report(y_test, y_hat))
    
