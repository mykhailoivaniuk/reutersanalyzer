import pandas as pd
import re
import time
from datetime import date as dt,timedelta

#First we load the data, then run asset count
#This function is applied to all the data after asset count(because nlp needs syntax for analyzign text and recognizing entities)
#After we returned csv from asset count, we get the dates for articles where assetMentions is not empty
#Then we split it into two different csv - one for getting financial data, one for text data analysis


def clean_data(path):

    df = pd.read_csv(path)
    df.text = df.text.astype(str)
    # make text in text column lowercase
    df.text = df.text.apply(lambda x: x.lower())

    # remove all punctuation except apostrophes and periods
    df.text = df.text.apply(lambda x: x.translate(str.maketrans('', '', '"!#$%&()*+,-/:;<=>?@[\]^_`{|}~')))

    # remove all punctuation
    df.text = df.text.apply(lambda x: x.translate(str.maketrans('', '', string.punctuation)))

    # remove numbers
    df.text = df.text.apply(lambda x: x.translate(str.maketrans('', '', string.digits)))

def time_to_sec(t):
   h, m, s = map(int, t.split(':'))
   return h * 3600 + m * 60 + s



#Check if article is published after after hours trading session, thus we need to increment day by one
#t - datetime in string 'YYYY-MM_DD HH::MM:SS'.
# Returns correct date
def next_day_check(t):
    date = re.search(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',t).group(0)
    time = re.search(r'[0-9]{2}:[0-9]{2}:[0-9]{2}', t).group(0)
    tradeEndTime = time_to_sec('20:00:00')
    time = time_to_sec(time)
    if time> tradeEndTime:
        return get_next_dates(date,1)
    return date


#Date in string iso yyyy:mm:dd
#Gets the date + offset date. If date + offset > today, returns today
def get_next_dates(d,offset):
    date = dt.fromisoformat(d)
    offset = timedelta(days = offset)
    next_day = offset + date
    if next_day > dt.today():
        return dt.today().isoformat()
    return next_day.isoformat()

#Converts csv with non_trading days and trading days bck to it's original form. We do this to minimize use of credits on iexfinance cloud
#Return dictionary with non_trading_date : trading_date pairs
def get_dates_dict(pathToDates):
    ds = pd.read_csv(pathToDates)
    list_of_dict = ds.to_dict('records')
    corresponding_dates = {}
    for dict in list_of_dict:
        corresponding_dates[dict['non_trading']] = dict['trading']
    return corresponding_dates

#Check if given date is present in the dictionary of dates that need replacement
def helper(corresponding_dates, date):
    if corresponding_dates.get(date) != None:
        return corresponding_dates.get(date)
    return date

#Final function, splits the date into date and time, and determines correct dates by:
#Check if we need to move original date by one day, if time of article is after tarding hours - next_day_check
#Calculate offset dates by taking 1 and 10 day horizons
#Check if current day, 1 day horizon and 10 days horizons are not weekends or holidays, and if they are we swap them
#with the closest trading date

def time_checker(df, pathToDates):
    print('--- Getting correct dates for trading days ---')
    start_time = time.time()
    # df = pd.read_csv(pathToData)
    #Firts we get initial dates
    df['day0'] = df['date'].apply(lambda x: next_day_check(x))
    df['day1'] = df['day0'].apply(lambda x: get_next_dates(x, 1))
    df['day10'] = df['day0'].apply(lambda x: get_next_dates(x,10))
    df = df.drop(['date'],axis = 1)
    #Now we recheck those dates and make sure that we only get trading dates
    corresponding_dates = get_dates_dict(pathToDates)
    df['day0'] = df['day0'].apply(lambda x: helper(corresponding_dates, x))
    df['day1'] = df['day1'].apply(lambda x: helper(corresponding_dates, x))
    df['day10'] = df['day10'].apply(lambda x: helper(corresponding_dates, x))
    # df.to_csv(filename,index = False)
    print("--- Got Correct Dates in %s seconds ---" % (time.time() - start_time))
    return df




