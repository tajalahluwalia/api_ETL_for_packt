# -*- coding: utf-8 -*-
"""PacktOriginal file is located at
    https://colab.research.google.com/drive/1aPO8lnZImvg_apoW4y_Jiwf8QSwwKSvX

“What are the top trending tags appearing in StackOverFlow this month?”



A pythonic interpretation. 

Can be hooked on to airflow to run on a set cadence.
"""

# documentation for the API
# https://stackapi.readthedocs.io/en/latest/

# install the api pkg 
!sudo pip3 install pyspark
!sudo pip3 install stackapi

##import required libraries

import time
import datetime
import pandas as pd
import pyspark.sql
from stackapi import StackAPI # import the API wrapper
from stackapi import StackAPIError # import error methods for debugging


# create spark session
spark = pyspark.sql.SparkSession \
        .builder \
        .appName("Packt Python Spark - StackOverflow Wrapper") \
        .getOrCreate()

# connect to the stackoverflow API using python wrapper
def stackoverflow_connect():
  try:
    # create a SITE object to query upon
    SITE = StackAPI('stackoverflow')
    SITE.page_size = 100
    SITE.max_pages=50 # this number would have to be tweaked
  except StackAPIError as e:
    print(e.message)
  return SITE

# get the json object for the current month 
def fetch_questions_JSON(SITE):
  # month_begin = int(datetime.datetime.now().replace(day = 1).timestamp())   # get the timestamp of the beginning of current month based on when the query is run  
  now = int(datetime.datetime.now().timestamp())   # get the timestamp of the current times based on when the query is run
  month_begin = int((datetime.datetime.now() - datetime.timedelta(30)).timestamp()) # use a timedelta to get the data 30 days ago from current date

  # get a JSON load of all the question in a timeframe ** 
  questions = SITE.fetch('questions' , fromdate = month_begin , todate = now
                        #  , min = 20
                        #  , tagged = 'python'
                        , sort = 'votes')
  return questions 

# read the json file into a pandas DF
def json_df_redux(questions):
  # pull the items from the JSON questions field 
  df = pd.json_normalize(questions['items'])
  return df


# upload the raw df into database using spark (intentionally left blank)
def load_raw_df_to_db(df):
  # conver the pandas df into spark df 
  raw_spark_df = spark.createDataFrame(df)
  mode = "overwrite"
  url = "jdbc:redshift://localhost:5432/etl_pipeline"
  properties = {"user": "<username>",
                "password": "<password>",
                "driver": "org.redshift.Driver"
                }
  raw_spark_df.write.jdbc(url=url,
                table = "raw_stackoverflow_questions",
                mode = mode,
                properties = properties)

# lets transform the questions pandas df to make some more insights about the tags

def tag_enrichment(df):
  df1 = df.explode('tags') # we are explosing the tags column into rows to get each tag detail
  monthly_top_20_tags = df1['tags'].value_counts()[:20]
  monthly_top_20_tags = monthly_top_20_tags.to_frame()
  return monthly_top_20_tags

# lastly, send this top 20 tags as an email to a distro or use the load_raw_df_to_db function above to push it to desired database
def email_tag_data(df):
  import smtplib
  sender = 'tajal.walia@gmail.com'
  receivers = ['curious@packt.com']
  message = """From: From Tajal
  To: Packt
  Subject: top 20 stackoverflow tags this month
  {}
  """.format(df)

  try:
    smtpObj = smtplib.SMTP('localhost')
    smtpObj.sendmail(sender, receivers, message)         
    print("Successfully sent email")
  except:
    print("Error: unable to send email")


if __name__ == "__main__":
    SITE = stackoverflow_connect()
    questions = fetch_questions_JSON(SITE)
    df = json_df_redux(questions)
    # load_raw_df_to_db(df) # optional step to push the raw dataframe into database of choice
    top_tags = tag_enrichment(df)
    email_tag_data(top_tags)



# -------- -------- airflow implementation of DAG -------- --------

# from airflow import DAG
# from airflow.operators.bash_operator import BashOperator
# from airflow.operators.python_operator import PythonOperator

# default_args = {'owner': 'tajal_ahluwalia','start_date': dt.datetime(2021, 6, 1),'retries': 3,'retry_delay': dt.timedelta(minutes=5)}

# with DAG('MyDBdag', default_args=default_args, schedule_interval=timedelta(minutes=5) , '0 0 1 * *') as dag:
#   SITE = stackoverflow_connect()
#   questions = fetch_questions_JSON(SITE)
#   df = json_df_redux(questions)
#   # load_raw_df_to_db(df) # optional step to push the raw dataframe into database of choice
#   tag_enrichment(df)

"""Test the functions locally"""

# demo of some functions

SITE = stackoverflow_connect()
questions = fetch_questions_JSON(SITE)
df = json_df_redux(questions)
# load_raw_df_to_db(df) # optional step to push the raw dataframe into database of choice
top_tags = tag_enrichment(df)

"""Outputs"""

# the raw dataframe
df.head(2)

# top trending tags appearing in StackOverFlow this month

top_tags.head(5)



