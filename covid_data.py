# %% [markdown]
# # Coronavirus Data Analysis


# %% package imports

# Module to send http requests
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


# %% Defintition of the rolling average function
def rolling_average(values, over):
    """Perform a rolling average on the set of values, 
    returning a list of the same length as values."""
    result = []
    for i in range(over-1):
        result.append(None)
    for i in range(len(values)-over+1):
        result.append(stats.mean(values[i:i+over]))
    return result


# %% Function to get http response
def get_response(url):
    """Perform a http GET request at the given url, 
    returning the response json."""
    response = get(url, timeout=10)
    if response.status_code >= 400:
      raise RuntimeError(f'Request failed: { response.text }')
    return response.json()


# %% Function to join list of dfs on date
def join_on_date(dfs):
    """Joins a dictionary of dataframes, where the key is 
    used as the suffix when producting a larger dataframe 
    joining the two."""
    result = pd.DataFrame()
    for suffix, df in dfs.items():
        if result.empty:
            result = df.rename(columns={f"date{suffix.replace(' ','')}":'date'})
        else:
            result = result.merge(df, left_on='date', right_on=f"date{suffix.replace(' ','')}")
            result['date'].fillna(result[f"date{suffix.replace(' ','')}"], inplace=True)
            del result[f"date{suffix.replace(' ','')}"]
    result['date'] = result['date'].map(date.fromisoformat)
    return result

# %% A helper function to produce lists of column names for plotting
def get_column_names(feature, areas):
    return [feature + area.replace(' ','') for area in areas]

# %% Function to get the data
def get_data(area_type, areas, request_dict):
    request_structure = '{"date":"date"'
    for key, value in request_dict.items():
        request_structure += f',"{key}":"{value}"'
    request_structure += '}'

    obtained_dfs = {}
    for area in areas:
        i = 0
        while i < 5:
            try:
                endpoint = (
                    'https://api.coronavirus.data.gov.uk/v1/data?'
                    f'filters=areaType={area_type};areaName={area}&'
                    f'structure={request_structure}'
                )
                data = get_response(endpoint)
                obtained_dfs[area] = pd.DataFrame(data['data']).sort_values('date')\
                    .reset_index(drop=True).add_suffix(area.replace(' ',''))
                break
            except:
                i +=1
                print(f'failed {i} times for {area}')
                continue

    joined_data = join_on_date(obtained_dfs)
    return joined_data

# %% Read table of population estimates (ONS Apr 2020)
def read_populations(file):
    df = pd.read_csv(file, header=1)
    df['Population'] = df['All ages']\
        .replace(',','',regex=True).fillna(0).astype(int)
    df.drop(columns='All ages', inplace=True)
    return df
df_populations = read_populations('populationestimates2020.csv')

# %% Collect data for nations of the UK
# TODO: Collect data for each feature seperately
nations = ['England', 'Scotland', 'Wales', 'Northern Ireland']
def get_data_nations():
    nation_params = {
        "newCases":"newCasesByPublishDate", 
        "newDeaths":"newDeaths28DaysByPublishDate",
        "newTestsOne":"newPillarOneTestsByPublishDate",
        "newTestsTwo":"newPillarTwoTestsByPublishDate", 
        "newTestsThree":"newPillarThreeTestsByPublishDate",
        "newTestsFour":"newPillarFourTestsByPublishDate"
    }
    joined_data_nations = get_data("nation", nations, nation_params)
    for nation in nations:
        population = int(df_populations[df_populations['Name']==nation.upper()]['Population'])
        population_in_millions = population / 10**6
        new_cases = joined_data_nations[f"newCases{nation.replace(' ','')}"]
        new_cases_per_million = joined_data_nations[f"newCases{nation.replace(' ','')}"] / population_in_millions
        new_deaths_per_million = joined_data_nations[f"newDeaths{nation.replace(' ','')}"] / population_in_millions
        new_tests = joined_data_nations[f"newTestsOne{nation.replace(' ','')}"].astype(float)\
            .add(joined_data_nations[f"newTestsTwo{nation.replace(' ','')}"].astype(float), fill_value=0.0)\
            .add(joined_data_nations[f"newTestsThree{nation.replace(' ','')}"].astype(float), fill_value = 0.0)\
            .add(joined_data_nations[f"newTestsFour{nation.replace(' ','')}"].astype(float), fill_value = 0.0)\
            .add(joined_data_nations[f"newTestsThree{nation.replace(' ','')}"].astype(float), fill_value = 0.0)
        positivity_rate = new_cases.astype(float) / new_tests.astype(float)
        rolling_positivity = rolling_average(positivity_rate, 7)
        rolling_new_cases_per_million = rolling_average(new_cases_per_million,7)
        rolling_new_deaths_per_million = rolling_average(new_deaths_per_million,7)

        joined_data_nations[f"newCasesPerMillion{nation.replace(' ','')}"] = new_cases_per_million
        joined_data_nations[f"newDeathsPerMillion{nation.replace(' ','')}"] = new_deaths_per_million
        joined_data_nations[f"newCasesPerMillion7Day{nation.replace(' ','')}"] = rolling_new_cases_per_million
        joined_data_nations[f"newDeathsPerMillion7Day{nation.replace(' ','')}"] = rolling_new_deaths_per_million
        joined_data_nations[f"positivity7Day{nation.replace(' ','')}"] = rolling_positivity
    return joined_data_nations

