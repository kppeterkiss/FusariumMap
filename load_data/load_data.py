import pandas as pd
import json
import os
from sqlalchemy_utils import drop_database, database_exists, create_database
from sqlalchemy import inspect, create_engine
from datetime import timedelta, datetime

local_test_no_auth = True

# https://www.geeksforgeeks.org/how-to-create-and-use-env-files-in-python/
from dotenv import load_dotenv, dotenv_values

from bs4 import BeautifulSoup as bs
import pandas as pd
import requests
import zipfile
import numpy as np

#%%
from datetime import date

domain = "https://odp.met.hu/"
# this contains daily measurements for all the the stations - with the station data
url = "https://odp.met.hu/weather/weather_reports/synoptic/hungary/hourly/csv/"
filetype = ".zip"
data_table_name = 'weather'
load_dotenv()

data_folder='../data/'
hourly_data_folder= '../data/odp_met_hourly/'
hourly_data_folder_extracted= '../data/odp_met_hourly/extracted/'

day_table_name = os.getenv("UPDATE_TIMES_TABLE_NAME")
fusarium_table_name = os.getenv('FUSARIUM_TABLE_NAME')






def  get_connection_env(swarm_mode):
    CHARSET = "utf-8"

    DB_HOST = os.getenv("DB_HOST_LOCAL")
    if swarm_mode:
        DB_HOST = os.getenv("DB_HOST_SWARM")
    # for local test with trust auth
    DB_USER = os.getenv("DB_USER")
    print("db usr", DB_USER)
    DB_PORT = os.getenv("DB_PORT")
    DB_PASS = os.getenv("DB_PASSWORD")
    print("db pw:", DB_PASS)
    DATABASE = os.getenv("DATABASE_NAME")
    print("name:", DATABASE)

    connect_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(DB_USER, DB_PASS, DB_HOST, DB_PORT, DATABASE)
    print(connect_string)

    if not database_exists(connect_string):
        create_database(connect_string)

    engine = create_engine(connect_string, connect_args={'client_encoding': CHARSET})
    return engine




def table_exists(engine, name):
    ins = inspect(engine)
    ret = ins.dialect.has_table(engine.connect(), name)
    print('Table "{}" exists: {}'.format(name, ret))
    return ret

def get_db_table(tn, engine):
    df = None
    if table_exists(engine, tn):
        df = pd.read_sql_table(day_table_name, engine)
    return df


def write_table(tn, df, engine):
    df.to_sql(tn, engine, if_exists='replace', method='multi', index=False)


def add_update_time(lst, engine):
    df = pd.DataFrame({'Time': lst})
    df.to_sql(day_table_name, engine, if_exists='replace', method='multi', index=False)


def append_to_table(name, df, engine, mode='append'):
    df.to_sql(name, engine, if_exists='append', method='multi', index=False)



def get_update_times_already_loaded(engine):
    lst=[]
    if table_exists(engine,day_table_name):
        print(f'loading {day_table_name}')
        df = pd.read_sql_table(day_table_name, engine)
        lst = df['Time'].to_list()
    return lst




def get_datetime(fn):
    try:
        print("getting date from {} ...".format(fn))

        srt = fn.split('.')[0].split('_')[-1]

        dt = pd.to_datetime(srt, format='%Y%m%d%H%M%S')
        '''year=int(fn[8:12])
        month=int(fn[12:14])
        day=int(fn[14:16])
        print(year, month,day)
        d= date(year,month,day)
        print(type(d),d)'''
        return dt
    except Exception as e:
        print('Exception:', e)
        return None



def get_soup(url):
    return bs(requests.get(url).text, 'html.parser')


