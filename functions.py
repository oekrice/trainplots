# -*- coding: utf-8 -*-

import pytz
import streamlit as st
from urllib.request import urlopen
import threading
import time
import numpy as np
import datetime

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
    search_url1 = "https://www.realtimetrains.co.uk/search/detailed/gb-nr:" + str(start_code) + '/to/gb-nr:' + str(end_code) + '/' + str(init_date)[:10] + '/0000-2359?stp=WVS&show=all&order=wtt'
    html = urlopen(search_url1).read().decode("utf-8")
    ref_index = 0
    go = True
    all_trains = []
    while go:
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
            test_url = "https://www.realtimetrains.co.uk/service/gb-nr:" + code + '/' + str(init_date)[:10]  + '/detailed#allox_id=0'
            testpts, testdists = find_line_info(test_url, init = False)
            if testpts is not None:
                found1 = True
            if testdists is not None:
                found2 = True
            goodcode = code
    del all_trains
    del html
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
    del html
    return linepts, linedists

def train_info(Data, train_code, update = False):
    #This function finds out everything about a train on a given date, using advanced scraping from RTT
    #Now need to determine the url using the encoded date information

    if train_code[-2:] == '_p':
        #This runs on the previous day
        url = 'https://www.realtimetrains.co.uk/service/gb-nr:' + train_code[:-2] + '/' + str(Data.plot_yesterday)[:10]  + '/detailed'
        yesterday_flag = True
    else:
        url = 'https://www.realtimetrains.co.uk/service/gb-nr:' + train_code + '/' + str(Data.plot_date)[:10]  + '/detailed'
        yesterday_flag = False
    failcount = 0
    go = True
    while go:
        try:
            page = urlopen(url)
            html_bytes = page.read()    
            html = html_bytes.decode("utf-8")
            go = False
        except:   #Try to go for the day before? Trains might have happened before midnight
            print('URL FAILED', url)
            return [],[],[],[],[]
        
    find_text = "train-operator"
    title_index = html.find(find_text) + len(find_text) + 2
    
    operator = html[title_index:title_index+2]

    find_text = ", identity"
    title_index = html.find(find_text) + len(find_text) + 1
    
    headcode = html[title_index:title_index+4]

    if headcode == "0B00":
        #Is actually a bus. Don't plot.
        return [], [], [], [], []
        
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
                    #Put in checks here for the different days
                    if yesterday_flag:
                        if dep > 1200:  #Train started on the previous day. Don't plot anything which is before midnight?
                            dep = dep - 2400
                        if arr > 1200:
                            arr = arr - 2400
                    calls[-1].append([call, arr, dep])
                    on_line = True
                    off_line_time = 0
            else:
                off_line_time = off_line_time + 1
                if off_line_time > 1:
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
    rt_flag = 2  #If this is zero, allow ONE extra waypoint to be assumed on the RT. Don't want to start unless there's a thing though
    active_flag = 0    #Flag to see whether a train is currently active. 0 for not yet, 1 for yes and 2 for finished.
    stationary_flag = False  #True if the train is stationary in real time (arrival logged but no departure)
    #BUT need to not do that if the train is stationary
    while go:   #For actual times
        find_text = "/search/detailed"
        add = True
        stopnext = False
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

                if arr_act == '<spa':
                    arr_act = -2

                try:
                    arr_act = int(arr_act)
                    
                except:
                    arr_act = -1
                       
                if arr_act > 0:
                    if html[arr_act_index+4:arr_act_index+9] == "&frac":
                        arr_act = arr_act + whichfrac(html[arr_act_index+9:arr_act_index+11])

                #print(html[dep_act_index-8:dep_act_index-2])
                #This stop isn't actually here (the train hasn't run here yet)
                #BUT if doing the update, DO include these!  

                if html[dep_act_index-8:dep_act_index-2] == "(RMME)" or html[dep_act_index-8:dep_act_index-2] == "table)":
                    active_flag = 1   #Just needs to be some data at SOME point for this to be a 1. BUT 1s should be rare in general
                    if arr_act > 0:   
                        stationary_flag = True
                    if (not update) or rt_flag > 1:   #This is past the end of what can be plotted for now, unless later things come along
                        arr_act = -2
                        dep_act = -2
                    elif stationary_flag:  #Plot as normal but do increase rt_flag
                        dep_act = -3 #Indicates to carry on plotting train as it may be stationary indefinitely
                        rt_flag += 2
                    else:
                        if arr_act > 0:
                            rt_flag += 2
                        else:
                            rt_flag += 1
                else:
                    rt_flag = 0

                #print(call, arr_act, dep_act) 

                if not on_line:
                    calls_rt.append([])
                     
                if len(calls_rt[-1]) > 0:   #Deal with logical impossibilities. Sometimes an arrival is logged before a previous departure -- just deal with it.
                    if int(calls_rt[-1][-1][2]) > dep_act and dep_act >= 0:
                        add = False
                    if int(calls_rt[-1][-1][1]) > arr_act and arr_act >= 0:
                        add = False
                    if int(calls_rt[-1][-1][2]) > arr_act + 120 and arr_act >= 0:  #This is dubious -- but deal with it later
                        add = False                    
                    
                if arr_act < 0 and dep_act < 0:
                    off_line_time = off_line_time + 1
                    if off_line_time > 2:
                        on_line = False
                    add = False
                    
                if go and add:
                    if active_flag == 0:
                        active_flag = 2 #This train is actually done, perhaps
                    if yesterday_flag:
                        if dep_act > 1200:  #Train started on the previous day. Don't plot anything which is before midnight?
                            dep_act = dep_act - 2400
                        if arr_act > 1200:
                            arr_act = arr_act - 2400

                    calls_rt[-1].append([call, arr_act, dep_act])
                        
                    on_line = True
                    off_line_time = 0
                    
                    #Check for previous false arrivals
                    if len(calls_rt[-1]) > 1:
                        if calls_rt[-1][-2][2] < 0 and calls_rt[-1][-2][1] > 0:
                            calls_rt[-1][-2][2] = calls_rt[-1][-2][1]

            else:
                #on_line = False  #Be BRUTRAL -- not on this exact line. Allow no reports.
                off_line_time = off_line_time + 1
                if off_line_time > 1:
                    on_line = False
            ref_index = end_index + 1

        else:
            go = False
        if flag:
            flag = False

    del html
    return calls, calls_rt, operator, headcode, active_flag