if not use_backup:
    df_data_nations = get_data_nations()
else:
    df_data_nations = pd.read_csv('data_backup_nations.csv')
if make_backup:
    df_data_nations.to_csv('data_backup_nations.csv')
if num_days:
    df_data_nations = df_data_nations.iloc[-num_days:]

# %% Plotting for nations
nation_new_cases_columns = get_column_names("newCasesPerMillion7Day", nations)
nation_new_deaths_columns = get_column_names("newDeathsPerMillion7Day", nations)
nation_positivity_columns = get_column_names("positivity7Day", nations)

df_data_nations.plot('date', nation_new_cases_columns)
plt.legend(labels=nations)
plt.title('New Cases per Million Population (7 day rolling)')
plt.xticks(rotation=30, ha='right')
plt.xlabel('Date')
plt.tight_layout()
if save_figs:
    if num_days:
        plt.savefig(f'new_cases_nations_{num_days}_days.svg')
    else:
        plt.savefig(f'new_cases_nations.svg')

df_data_nations.plot('date', nation_new_deaths_columns)
plt.legend(labels=nations)
plt.title('New Deaths per Million Population (7 day rolling)')
plt.xticks(rotation=30, ha='right')
plt.xlabel('Date')
plt.tight_layout()
if save_figs:
    if num_days:
        plt.savefig(f'new_deaths_nations_{num_days}_days.svg')
    else:
        plt.savefig(f'new_deaths_nations.svg')

df_data_nations.plot('date', nation_positivity_columns)
plt.legend(labels=nations)
plt.title('Positivity rate (7 day rolling)')
plt.xticks(rotation=30, ha='right')
plt.ylim(-0.005,positivity_ylim)
plt.xlabel('Date')
plt.tight_layout()
if save_figs:
    if num_days:
        plt.savefig(f'positivity_nations_{num_days}_days.svg')
    else:
        plt.savefig(f'positivity_nations.svg')



# %% Read the list of upper tier local authorities, select which local authorities to use
df_utlas = pd.read_csv('utlas.csv', names=["Name"])
df_utla_populations = df_utlas.merge(df_populations, how='left', on="Name")
df_utla_populations.rename(columns = {"Geography1":"Geography"})

if not utlas:
    utlas = list(df_utlas['Name'])

# %% Get data for local authorities
def get_data_utlas():
    utla_params = {"newCases":"newCasesBySpecimenDate"}
    joined_data_utlas = get_data("utla", utlas, utla_params)

    # Remove the last 2 days to mitigate reporting delay using Specimen date
    joined_data_utlas.drop(index=[len(joined_data_utlas)-1, len(joined_data_utlas)-2], inplace=True)

    for utla in utlas:
        try:
            population = int(df_utla_populations[df_utla_populations['Name']==utla]['Population'])
            population_in_millions = population / 10**6
            new_cases_per_million = joined_data_utlas[f"newCases{utla.replace(' ','')}"]/population_in_millions
            rolling_new_cases_per_million = rolling_average(new_cases_per_million,7)
            joined_data_utlas[f"newCasesPerMillion{utla.replace(' ','')}"] = new_cases_per_million
            joined_data_utlas[f"newCasesPerMillion7Day{utla.replace(' ','')}"] = rolling_new_cases_per_million
        except:
            print(f'Failed processing {utla}, removing it.')
            utlas.remove(utla)

    joined_data_utlas = joined_data_utlas[:-2]

    if num_days:
        joined_data_utlas = joined_data_utlas.iloc[-num_days:]
    
    return joined_data_utlas

if not use_backup:
    joined_data_utlas = get_data_utlas()
else:
    joined_data_utlas = pd.read_csv('data_backup_utlas.csv')
if make_backup:
    joined_data_utlas.to_csv('data_backup_utlas.csv')
# %% Plotting for local authorities
if len(utlas) > 10:
    utla_sample = sample(utlas,5)
else:
    utla_sample = utlas

utlas_new_cases_columns = get_column_names("newCasesPerMillion7Day", utla_sample)


joined_data_utlas.plot('date', utlas_new_cases_columns)
plt.legend(labels=utla_sample)
plt.title('New Cases per Million Population (7 day rolling)')
plt.xticks(rotation=30, ha='right')
plt.xlabel('Date')
plt.tight_layout()
if save_figs:
    if num_days:
        plt.savefig(f'new_cases_utlas_{num_days}_days.svg')
    else:
        plt.savefig(f'new_cases_utlas.svg')
# %%
