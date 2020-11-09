# Coronavirus in the UK

## Visualisations and elementary analysis
The goal of this project is to make simple visualisations of the case, death and testing data for different regions of the UK, using the data from the [Coronavirus (COVID-19) in the UK](https://coronavirus.data.gov.uk/developers-guide) data and API, developed by Public Health England and NHSX. 
The population data is from the mid-year population estimates, `Mid 2019: April 2019 local authority district codes', which is made available by the ONS [here](https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland).
These files contain public sector information from these sources licensed under the Open Government Licence v3.0.
Mapping data contains OS data © Crown copyright and database right 2019.

## Example visualisations
These visualisations each use a 7-day rolling average to draw attention to the overall trend and reduce the effect of variations during the working week and noise.
These figures last updated on 04/10/2020.

### Cases by nation throughout the pandemic
![Case rate by nation in the UK](img/nation_cases.svg)

### Deaths by nation throughout the pandemic
![Death rate by nation in the UK](img/nation_deaths.svg)

### Hospital admissions by NHS region throughout the pandemic
![Admission rate by region in the UK](img/nhs_admissions.svg)

### Cases by the upper-tier local authority
![Case rate by nation in the UK](img/utla_cases.svg)

This displays cases in a small number of local authorities. Here the cases are by specimen date, which leads to a downtick for the most recent dates, due to reporting lag. In order to combat this effect the data from the most recent days has been omitted.

## Map of confirmed cases by the upper-tier local authority
![The cases per million at each upper-tier local authority (gif).](img/map_gif.gif)
This gif displays the most recent 250 days of COVID-19 data for local authorities in the UK.
Areas are grey where/when data is not available.

Images last updated 09-11-2020.
