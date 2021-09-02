import pandas as pd
from datetime import *
import statsmodels.formula.api as smf

df_bin = pd.read_csv("data/lichess_swiss_processed_sample.csv")
df_cont = df_bin[df_bin['y_bin']==1].copy()
df_bin_train = df_bin.sample(frac=.8,random_state=1)
df_bin_test = df_bin.loc[~df_bin.index.isin(df_bin_train.index)].copy()
df_cont_train = df_cont.sample(frac=.8,random_state=1)
df_cont_test = df_cont.iloc[~df_cont.index.isin(df_cont_train.index)].copy()
classification_formula = """
y_bin~target_rating_gain*rating_latest*bullet+target_rating_gain*rating_latest*blitz+
target_rating_gain*rating_latest*classical+
target_rating_gain_squared*rating_latest+
rating_peak_diff*target_rating_gain+rating_180_diff*bullet+rating_180_diff*blitz+
rating_updates_30+rating_updates_90*bullet+rating_updates_90*blitz+
rating_stdev_90
"""
logit = smf.logit(formula=classification_formula,data=df_bin_train).fit()
regression_formula = """
y_cont~
target_rating_gain*rating_latest*bullet+target_rating_gain*rating_latest*blitz+
target_rating_gain*rating_latest*classical+
target_rating_gain_squared*bullet+target_rating_gain_squared*blitz+
rating_latest_squared+rating_peak_diff*bullet+rating_peak_diff*blitz+
rating_peak_diff*target_rating_gain+
rating_180_diff*bullet+rating_180_diff*blitz+
rating_90_diff+rating_30_diff*bullet+rating_30_diff*classical+
rating_updates_30+rating_updates_90*blitz+rating_updates_90*classical+
rating_stdev_30
"""
ols = smf.ols(formula=regression_formula,data=df_cont_train).fit()
model_params=pd.concat([logit.params,ols.params],axis=1).reset_index()
model_params.columns = ['var_name','logit','ols']
model_params.to_csv(f"data/model_params_{datetime.today().strftime('%Y%m%d')}.csv",index=False)
