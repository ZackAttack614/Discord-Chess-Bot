import pandas as pd
from datetime import *
import numpy as np

df = pd.read_csv("data/lichess_swiss_rating_histories_sample.csv",parse_dates=['date'])
# The latest date we have data on
max_outcome_date = df['date'].max()
# The latest date that can be used for training to ensure we'll always have 2 years in advance of outcomes data
max_training_date = max_outcome_date - timedelta(days=365*2)
# The latest ratings that can be used for training
df_training = df.query('date<=@max_training_date')
df_outcomes = df.query('date>@max_training_date')
latest_training_ratings = df_training.sort_values("date",ascending=False).drop_duplicates(['user_id','time_control'])
max_training_date_minus_30 = max_training_date-timedelta(days=30)
max_training_date_minus_90 = max_training_date-timedelta(days=90)
max_training_date_minus_180 = max_training_date-timedelta(days=180)
hist_ratings_30 = df_training.query('date<=@max_training_date_minus_30').sort_values("date",ascending=False).drop_duplicates(['user_id','time_control'])
hist_ratings_90 = df_training.query('date<=@max_training_date_minus_90').sort_values("date",ascending=False).drop_duplicates(['user_id','time_control'])
hist_ratings_180 = df_training.query('date<=@max_training_date_minus_180').sort_values("date",ascending=False).drop_duplicates(['user_id','time_control'])
hist_ratings_peak = df_training.sort_values("rating",ascending=False).drop_duplicates(['user_id','time_control'])
rating_stdev_30 = df_training.query('date>=@max_training_date_minus_30').groupby(['user_id','time_control'])['rating'].std().fillna(0).reset_index().rename(columns={"rating":"rating_stdev_30"})
rating_stdev_90 = df_training.query('date>=@max_training_date_minus_90').groupby(['user_id','time_control'])['rating'].std().fillna(0).reset_index().rename(columns={"rating":"rating_stdev_90"})
rating_stdev_180 = df_training.query('date>=@max_training_date_minus_180').groupby(['user_id','time_control'])['rating'].std().fillna(0).reset_index().rename(columns={"rating":"rating_stdev_180"})
rating_updates_30 = df_training.query('date>=@max_training_date_minus_30').groupby(['user_id','time_control']).size().reset_index().rename(columns={0:"rating_updates_30"})
rating_updates_90 = df_training.query('date>=@max_training_date_minus_90').groupby(['user_id','time_control']).size().reset_index().rename(columns={0:"rating_updates_90"})
non_target_rating_updates_30 = rating_updates_30.pivot(index='user_id',columns='time_control',values='rating_updates_30').fillna(0)
df_base = latest_training_ratings.merge(hist_ratings_30[['user_id','time_control','rating']],
                how='left',on=['user_id','time_control'],suffixes=['_latest','_30']).merge(
            hist_ratings_90[['user_id','time_control','rating']],
                how='left',on=['user_id','time_control']).merge(
            hist_ratings_180[['user_id','time_control','rating']],
                how='left',on=['user_id','time_control'],suffixes=['_90','_180']).merge(
            hist_ratings_peak[['user_id','time_control','rating']].rename(columns={'rating':'rating_peak'}),
                how='left',on=['user_id','time_control']).merge(
            rating_updates_30,how='left',on=['user_id','time_control']).merge(
            rating_updates_90,how='left',on=['user_id','time_control']).merge(
            rating_stdev_30,how='left',on=['user_id','time_control']).merge(
            rating_stdev_90,how='left',on=['user_id','time_control']).merge(
            rating_stdev_180,how='left',on=['user_id','time_control']).merge(
            non_target_rating_updates_30,how='left',on='user_id'
)
df_base['rating_30_diff'] = df_base['rating_latest']-df_base['rating_30']
df_base['rating_90_diff'] = (df_base['rating_latest']-df_base['rating_90']).combine_first(df_base['rating_30_diff'])
df_base['rating_180_diff'] = (df_base['rating_latest']-df_base['rating_180']).combine_first(df_base['rating_90_diff'])
df_base['rating_peak_diff'] = df_base['rating_latest']-df_base['rating_peak']
df_base['time_control_copy'] = df_base['time_control']
df_base['rating_latest_rounded'] = df_base['rating_latest'].round(-2)
df_base['rating_latest_squared'] = df_base['rating_latest']**2
df_base['rating_latest_rounded_200'] = 200*np.ceil(df_base['rating_latest_rounded']/200).astype(int)
df_base['rating_latest_rounded_300'] = 300*np.ceil(df_base['rating_latest_rounded']/300).astype(int)
df_base = pd.get_dummies(df_base,columns=['time_control_copy'],prefix_sep="")
df_base.columns = [x.replace("time_control_copy","").lower() for x in df_base.columns]
# Filter to people who have played rated games in the time control before 30 days ago...
# ... and have played at least one rated game in the time control within the last 30 days
df_base = df_base[(df_base['rating_30'].notna())&(df_base['date']>=max_training_date_minus_30)]
# Generate target ratings
df_targets = pd.concat([df_base for x in range(5)])
np.random.seed(1)
def get_target_rating_gain(x):
    # Right side of interval is exclusive, so this goes from 1-3
    die = np.random.randint(1,4)
    if die == 1:
        return np.random.randint(1,100)
    elif die == 2:
        return np.random.randint(1,300)
    elif die == 3:
        if x < 1550:
            return np.random.randint(100,700)
        elif x < 1900:
            return np.random.randint(100,500)
        else:
            return np.random.randint(100,400)
    else:
        print(1/0)

df_targets['target_rating_gain'] = df_targets['rating_latest'].apply(get_target_rating_gain)
df_targets.drop_duplicates(subset=['user_id','time_control','target_rating_gain'],inplace=True)
df_targets['target_rating'] = df_targets['rating_latest'] + df_targets['target_rating_gain']
df_targets['target_rating_gain_rounded'] = df_targets['target_rating_gain'].round(-2)
df_targets['target_rating_gain_squared'] = df_targets['target_rating_gain']**2
df_temp = df_targets[['user_id','time_control','target_rating','date']].copy()
df_temp = df_temp.merge(df_outcomes,on=['user_id','time_control'],how='outer',suffixes=['_latest','_future'])

# Successes - filter to where future rating >= target rating, then take earliest date for each user/time control
df_successes = df_temp.query('rating>=target_rating').sort_values("date_future").drop_duplicates(['user_id','time_control','target_rating'])
# Successes and failures 
df_bin = df_targets.merge(df_successes[['user_id','time_control','target_rating','date_future']],on=['user_id','time_control','target_rating'],how='left')
# Was the target rating achieved?
df_bin['y_bin'] = df_bin['date_future'].notna().astype(int)
# If so, when?
df_bin['y_cont'] = (df_bin['date_future']-max_training_date).dt.days
df_bin.to_csv("data/lichess_swiss_processed_sample.csv",index=False)