count = 0
new_data = []
def scrap_and_load_input_data(dates,engine):
    # dfs: list of all the new dataframes that comes from the new scrap
    dfs = []
    # check what files are on the page
    found_links=[]
    for link in get_soup(url).find_all('a'):
        file_link = link.get('href')
        # links on icon too (?)
        if file_link in found_links:
            continue
        found_links.append(file_link)
        # print(link)
        if filetype not in file_link:
            print('Not searched file {}'.format(file_link))
            continue
        print(file_link)
        # get the upload time of the file
        d = get_datetime(file_link)
        print('File found for {}'.format(d))
        # if we already loaded the file into db, or not the expected format then skip
        if d in dates:
            print('Already loaded {}, SKIPPED'.format(d))
            continue
        if not d:
            print('Not per date measurement file, SKIPPED')
            continue
        print('Downloading {}'.format(file_link))

        # file with data not loaded into weather table yet download
        with open(hourly_data_folder + file_link, 'wb') as file:
            response = requests.get(url + file_link)
            print('Response Code:', response.status_code)
            file.write(response.content)

        extracted_folder = hourly_data_folder_extracted + file_link.split('.')[0] + '/'
        print(f'Extracting {hourly_data_folder + file_link} ')
        # create folder with the same name of zip, and extract content in it
        with zipfile.ZipFile(hourly_data_folder + file_link, 'r') as zip_ref:
            if not os.path.exists(extracted_folder):
                os.mkdir(extracted_folder)
            zip_ref.extractall(extracted_folder)
            # iterate over all the downloaded files (per zip, with hourly update we expect a single file)
            for f in os.listdir(extracted_folder):
                # content of file to df
                df = pd.read_csv(extracted_folder + f, sep=";", skipinitialspace=True,parse_dates=['Time'], date_format='%Y%m%d%H%M%S')
                # collect dataframes in order to process for the result fusarium table
                dfs.append(df)
                # load the data from file into weather table
                append_to_table(data_table_name, df, engine)
                # delete file
                os.remove(extracted_folder + f)
            # delete directory
            os.rmdir(extracted_folder)
        os.remove(hourly_data_folder + file_link)
        # push the file update time into  update_time table
        days_df = pd.DataFrame.from_dict({'Time': [pd.to_datetime(d)]})
        append_to_table(day_table_name, days_df, engine)
    ret=pd.DataFrame()
    if len(dfs)>0:
        ret= pd.concat(dfs,axis=0, ignore_index=True)
    return ret


# function for calculating p -value
# TODO do we need sorting by time?
def caculate_p(df1):


    df = df1.copy()
    df['equal_last'] = df.groupby('StationNumber').apply(
        lambda x: x['TRH9010_cond'] == x['TRH9010_cond'].shift(1)).to_list()
    # did the truth value of the condition change? we set 1, if there was no change
    df['crossing'] = df['equal_last'].map({True: np.nan, False: 1})
    # number of  hours without  change
    a = df.groupby('StationNumber').apply(lambda x: x['crossing'].cumsum().ffill())
    #  stage = number of the current period without change, for grouping and counting the length of it
    df['stage'] = a.reset_index(level=0,drop=True)
    # for how many hours there was no change
    # here should add history, stage should be set to 0 if no change between it

    df['TRH9010'] = df.groupby(['StationNumber', 'stage'])['TRH9010_cond'].transform('cumcount')
    # fusarium p
    df['p'] = 0.0
    df.loc[(df['TRH9010_cond'] == True) & (df['TRH9010'] > 0), 'p'] = 6.8128 * df['TRH9010'] - 3.3756
    return df.drop(columns=['equal_last', 'crossing', 'stage'])


# caculate_p(df)
def add_history(df_hist, df1):
    df2 = df1.reset_index()
    firsts = df2.groupby('StationNumber').first()
    firsts.set_index('index')
    lasts = df_hist.groupby('StationNumber').last().reset_index()
    merged = firsts.merge(lasts, on='StationNumber', suffixes=('', '_last'))

    merged['TRH9010'] = np.where(merged['TRH9010_cond'] == merged['TRH9010_cond_last'],
                                 1 + merged['TRH9010_last'], merged['TRH9010'])
    new_counts = merged.loc[:, ~merged.columns.str.endswith('_last')]
    df1.loc[firsts.index] = merged
    return df1


