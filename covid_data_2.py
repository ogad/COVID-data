# %% Package imports
from requests import get

import matplotlib.pyplot as plt
plt.style.use('seaborn-notebook')
import pandas as pd
from random import sample
from datetime import date
import statistics as stats

# %% Settings
make_backup = False # True or false
use_backup = False # True or false
save_figs = False
num_days = False # False, or number of days to plot
positivity_ylim = 0.1
# To plot different Upper tier local authorities, simply add their name to this list.
# If more than 10, will plot a random sample of 5 of these.
# If False, will take a random sample of all the UTLAs; will retrieve data from all UTLAs
utlas = [
    'Cheshire West and Chester',
    'Leicester',
    'Northumberland',
    'North Yorkshire',
    'Wirral', 
    'Oxfordshire',
    'Cumbria'
]

# %% Function definitions
def rolling_average(values, over):
    """Perform a rolling average on the set of values, 
    returning a list of the same length as values."""
    result = []
    for i in range(over-1):
        result.append(None)
    for i in range(len(values)-over+1):
        result.append(stats.mean(values[i:i+over]))
    return result

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
                break
    dataframe['date'] = dataframe['date'].map(date.fromisoformat)
    return dataframe

def read_populations(file):
    df = pd.read_csv(file, header=1)
    df['Population'] = df['All ages']\
        .replace(',','',regex=True).fillna(0).astype(int)
    df.drop(columns='All ages', inplace=True)
    return df

def per_million(value, population):
    return value / (int(population) / 10**6)

def get_population(area, pop_df):
    return pop_df[pop_df['Name'] == area].reset_index(drop=True).at[0,'Population']

def plot(areas, dfs, feature, title=None):
    plt.figure()
    for area in areas:
        plot_df = dfs[area].dropna(subset=[feature])
        plt.plot(plot_df['date'], plot_df[feature], label=area)
    plt.legend()
    plt.xlabel('Date')
    if title:
        plt.title(title)

def positivity_rate(df):
    return df['newCases'].astype(float) / df['newTests'].astype(float)


# %% 
def get_data_nations(nations, pop_df):
    nation_dfs = {}
    nation_features = {
        "newCases":"newCasesByPublishDate", 
        "newDeaths":"newDeaths28DaysByPublishDate",
        "newTestsOne":"newPillarOneTestsByPublishDate",
        "newTestsTwo":"newPillarTwoTestsByPublishDate",
        "newTestsThree": "newPillarThreeTestsByPublishDate",
        "newTestsFour":"newPillarFourTestsByPublishDate"
    }
    for nation in nations:
        df = get_data('nation', nation, nation_features)
        pop = get_population(nation, pop_df)
        df['newDeathsPerMillion'] = per_million(df['newDeaths'], pop)
        df['newDeathsPerMillion7Day'] = rolling_average(df['newDeathsPerMillion'],7)
        df['newCasesPerMillion'] = per_million(df['newCases'], pop)
        df['newCasesPerMillion7Day'] = rolling_average(df['newCasesPerMillion'],7)
        df['newTests'] = df['newTestsOne'].astype(float)\
            .add(df['newTestsTwo'].astype(float),fill_value = 0.0)\
            .add(df['newTestsThree'].astype(float), fill_value = 0.0)\
            .add(df['newTestsFour'].astype(float), fill_value = 0.0)
        df['newTests'].fillna(0, inplace=True)
        df['positivity'] = positivity_rate(df)
        df['positivity7Day'] = rolling_average(df['positivity'], 7)
        nation_dfs[nation] = df
        print(nation)
        print(df['newTests'].tail())
    return nation_dfs

# %%

nations = ['ENGLAND', 'SCOTLAND', 'WALES', 'NORTHERN IRELAND']
df_populations = read_populations('populationestimates2020.csv')
nation_dfs = get_data_nations(nations, df_populations)
plot(nations, nation_dfs, 'newDeathsPerMillion7Day', title="New Cases per Million (7 day rolling)")
plot(nations, nation_dfs, 'newCasesPerMillion7Day', title="New Deaths per Million (7 day rolling)")
plot(nations, nation_dfs, 'positivity7Day', title="Positivity rate (7 day rolling)")


# %%
