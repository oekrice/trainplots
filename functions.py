# -*- coding: utf-8 -*-

import streamlit as st
from urllib.request import urlopen
import threading
import time
import numpy as np

def station_name(Data, station_code):
    #Looks up the station code and returns the proper name
    #st.write(Data.stations)
    ind = Data.stations.index[Data.stations["crsCode"] == station_code][0]
    return Data.stations["stationName"][ind]

def station_code(Data, station_name):
    #Looks up the station code and returns the proper name
    #st.write(Data.stations)
    ind = Data.stations.index[Data.stations["stationName"] == station_name][0]
    return Data.stations["crsCode"][ind]

def find_trains_pts(Data, init_date, start_code, end_code):
    #Finds trains between two points (as codes)
    #Check first direction first
    search_url1 = "https://www.realtimetrains.co.uk/search/detailed/gb-nr:" + str(start_code) + '/to/gb-nr:' + str(end_code) + '/' + str(init_date) + '/0000-2359?stp=WVS&show=all&order=wtt'
    html = urlopen(search_url1).read().decode("utf-8")
    ref_index = 0
    go = True
    all_trains = []
    while go:
    #print(html)
        find_text = "/service/gb-nr"
        title_index = html[ref_index:].find(find_text) + ref_index
        if title_index - ref_index >= 0:
            start_index = title_index + len(find_text)
            end_index = html[start_index:].find("class") - 2 + start_index
            ref_index = end_index + 1
            train_index = html[start_index+1:start_index+7]
            all_trains.append(train_index)
        else:
            go = False
    #Check these trains for distance data
    found1 = False; found2 = False
    testpts = None; testdists = None; goodcode = None
    for code in all_trains:
        if not found1 or not found2:
            test_url = "https://www.realtimetrains.co.uk/service/gb-nr:" + code + '/' + str(init_date) + '/detailed#allox_id=0'
            testpts, testdists = find_line_info(test_url, init = False)
            if testpts is not None:
                found1 = True
            if testdists is not None:
                found2 = True
            goodcode = code
    return goodcode, testpts, testdists

#@st.cache_data
def find_line_info(url, init = False, unspecified = False):
    try:
        page = urlopen(url)
    except:
        if init:
            st.error("Train not found. url giving the error: %s" % url)            
            st.stop()
        else:
            return None, None
        
    html_bytes = page.read()    
    html = html_bytes.decode("utf-8")
    ref_index = 0
    linepts = []
    linedists = []
    miles = []
    chains = []
    go = True
    while go:
    #print(html)
        find_text = "/search/detailed"
        title_index = html[ref_index:].find("/search/detailed/gb-nr") + ref_index
        if title_index - ref_index >= 0:
            start_index = title_index + len(find_text)
            end_index = html[start_index:].find("class") - 2 + start_index
            ref_index = end_index + 1
            linepts.append(html[start_index+7:end_index-16])
        else:
            go = False
            
    ref_index = 0
    go = True
    while go:
        find_text = 'class="miles"'
        title_index = html[ref_index:].find(find_text) + ref_index
        if title_index - ref_index >= 0:
            start_index = title_index
            end_index = html[start_index:].find("</span") + start_index
            ref_index = end_index + 1
            miles.append(int(html[start_index+14:end_index]))
        else:
            go = False

    ref_index = 0
    go = True
    while go:
        find_text = 'class="chains"'
        title_index = html[ref_index:].find(find_text) + ref_index
        if title_index - ref_index >= 0:
            start_index = title_index
            end_index = html[start_index:].find("</span") + start_index
            ref_index = end_index + 1
            chains.append(int(html[start_index+15:end_index]))
        else:
            go = False
    if len(miles) > 0:
        for i in range(len(miles)):
            linedists.append(miles[i] + chains[i]/80)
    else:
        linedists = None
    if len(linepts) == 0:
        linepts = None
    return linepts, linedists