def caculate_p_incremental(df1, history_df):
    df = df1.copy()
    df['equal_last'] = df.groupby('StationNumber').apply(
        lambda x: x['TRH9010_cond'] == x['TRH9010_cond'].shift(1)).to_list()
    # did the truth value of the condition change? we set 1, if there was no change
    df['crossing'] = df['equal_last'].map({True: np.nan, False: 1})
    # number of  hours without  change
    a = df.groupby('StationNumber').apply(lambda x: x['crossing'].cumsum().ffill())
    #  stage = number of the current period without change, for grouping and counting the length of it
    df['stage'] = a.reset_index(level=0, drop=True)
    # for how many hours there was no change
    # here should add history, stage should be set to 0 if no change between it
    df['TRH9010'] = df.groupby(['StationNumber', 'stage'])['TRH9010_cond'].transform('cumcount')
    df = add_history(history_df, df)
    # fusarium p
    df['p'] = 0.0
    df.loc[(df['TRH9010_cond'] == True) & (df['TRH9010'] > 0), 'p'] = 6.8128 * df['TRH9010'] - 3.3756
    return df.drop(columns=['equal_last', 'crossing', 'stage'])


def get_fusarium_history(first_date, tn,engine):
    if not table_exists(engine, tn):
        return None
        # TODO  magic constant
    d = first_date - timedelta(minutes=70)
    q = "SELECT \"Time\", u, ta, \"Latitude\", \"Longitude\", \"StationNumber\", \"TRH9010_cond\" ,\"p\" FROM {} WHERE \"Time\" >= '{}'".format(
        tn, d)
    print(q)
    sql_df = pd.read_sql(
        q,
        con=engine
    )
    if sql_df.empty:
        return None


def increment_p(df, first_date, hist_tn,engine):
    # function for calculating p -value
    df['TRH9010_cond'] = (df['ta'] > 15) & (df['ta'] < 30) & (df['u'] > 90)
    df_hist = get_fusarium_history(first_date, hist_tn,engine)
    if df_hist:
        df = caculate_p_incremental(df_hist, df)
        print('adding history.. ')
    else:
        print('No history to use')
        df = caculate_p(df)
    # if there is incrementation, otherwise at first fill, we write everything we got
    print(df.head())

    if df_hist:
        df = df[df['Time'] >= first_date]
    return df

def setup_dirs():
    if not  os.path.exists(data_folder):
        # Create a new directory because it does not exist
        os.makedirs(data_folder)
    if not  os.path.exists(hourly_data_folder):
        # Create a new directory because it does not exist
        os.makedirs(hourly_data_folder)
    if not  os.path.exists(hourly_data_folder_extracted):
        # Create a new directory because it does not exist
        os.makedirs(hourly_data_folder_extracted)

def main(swarm_mode):
    print('Chacking for data updates..')
    load_dotenv()
    engine = get_connection_env()
    # load from the update_times table the already processed timestamps
    times_already_loaded = get_update_times_already_loaded(engine)
    data_folder = '../data/odp_met_daily/'
    df = scrap_and_load_input_data(times_already_loaded, engine)
    if df.empty:
        print("No new data")
        return
    # what is the first measurement time in the new data?
    # we will load from fusarium table the processed data from an hour before,
    #in order to combine it with recent data
    time = df['Time'].min()
    incremented = increment_p(df, time, fusarium_table_name,engine)
    incremented = incremented[['Time', 'u', 'ta', 'Latitude', 'Longitude', 'StationNumber','TRH9010_cond','TRH9010','p']]
    append_to_table(fusarium_table_name, incremented, engine)


import schedule
import time
import argparse


def arg_parse():
    """
    Parse arguements to the detect module

    """

    parser = argparse.ArgumentParser(description='YOLO v3 Detection Module')

    parser.add_argument('--swarm',
                        action='store_true', help="Switch to swarm mode")

    return parser.parse_args()

if __name__ == "__main__":
    args = arg_parse()
    i=0
    schedule.every().hour.at(":10").do(main, args.swarm)

    while i < 30:
        schedule.run_pending()
        time.sleep(600)
        print('waiting..')
        i += 1
    '''
    main()
    '''