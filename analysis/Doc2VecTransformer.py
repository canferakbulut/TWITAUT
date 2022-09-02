#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug  7 12:22:30 2022

@author: canferakbulut
"""

#credit to: @avisheknag17

from sklearn.base import BaseEstimator
from gensim.models.doc2vec import TaggedDocument, Doc2Vec
from gensim.parsing.preprocessing import preprocess_string
from sklearn.base import BaseEstimator
from sklearn import utils as skl_utils
from tqdm import tqdm
import multiprocessing
import numpy as np

class Doc2VecTransformer(BaseEstimator):

    def __init__(self, vector_size = None, epochs = None, window = None, min_count = None, dm = None):
        self.epochs = epochs
        self._model = None
        self.vector_size = vector_size
        self.window = window
        self.min_count = min_count
        self.workers = multiprocessing.cpu_count() - 1
        self.dm = dm

    def fit(self, x, y=None):
        tagged_x = [TaggedDocument(doc.split(), [tag]) for doc, tag in zip(x, y)]
        model = Doc2Vec(documents=tagged_x, vector_size=self.vector_size, dm= self.dm, 
                        window = self.window, 
                        min_count = self.min_count,
                        workers=self.workers)

        model.train(skl_utils.shuffle(tagged_x), total_examples=len(tagged_x), epochs=self.epochs)

        self._model = model
        
        return self

    def transform(self, x):
        return np.matrix(np.array([self._model.infer_vector(doc.split())
                                     for doc in x]))
    
