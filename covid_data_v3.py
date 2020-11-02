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

dataframes = []
for p in range(1,22):
    endpoint = (
        'https://api.coronavirus.data.gov.uk/v1/data?'
        'filters=areaType=utla&'
        'structure={"date": "date", "areaName":"areaName", "newCases":"newCasesBySpecimenDate"}&'
        f'page={p}'
    )
    response_json = get_response(endpoint)
    dataframe = pd.DataFrame(response_json['data']).sort_values('date')\
        .reset_index(drop=True)
    dataframes.append(dataframe)
df = pd.concat(dataframes)
# %%
df = df.pivot(columns='areaName',index='date',values='newCases')
# %%