def train_info(Data, train_code):
    #This function finds out everything about a train on a given date, using advanced scraping from RTT
    url = 'https://www.realtimetrains.co.uk/service/gb-nr:' + train_code + '/' + str(Data.plot_date) + '/detailed'
    failcount = 0
    go = True
    while go:
        try:
            page = urlopen(url)
            html_bytes = page.read()    
            html = html_bytes.decode("utf-8")

            go = False
        except:
            if failcount > 2:
                return [], [], [], []
            else:
                time.sleep(0.05)
                failcount += 1
        
    
    find_text = "train-operator"
    title_index = html.find(find_text) + len(find_text) + 2
    
    operator = html[title_index:title_index+2]

    find_text = ", identity"
    title_index = html.find(find_text) + len(find_text) + 1
    
    headcode = html[title_index:title_index+4]

    if headcode == "0B00":
        #Is actually a bus
        return [], [], [], []
        
    def whichfrac(string):
        #Determes which fraction of the minute is recorded
        if string == "12":
            return 0.5
        elif string == "34":
            return 0.75
        elif string == "14":
            return 0.25
        
    #FIND PLANNED DATE
    ref_index = 0
    calls = []
    go = True
    off_line_time = 0
    started = False

    on_line = False  #flag to tell if a train is on the line. For splitting up the journeys when trains rejoin the route. Being a bit st =id...
    while go:   #For scheduled times
        find_text = "/search/detailed"
        title_index = html[ref_index:].find("/search/detailed/gb-nr") + ref_index
        if title_index - ref_index >= 0:
            start_index = title_index + len(find_text)
            end_index = html[start_index:].find("class") - 2 + start_index
            end_search_index = html[start_index + 1:].find(find_text) - 1 + start_index
            call = html[start_index+7:end_index-16]
            if call in Data.linepts:

                dep_index = html[start_index:end_search_index].find('dep">') + start_index
                dep = html[dep_index+5:dep_index+9]
                if dep == '</di' and not started:
                    dep = -2
                    started = True
                #print(dep)
                try:
                    dep = int(dep)
                    
                except:
                    dep = -1
                
                if dep > 0:
                    if html[dep_index+9:dep_index+14] == "&frac":
                        dep = dep + whichfrac(html[dep_index+14:dep_index+16])
                    
                arr_index = html[start_index:end_search_index].find('arr">') + start_index
                arr = html[arr_index+5:arr_index+9]
                if arr == '</di':
                    arr = -2

                try:
                    arr = int(arr)
                    
                except:
                    arr = -1
                       
                if arr > 0:
                    if html[arr_index+9:arr_index+14] == "&frac":
                        arr = arr + whichfrac(html[arr_index+14:arr_index+16])
                        
                if not on_line:
                    calls.append([])
                        
                if len(calls[-1]) > 0:
                    if int(calls[-1][-1][2]) > dep and dep >= 0:
                        go = False
                    if int(calls[-1][-1][1]) > arr and arr >= 0:
                        go = False
                    if int(calls[-1][-1][2]) > arr + 60 and arr >= 0:
                        go = False

                if go:
                    calls[-1].append([call, arr, dep])
                        
                    on_line = True
                    off_line_time = 0
            else:
                off_line_time = off_line_time + 1
                if off_line_time > 2:
                    on_line = False
            ref_index = end_index + 1

        else:
            go = False
            
    ref_index = 0
    calls_rt = []
    go = True
    off_line_time = 0
    
    on_line = False  #flag to tell if a train is on the line. For splitting up the journeys when trains rejoin the route. Being a bit stupid...
    flag = False
    while go:   #For actual times
        find_text = "/search/detailed"
        add = True
        title_index = html[ref_index:].find("/search/detailed/gb-nr") + ref_index
        if title_index - ref_index >= 0:
            start_index = title_index + len(find_text)
            end_index = html[start_index:].find("class") - 2 + start_index
            end_search_index = html[start_index + 1:].find(find_text) - 1 + start_index
            call = html[start_index+7:end_index-16]
            if call in Data.linepts:

                dep_index = html[start_index:end_search_index].find('dep">') + start_index
                
                #Search for things AFTER this dep
                start_index = dep_index + 10
                dep_search_index = html[start_index:end_search_index].find('dep') + start_index + 14

                dep_act_index = html[dep_search_index:end_search_index].find('">') + dep_search_index + 2

                dep_act = html[dep_act_index:dep_act_index+4]
            
                try:
                    dep_act = int(dep_act)
                    
                except:
                    if dep_act == "<div>":
                        dep_act = -1
                    else:
                        dep_act = -2

                if dep_act > 0:
                    if html[dep_act_index+4:dep_act_index+9] == "&frac":
                        dep_act = dep_act + whichfrac(html[dep_act_index+9:dep_act_index+11])

                arr_search_index = html[start_index:end_search_index].find('arr') + start_index + 14

                arr_act_index = html[arr_search_index:end_search_index].find('">') + arr_search_index + 2
                
                arr_act = html[arr_act_index:arr_act_index+4]

                #print(html[dep_act_index-8:dep_act_index-2])
                #This stop isn't actually here (the train didn't run)
                if html[dep_act_index-8:dep_act_index-2] == "(RMME)" or html[dep_act_index-8:dep_act_index-2] == "table)":
                    arr_act = -2
                    dep_act = -2
                    
                if arr_act == '<spa':
                    arr_act = -2

                try:
                    arr_act = int(arr_act)
                    
                except:
                    arr_act = -1
                       
                if arr_act > 0:
                    if html[arr_act_index+4:arr_act_index+9] == "&frac":
                        arr_act = arr_act + whichfrac(html[arr_act_index+9:arr_act_index+11])
                        
                if not on_line:
                    calls_rt.append([])
                     
                if len(calls_rt[-1]) > 0:   #Deal with logical impossibilities. Sometimes an arrival is logged before a previous departure -- just deal with it.
                    if int(calls_rt[-1][-1][2]) > dep_act and dep_act >= 0:
                        add = False
                    if int(calls_rt[-1][-1][1]) > arr_act and arr_act >= 0:
                        add = False
                    if int(calls_rt[-1][-1][2]) > arr_act + 60 and arr_act >= 0:  #This is dubious -- but deal with it later
                        add = False

                if arr_act < 0 and dep_act < 0:
                    off_line_time = off_line_time + 1
                    if off_line_time > 2:
                        on_line = False
                    add = False
                    
                if go and add:
                    calls_rt[-1].append([call, arr_act, dep_act])
                        
                    on_line = True
                    off_line_time = 0
                    
                    #Check for previous false arrivals
                    if len(calls_rt[-1]) > 1:
                        if calls_rt[-1][-2][2] < 0 and calls_rt[-1][-2][1] > 0:
                            calls_rt[-1][-1][2] = calls_rt[-1][-2][1]

            else:
                off_line_time = off_line_time + 1
                if off_line_time > 5:
                    on_line = False
            ref_index = end_index + 1

        else:
            go = False
        if flag:
            print(calls_rt)
            flag = False

    #On old-signalled lines reports can get messy -- this clears them up. Need to look into this more...
    #BUT this might break other things...
    #for calls in calls_rt:   #If no reported departure time, assume the same as arrival
    #    for k in range(1, len(calls) - 1):
    #        if calls[k][2] < 0.0 and calls[k][1] > 0.0:
    #            calls[k][2] = calls[k][1]
    '''
    for calls in calls_rt:
        for k in range(1, len(calls) - 1):
            if calls[k][1] == -2:
                calls[k][1] = -1
                
            if calls[k][2] == -2:
                calls[k][2] = calls[k][1]
                calls[k][1] = -1
    '''
    return calls, calls_rt, operator, headcode

