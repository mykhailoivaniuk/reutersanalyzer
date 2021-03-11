import pandas as pd
import numpy as np
import time
import csv
import spacy
from spacy import displacy
from collections import Counter
from dict2CSV import to_dict
import en_core_web_sm
from dataCleaning import time_checker
from financial_data import get_fin_data 
import re
import string
import string
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords


nlp = en_core_web_sm.load()

nltk.download('stopwords')
nltk.download('vader_lexicon')
nltk.download('punkt')

#Function is applied to the list of sentences and it deletes sentences from Reuters that describe article picture or show Reuters ads
def sentence_clean(sent_list):
    new_list = []
    blacklist = ['Graphic:','FILE PHOTO','File Photo', 'LIVE']
    for sentence in sent_list:
        dismiss = 0
        if sentence == '':
            continue
        for item in blacklist:
            if item in sentence:
                dismiss += 1
        if dismiss == 0:
            new_list.append(sentence)
    return new_list

#Not sure what exactly this is
def space(comment):
    doc = nlp(comment)
    return " ".join([token.lemma_ for token in doc])

#This function takes a df as an argument and appends new columns such as:
#sentence_count, word_count, compound Vader scores and total Vader scores in each category

def text_analysis(df):
    print('--- Text Analysis Started ---')
    start_time = time.time()
    df.text = df.text.astype(str)
    df['sentence_count'] = df.text.apply(lambda x: len(sentence_clean(re.split(r'[.!?]+', x))))
    df['text'] = df.text.apply(lambda x: '.'.join(sentence_clean(re.split(r'[.!?]+', x))))
    df['word_count'] = df.text.apply(lambda x: len(re.findall(r'\w+', x)))

    df.text = df.text.astype(str)

    #Sentiment Analysis starts here


    # remove stopwords in "new_text"
    stop = stopwords.words('english')
    df['lemmatized'] = df.text.apply(lambda x: x.lower())
    #
    # remove all punctuation except apostrophes and periods
    df['lemmatized'] = df['lemmatized'].apply(lambda x: x.translate(str.maketrans('', '', '"!#$%&()*+,-/:;<=>?@[\]^_`{|}~')))

    # remove all punctuation
    df['lemmatized'] = df['lemmatized'].apply(lambda x: x.translate(str.maketrans('', '', string.punctuation)))

    # remove numbers
    df['lemmatized'] = df['lemmatized'].apply(lambda x: x.translate(str.maketrans('', '', string.digits)))
    df['lemmatized'] = df['lemmatized'].apply(lambda x: " ".join(x for x in x.split() if x not in stop))

    # lemmatize
    nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])
    df['lemmatized'] = df['lemmatized'].apply(space)

    # find compound Vader scores
    analyzer = SentimentIntensityAnalyzer()

    cs = []
    for row in range(len(df)):
        cs.append(analyzer.polarity_scores(df['lemmatized'].iloc[row])['compound'])

    df['score'] = cs
    df = df[(df[['score']] != 0).all(axis=1)].reset_index(drop=True)

    # find individual pos neg scores
    df['scores'] = df['lemmatized'].apply(lambda text: analyzer.polarity_scores(text))
    print("--- Text Analysis Finished: %s seconds ---" % (time.time() - start_time))
    return df


#Searches for organization names in text and cleans their names from excessive words
def asset_cleaner(text):
    orgList = []
    doc = nlp(text)
    # List of words to filter and clean up
    words_to_filter = ["Inc.", " Inc", " Co." " Co", " LTD", 'ltd', 'ltd.', 'LTD.', 'The', 'the',
                       " Inc.,", " Inc, ", ' inc,.', ' inc,', 'Corporation', 'Company', "\'s ", 'Corp',
                       '.com', ' SA ']
    # Appending entities which have the label 'ORG' to the list
    for entity in doc.ents:
        if entity.label_ == 'ORG':
            company = entity.text
            for word in words_to_filter:
                company = company.replace(word, "")
            orgList.append(company.strip())
    # print('Finished')
    return orgList


#Checks whether resulting short name from asset cleaner is in our companies file, and if it is returns corresponding ticker
def assetFilter(orgList, compTickers):
    tickers = []
    for org in orgList:
        if compTickers.get(org) == None:
            continue
        tickers.append(compTickers[org])
    if tickers == []:
        return 0
    return np.array(tickers)



def analyze_data(textpath, tickerpath,api,token):
    # Read text data
    print('--- Data Analyzer Started ---')
    fullapiname = ''
    if api  == 'iex':
        fullapiname = "IEX Trading"
    if api == 'poly':
        fullapiname = 'Polygon API'
    start_time = time.time()
    textdf = pd.read_csv(textpath)
    compTickers = to_dict(tickerpath,'short name','ticker')
    textdf['AssetMentions'] = textdf['text'].apply(lambda x: asset_cleaner(str(x)))
    textdf['AssetMentions'] = textdf['AssetMentions'].apply(lambda x: assetFilter(x,compTickers))
    textdf = textdf[textdf["AssetMentions"] != 0]
    textdf["TotalMentions"] = textdf["AssetMentions"].apply(lambda x: len(x))
    textdf['AssetMentions'] = textdf['AssetMentions'].apply(lambda x: np.unique(x))
    textdf = time_checker(textdf,'trading_days.csv')
    print(f'--- Started requesting financial data from {fullapiname} ---')
    start_time2 = time.time()
    textdf['result'] = textdf.apply(lambda x: get_fin_data(x,api,token), axis=1)
    print(f"--- Finished getting financial data in {(time.time() - start_time2)}s seconds ---")
    findata = pd.DataFrame(columns = ['ticker','day0','data0','date1','data1', 'date10', 'data10'])
    text_data = text_analysis(textdf.drop(columns = ['day1','day10','result']))
    for results in textdf['result']:
        for result in results:
            findata = findata.append({'ticker': result['ticker'],'day0':result['day0'],'data0':result['data0'],'date1':result['date1'],
                            'data1':result['data1'],'date10':result['date10'],'data10':result['data10']}, ignore_index = True)
    text_data.to_csv('NewsData.csv',index = False)
    findata.to_csv('StockData.csv',index = False)
    print("--- Complete Analysis finished in %s seconds ---" % (time.time() - start_time))
