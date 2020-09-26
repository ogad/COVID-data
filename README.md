# Coronavirus in the UK
## Visualisations and elementary analysis
The goal of this project is to make simple visualisations of the case, death and testing data for different regions of the UK, using the data from the Coronavirus (COVID-19) in the UK data and API, developed by Public Health England and NHSX. These files contain public sector information licensed under the Open Government Licence v3.0.
## Example visualisations
These visualisations each use a 7-day rolling average to draw attention to the overall trend and reduce the effect of variations during the working week and noise.
## Cases by nation throughout the pandemic
![Case rate by nation in the UK](new_cases_nations.svg)
## Deaths by nation throughout the pandemic
![Death rate by nation in the UK](new_deaths_nations.svg)
## Positivity rate by nation throughout the pandemic
![Positivity rate by nation in the UK](positivity_nations.svg)
The y-axis is limited here to a maximum of 0.1, to better visualise the more recent data. This is needed due to a large spike during the first wave of cases, when test availability was more severely limited.
## Cases by the upper-tier local authority
![Case rate by nation in the UK](new_cases_utlas.svg)
This displays cases in a small number of local authorities. Here the cases are by specimen date, which leads to a downtick for the most recent dates, due to reporting lag. In order to combat this effect the data from the most recent days has been omitted.
