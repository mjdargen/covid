import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import filecmp
import shutil
import datetime

base_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/'
files = ['time_series_covid19_confirmed_US.csv', 'time_series_covid19_confirmed_global.csv',
         'time_series_covid19_deaths_US.csv', 'time_series_covid19_deaths_global.csv']
DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def make_dirs():
    if not os.path.exists(f'{DIR_PATH}/input'):
        os.makedirs(f'{DIR_PATH}/input')

    if not os.path.exists(f'{DIR_PATH}/output'):
        os.makedirs(f'{DIR_PATH}/output')


def check_updates():
    # request and download txt
    r = requests.get(base_url + files[0])
    content = r.content.decode('utf-8')

    # requests downloads the content, create a new file to store the data
    with open(f"{DIR_PATH}/new.csv", "w") as f:
        f.write(content)

    # see if files match
    try:
        filecmp.cmp(f"{DIR_PATH}/old.csv", f"{DIR_PATH}/new.csv")
    except IOError:
        # old file doesn't exist yet, create empty file
        f = open(f"{DIR_PATH}/old.csv", "w")
        f.close()

    # files match, no new forms submitted
    if filecmp.cmp(f"{DIR_PATH}/old.csv", f"{DIR_PATH}/new.csv"):
        print("No updates. Exiting...")
        return False
    # files don't match, so process new data
    else:
        print("Updates! Proceeding... ")
        with open(f"{DIR_PATH}/new.csv", "r") as f:
            contents = f.read()
        with open(f"{DIR_PATH}/old.csv", "w") as f:
            f.write(contents)
        return True


def download_files():
    # request and download txt
    for file in files:
        r = requests.get(base_url + file)
        content = r.content.decode('utf-8')
        with open(f"{DIR_PATH}/input/{file}", "w") as f:
            f.write(content)


def confirmed_county(state, county):
    # read in file
    cvDF = pd.read_csv(f'{DIR_PATH}/input/{files[0]}', encoding='utf-8')

    # remove columns we don't care about
    cvDF = cvDF.drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Combined_Key',
                      'Lat', 'Long_', 'Country_Region'], axis=1)

    # filter by state
    cvDF = cvDF.loc[cvDF['Province_State'] == state]

    # filter by county
    cvDF = cvDF.loc[cvDF['Admin2'] == county]

    # drop everything but dates and cases
    cvDF = cvDF.drop(['Admin2', 'Province_State'], axis=1)

    # now that everything is dropped, we can transpose
    # we will now have 2 columns:
    # the 1st column is the index containing the date
    # the 2nd column contains the total number of confirmed cases
    cvDF = cvDF.transpose()

    # name the unnamed column
    # cvDF.columns allows us to rename all columns using a list of strings.
    # there is technically only one column since date is an index
    cvDF.columns = ['confirmed']

    # convert date to a special pandas "datetime" value so it recognizes it
    cvDF.index = pd.to_datetime(cvDF.index, format='%m/%d/%y')

    # plot the total number of confirmed cases
    fig = px.line(x=cvDF.index, y=cvDF['confirmed'])
    fig.update_layout(title=f"Number of Confirmed COVID-19 Cases in {county} County",
                      xaxis_title="Date",
                      yaxis_title="Confirmed COVID-19 Cases")
    fig.show()
    fig.write_html(f'{DIR_PATH}/output/confirmed_{county}.html')


