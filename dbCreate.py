import pandas as pd
from pandas.io import sql
from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://{user}:{pw}@localhost/{db}?charset=utf8"
                       .format(user="****",
                               pw="****",
                               db="****"))
data = pd.read_csv('init_db/Train_schedule.csv')
data.to_sql(con=engine, name='train_schedule', if_exists='replace', index=False)

data1 = pd.read_csv('init_db/booking.csv')
data1.to_sql(con=engine, name='booking', if_exists='replace', index=True)
