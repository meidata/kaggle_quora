#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 14 17:08:27 2017

@author: meiyi
"""

import pandas as pd
import numpy as np
from scipy import sparse as ssp


path_feature = '/Users/meiyi/Desktop/kaggle_quora/features/'

# basic features ---- features engineering

test_data = pd.DataFrame()

for i in range(0,10):
    filename = 'test_'+str(i)+'_quora_features.pkl'
    data = pd.read_pickle(path_feature+filename)
    test_data = test_data.append(data)
    
    
train_data = pd.read_pickle(path_feature + 'train_quora_features.pkl')


# w2v features ---- features engineering

test_w2v_q1 = pd.DataFrame()

for i in range(0,10):
    filename = 'test_'+str(i)+'_q1_w2v_google.pkl'
    ary = np.load(path_feature+filename)
    data = pd.DataFrame(ary,columns=['q1_' + i for i in list(map(str,range(0,ary.shape[1])))])
    test_w2v_q1 = test_w2v_q1.append(data)

test_w2v_q2 = pd.DataFrame()

for i in range(0,10):
    filename = 'test_'+str(i)+'_q2_w2v_google.pkl'
    ary = np.load(path_feature+filename)
    data = pd.DataFrame(ary,columns=['q2_' + i for i in list(map(str,range(0,ary.shape[1])))])
    test_w2v_q2 = test_w2v_q2.append(data)


train_w2v_q1 = np.load(path_feature+'train_q1_w2v_google.pkl')
train_w2v_q1 = pd.DataFrame(train_w2v_q1,columns=['q1_' + i for i in list(map(str,range(0,train_w2v_q1.shape[1])))])
  
train_w2v_q2 = np.load(path_feature+'train_q2_w2v_google.pkl')
train_w2v_q2 = pd.DataFrame(train_w2v_q2,columns=['q2_' + i for i in list(map(str,range(0,train_w2v_q2.shape[1])))])
  


# magic features 

train_comb = pd.read_pickle(path_feature+'magic_feature_train.pkl')
test_comb = pd.read_pickle(path_feature+'magic_feature_test.pkl')




# features stacking

train_features = pd.concat([train_data[train_data.columns.difference(['question1', 'question2'])],
                             #train_w2v_q1,
                             #train_w2v_q2,
                             train_comb[train_comb.columns.difference(['id','is_duplicate'])]], axis=1)
    #.tocsr()

    
test_features = pd.concat([test_data[test_data.columns.difference(['question1', 'question2'])],
                            #test_w2v_q1
                            #test_w2v_q2,
                            test_comb[test_comb.columns.difference(['id'])]],axis=1)
    #.tocsr()
    
    

from sklearn.model_selection import train_test_split

feature_col = train_features.columns.difference(['id']).values.tolist()

pos_train, pos_test = train_test_split(train_features.ix[train_features['is_duplicate']==1,feature_col], test_size = 0.3)
neg_train, neg_test = train_test_split(train_features.ix[train_features['is_duplicate']==0,feature_col], test_size = 0.3)

train_X = pos_train.append(neg_train)
test_X = pos_test.append(neg_test)

train_y = train_X.is_duplicate.values
train_X = train_X[train_X.columns.difference(['is_duplicate'])]

test_y = test_X.is_duplicate.values
test_X = test_X[test_X.columns.difference(['is_duplicate'])]



import xgboost as xgb

# Set our parameters for xgboost
params = {}
params['objective'] = 'binary:logistic'
params['eval_metric'] = 'logloss'
params['eta'] = 0.02
params['max_depth'] = 4

d_train = xgb.DMatrix(train_X, label=train_y)
d_valid = xgb.DMatrix(test_X, label=test_y)

watchlist = [(d_train, 'train'), (d_valid, 'valid')]

a = 0.165 / 0.37

b = (1 - 0.165) / (1 - 0.37)

def kappa(preds, y):
    score = []
    for pp,yy in zip(preds, y.get_label()):
        score.append(a * yy * np.log (pp) + b * (1 - yy) * np.log(1-pp))
    score = -np.sum(score) / len(score)

    return 'kappa', float(score)

bst = xgb.train(params, d_train, 1000, watchlist, early_stopping_rounds=5, verbose_eval=10, feval = kappa)

feature_col_test = train_X.columns.values.tolist()

d_test = xgb.DMatrix(test_features.ix[:,feature_col_test])
p_test = bst.predict(d_test)

sub = pd.DataFrame()
sub['test_id'] = test_comb['id']
sub['is_duplicate'] = p_test
path = '/Users/meiyi/Desktop/kaggle_quora/'
sub.to_csv(path+'xgb_1405.csv', index=False)
    


