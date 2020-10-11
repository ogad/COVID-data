# %% Package imports
from requests import get

import matplotlib.pyplot as plt
plt.style.use('seaborn-notebook')
import pandas as pd
from random import sample
from datetime import date, timedelta
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

def per_million(value, population):
    return value / (int(population) / 10**6)

def get_population(area, pop_df):
    return pop_df[pop_df['Name'] == area].reset_index(drop=True).at[0,'Population']

def plot(areas, dfs, feature, title=None, ylim=None, file=None, drop=0):
    plt.figure(figsize=(7.5,5))
    for area in areas:
        plot_df = dfs[area].dropna(subset=[feature])
        plot_df = plot_df.drop(plot_df.tail(drop).index)
        if num_days:
            change_days = timedelta(days=num_days)
            plot_df = plot_df[plot_df['date'] >= date.today() - change_days]
        plt.plot(plot_df['date'], plot_df[feature], label=area)
    plt.legend()
    plt.xlabel('Date')
    if title:
        plt.title(title)
    plt.xticks(rotation=30, ha='right')
    if ylim:
        plt.ylim(-0.05*ylim,ylim)
    plt.tight_layout()
    if save_figs and file:
        plt.savefig(f'img/{file}.svg')


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
        "newTestsFour":"newPillarFourTestsByPublishDate",
        "newAdmissions": "newAdmissions"
    }
    for nation in nations:
        if not use_backup:
            df = get_data('nation', nation, nation_features)
            pop = get_population(nation, pop_df)
            df['newDeathsPerMillion'] = per_million(df['newDeaths'], pop)
            df['newDeathsPerMillion7Day'] = rolling_average(df['newDeathsPerMillion'],7)
            df['newCasesPerMillion'] = per_million(df['newCases'], pop)
            df['newCasesPerMillion7Day'] = rolling_average(df['newCasesPerMillion'],7)
            df['newAdmissionsPerMillion'] = per_million(df['newAdmissions'], pop)
            df['newAdmissionsPerMillion7Day'] = rolling_average(df['newAdmissionsPerMillion'].fillna(0),7)
            df['newTests'] = df['newTestsOne'].astype(float)\
                .add(df['newTestsTwo'].astype(float),fill_value = 0.0)\
                .add(df['newTestsThree'].astype(float), fill_value = 0.0)\
                .add(df['newTestsFour'].astype(float), fill_value = 0.0)
            df['newTests'].fillna(0, inplace=True)
            df['positivity'] = positivity_rate(df)
            df['positivity7Day'] = rolling_average(df['positivity'], 7)
            nation_dfs[nation] = df
        else:
            df = pd.read_csv(f'backups/{nation}.csv')
            df['date'] = df['date'].map(date.fromisoformat)
            nation_dfs[nation] = df
        if make_backup:
            df.to_csv(f'backups/{nation}.csv')
    return nation_dfs

# %% 
def get_data_utlas(utlas, pop_df):
    utla_dfs = {}
    utla_features = {
        "newCases":"newCasesBySpecimenDate"
    }
    for utla in utlas:
        if not use_backup:
            try:
                df = get_data('utla', utla, utla_features)
                pop = get_population(utla, pop_df)
                df['newCasesPerMillion'] = per_million(df['newCases'], pop)
                df['newCasesPerMillion7Day'] = rolling_average(df['newCasesPerMillion'],7)
                utla_dfs[utla] = df
            except:
                print(f"problem with {utla}")
                utla_dfs[utla] = None
        else:
            df = pd.read_csv(f'backups/{utla}.csv')
            df['date'] = df['date'].map(date.fromisoformat)
            utla_dfs[utla] = df
        if make_backup:
            df.to_csv(f'backups/{utla}.csv')
    return utla_dfs

# %%

nations = ['ENGLAND', 'SCOTLAND', 'WALES', 'NORTHERN IRELAND']
df_populations = read_populations('populationestimates2020.csv')
nation_dfs = get_data_nations(nations, df_populations)
plot(nations, nation_dfs, 'newDeathsPerMillion7Day', title="New Cases per Million (7 day rolling)", file='nation_deaths')
plot(nations, nation_dfs, 'newCasesPerMillion7Day', title="New Deaths per Million (7 day rolling)", file='nation_cases')
plot(nations, nation_dfs, 'positivity7Day', title="Positivity rate (7 day rolling)", ylim=0.1, file='nation_positivity')
plot(nations, nation_dfs, 'newAdmissionsPerMillion7Day', title="New admissions per Million (7 day rolling)", drop=2, file='nation_admissions')

# %%
utla_dfs = get_data_utlas(utlas, df_populations)
plot(utlas, utla_dfs, 'newCasesPerMillion7Day', title="New Cases per Million (7 day rolling)", drop=2, file='utla_cases')

# %%
import geopandas as gp 

def get_geo_data():
    gdf = gp.read_file('mapping')
    df_geo_utlas = get_data_utlas(gdf['ctyua19nm'], df_populations)
    return (gdf, df_geo_utlas)

def dict_to_col(key, dict):
    try:
        return dict[key].tolist()[0]
    except:
        return None

# %%

def map_date(gdf, df_geo_utlas, date_to_plot):
    newCasesDate = {}
    for utla in gdf['ctyua19nm']:
        if df_geo_utlas[utla] is not None:
            newCasesDate[utla] = df_geo_utlas[utla][df_geo_utlas[utla]['date'] == date.fromisoformat(date_to_plot)]['newCasesPerMillion7Day']
        else:
            newCasesDate[utla] = None

    gdf[f'newCases{date_to_plot}'] = gdf['ctyua19nm'].map(lambda x : dict_to_col(x, newCasesDate))

    fig, ax = plt.subplots(1, 1)
    gdf.plot(column=f'newCases{date_to_plot}', ax=ax, legend=True, cmap='Reds', edgecolor='black', missing_kwds={'color':'lightgrey'})
# %%
gdf, df_geo_utlas = get_geo_data()
# %%
map_date(gdf, df_geo_utlas, '2020-08-22')