import requests
import datetime
import numpy as np
import pandas as pd
import json
import os

model_params = pd.read_csv("data/model_params_20210825.csv")

# Convert rating history info from JSON to Dataframe
async def process_rating_history(response_json):
    rating_history = dict()
    for x in response_json:
        if x['name'] in ['Bullet','Blitz','Rapid','Classical'] and len(x['points']) > 0:
            tbl = pd.DataFrame(x['points'])
            tbl.columns = ['year','month','day','rating']
            tbl['month'] = tbl['month']+1
            tbl['date'] = pd.to_datetime(tbl.year*10000+tbl.month*100+tbl.day,format='%Y%m%d')
            rating_history[x['name']] = tbl
    return(rating_history)

# Calculate the values that are inputs to the models
async def get_predictor_values(rating_history,target_rating,variant):
    target_rating_history = rating_history[variant]
    today = datetime.datetime.today()
    t_minus_30 = today-datetime.timedelta(days=30)
    t_minus_90 = today-datetime.timedelta(days=90)
    t_minus_180 = today-datetime.timedelta(days=180)
    target_rating_history_30 = target_rating_history.query('date>=@t_minus_30')
    target_rating_history_pre_30 = target_rating_history.query('date<@t_minus_30')
    target_rating_history_90 = target_rating_history.query('date>=@t_minus_90')
    target_rating_history_180 = target_rating_history.query('date>=@t_minus_180')    
    rating_latest = target_rating_history['rating'].values[-1]
    target_rating_gain = target_rating-rating_latest
    predictor_values = dict(Intercept=1,target_rating_gain=target_rating_gain,
        target_rating_gain_squared=target_rating_gain**2,
        rating_latest=rating_latest,
        rating_latest_squared = rating_latest**2,
        bullet = int(variant == 'Bullet'), blitz = int(variant == 'Blitz'),
        rapid = int(variant == 'Rapid'), classical = int(variant == 'Classical'),
        rating_peak_diff = rating_latest-target_rating_history['rating'].max(),
        rating_30_diff = rating_latest-target_rating_history_30['rating'].values[0] if len(target_rating_history_30) > 0 else 0,
        rating_90_diff = rating_latest-target_rating_history_90['rating'].values[0] if len(target_rating_history_90) > 0 else 0,
        rating_180_diff = rating_latest-target_rating_history_180['rating'].values[0] if len(target_rating_history_180) > 0 else 0,
        rating_updates_30 = len(target_rating_history_30),
        rating_updates_90 = len(target_rating_history_90),
        rating_updates_180 = len(target_rating_history_180),
        # Number of rating updates before 30 days ago
        rating_updates_pre_30 = len(target_rating_history_pre_30),
        rating_stdev_30 = target_rating_history_30['rating'].std() if len(target_rating_history_30) > 1 else 0,
        rating_stdev_90 = target_rating_history_90['rating'].std() if len(target_rating_history_90) > 1 else 0
                                   )
    return(predictor_values)

# Calculate the probability of success given a set of predictor values and a classification model
async def get_prob_success(predictor_values,model_params):
    logit_params = model_params[['var_name','logit']].dropna()
    log_odds = 0
    for i in range(len(logit_params)):
        term_name = logit_params['var_name'].values[i]
        coef = logit_params['logit'].values[i]
        var_names = term_name.split(":")
        value = np.prod([predictor_values[j] for j in var_names])
        log_odds += coef*value
    prob_success = 100*1/(1+np.exp(-1*(log_odds)))
    return round(prob_success)

# Calculate the predicted days until target rating given a set of predictor values and a regression model
async def get_predicted_date(predictor_values,model_params):
    ols_params = model_params[['var_name','ols']].dropna()
    predicted_days = 0
    for i in range(len(ols_params)):
        term_name = ols_params['var_name'].values[i]
        coef = ols_params['ols'].values[i]
        var_names = term_name.split(":")
        value = np.prod([predictor_values[j] for j in var_names])
        predicted_days += coef*value
    predicted_days = max(predicted_days,0)
    predicted_days = min(predicted_days,365*2)
    predicted_date = (datetime.datetime.today()+datetime.timedelta(days=predicted_days)).strftime(format="%B %d, %Y")
    return(predicted_date)

class Mock_Response():
    def __init__(self,username):
        self.username = username
        self.status_code = 200 if f"{username}.json" in os.listdir("mock_data") else 400
    def json(self):
        with open(f"mock_data/{self.username}.json") as f:
            data = json.load(f)
            return data

# Calculate the scores based on inputs
async def score(username,target_rating,variant,model_params,testing=False):
    url = f'https://lichess.org/api/user/{username}/rating-history'
    if testing:
        response = Mock_Response(username)
    else:
        response = requests.get(url)
    if response.status_code != 200:
        return (True,f"Error: can't retrieve lichess data for user {username}.",None,None)
    else:
        response_json = response.json()
        if not any(response_json):
            return (True,"Error: no lichess data available",None,None)
        rating_history = await process_rating_history(response_json)
        if variant not in rating_history:
            return(True,f"Error: user {username} has no rating history for variant {variant.title()}.",None,None)
        predictor_values = await get_predictor_values(rating_history,target_rating,variant)
        if predictor_values['rating_latest'] >= target_rating:
            return(True,f"Error: {username} has already achieved the target rating {target_rating} {variant}.",None,None)
        elif predictor_values['target_rating_gain'] > 1000:
            return(True,"Error: please submit a target rating gain of less than +1000 points.",None,None)
        prob_success = await get_prob_success(predictor_values,model_params)
        predicted_date = await get_predicted_date(predictor_values,model_params)
        if predictor_values['rating_updates_pre_30'] == 0 or predictor_values['rating_updates_30'] == 0 or predictor_values['rating_updates_180'] < 5:
            return(True,f"Warning: results may be unreliable due to limited {variant} data for user {username}.",
                    prob_success,predicted_date)
        return(False,None,prob_success,predicted_date)

# Check if discord inputs are valid, and if so return the predictions
async def process_inputs(name, rating, variant='Rapid',testing=False):
    # Check that rating is valid
    if not rating.isnumeric() or int(rating) < 500 or int(rating) > 3200:
        return(True,"Error: rating must be a positive integer between 500 and 3200.",None,None)
    # Check that variant is valid
    elif variant.title() in ['Bullet','Blitz','Rapid','Classical']:
        error_bool,error,prob_success,predicted_date = await score(username = name, target_rating = int(rating),
          variant = variant.capitalize(), model_params = model_params,testing=testing)
        return(error_bool,error,prob_success,predicted_date)
    else:
        return(True,"Error: variant not supported. Try bullet, blitz, rapid, or classical.",None,None)