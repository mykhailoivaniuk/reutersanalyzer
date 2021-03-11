import string
import pandas as pd
import numpy as np
import requests
import datetime
import re
from datetime import date,timedelta,datetime
import time

def daterange(date1, date2):
    for n in range(int ((date2 - date1).days)+1):
        yield date1 + timedelta(n)

def get_weekends(startDate,endDate):
    weekends = [5,6]
    weekend_dates = []
    for dt in daterange(startDate, endDate):
        if dt.weekday() in weekends:
            weekend_dates.append(dt.strftime("%Y-%m-%d"))
    return weekend_dates

def api_holidate_call(type,direction,last,startDate):
    base_url = 'https://cloud.iexapis.com/stable'
    token = 'pk_cbb2af1cab3147a5b427316a2c28881c'
    params = """/ref-data/us/dates/{}/{}/{}/{}?token={}""".format(type, direction, last, startDate, token)
    api_call = base_url + params
    return api_call

def response_parser(keyname,data):
    dates = []
    current_year = date.today().year
    for element in range(len(data)):
        found_date = data[element][keyname]
        if date.fromisoformat(found_date).year>current_year:
            break
        dates.append(found_date)
    return dates
#Same as response parser, but for individual dates
def response_parser_one(keyname,data):
    current_year = date.today().year
    for element in range(len(data)):
        found_date = data[element][keyname]
        return found_date

#StartDate has to be in format 'YYYY-MM-DD'
def get_non_trading_days(startDate):
    #Initialize params for api_call
    type = 'holiday' #or trade
    direction = 'next'
    startDate1 = re.sub('-','',startDate)
    last = (date.today() - date.fromisoformat(startDate)).days
    startDate2 = date.fromisoformat(startDate)
    endDate = date.today()
    api_call = api_holidate_call(type,direction,last,startDate1)

    #Fetch the data from the API
    #Response is formatted as a list of dictionaries
    response = requests.get(api_call)
    data = response.json()
    holidays = response_parser('date',data)
    weekends = get_weekends(startDate2,endDate)
    final_holidays = []
    final_weekends = []
    for holiday in holidays:
        if date.fromisoformat(holiday) > date.today():
            continue
        final_holidays.append(holiday)
    for weekend in weekends:
        if date.fromisoformat(weekend) > date.today():
            continue
        final_weekends.append(weekend)
    if len(final_holidays) != 0:
        if final_holidays[0] == startDate:
            final_holidays = final_holidays[1:]
    if len(final_weekends) != 0:
        if final_weekends[0] == startDate:
            final_weekends = final_weekends[1:]
    print(f'--- Found {len(final_holidays)} holidays , {len(final_weekends)/2} weekends  ---')
    return final_holidays, final_weekends



def get_trading_dates(holidays,weekends,corresponding_dates):
    failed_weekends = []
    failed_holidays = []
    keyname = 'date'
    completed = 0
    failed = 0
    for holiday in holidays:
        try:
            type = 'trade'  # or holiday
            direction = 'next'
            last = 1
            startDate = re.sub(r'-','',holiday)
            # print(startDate)
            api_call = api_holidate_call(type,direction,last,startDate)
            response = requests.get(api_call)
            data = response.json()
            # print(response.json())
            corresponding_dates[holiday] = response_parser_one(keyname,data)
            completed += 1
            print(f'--- Trading date for holiday {holiday} found ---')
        except:
            failed += 1
            # corresponding_dates[holiday] = None
            failed_holidays.append(holiday)

    # print(f'completed {completed}, failed {failed}')
    completed = 0
    failed = 0
    for i in range(0,len(weekends) - 1,2):
        type = 'trade'  # or holiday
        direction = 'next'
        last = 1
        startDate = re.sub(r'-', '', weekends[i])
        api_call = api_holidate_call(type, direction, last, startDate)
        response = requests.get(api_call)
        try:
            response.raise_for_status()
            data = response.json()
            corresponding_dates[weekends[i]] = response_parser_one(keyname, data)
            corresponding_dates[weekends[i + 1]] = response_parser_one(keyname, data)
            completed += 1
            print(f'--- Trading date for weekend {weekends[i]} found ---')
        except:
            startDate = re.sub(r'-', '', weekends[i+1])
            api_call = api_holidate_call(type, direction, last, startDate)
            response = requests.get(api_call)
            try:
                data2 = response.json()
                corresponding_dates[weekends[i]] = response_parser_one(keyname, data2)
                corresponding_dates[weekends[i + 1]] = response_parser_one(keyname, data2)
                completed += 1
                print(f'--- Trading date for weekend {weekends[i]} found ---')
            except:
                #print(f'failed {weekends[i]},{weekends[i + 1]}')
                corresponding_dates[weekends[i]] = None
                corresponding_dates[weekends[i + 1]] = None
                failed += 1
                failed_weekends.append(weekends[i],weekends[i+1])

    # print(f'completed{completed}, failed {failed}')
    # print(corresponding_dates)

    return corresponding_dates, completed, failed,failed_weekends,failed_holidays

def sort_dates(dates_dict):
    ordered_dates = sorted(dates_dict.items(), key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'),
                           reverse=False)
    final_dates = {}
    for tuple in ordered_dates:
        if date.fromisoformat(tuple[0]) > date.today():
            continue
        final_dates[tuple[0]] = tuple[1]
    return final_dates

def update_dates():
    print('--- Updating Trading Dates ---')
    start_time = time.time()
    current_dates = pd.read_csv('trading_days.csv')
    last_date = current_dates['non_trading'].iloc[-1]
    print(f'--- Last non-trading_date is {last_date} ---')
    holidays,weekends = get_non_trading_days(last_date)
    dates = {}
    corresponding_dates,completed,failed,failed_weekends,failed_holidays = get_trading_dates(holidays,weekends,dates)
    while len(failed_holidays) != 0 and len(failed_weekends) != 0:
        print(f'--- Failed to fetch {len(failed_weekends)+len(failed_holidays)} dates. Trying again ---')
        corresponding_dates, completed, failed, failed_weekends, failed_holidays = get_trading_dates(failed_holidays, failed_weekends,corresponding_dates)
    corresponding_dates = sort_dates(corresponding_dates)
    for key,value in corresponding_dates.items():
        current_dates = current_dates.append({'non_trading':key,'trading':value},ignore_index = True)
    current_dates.to_csv('trading_days.csv',index = False)
    print("--- Finished updating trading dates file in: %s seconds ---" % (time.time() - start_time))
    # print(f'--- Failed {failed_weekends} weekends , Failed Holidays {failed_holidays} ---')
    return completed,failed




