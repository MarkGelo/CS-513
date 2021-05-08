import numpy as np
import pandas as pd

probe_path = 'Partition6467ProbePoints.csv'
link_path = 'Partition6467LinkData.csv'

def sloping(matched_probes, links):
    """
    Derives road slope for each road link
    Looks at the probes matched to the same link and finds slope between connected probes
    Evaluate the average derived slope with the average surveyed slope
    """

    print("Deriving and evaluating slopes...")
    cols = ['linkPVID', 'surveyedSlopeInfo', 'surveyedSlope', 'derivedSlopeList', 'derivedSlope']
    link_slopes = pd.DataFrame(columns = cols)
    for link, probes in matched_probes.groupby(['linkPVID']):
        #print(link)
        #print(len(probes))
        
        surveyed_link_slopes = links.loc[links['linkPVID'] == link]['slopeInfo2']
        s_slopes = surveyed_link_slopes.values.flatten()
        if len(s_slopes) == 1 and s_slopes[0] is None: # link data doesnt have slope so cant compare
            continue
            #pass

        # sort probes using time -- result in mostly correct connected probes
        probes['dateTime'] = pd.to_datetime(probes['dateTime'], format = '%m/%d/%Y %I:%M:%S %p')
        probes = probes.sort_values(by = ['dateTime'])
        #print(probes)
        idxs = [index for index, probe in probes.iterrows()]
        derived_slopes = []
        for i in range(len(idxs) - 1):
            # should check if relatively same time, cuz probes can have different dates yet be in same link
            # can check if the probes are close to each other, within a possible range, nvm could just do by sampleID
            probe1 = probes.loc[idxs[i], :]
            probe2 = probes.loc[idxs[i + 1], :]
            # time_dif = (probe1['dateTime'] - probe2['dateTime']) / pd.Timedelta('1 minute')
            # if np.abs(time_dif) > 10: # if 10 mins time difference then probes prob arent connected -- bad tho -- nvm could just do sampleID
            #     continue
            if probe1['sampleID'] != probe2['sampleID']:
                continue
            altitude1 = probe1['altitude']
            altitude2 = probe2['altitude']
            distance = haversine([probe1['latitude'], probe1['longitude']], [probe2['latitude'], probe2['longitude']])
            slope = np.arctan((altitude1 - altitude2) / distance)
            derived_slopes.append(slope)
            #print(f"Probes {i} {i + 1} - Slope: {slope}")
            #print(altitude1, altitude2)
        #print(link)

        # calculating surveyed link slope
        #surveyed_link_slope = sum([slope[1] for slopes in surveyed_link_slopes for slope in slopes]) / len(surveyed_link_slopes)
        s_slopes = [slope[1] for slopes in surveyed_link_slopes for slope in slopes] #if s_slopes is not None else [0]
        # if link == 51883083:
        #     print(s_slopes, ":", np.mean(s_slopes))
        #print(surveyed_link_slopes)
        #print(surveyed_link_slope)
        if not derived_slopes:
            continue
        link_slopes = link_slopes.append(pd.DataFrame([[link, s_slopes, 
                                            np.mean(s_slopes), derived_slopes, np.mean(derived_slopes)]], columns = cols))

    #print(link_slopes)
    # calculates error
    link_slopes['error'] = link_slopes['surveyedSlope'] - link_slopes['derivedSlope']
    error = link_slopes['error'].mean()
    print("Error:", error)

    link_slopes.to_csv('Partition6467Slopes.csv', index = False)
    
    return link_slopes

