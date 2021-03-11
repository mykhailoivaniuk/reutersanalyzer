import csv
import pandas as pd
from pandas import DataFrame as DF


def dict2CSV(dict_data: "dict", csv_columns: "list of strings", csv_file: "string"):
# dict2CSV: listof string? string? -> void
# dict_data: nested dictionary 
# csv_columns is list of column names ["Title", "Date", "Text"]
# csv_file is path of existing csv file to put data in ["/data/50pages.csv"]
    with open(csv_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        for key,val in sorted(dict_data.items()):
            row = dict_data[key]
            row.update(val)
            writer.writerow(row)

numbers = {'1':'2','3':'4'}

#Takes in dictionary without column names. Designed for trad
def dictCSV(dictionary,columns,csvFile):
    keys = dictionary.keys()
    values = dictionary.values()
    data = {columns[0]:keys,columns[1]:values}
    df = DF.from_dict(data)
    df.to_csv(csvFile,index =False)

#Creates dictionary from given csv file and corresponding two columns, where column1 is key, column2 is value
def to_dict(path, column1, column2):
    ds = pd.read_csv(path)
    list_of_dict = ds.to_dict('records')
    result = {}
    for dict in list_of_dict:
        result[dict[column1]] = dict[column2]
    return result