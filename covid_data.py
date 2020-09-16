# %% [markdown]
# # Coronavirus Data Analysis

# %%

# Module to send http requests
from requests import get

import matplotlib.pyplot as plt
import pandas as pd
from random import sample
from datetime import date
import statistics as stats


# %%
# Read table of population estimates (ONS Apr 2020)
df_populations = pd.read_csv('populationestimates2020.csv', header=1)
df_populations['Population'] = df_populations['All ages'].replace(',','',regex=True).fillna(0).astype(int)
df_populations.drop(columns='All ages', inplace=True)

# Read the list of upper tier local authorities and make a dataframe of their populations
df_utlas = pd.read_csv('utlas.csv', names=["Name"])
df_utla_populations = df_utlas.merge(df_populations, how='left', on="Name")
df_utla_populations.rename(columns = {"Geography1":"Geography"})


# %%
def rolling_average(values, over):
    """Perform a rolling average on the set of values, returning a list of the same length as values."""
    result = []
    for i in range(over-1):
        result.append(None)
    for i in range(len(values)-over+1):
        result.append(stats.mean(values[i:i+over]))
    return result


# %%
def get_response(url):
    """Perform a http GET request at the given url, returning the response json."""
    response = get(endpoint, timeout=10)
    if response.status_code >= 400:
      raise RuntimeError(f'Request failed: { response.text }')
    return response.json()


# %%
def join_on_date(dfs):
    """Joins a dictionary of dataframes, where the key is used as the suffix when producting a larger dataframe joining the two."""
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


# %%
nations = ['England', 'Scotland', 'Wales', 'Northern Ireland']

nation_dfs = {}
for nation in nations:
    print(f'processing {nation}')
    endpoint = (
      'https://api.coronavirus.data.gov.uk/v1/data?'
      f'filters=areaType=nation;areaName={nation}&'
      'structure={"date":"date","newCases":"newCasesByPublishDate", "newDeaths":"newDeaths28DaysByPublishDate", "newTestsOne":"newPillarOneTestsByPublishDate","newTestsTwo":"newPillarTwoTestsByPublishDate","newTestsThree":"newPillarThreeTestsByPublishDate","newTestsFour":"newPillarFourTestsByPublishDate"}'
    )
    data = get_response(endpoint)
    nation_dfs[nation] = pd.DataFrame(data['data'])                                .sort_values('date')                                .reset_index(drop=True)                                .add_suffix(nation.replace(' ',''))


# %%
joined_data_nations = join_on_date(nation_dfs)
joined_data_nations.head()


# %%
# joined_data_nations.to_csv('data_backup_nations.csv')


# %%
for nation in nations:
    population_in_millions = int(df_populations[df_populations['Name']==nation.upper()]['Population']) / 10**6
    new_cases = joined_data_nations[f"newCases{nation.replace(' ','')}"]
    new_cases_per_million = joined_data_nations[f"newCases{nation.replace(' ','')}"] / population_in_millions
    new_deaths_per_million = joined_data_nations[f"newDeaths{nation.replace(' ','')}"] / population_in_millions
    new_tests = joined_data_nations[f"newTestsOne{nation.replace(' ','')}"].astype(float)        .add(joined_data_nations[f"newTestsTwo{nation.replace(' ','')}"].astype(float), fill_value=0.0)        .add(joined_data_nations[f"newTestsThree{nation.replace(' ','')}"].astype(float), fill_value = 0.0)        .add(joined_data_nations[f"newTestsFour{nation.replace(' ','')}"].astype(float), fill_value = 0.0)        .add(joined_data_nations[f"newTestsThree{nation.replace(' ','')}"].astype(float), fill_value = 0.0)
    positivity_rate = new_cases.astype(float) / new_tests.astype(float)
    rolling_positivity = rolling_average(positivity_rate, 7)
    rolling_new_cases_per_million = rolling_average(new_cases_per_million,7)
    rolling_new_deaths_per_million = rolling_average(new_deaths_per_million,7)
    
    joined_data_nations[f"newCasesPerMillion{nation.replace(' ','')}"] = new_cases_per_million
    joined_data_nations[f"newDeathsPerMillion{nation.replace(' ','')}"] = new_deaths_per_million
    joined_data_nations[f"newCasesPerMillion7Day{nation.replace(' ','')}"] = rolling_new_cases_per_million
    joined_data_nations[f"newDeathsPerMillion7Day{nation.replace(' ','')}"] = rolling_new_deaths_per_million
    joined_data_nations[f"positivity7Day{nation.replace(' ','')}"] = rolling_positivity

