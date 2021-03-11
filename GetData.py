from dataTransform import analyze_data
from processdata import load_data
import os
import pandas as pd


def NewsAnalyzer (workType, api,token,name,path,count):

    if workType == 'sample':
        print('Entered {} mode'.format(workType))
        df = pd.read_csv('1700pages.csv')
        df = df[1000:1100]
        df.to_csv('sample.csv',index = False)
        analyze_data('sample.csv', 'companies.csv',api,token)
        os.remove('sample.csv')

    if workType == 'full':
        
        print('Entered {} mode'.format(workType))
        completed, failed = load_data('FullRaw', 2100)
        analyze_data('FullRaw.csv', 'companies.csv',api, token)
        os.remove('FullRaw.csv')
    
    if workType == 'demo':

        print('Entered {} mode'.format(workType))
        completed, failed = load_data('RawDemo', 10)
        df = pd.read_csv('1700pages.csv')
        df = df[1000:1100]
        df.to_csv('sample.csv',index = False)
        analyze_data('sample.csv', 'companies.csv',api,token)
        os.remove('sample.csv')
        os.remove('RawDemo.csv')
    
    if workType == 'existing':

        print('Entered {} mode'.format(workType))
        print('Download StockData and NewsData from github at ')
    
    if workType == 'scrape':

        print('Entered {} mode'.format(workType))
        name = str(input('Filename for scraped data(without format extension): '))
        completed,failed = load_data(name,count)

    if workType == 'analyze':

        print('Entered {} mode'.format(workType))
        analyze_data(f'{name}.csv', 'companies.csv',api,token)

    if workType == 'custom':

        print('Entered {} mode'.format(workType))
        name = str(input('Filename for scraped data(without format extension): '))
        completed,failed = load_data(name,count)
        analyze_data(f'{name}.csv', 'companies.csv',api,token)