def new_county(state, county):
    # read in file
    cvDF = pd.read_csv(f'{DIR_PATH}/input/{files[0]}', encoding='utf-8')

    # remove columns we don't care about
    cvDF = cvDF.drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Combined_Key',
                      'Lat', 'Long_', 'Country_Region'], axis=1)

    # filter by state
    cvDF = cvDF.loc[cvDF['Province_State'] == state]

    # filter by county
    cvDF = cvDF.loc[cvDF['Admin2'] == county]

    # drop everything but dates and cases
    cvDF = cvDF.drop(['Admin2', 'Province_State'], axis=1)

    # now that everything is dropped, we can transpose
    # we will now have 2 columns:
    # the 1st column is the index containing the date
    # the 2nd column contains the total number of new cases
    cvDF = cvDF.transpose()

    # name the unnamed column
    # cvDF.columns allows us to rename all columns using a list of strings.
    # there is technically only one column since date is an index
    cvDF.columns = ['confirmed']

    # create new column for the number of new cases
    cvDF['new'] = 0

    # loop to compute number of new cases each day
    prev = 0  # previous day's num of confirmed cases
    # iterate through every row (rows correspond to days)
    for index, row in cvDF.iterrows():
        # to get the number of new cases that day
        # subtract yesterday's confirmed cases from today's confirmed cases
        cvDF.loc[index, 'new'] = cvDF.loc[index, 'confirmed'] - prev
        # store this index's num of cases for use next time through
        prev = cvDF.loc[index, 'confirmed']

    # convert date to a special pandas "datetime" value so it recognizes it
    cvDF.index = pd.to_datetime(cvDF.index, format='%m/%d/%y')

    # convert to list to fill in zeros with averages of next day's data
    new = cvDF['new'].tolist()
    for idx, val in enumerate(new):
        if val == 0:
            for length, zero in enumerate(new[idx+1:]):
                if zero != 0:
                    break
            length += 1
            if idx+length >= len(new) and new[-1] == 0:
                break
            mean = new[idx+length] // (length+1)
            new[idx+length] = new[idx+length] - mean * (length)
            for i in range(length):
                new[idx+i] = mean
    cvDF = cvDF.assign(new=new)

    # plot the total number of confirmed cases
    fig = px.line(x=cvDF.index, y=cvDF['new'])
    fig.update_layout(title=f"Number of New COVID-19 Cases in {county} County",
                      xaxis_title="Date",
                      yaxis_title="New COVID-19 Cases")
    fig.show()
    fig.write_html(f'{DIR_PATH}/output/new_{county}.html')


def confirmed_state(state):
    # read in file
    cvDF = pd.read_csv(f'{DIR_PATH}/input/{files[0]}', encoding='utf-8')

    # remove columns we don't care about
    cvDF = cvDF.drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Combined_Key',
                      'Lat', 'Long_', 'Country_Region', 'Admin2'], axis=1)

    # filter by state
    cvDF = cvDF.loc[cvDF['Province_State'] == state]

    # group all entries (counties) in a state together
    # sum all other columns
    # when you group by state, it automatically makes state the index
    cvDF = cvDF.groupby(['Province_State']).sum()

    # now that everything is dropped, we can transpose
    # we will now have 2 columns:
    # the 1st column is the index containing the date
    # the 2nd column contains the total number of confirmed cases
    cvDF = cvDF.transpose()

    # name the unnamed column
    # cvDF.columns allows us to rename all columns using a list of strings.
    # there is technically only one column since date is an index
    cvDF.columns = ['confirmed']

    # convert date to a special pandas "datetime" value so it recognizes it
    cvDF.index = pd.to_datetime(cvDF.index, format='%m/%d/%y')

    # plot the total number of confirmed cases
    fig = px.line(x=cvDF.index, y=cvDF['confirmed'])
    fig.update_layout(title=f"Number of Confirmed COVID-19 Cases in {state}",
                      xaxis_title="Date",
                      yaxis_title="Confirmed COVID-19 Cases")
    fig.show()
    fig.write_html(f'{DIR_PATH}/output/confirmed_{state}.html')


