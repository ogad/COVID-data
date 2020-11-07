# %%
import pandas as pd
from requests import get
from datetime import date
import seaborn as sns
from statistics import mean

# %% Function defs
def get_response(url):
    """Perform a http GET request at the given url, 
    returning the response json."""
    response = get(url, timeout=10)
    if response.status_code >= 400:
      raise RuntimeError(f'Request failed: { response.text }')
    return response.json()

def read_populations(file):
    df = pd.read_csv(file, header=1)
    df['Population'] = df['All ages']\
        .replace(',','',regex=True).fillna(0).astype(int)
    df.drop(columns='All ages', inplace=True)
    return df

def get_data(area_type, structure_items):
    dataframes = []
    p=0
    while True:
        p += 1
        endpoint = (
            'https://api.coronavirus.data.gov.uk/v1/data?'
            f'filters=areaType={area_type}&'
            f'structure={{"date": "date", "areaName":"areaName", "areaCode":"areaCode", {structure_items}}}&'
            f'page={p}'
        )
        try:
            response_json = get_response(endpoint)
        except:
            break
        dataframe = pd.DataFrame(response_json['data']).sort_values('date')\
            .reset_index(drop=True)
        dataframes.append(dataframe)
    df = pd.concat(dataframes)
    df['date'] = pd.to_datetime(df['date'])
    df['pop'] = [pop_dict[code] for code in df['areaCode']]
    return df

def add_per_mill(df, item):
    df[f'{item}PerMillion'] = df[item] / (df['pop']/10.0**6)
    return df

def calc_rolling_mean(df_la, win_size=7):
    if len(df_la.areaName.unique()) != 1:
        raise Exception('df needs to have only one area')
    return df_la.sort_values('date').rolling("7D", on='date').mean()

def get_la_rolling(df, la_code):
    df_la = df[df.areaCode == utla_code]
    df_la_rolling = calc_rolling_mean(df_la)
    df_utla_rolling['areaCode'] = la_code
    return df_la_rolling


# %% Get data
df_pops = read_populations('populationestimates2020.csv')
pop_dict = df_pops.set_index('Code').to_dict()['Population']

df = get_data("utla", '"newCases":"newCasesBySpecimenDate"')
df = add_per_mill(df,'newCases')

# %% Graphing
utlas = [
    'Cheshire West and Chester',
    'Leicester',
    'Northumberland',
    "Wirral",
    'North Yorkshire'
]
df_utlas = df[df.areaName.isin(utlas)]

codes = df_utlas['areaCode'].unique()
utla_rolling_dfs = [get_la_rolling(df_utlas, code) for code in codes]
df_utlas_rolling = pd.concat(utla_rolling_dfs)
df_utlas = df.merge(df_utlas_rolling, on=['date', 'areaCode'], suffixes=('','Rolling'))

sns.lineplot(x='date',y='newCasesPerMillionRolling', hue='areaName',data=df_utlas)
# %%