def matching(probes, links, limit: int = None):
    """
    Matches probes to a link
    Uses haversine to determine the closest link to a probe
    """
    
    lim = len(probes) if not limit else limit
    hav = lambda p, x: min(haversine(p, a[:2]) for a in x)
    link_temp = links.loc[:, ['linkPVID', 'shapeInfo2', 'directionOfTravel']] # get relevant info from link data
    matched_col = ['sampleID', 'dateTime', 'sourceCode', 'latitude', 'longitude', 'altitude', 'speed', 
                                            'heading', 'linkPVID', 'direction', 'distFromRef', 'distFromLink']
    matched_probes = pd.DataFrame(columns = matched_col)
    for index, row in probes.iterrows():
        if index >= lim:
            break
        if index % (int(lim / 20) if lim >= 20 else 1) == 0:
            print(f"Matching ... {int((index / lim) * 100)}%")

        # find closest link to a probe and gets linkPVID, dist_ref, dist_link
        link_temp['dist'] = link_temp['shapeInfo2'].apply(lambda x: min(haversine([row['latitude'], row['longitude']], a[:2]) for a in x))
        matched_link = link_temp.iloc[link_temp['dist'].idxmin()]['linkPVID']
        dist_link = link_temp['dist'].min()
        idx = link_temp[link_temp['linkPVID'] == matched_link].index.tolist()[0]
        direction = link_temp['directionOfTravel'][idx]
        ref = link_temp['shapeInfo2'][idx]
        #print(ref)
        dist_ref = hav([row['latitude'], row['longitude']], ref)
        #print(matched_link, dist_ref, dist_link)
        
        # add matched to probe data
        #sampleID, dateTime, sourceCode, latitude, longitude, altitude, speed, heading, linkPVID, direction, distFromRef, distFromLink
        matched_probes = matched_probes.append(pd.DataFrame([[row['sampleID'], row['dateTime'], row['sourceCode'], row['latitude'], 
                                                row['longitude'], row['altitude'], row['speed'], row['heading'], matched_link, direction, 
                                                dist_ref, dist_link]], columns = matched_col))
        #print(matched_probes)
    
    # save matched_probes to csv file
    matched_probes.to_csv('Partition6467MatchedPoints.csv', index = False)

    print("Matching done")

def haversine(p1: list, p2: list):
    """
    Calculates great circle distance between two points
    """
    
    lat1, lon1 = p1
    lat2, lon2 = p2
    # decimal to radians
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return c * 6371 # 6371 is radius of earth in km

def read_data(probe, link):
    """
    Uses pandas to read the csv files and processes the data
    Returns probes and links dataframe
    """

    probes = pd.read_csv(probe, header = None, names = ['sampleID', 'dateTime', 'sourceCode', 'latitude',
                                                        'longitude', 'altitude', 'speed', 'heading'])
    links = pd.read_csv(link, header = None, names = ['linkPVID', 'refNodeID', 'nrefNodeID', 'length', 'functionalClass', 
                                                    'directionOfTravel', 'speedCategory', 'fromRefSpeedLimit', 'toRefSpeedLimit', 
                                                    'fromRefNumLanes', 'toRefNumLanes', 'multiDigitized', 'urban', 'timeZone', 'shapeInfo', 
                                                    'curvatureInfo', 'slopeInfo'])
    
    # links have null values -- when ,, -- have lots of slope nulls
    links = links.fillna(0)
    
    '''
    shapeInfo contains an array of shape entries (e.g. lat/lon/elev|lat/lon/elev). 
    The elevation values will be null for link’s that don’t have 3D data.
    slopeInfo contains an array of slope entries (dist/slope|dist/slope). 
    This entire field will be null if there is no slope data for the link.'''
    to_list = lambda r: [[float(d) if d else float(0) for d in s.split('/')] for s in r.split('|')] if isinstance(r, str) else None # [[], [], []]

    links['shapeInfo2'] = links['shapeInfo'].apply(to_list)
    links['slopeInfo2'] = links['slopeInfo'].apply(to_list)

    return probes, links

if __name__ == "__main__":
    probes, links = read_data(probe = probe_path, link = link_path)

    #print(len(links))
    #print(len(links[links['slopeInfo'] == 0]))

    matching(probes, links, limit = 2000) # limit is the # of probes to matche and evaluate
    # for testing -- and already have MatchedPoints.csv, then comment line above
    matched_probes = pd.read_csv('Partition6467MatchedPoints.csv', header = 0)
    link_slopes = sloping(matched_probes, links)