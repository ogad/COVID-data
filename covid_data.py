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

# %% Function to get the data
def get_data(area_type, areas, request_dict):
    request_structure = '{"date":"date"'
    for key, value in request_dict.items():
        request_structure += f',"{key}":"{value}"'
    request_structure += '}'

    obtained_dfs = {}
    for area in areas:
        while True:
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
                continue

    joined_data = join_on_date(obtained_dfs)
    return joined_data




# %% Read table of population estimates (ONS Apr 2020)
df_populations = pd.read_csv('populationestimates2020.csv', header=1)
df_populations['Population'] = df_populations['All ages']\
    .replace(',','',regex=True).fillna(0).astype(int)
df_populations.drop(columns='All ages', inplace=True)


# %% Collect data for nations of the UK
nations = ['England', 'Scotland', 'Wales', 'Northern Ireland']

nation_params = {
    "newCases":"newCasesByPublishDate", 
    "newDeaths":"newDeaths28DaysByPublishDate",
    "newTestsOne":"newPillarOneTestsByPublishDate",
    "newTestsTwo":"newPillarTwoTestsByPublishDate", 
    "newTestsThree":"newPillarThreeTestsByPublishDate",
    "newTestsFour":"newPillarFourTestsByPublishDate"
}
joined_data_nations = get_data("nation", nations, nation_params)

# Uncomment to backup:
# joined_data_nations.to_csv('data_backup_nations.csv')


# %% Calculate derived quantities for nations
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

# %% Plotting for nations
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

joined_data_nations.plot('date', nation_positivity_columns)
plt.legend(labels=nations)
plt.title('Positivity rate (7 day rolling)')
plt.xticks(rotation=30, ha='right')



# %% Read the list of upper tier local authorities, select which local authorities to use
df_utlas = pd.read_csv('utlas.csv', names=["Name"])
df_utla_populations = df_utlas.merge(df_populations, how='left', on="Name")
df_utla_populations.rename(columns = {"Geography1":"Geography"})

# To plot different Upper tier local authorities, simply add their name to this list.
utlas = [
    'Cheshire West and Chester',
    'Leicester',
    'Northumberland',
    'North Yorkshire',
    'Wirral', 
    'Oxfordshire',
    'Cumbria']
# utlas = list(df_utlas['Name'])

# %% Get data for local authorities

utla_params = {
    "newCases":"newCasesBySpecimenDate"
}
joined_data_utlas = get_data("utla", utlas, utla_params)

# Remove the last 2 days to mitigate reporting delay using Specimen date
joined_data_utlas.drop(index=[len(joined_data_utlas)-1, len(joined_data_utlas)-2], inplace=True)

# joined_data_utlas.to_csv('data_backup_utlas.csv')


# %% Calculate derived quantities for local authorities
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


# %% Plotting for local authorities
if len(utlas) > 10:
    utla_sample = sample(utlas,5)
else:
    utla_sample = utlas

utlas_new_cases_columns = [f"newCasesPerMillion7Day{utla.replace(' ','')}" for utla in utla_sample]

joined_data_utlas.plot('date', utlas_new_cases_columns)
plt.legend(labels=utla_sample)
plt.title('New Cases per Million Population (7 day rolling)')
plt.xticks(rotation=30, ha='right')
plt.show()
