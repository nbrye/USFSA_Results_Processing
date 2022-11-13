# Imports
import pandas as pd
import requests 
import bs4


# Function to parse the main page
def parse_main(url):
    
    '''
    Takes a USFSA url containing pages of results and 
    extracts the links from each individual page
    
    :param url: A url corresponding to a main results page
    :returns: A list of webpages stemming from the main results 
    page
    '''
    
    # Helper function to extract links
    def _extract_link(x):
        return x.find("a")["href"]
    
    request = requests.get(url)
    
    # Important variables to store
    soup   = bs4.BeautifulSoup(request.text)
    events = soup.find_all("td", attrs = {"rowspan": 1})
    links  = soup.find_all("td", attrs = {"class": "cm rb"})
    
    # Extract the url ends for each webpage
    ends = list(map(_extract_link, links))

    # Request urls for each webpage
    baseurl  = url.replace("index.html", "")
    webpages = [baseurl + i for i in ends]
    
    return webpages, events

    

# Function to parse each results page
def parse_results(html, team = False):
    
    '''
    Takes an html text object containing the results of
    one group
    
    :param html: html text
    :param team: A boolean stating whether or not the event is a team 
    maneuvers event
    :returns: A DataFrame containing the place and university
    for each start
    '''
    
    # Create a soup object and extract the rows of the results table
    soup = bs4.BeautifulSoup(html.text)
    res  = soup.find_all("td", attrs = {"colspan":1})
    rows = soup.find_all("tr")
    rows = [x for x in rows if (len(x.find_all("td")) == 9 or len(x.find_all("td")) == 7)]
    
    # Extract the University names from each page
    out = []
    for i, x in enumerate(res):
        if team:
            uni = x.text
        else:
            uni = x.text.split(", ")[-1]
        out.append([rows[i].find("td").text, uni, rows[i].find_all("td")[-1].text])
        
    return pd.DataFrame(out, columns = ["Place", "College", "Tie"])




# Function to parse all of the results and remove withdrawals
def format_results(webpages):
    
    '''
    Takes a list of webpages and converts each results page to
    a DataFrame
    
    :param webpages: A list of webpage urls
    :returns: A list of DataFrames for each set of results
    '''
    
    DFS = []
    for i, x in enumerate(webpages):
        temp = requests.get(x)
        try:
            data = parse_results(temp)
            data = data.loc[~data["Tie"].str.contains("Withdraw")]
            DFS.append(data)
        except:
            pass
    return DFS


# Function to assign points for each event and totals for each team
def assign_points(DFS):
    
    '''
    Takes a list of DataFrames from format_results and totals the
    points for each collegiate team
    
    :param DFS: A list of results DataFrames
    :returns: A Series containing the point totals for each team
    at the current point in the competition
    '''
    
    OUT = []
    for i, x in enumerate(DFS):
        num = len(x)

        # Assign a number of points to each column
        x = x.assign(points = lookup[num])

        # Handle ties
        temp = x.groupby("Place")["points"].transform(lambda x: x.mean())
        x = x.assign(points = temp)

        # Handle championship event edge case
        if "Championship" in events[i].text or "International" in events[i].text:
            x["points"] = x["points"] + 2

        OUT.append(x)
        
    FULL = pd.concat(OUT)
    
    return FULL.groupby("College")["points"].sum().sort_values(ascending = False)


