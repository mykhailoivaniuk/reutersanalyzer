import pandas as pd
import requests as r
import re
import pandas as pd
import time


def api_call(company,date,api,token):
    if api == 'iex':
        base_url = 'https://cloud.iexapis.com/stable'
        params = """/stock/{}/chart/date/{}?chartByDay=true&token={}""".format(company, date, token)
        api_call = base_url + params
        return api_call
    if api == 'poly':
        base_url = 'https://api.polygon.io/v1/open-close/'
        params = """{}/{}??unadjusted=true&apiKey={}""".format(company, date, token)
        api_call = base_url + params
        return api_call
    else:
        raise Exception('Wrong API input')

def get_fin_data(row,api,token):
    companies = row["AssetMentions"]
    dates = [row['day0'],row['day1'],row['day10']]
    final_answers = []
    for company in companies:
        answers = {}
        for date in dates:

            if api == 'poly':
                resp = r.get(api_call(company,date,api,token)).json()
                if resp['status'] != "OK":
                    answers[date] = [0,0,0,0]
                    continue
                else:
                    answers[date] = [resp.get("open"), resp.get("close"), resp.get("afterHours"), resp.get("preMarket")]
                print(f'Got {company} at {date}')


            if api == 'iex':
                    resp_iex = r.get(api_call(company,re.sub('-','',date),api,token)).json()
                    if resp_iex == [] or resp_iex == None:
                        answers[date] = [0, 0, 0, 0]
                        continue
                    else:
                        resp_iex = resp_iex[0]
                        answers[date] = [resp_iex["uOpen"],resp_iex["uClose"],resp_iex['uLow'],resp_iex['uHigh']]
                        print(f'Got {company} at {date}')


        result = {'ticker':company,'day0':dates[0],'data0':answers[dates[0]],'date1':dates[1],
                        'data1':answers[dates[1]],'date10':dates[2],'data10':answers[dates[2]]}
        final_answers.append(result)
    return final_answers