def new_state(state):
    # read in file
    cvDF = pd.read_csv(f'{DIR_PATH}/input/{files[0]}', encoding='utf-8')

    # remove columns we don't care about
    cvDF = cvDF.drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Combined_Key',
                      'Lat', 'Long_', 'Country_Region', 'Admin2'], axis=1)

    # filter by state
    cvDF = cvDF.loc[cvDF['Province_State'] == state]

    # group all entries (counties) in a state together
    # sum all other columns
    # when you group by state, it automatically makes state the index
    cvDF = cvDF.groupby(['Province_State']).sum()

    # now that everything is dropped, we can transpose
    # we will now have 2 columns:
    # the 1st column is the index containing the date
    # the 2nd column contains the total number of new cases
    cvDF = cvDF.transpose()

    # name the unnamed column
    # cvDF.columns allows us to rename all columns using a list of strings.
    # there is technically only one column since date is an index
    cvDF.columns = ['confirmed']

    # create new column for the number of new cases
    cvDF['new'] = 0

    # loop to compute number of new cases each day
    prev = 0  # previous day's num of confirmed cases
    # iterate through every row (rows correspond to days)
    for index, row in cvDF.iterrows():
        # to get the number of new cases that day
        # subtract yesterday's confirmed cases from today's confirmed cases
        cvDF.loc[index, 'new'] = cvDF.loc[index, 'confirmed'] - prev
        # store this index's num of cases for use next time through
        prev = cvDF.loc[index, 'confirmed']

    # convert to list to fill in zeros with averages of next day's data
    new = cvDF['new'].tolist()
    for idx, val in enumerate(new):
        if val == 0:
            for length, zero in enumerate(new[idx+1:]):
                if zero != 0:
                    break
            length += 1
            if idx+length >= len(new) and new[-1] == 0:
                break
            mean = new[idx+length] // (length+1)
            new[idx+length] = new[idx+length] - mean * (length)
            for i in range(length):
                new[idx+i] = mean
    cvDF = cvDF.assign(new=new)

    # convert date to a special pandas "datetime" value so it recognizes it
    cvDF.index = pd.to_datetime(cvDF.index, format='%m/%d/%y')

    # plot the total number of confirmed cases
    fig = px.line(x=cvDF.index, y=cvDF['new'])
    fig.update_layout(title=f"Number of New COVID-19 Cases in {state}",
                      xaxis_title="Date",
                      yaxis_title="New COVID-19 Cases")
    fig.show()
    fig.write_html(f'{DIR_PATH}/output/new_{state}.html')


def confirmed_by_county(state):
    # read in file
    cvDF = pd.read_csv(f'{DIR_PATH}/input/{files[0]}', encoding='utf-8')

    # remove columns we don't care about
    cvDF = cvDF.drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Combined_Key',
                      'Lat', 'Long_', 'Country_Region'], axis=1)

    # filter by state
    cvDF = cvDF.loc[cvDF['Province_State'] == state]

    # need to make the county (Admin2) the index for transposing.
    cvDF.index = cvDF['Admin2']
    # drop state and county fields.
    cvDF = cvDF.drop(['Province_State', 'Admin2'], axis=1)

    # now that everything is dropped, we can transpose
    # we will now have 2 columns:
    # the 1st column is the index containing the date
    # the rest of the columns are number of confirmed cases by county.
    cvDF = cvDF.transpose()
    cvDF = cvDF.drop(['Unassigned'], axis=1)

    # convert date to a special pandas "datetime" value so it recognizes it
    cvDF.index = pd.to_datetime(cvDF.index, format='%m/%d/%y')

    # create a plot and add a trace for each year column
    fig = go.Figure()
    # for every column
    for col in cvDF.columns:
        fig = fig.add_trace(go.Scatter(x=cvDF.index, y=cvDF[col], name=col))

    # update the graph elements and show
    fig.update_layout(title=f"Confirmed COVID-19 Cases in {state} by County",
                      xaxis_title="Date",
                      yaxis_title="Number of Cases")
    fig.show()
    fig.write_html(f'{DIR_PATH}/output/confirmed_{state}_by_county.html')