def add_train_info(Data, train_code, update = 0, update_index = -1):
    #Just does train info but appends the information
    calls, calls_rt, ops, headcode, active_flag = train_info(Data, train_code, update = True)

    if update == 0:   #append to a nothing -- this train doesn't exist yet
        for c in range(len(calls)):
            if len(calls[c]) > 1:
                Data.allcalls.append(calls[c])
                Data.allops.append(ops)
                Data.allheads.append(headcode)
                Data.allcodes.append(train_code)
        for c in range(len(calls_rt)):
            if len(calls_rt[c]) > 1:
                Data.allcalls_rt.append(calls_rt[c])
                Data.allops_rt.append(ops)
                Data.allheads_rt.append(headcode)
                Data.allcodes_rt.append(train_code)
                Data.allactives_rt.append(active_flag)
    elif update == 1:   #This train does exist, so just change some things
        for c in range(len(calls)):
            if len(calls[c]) > 1:
                if Data.allcalls[update_index][0][0] == calls[c][0][0]:
                    Data.allcalls[update_index] = calls[c]
                    Data.allops[update_index] = ops
                    Data.allheads[update_index] = headcode
    elif update == 2:   #Same as above but for rt
        for c in range(len(calls_rt)):
            if len(calls_rt[c]) > 1:
                if Data.allcalls_rt[update_index][0][0] == calls_rt[c][0][0]:
                    Data.allcalls_rt[update_index] = calls_rt[c]
                    Data.allops_rt[update_index] = ops
                    Data.allheads_rt[update_index] = headcode
                    Data.allactives_rt[update_index] = active_flag
    else:   #For creating an rt for an existing not rt. Can overwrite if necessary in a minute, which it will do
        for c in range(len(calls_rt)):
            if len(calls_rt[c]) > 1:
                Data.allcalls_rt.append(calls_rt[c])
                Data.allops_rt.append(ops)
                Data.allheads_rt.append(headcode)
                Data.allcodes_rt.append(train_code)
                Data.allactives_rt.append(active_flag)
    return

