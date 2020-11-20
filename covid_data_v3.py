# %%
import pandas as pd
from requests import get
from datetime import date, timedelta
import seaborn as sns
from statistics import mean
import matplotlib.pyplot as plt
import geopandas as gpd
import imageio

# %% Function defs
def get_response(url):
    """Perform a http GET request at the given url, 
    returning the response json."""
    response = get(url, timeout=10)
    if response.status_code >= 400:
      raise RuntimeError(f'Request failed: { response.text }')
    return response.json()

def read_populations(file):
    """Read populations into a """
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
    try:
        df['pop'] = [pop_dict[code] for code in df['areaCode']]
    except:
        pass
    return df

def add_per_mill(df, item):
    df[f'{item}PerMillion'] = df[item] / (df['pop']/10.0**6)
    return df

def calc_rolling_mean(df_la, win_size=7):
    if len(df_la.areaName.unique()) != 1:
        raise Exception('df needs to have only one area')
    return df_la.sort_values('date').rolling("7D", on='date').mean()

def get_la_rolling(df, la_code):
    df_la = df[df.areaCode == la_code]
    df_la_rolling = calc_rolling_mean(df_la)
    df_la_rolling['areaCode'] = la_code
    return df_la_rolling

def make_rolling(df):
    codes = df['areaCode'].unique()
    rolling_dfs = [get_la_rolling(df, code) for code in codes]
    df_rolling = pd.concat(rolling_dfs)
    df = df.merge(df_rolling, on=['date', 'areaCode', 'pop'], suffixes=('','Rolling'))
    return df


# %% Get data
df_pops = read_populations('populationestimates2020.csv')
pop_dict = df_pops.set_index('Code').to_dict()['Population']

# %% Graphing
df = get_data("utla", '"newCases":"newCasesBySpecimenDate"')
df = add_per_mill(df,'newCases')
df = make_rolling(df)
utlas = [
    'Cheshire West and Chester',
    'Leicester',
    'Northumberland',
    "Wirral",
    'North Yorkshire'
]
df_utlas = df[df.areaName.isin(utlas)]

sns.lineplot(x='date',y='newCasesPerMillionRolling', hue='areaName',data=df_utlas)
plt.xticks(rotation=30, ha='right')
plt.title('New cases per million people by UTLA (7 day rolling)')
plt.ylabel("New cases per million population")
plt.xlabel("Date")
plt.legend(title = "Upper-tier local authority")
plt.tight_layout()
plt.savefig("img/utla_cases.svg")
# %%
df = get_data("nation", '"newCases":"newCasesByPublishDate", "newDeaths":"newDeaths28DaysByPublishDate"')
df = add_per_mill(df,'newCases')
df = add_per_mill(df,'newDeaths')
nations = list(df.areaName.unique())
df = make_rolling(df)
plt.figure()
sns.lineplot(x='date',y='newCasesPerMillionRolling', hue='areaName', data=df)
plt.xticks(rotation=30, ha='right')
plt.title('New cases per million people by Nation (7 day rolling)')
plt.ylabel("New cases per million population")
plt.xlabel("Date")
plt.legend(title = "Nation")
plt.tight_layout()
plt.savefig("img/nation_cases.svg")

plt.figure()
sns.lineplot(x='date',y='newDeathsPerMillionRolling', hue='areaName', data=df)
plt.xticks(rotation=30, ha='right')
plt.title('New deaths per million people by Nation (7 day rolling)')
plt.ylabel("New deaths per million population")
plt.xlabel("Date")
plt.legend(title = "Nation")
plt.tight_layout()
plt.savefig("img/nation_deaths.svg")