def new_by_county(state):
    # read in file
    cvDF = pd.read_csv(f'{DIR_PATH}/input/{files[0]}', encoding='utf-8')

    # remove columns we don't care about
    cvDF = cvDF.drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Combined_Key',
                      'Lat', 'Long_', 'Country_Region'], axis=1)

    # filter by state
    cvDF = cvDF.loc[cvDF['Province_State'] == state]

    # need to make the county (Admin2) the index for transposing.
    cvDF.index = cvDF['Admin2']
    # drop state and county fields.
    cvDF = cvDF.drop(['Province_State', 'Admin2'], axis=1)

    # now that everything is dropped, we can transpose
    # we will now have 2 columns:
    # the 1st column is the index containing the date
    # the 2nd column contains the total number of confirmed cases
    cvDF = cvDF.transpose()
    cvDF = cvDF.drop(['Unassigned'], axis=1)

    # loop to compute number of new cases each day by county
    for col in cvDF.columns:
        prev = [0]  # previous day's num of confirmed cases
        for index, row in cvDF.iterrows():
            # store this index's num of cases for use next time through
            prev.append(cvDF.loc[index, col])
            # to get the number of new cases that day
            # subtract yesterday's confirmed cases from today's confirmed cases
            cvDF.loc[index, col] = prev[-1] - prev[-2]

    # convert to list to fill in zeros with averages of next day's data
    for col in cvDF.columns:
        new = cvDF[col].tolist()
        for idx, val in enumerate(new):
            if val == 0:
                for length, zero in enumerate(new[idx+1:]):
                    if zero != 0:
                        break
                length += 1
                if idx+length >= len(new) and new[-1] == 0:
                    break
                mean = new[idx+length] // (length+1)
                new[idx+length] = new[idx+length] - mean * (length)
                for i in range(length):
                    new[idx+i] = mean
        cvDF[col] = new

    # convert date to a special pandas "datetime" value so it recognizes it
    cvDF.index = pd.to_datetime(cvDF.index, format='%m/%d/%y')

    # create a plot and add a trace for each year column
    fig = go.Figure()
    # for every column
    for col in cvDF.columns:
        fig = fig.add_trace(go.Scatter(x=cvDF.index, y=cvDF[col], name=col))

    # update the graph elements and show
    fig.update_layout(title=f"New COVID-19 Cases in {state} by County",
                      xaxis_title="Date",
                      yaxis_title="Number of Cases")
    fig.show()
    fig.write_html(f'{DIR_PATH}/output/new_{state}_by_county.html')


def confirmed_by_state():
    # read in file
    cvDF = pd.read_csv(f'{DIR_PATH}/input/{files[0]}', encoding='utf-8')

    # remove columns we don't care about
    cvDF = cvDF.drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Combined_Key',
                      'Lat', 'Long_', 'Country_Region'], axis=1)

    # group all entries (counties) in a state together
    # sum all other columns
    # when you group by state, it automatically makes state the index
    cvDF = cvDF.groupby(['Province_State']).sum()

    # now that everything is dropped, we can transpose
    # we will now have 2 columns:
    # the 1st column is the index containing the date
    # the rest of the columns are number of confirmed cases by county.
    cvDF = cvDF.transpose()

    # convert date to a special pandas "datetime" value so it recognizes it
    cvDF.index = pd.to_datetime(cvDF.index, format='%m/%d/%y')

    # create a plot and add a trace for each year column
    fig = go.Figure()
    # for every column
    for col in cvDF.columns:
        fig = fig.add_trace(go.Scatter(x=cvDF.index, y=cvDF[col], name=col))

    # update the graph elements and show
    fig.update_layout(title="Confirmed COVID-19 Cases by State",
                      xaxis_title="Date",
                      yaxis_title="Number of Cases")
    fig.show()
    fig.write_html(f'{DIR_PATH}/output/confirmed_by_state.html')


