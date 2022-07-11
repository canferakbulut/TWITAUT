#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  5 10:52:00 2022

@author: canferakbulut
"""
import pandas as pd
import numpy as np 
import random

def samples_to_annotate(df, nsample = 30000, noverlap = 1000, seed = 30):
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
    
    
                          