# %%
df = get_data("nhsRegion", '"newAdmissions":"newAdmissions"')
df = add_per_mill(df,'newAdmissions')
df = make_rolling(df)
plt.figure()
sns.lineplot(x='date',y='newAdmissionsPerMillionRolling', hue='areaName', data=df)
plt.xticks(rotation=30, ha='right')
plt.title('New admissions per million people by NHS region (7 day rolling)')
plt.ylabel("New admissions per million population")
plt.xlabel("Date")
plt.legend(title = "NHS region")
plt.tight_layout()
plt.savefig("img/nhs_admissions.svg")

# %%
# def get_geo_data():
#     gdf = gpd.read_file('mapping')
#     # gdf.replace({'City of Edinburgh':'Edinburgh (City of)','Na h-Eileanan Siar':'Comhairle nan Eilean Siar'}, inplace=True)
#     return gdf

def dict_to_col(key, dict):
    try:
        return dict[key].tolist()[0]
    except:
        return None

def map_date(gdf, df, area_type, date_to_plot, ax, range=None, feature='Cases'):
    code_column = {
        'utla': 'ctyua19cd',
        'nhsRegion': 'nhser20cd'
    }
    newFeatureDate = {}
    for code in gdf[code_column[area_type]]:
        if df[df['areaCode'] == code] is not None:
            df_utla = df[df['areaCode']==code]
            df_utla = df_utla[df_utla['date'] == pd.Timestamp(date_to_plot)]
            newFeatureDate[code] = df_utla[f'new{feature}PerMillionRolling']
        else:
            newFeatureDate[code] = None
    gdf[f'new{feature}{date_to_plot}'] = gdf[code_column[area_type]].map(lambda x : dict_to_col(x, newFeatureDate))
    if range is None:
        gdf.plot(column=f'new{feature}{date_to_plot}', ax=ax,legend=True, cmap='YlOrRd', edgecolor='black', lw=.3, missing_kwds={'color':'lightgrey'})
    else:
        gdf.plot(column=f'new{feature}{date_to_plot}', ax=ax, legend=True, cmap='YlOrRd', edgecolor='black', lw=.3, missing_kwds={'color':'lightgrey'}, vmin=range[0], vmax=range[1])
    ax.axis('off')
    ax.set_title(f"{feature} per million - {date_to_plot}")
    return ax

# %%
def make_gif(shapefile, area_type, metric, num_days, remove_days=2, make_images=False):
    structure_dict = {
        'newCases' : '"newCases":"newCasesBySpecimenDate"',
        'newAdmissions': '"newAdmissions": "newAdmissions"'
    }
    feature_dict = {
        'newCases' : 'Cases',
        'newAdmissions': 'Admissions'
    }
    gdf = gpd.read_file(shapefile)
    df = get_data(area_type, structure_dict[metric])
    df = add_per_mill(df,metric)
    df = make_rolling(df)
    dates = [date.today() - timedelta(remove_days + num_days - x) for x in range(num_days)]
    max_val = df[f'{metric}PerMillionRolling'].max()


    images = []
    for day in dates:
        date_str = day.strftime('%Y-%m-%d')
        filename = f'img/maps/{date_str}_{area_type}_{metric}_{max_val}.png'
        if make_images:
            fig, ax = plt.subplots(figsize=(4,6))
            map_date(gdf, df, area_type, date_str, ax, range=(0,max_val), feature=feature_dict[metric])
            fig.savefig(filename, dpi=300)
            plt.close()
            images.append(imageio.imread(filename))
        else:
            try:
                images.append(imageio.imread(filename))
            except:
                fig, ax = plt.subplots(figsize=(4,6))
                map_date(gdf, df, area_type, date_str, ax, range=(0,max_val), feature=feature_dict[metric])
                fig.savefig(filename, dpi=300)
                plt.close()
                images.append(imageio.imread(filename))

    for _ in range(20):
        images.append(images[-1])

    imageio.mimsave(f'img/map_gif_{area_type}_{metric}.gif', images)

if __name__ == "__main__":
    make_gif('mapping','utla','newCases', 250)
    make_gif('mapping_nhs','nhsRegion','newAdmissions', 200)

# %%