def new_by_state():
    # read in file
    cvDF = pd.read_csv(f'{DIR_PATH}/input/{files[0]}', encoding='utf-8')

    # remove columns we don't care about
    cvDF = cvDF.drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Combined_Key',
                      'Lat', 'Long_', 'Country_Region'], axis=1)

    # group all entries (counties) in a state together
    # sum all other columns
    # when you group by state, it automatically makes state the index
    cvDF = cvDF.groupby(['Province_State']).sum()

    # now that everything is dropped, we can transpose
    # we will now have 2 columns:
    # the 1st column is the index containing the date
    # the rest of the columns are number of confirmed cases by county.
    cvDF = cvDF.transpose()

    # loop to compute number of new cases each day by county
    for col in cvDF.columns:
        prev = [0]  # previous day's num of confirmed cases
        for index, row in cvDF.iterrows():
            # store this index's num of cases for use next time through
            prev.append(cvDF.loc[index, col])
            # to get the number of new cases that day
            # subtract yesterday's confirmed cases from today's confirmed cases
            cvDF.loc[index, col] = prev[-1] - prev[-2]

    # convert date to a special pandas "datetime" value so it recognizes it
    cvDF.index = pd.to_datetime(cvDF.index, format='%m/%d/%y')

    # convert to list to fill in zeros with averages of next day's data
    for col in cvDF.columns:
        new = cvDF[col].tolist()
        for idx, val in enumerate(new):
            if val == 0:
                for length, zero in enumerate(new[idx+1:]):
                    if zero != 0:
                        break
                length += 1
                if idx+length >= len(new) and new[-1] == 0:
                    break
                mean = new[idx+length] // (length+1)
                new[idx+length] = new[idx+length] - mean * (length)
                for i in range(length):
                    new[idx+i] = mean
        cvDF[col] = new

    # create a plot and add a trace for each year column
    fig = go.Figure()
    # for every column
    for col in cvDF.columns:
        fig = fig.add_trace(go.Scatter(x=cvDF.index, y=cvDF[col], name=col))

    # update the graph elements and show
    fig.update_layout(title="New COVID-19 Cases by State",
                      xaxis_title="Date",
                      yaxis_title="Number of Cases")
    fig.show()
    fig.write_html(f'{DIR_PATH}/output/new_by_state.html')


def generate_docs():
    local = ['confirmed_Wake', 'new_Wake', 'confirmed_North Carolina', 'new_North Carolina',
             'confirmed_North Carolina_by_county', 'new_North Carolina_by_county',
             'confirmed_by_state', 'new_by_state']
    for f in local:
        src = f'{DIR_PATH}/output/{f}.html'
        dst = f'{DIR_PATH}/docs/{f}.html'
        shutil.copyfile(src, dst)

    with open(f'{DIR_PATH}/docs/index.html', 'r') as f:
        contents = f.read().splitlines()
    for i in range(len(contents)):
        if '  <p id="update" style="font-style: italic;">' in contents[i]:
            contents[i] = '  <p id="update" style="font-style: italic;">'
            timestamp = datetime.datetime.now().strftime("%B %d, %Y")
            inner = f"These graphs were last updated: {timestamp}."
            contents[i] += inner + '</p>'
    with open(f'{DIR_PATH}/docs/index.html', 'w') as f:
        f.write('\n'.join(contents))


def main():
    # prep, check for updates, download updates
    make_dirs()
    new = check_updates()
    if new:
        print("Downloading new data...")
        download_files()

    # collect state/county input
    cvDF = pd.read_csv(f'{DIR_PATH}/input/{files[0]}', encoding='utf-8')
    state = input("Enter your state: ").lower().title()
    while state not in cvDF['Province_State'].unique():
        print(f'{state} not recognized!')
        state = input("Enter your state: ").lower().title()
    county = input("Enter your county: ").lower().title()
    cvDF = cvDF.loc[cvDF['Province_State'] == state]
    while county not in cvDF['Admin2'].unique():
        print(f'{county} not recognized!')
        county = input("Enter your county: ").lower().title()

    # prepare plots
    confirmed_county(state, county)
    new_county(state, county)
    confirmed_state(state)
    new_state(state)
    confirmed_by_county(state)
    new_by_county(state)
    confirmed_by_state()
    new_by_state()

    # generates sample plots for docs - not needed
    # generate_docs()


if __name__ == '__main__':
    main()