nation_new_cases_columns = [f"newCasesPerMillion7Day{nation.replace(' ','')}" for nation in nations]
nation_new_deaths_columns =  [f"newDeathsPerMillion7Day{nation.replace(' ','')}" for nation in nations]
nation_positivity_columns =  [f"positivity7Day{nation.replace(' ','')}" for nation in nations]



joined_data_nations.plot('date', nation_new_cases_columns)
plt.legend(labels=nations)
plt.title('New Cases per Million Population (7 day rolling)')
plt.xticks(rotation=30, ha='right')

joined_data_nations.plot('date', nation_new_deaths_columns)
plt.legend(labels=nations)
plt.title('New Deaths per Million Population (7 day rolling)')
plt.xticks(rotation=30, ha='right')

joined_data_nations|.plot('date', nation_positivity_columns)
plt.legend(labels=nations)
plt.title('Positivity rate (7 day rolling)')
plt.xticks(rotation=30, ha='right')


# %%
# To plot different Upper tier local authorities, simply add their name to this list.
utlas = ['Cheshire West and Chester','Leicester','Northumberland','North Yorkshire', 'Wirral', 'Oxfordshire', 'Cumbria']
# utlas = ['Bolton', 'Bradford', 'Blackburn with Darwen']
# utlas = list(df_utlas['Name'])


utla_dfs = {}
for utla in utlas:
    try:
        print(f'processing {utla}')
        endpoint = (
          'https://api.coronavirus.data.gov.uk/v1/data?'
          f'filters=areaType=utla;areaName={utla}&'
          'structure={"date":"date","newCases":"newCasesBySpecimenDate"}'
        )
        data = get_response(endpoint)
        utla_dfs[utla] = pd.DataFrame(data['data'])                                    .sort_values('date')                                    .reset_index(drop=True)                                    .add_suffix(utla.replace(' ',''))
    except:
        utlas.remove(utla)
        print("Failed, moving on.")


# %%
joined_data_utlas = join_on_date(utla_dfs)
# Remove the last 2 days to mitigate reporting delay using Specimen date
joined_data_utlas.drop(index=[len(joined_data_utlas)-1, len(joined_data_utlas)-2], inplace=True)


# %%
# joined_data_utlas.to_csv('data_backup_utlas.csv')


# %%
for utla in utlas:
    try:
        population_in_millions = int(df_utla_populations[df_utla_populations['Name']==utla]['Population']) / 10**6
        new_cases_per_million = joined_data_utlas[f"newCases{utla.replace(' ','')}"]/population_in_millions
        rolling_new_cases_per_million = rolling_average(new_cases_per_million,7)
        joined_data_utlas[f"newCasesPerMillion{utla.replace(' ','')}"] = new_cases_per_million
        joined_data_utlas[f"newCasesPerMillion7Day{utla.replace(' ','')}"] = rolling_new_cases_per_million
    except:
        print(f'Failed processing {utla}, removing it.')
        utlas.remove(utla)


# %%
# utlas_new_cases_columns = [f"newCasesPerMillion7Day{utla.replace(' ','')}" for utla in utlas]
utla_sample = sample(utlas,5)
utlas_new_cases_columns = [f"newCasesPerMillion7Day{utla.replace(' ','')}" for utla in utla_sample]

joined_data_utlas.plot('date', utlas_new_cases_columns)
plt.legend(labels=utla_sample)
plt.title('New Cases per Million Population (7 day rolling)')
plt.xticks(rotation=30, ha='right')


# %%