def add_train_info(Data, train_code):
    #Just does train info but appends the information
    calls, calls_rt, ops, headcode = train_info(Data, train_code)
    for c in range(len(calls)):
        if len(calls[c]) > 1:
            Data.allcalls.append(calls[c])
            Data.allops.append(ops)
            Data.allheads.append(headcode)
    for c in range(len(calls_rt)):
        if len(calls_rt[c]) > 1:
            Data.allcalls_rt.append(calls_rt[c])
            Data.allops_rt.append(ops)
            Data.allheads_rt.append(headcode)
    return

def find_train_data(Data):
    #Finds the data for the trains with IDs in all_trains.
    #Can specify various filtering in this function I'd say
    threads = []
    Data.allcalls = []; Data.allops = []
    Data.allcalls_rt = []; Data.allops_rt = []; Data.allheads = []; Data.allheads_rt = []
    lump_size = 100
    progress_bar = st.progress(0, text = "Finding all trains")
    go = True; start = 0
    Data.linepts = st.session_state.linepts
    start_ind = 0
    while go:
        end_ind = min(start_ind + lump_size, len(st.session_state.all_trains[:]))
        for k, train in enumerate(st.session_state.all_trains[start_ind:end_ind]):
            x = threading.Thread(target=add_train_info, args=(Data, train), daemon = False)
            threads.append(x)
            x.start()
            
        for j, x in enumerate(threads):
            x.join()
        if end_ind == len(st.session_state.all_trains[:]):
            go = False
        start_ind = start_ind + lump_size
        
        progress_bar.progress(end_ind/len(st.session_state.all_trains[:]), text = "%d%% complete" % (100*(end_ind/len(st.session_state.all_trains[:]))))
    st.session_state.found_alltrains = True

    progress_bar.progress(1.0, text = "All trains found")
    st.session_state.allcalls = Data.allcalls
    st.session_state.allops = Data.allops
    st.session_state.allcalls_rt = Data.allcalls_rt
    st.session_state.allops_rt = Data.allops_rt
    st.session_state.allheads = Data.allheads
    st.session_state.allheads_rt = Data.allheads_rt
    
    #Run throught to make distances
    def ttox(t):  
        #Converts time into minutes since midnight
        if t >= 0:
            return (t//100)*60 + t - 100*(t//100)
        else:
            return t

    if st.session_state.linedists is None:   #Figure out the average times between points
        st.session_state.linetimes = np.zeros(len(st.session_state.linepts))
        timecounts = np.zeros(len(st.session_state.linepts))
        for calls in st.session_state.allcalls:
            for i in range(1, len(calls)):
                ind0 = st.session_state.linepts.index(calls[i-1][0])
                ind1 = st.session_state.linepts.index(calls[i][0])
                t0 = ttox(calls[i-1][2])
                if calls[i][1] > 0:
                    t1 = ttox(calls[i][1])
                else:
                    t1 = ttox(calls[i][2])
                if ind1 == ind0 + 1:
                    st.session_state.linetimes[ind1] += t1 - t0
                    timecounts[ind1] += 1
                elif ind0 == ind1 + 1:
                    st.session_state.linetimes[ind0] += t1 - t0
                    timecounts[ind0] += 1
        timecounts[0] = 1.0
        st.session_state.linetimes = st.session_state.linetimes/timecounts
        for i in range(1, len(st.session_state.linetimes)):
            st.session_state.linetimes[i] = st.session_state.linetimes[i-1] + st.session_state.linetimes[i] 
    return
    
def find_all_trains(Data):
    '''
    Finds all the train codes that pass through linepts on a given date.
    '''
    def pturl(code):
        return 'https://www.realtimetrains.co.uk/search/detailed/gb-nr:' + code + '/' + str(Data.plot_date) + '/0000-2359?stp=WVS&show=all&order=wtt'
    
    def trains_at_point(point, all_trains, traincount):
        #This should be sped up with multithreading
        url = pturl(point)
        try:
            html = urlopen(url).read().decode("utf-8")
        except:
            return
        ref_index = 0
        go = True
        while go:
        #print(html)
            find_text = "/service/gb-nr"
            title_index = html[ref_index:].find(find_text) + ref_index
            
            if title_index - ref_index >= 0:
                start_index = title_index + len(find_text)
                end_index = html[start_index:].find("class") - 2 + start_index
                ref_index = end_index + 1
                train_index = html[start_index+1:start_index+7]
                if train_index not in all_trains:
                    all_trains.append(train_index)
                    traincount.append(1)
                else:
                    traincount[all_trains.index(train_index)] += 1
                #print(html[start_index+1:start_index+7])
            else:
                go = False
        return

    all_trains = []
    traincount = []   #number of stations in the range that the train calls at
    threads = []
    for k in range(len(st.session_state.linepts)):
        x = threading.Thread(target=trains_at_point, args=(st.session_state.linepts[k], all_trains, traincount), daemon = False)
        threads.append(x)
        x.start()
    for j, x in enumerate(threads):
        x.join()

    return all_trains

