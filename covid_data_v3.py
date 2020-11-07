# %%
import pandas as pd
from requests import get
from datetime import date
import seaborn as sns
from statistics import mean

# %%
def get_response(url):
    """Perform a http GET request at the given url, 
    returning the response json."""
    response = get(url, timeout=10)
    if response.status_code >= 400:
      raise RuntimeError(f'Request failed: { response.text }')
    return response.json()

def get_data(area_type, area, request_dict):
    request_structure = '{"date":"date"'
    for key, value in request_dict.items():
        request_structure += f',"{key}":"{value}"'
    request_structure += '}'
    i = 0
    dataframe = None
    while i < 5:
        try:
            endpoint = (
                'https://api.coronavirus.data.gov.uk/v1/data?'
                f'filters=areaType={area_type};areaName={area}&'
                f'structure={request_structure}'
            )
            response_json = get_response(endpoint)
            dataframe = pd.DataFrame(response_json['data']).sort_values('date')\
                .reset_index(drop=True)
            break
        except:
            i +=1
            print(f'failed {i} times for {area}')
            if i < 5:
                continue
            else:
                print("moving on...")
                raise Exception("Something isn't working obtaining the data!")
    dataframe['date'] = dataframe['date'].map(date.fromisoformat)
    return dataframe

def read_populations(file):
    df = pd.read_csv(file, header=1)
    df['Population'] = df['All ages']\
        .replace(',','',regex=True).fillna(0).astype(int)
    df.drop(columns='All ages', inplace=True)
    return df

# %%
df_pops = read_populations('populationestimates2020.csv')
pop_dict = df_pops.set_index('Code').to_dict()['Population']

# %%

dataframes = []
p=0
while True:
    p += 1
    endpoint = (
        'https://api.coronavirus.data.gov.uk/v1/data?'
        'filters=areaType=utla&'
        'structure={"date": "date", "areaName":"areaName", "areaCode":"areaCode", "newCases":"newCasesBySpecimenDate"}&'
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

# %%
df['date'] = pd.to_datetime(df['date'])
df['pop'] = [pop_dict[code] for code in df['areaCode']]
df['newCasesPerMillion'] = df['newCases'] / (df['pop']/10.0**6)
# %%
utlas = [
    'Cheshire West and Chester',
    'Leicester',
    'Northumberland',
    'North Yorkshire'
]
df_utlas = df[df.areaName.isin(utlas)]

def calc_rolling_mean(df, win_size=7):
    if len(df.areaName.unique()) != 1:
        raise Exception('df needs to have only one area type')
    return df.sort_values('date').rolling(win_size, on='date').mean()

def get_la_rolling(df, utla_code):
    df_la = df[df.areaCode == utla_code]
    return calc_rolling_mean(df_la)

codes = df_utlas['areaCode'].unique()
utla_rolling_dfs = []
for code in codes:
    df_utla_rolling = get_la_rolling(df_utlas, code)
    df_utla_rolling['areaCode'] = code
    utla_rolling_dfs.append(df_utla_rolling)
df_utlas_rolling = pd.concat(utla_rolling_dfs)
df_utlas = df.merge(df_utlas_rolling, on=['date', 'areaCode'], suffixes=('','Rolling'))

sns.lineplot(x='date',y='newCasesPerMillionRolling', hue='areaName',data=df_utlas)
# %%