def startend(calls):
    #Gives start and end time for the set of calls
    start = calls[0][2]%100 + 60*(calls[0][2]//100) 
    if calls[-1][1] >= 0:  #Is an arrival time
        end = calls[-1][1]%100 + 60*( calls[-1][1]//100)
    else:   #Is not, so use latest departure
        end = calls[-1][2]%100 + 60*( calls[-1][2]//100)
    return start,end

def update_train_data(Data):
    #To be used with the live thing -- using current time to see which trains are currently active. Won't add more because hard.
    #I think this is the updating bug which only appeared after the BST update

    uk_tz = pytz.timezone('Europe/London')

    current_time = datetime.datetime.now().astimezone(uk_tz)
    current_minutes = current_time.hour*60 + current_time.minute - 1
    #current_minutes = datetime.datetime.now().hour*60 + datetime.datetime.now().minute
    Data.allcalls = st.session_state.allcalls; Data.allops = st.session_state.allops
    Data.allcalls_rt = st.session_state.allcalls_rt ; Data.allops_rt = st.session_state.allops_rt; Data.allheads = st.session_state.allheads; Data.allheads_rt = st.session_state.allheads_rt
    Data.allcodes = st.session_state.allcodes; Data.allcodes_rt = st.session_state.allcodes_rt; Data.allactives_rt = st.session_state.allactives_rt
    Data.linepts = st.session_state.linepts
    #Do calls
    #print('Check lengths', len(Data.allactives_rt), len(Data.allcodes_rt))
    threads = []
    for k, calls in enumerate(st.session_state.allcalls):  #Checking for trains which have started running in this time. I think this is time...
        start, end = startend(st.session_state.allcalls[k])
        if (start > current_minutes - 90 and start < current_minutes + 30):
            if (st.session_state.allcodes[k] not in st.session_state.allcodes_rt):
                #print('Checking for new train', st.session_state.allcodes[k], current_minutes, start)
                #This train may start running in this timeframe -- add a blank thing somehow to the rt? Can then redo in a minute if necessary
                x = threading.Thread(target=add_train_info, args=(Data, st.session_state.allcodes[k], 3, k), daemon = False)
                threads.append(x)
                x.start()
        #print(k, st.session_state.allheads[k], start , end, current_minutes)
        #x = threading.Thread(target=add_train_info, args=(Data, st.session_state.allcodes[k], 1, k), daemon = False)
        #threads.append(x)
        #x.start()

    #Do calls_rt. For trains which are already running but need more info.
    for j, x in enumerate(threads):
        x.join()
    for k, calls in enumerate(st.session_state.allcalls_rt):
        if Data.allactives_rt[k] == 1:
            #print('Updating train', st.session_state.allcodes_rt[k])
            x = threading.Thread(target=add_train_info, args=(Data, st.session_state.allcodes_rt[k], 2, k), daemon = False)
            threads.append(x)
            x.start()
    for j, x in enumerate(threads):
        x.join()
    

    st.session_state.allcalls = Data.allcalls
    st.session_state.allops = Data.allops
    st.session_state.allcalls_rt = Data.allcalls_rt
    st.session_state.allops_rt = Data.allops_rt
    st.session_state.allactives_rt = Data.allactives_rt
    st.session_state.allheads = Data.allheads
    st.session_state.allheads_rt = Data.allheads_rt
    st.session_state.allcodes = Data.allcodes
    st.session_state.allcodes_rt = Data.allcodes_rt
    
def find_train_data(Data):
    #Finds the data for the trains with IDs in all_trains.
    #Can specify various filtering in this function I'd say
    threads = []
    Data.allcalls = []; Data.allops = []
    Data.allcalls_rt = []; Data.allops_rt = []; Data.allheads = []; Data.allheads_rt = []
    Data.allcodes = []; Data.allcodes_rt = []; Data.allactives_rt = []
    lump_size = 100
    progress_bar = st.progress(0, text = "Finding all trains")
    go = True; start = 0
    Data.linepts = st.session_state.linepts
    start_ind = 0
    
    if False:
        #Testing module --- loking for a particular train on this route
        add_train_info(Data, "W23819", 0, -1)
        print(Data.allcalls_rt[0])
        print('Test complete, maybe...')
        st.stop()

    while go:
        end_ind = min(start_ind + lump_size, len(st.session_state.all_trains[:]))
        for k, train in enumerate(st.session_state.all_trains[start_ind:end_ind]):
            x = threading.Thread(target=add_train_info, args=(Data, train,0,-1), daemon = False)
            threads.append(x)
            x.start()
            
        for j, x in enumerate(threads):
            x.join()
        if end_ind == len(st.session_state.all_trains[:]):
            go = False
        start_ind = start_ind + lump_size

        progress_bar.progress(end_ind/len(st.session_state.all_trains[:]), text = "%d%% complete" % (100*(end_ind/len(st.session_state.all_trains[:]))))
    st.session_state.found_alltrains = True
    print(st.session_state.linepts[0], 'to', st.session_state.linepts[-1])

    progress_bar.progress(1.0, text = "All trains found")
    st.session_state.allcalls = Data.allcalls
    st.session_state.allops = Data.allops
    st.session_state.allcalls_rt = Data.allcalls_rt
    st.session_state.allops_rt = Data.allops_rt
    st.session_state.allheads = Data.allheads
    st.session_state.allheads_rt = Data.allheads_rt
    st.session_state.allcodes = Data.allcodes
    st.session_state.allcodes_rt = Data.allcodes_rt
    st.session_state.allactives_rt = Data.allactives_rt
    
    #Run throught to make distances
    def ttox(t):  
        #Converts time into minutes since midnight
        if t >= 0:
            return (t//100)*60 + t - 100*(t//100)
        else:
            return t

    if True:#st.session_state.linedists is None:   #Figure out the average times between points
        #Perhaps not average -- some kind of percentile?
        st.session_state.linetimes = np.zeros(len(st.session_state.linepts))
        timecounts = np.zeros(len(st.session_state.linepts))
        alltimes_mat = [[] for _ in range(len(st.session_state.linepts))]
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
                    alltimes_mat[ind1].append(t1 - t0)
                    timecounts[ind1] += 1
                elif ind0 == ind1 + 1:
                    alltimes_mat[ind0].append(t1 - t0)

                    timecounts[ind0] += 1
                    
        timecounts[0] = 1.0
        st.session_state.linetimes[0] = 0.0
        for i in range(1, len(st.session_state.linetimes)):
            if len(alltimes_mat[i]) > 0:
                st.session_state.linetimes[i] = st.session_state.linetimes[i-1] +  np.percentile(alltimes_mat[i], 10)
            else:
                st.session_state.linetimes[i] = 5.0
    st.session_state.linetimes = st.session_state.linetimes*1.5
    del alltimes_mat
    
    return
    
def find_all_trains(Data):
    '''
    Finds all the train codes that pass through linepts on a given date.
    '''
    def pturl(code):
        return 'https://www.realtimetrains.co.uk/search/detailed/gb-nr:' + code + '/' + str(Data.plot_date)[:10]  + '/0000-2359?stp=WVS&show=all&order=wtt'
    
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
                train_start_date = str(html[start_index+8:start_index+18])

                if train_start_date[-1] == '/':   #This train code is only 5 charachters for some reason. Change things as appropriate
                    train_index = html[start_index+1:start_index+6]
                    train_start_date = str(html[start_index+7:start_index+17])

                if train_start_date != str(Data.plot_date)[:10]:
                    train_index = train_index + '_p'  #Indicates this train is registered from the previous day.

                #Obtain date this train ran as well (and append as a suffix for obtaining line info)

                if train_index not in all_trains:
                    all_trains.append(train_index)
                    traincount.append(1)
                else:
                    traincount[all_trains.index(train_index)] += 1
                
                #print(html[start_index+1:start_index+7])
            else:
                go = False
        del html
        return

    all_trains = []
    traincount = []   #number of stations in the range that the train calls at
    threads = []

    for k in range(len(st.session_state.linepts)):
        #trains_at_point(st.session_state.linepts[k], all_trains, traincount)

        x = threading.Thread(target=trains_at_point, args=(st.session_state.linepts[k], all_trains, traincount), daemon = False)
        threads.append(x)
        x.start()
    for j, x in enumerate(threads):
        x.join()

    return all_trains

