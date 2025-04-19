
import streamlit as st
from streamlit.logger import get_logger

import datetime
from functions import find_line_info, train_info, station_name, station_code, find_all_trains, find_train_data, find_trains_pts, update_train_data
from plot_functions import plot_trains
import time
import os
import io

import pandas as pd
import numpy as np
import time as time_module
import pytz

LOGGER = get_logger(__name__)

class all_data():
    #Contains some things
    def __init__(self):
        self.stations = pd.read_csv("stations.csv")
        #Create list for dropdowns
        self.full_names = []
        for k in range(len(self.stations["stationName"])):
            self.full_names.append(self.stations["stationName"][k] + ' (' + self.stations["crsCode"][k] + ')')
            
if "all_trains" not in st.session_state:
    st.session_state.all_trains = None
if "allcalls" not in st.session_state:
    st.session_state.allcalls = None
if "allops" not in st.session_state:
    st.session_state.allops = None
if "allcodes" not in st.session_state:
    st.session_state.allcodes = None
if "allcalls_rt" not in st.session_state:
    st.session_state.allcalls_rt = None
if "allops_rt" not in st.session_state:
    st.session_state.allops_rt = None
if "allheads" not in st.session_state:
    st.session_state.allheads = None
if "allheads_rt" not in st.session_state:
    st.session_state.allheads_rt = None
if "allcodes_rt" not in st.session_state:
    st.session_state.allcodes_rt = None
if "timeref" not in st.session_state:
    st.session_state.timeref = None
if "current_datetime" not in st.session_state:
    st.session_state.current_datetime = None
if "linepts" not in st.session_state:
    st.session_state.linepts = None
if "linedists" not in st.session_state:
    st.session_state.linedists = None
if "stat_selected_1" not in st.session_state:
    st.session_state.stat_selected_1 = False
if "found_alltrains" not in st.session_state:
    st.session_state.found_alltrains = False
if "diag_flag" not in st.session_state:
    st.session_state.diag_flag = False
if "update_time" not in st.session_state:
    st.session_state.update_time = False
if "refresh" not in st.session_state:
    st.session_state.refresh = False
if "paras_chosen" not in st.session_state:
    st.session_state.paras_chosen = True
if "update_start" not in st.session_state:
    st.session_state.update_start = False
    
def reset_route():
    st.session_state.all_trains = None
    st.session_state.allcalls = None
    st.session_state.allops = None
    st.session_state.allcalls_rt = None
    st.session_state.allops_rt = None
    st.session_state.allheads = None
    st.session_state.allheads_rt = None
    st.session_state.linepts = None
    st.session_state.linedists = None
    st.session_state.stat_selected_1 = None
    st.session_state.found_alltrains = False
    st.session_state.refresh = False
    st.session_state.paras_chosen = True
    st.session_state.update_time = False

def reset_trains():
    st.session_state.all_trains = None
    st.session_state.allcalls = None
    st.session_state.allops = None
    st.session_state.allcalls_rt = None
    st.session_state.allops_rt = None
    st.session_state.allheads = None
    st.session_state.allheads_rt = None
    st.session_state.found_alltrains = False
    st.session_state.refresh = False
    st.session_state.paras_chosen = True
    st.session_state.update_time = False

if not os.path.exists('./tmp/'):
    os.mkdir('./tmp/')
    
def run():
    st.set_page_config(
        page_title="Train Location Plotting",
        page_icon="🛤️",
    )

    st.write("# Train Location Plotting")

    #st.sidebar.success("Select a demo above.")

    with st.expander("What this is and how to use it"):
        st.markdown(
            """
            This is a tool to plot the locations of trains on a given route, either in real-time or at any point over the last week, using data from RealTimeTrains. \\
            There are two options to specify the route -- either specify start and end stations or use a specific RTT train code from some point in the last week. \\
            All the trains along the route at any point on the plotting day will be found, and all their timing data. This can be quite slow. \\
            Various plotting parameters can be set, but the time range is limited if plotting live trains. \\
            By default both scheduled and actual timings are shows, the latter less transparently than the former. \\
            Large plots will be compressed in the browser, but full resolution images can be downloaded.  \\
            Behold -- Newcastle to York on the 18th March:
            """
        )
        st.image("NCL_YRK.png")

    with st.expander("Limitations and known bugs"):
        st.markdown(
            """
            The plots attempt to find smooth curves which fit the given timing data. Sometimes the data is not quite right and this causes strange things to happen, such as trains travelling backwards for a bit. \\
            Trains will go missing around midnight sometimes. This is fixable but a lot of effort. \\
            Occasionally the RTT data is input strangely enough (with VST or STP workings usually) that trains will appear in completely random places. I've tried to catch all of these but it's hard to stop them all. \\
            If a train takes a suspiciously long time to pass between waypoints, I will assume it has stopped for a bit even if it didn't in reality. This can make it seem like trains are on top of each other in the middle of nowhere when actually they were stopped some distance apart.  \\
            Trains not detected initially will not show up on the live plots if they subsequently become a thing. If this is important just find all the trains again and they'll show up. \\
            On manually-signalled lines trains sometimes don't get logged so it looks like they don't stop anywhere or go missing for a while.
            """
        )
    

    select_type = st.pills("Specify stations or specific train using RTT number?", options = ["Stations", "RTT Number"], default = "Stations")
    
    @st.cache_data
    def get_data():
        Data = all_data()
        return Data

    uk_tz = pytz.timezone('Europe/London')

    Data = get_data()
    
    #Establish the first train to use
    if select_type == "RTT Number":
        rtt_code = st.text_input("Input RTT code (eg. P13795)", on_change = reset_route)
        if rtt_code == '':
            st.stop()
        init_date = st.date_input("Date this train happened", value ="today", min_value = uk_tz.localize(datetime.datetime.today()) - datetime.timedelta(days = 7), max_value = uk_tz.localize(datetime.datetime.today()), on_change = reset_route)
        init_url = "https://www.realtimetrains.co.uk/service/gb-nr:" + rtt_code + '/' + str(init_date)[:10]  + '/detailed#allox_id=0'
        st.session_state.linepts, st.session_state.linedists = find_line_info(init_url, init = True, unspecified = False)
        st.session_state.stat_selected_1 = True

        #Options for plotting: Generate as a list (useful for later anyway, probably)
        station_names = []; station_inds = []
        for si, stat in enumerate(st.session_state.linepts):
            try:
                station_names.append(station_name(Data, stat))
                station_inds.append(si)
            except:  #Won't manage ones that aren't stations
                pass
        cols = st.columns(2)
        with cols[0]:
            start_name = st.selectbox("Start station", station_names, index = 0, on_change = reset_route)
        with cols[1]:
            end_name = st.selectbox("End station", station_names, index = len(station_names) - 1, on_change = reset_route)
        if start_name == end_name:
            st.error("Can't have the same start and end station. Trains which go in a loop aren't supported as that's hard. Sorry.")
        start_ind = station_inds[station_names.index(start_name)]
        end_ind = station_inds[station_names.index(end_name)]

        #Trim or reverse as appropriate
        if start_ind < end_ind:
            st.session_state.linepts = st.session_state.linepts[start_ind:end_ind + 1]
            if st.session_state.linedists is not None:
                st.session_state.linedists = st.session_state.linedists[start_ind:end_ind + 1]
        else:
            st.session_state.linepts = st.session_state.linepts[end_ind:start_ind + 1][::-1]
            if st.session_state.linedists is not None:
                st.session_state.linedists = st.session_state.linedists[end_ind:start_ind + 1][::-1]

    else:   #Specifying stations
        cols = st.columns(2)
        init_date = uk_tz.localize(datetime.datetime.today())

        with cols[0]:
            start_name = st.selectbox("Start station", Data.full_names, index = None,  on_change = reset_route, key = 24556567)
        with cols[1]:
            end_name = st.selectbox("End station", Data.full_names, index = None, on_change = reset_route, key = 4568934)
            
        if start_name is None or end_name is None:
            st.stop()
            

        start_code = start_name[-4:-1]
        end_code = end_name[-4:-1]
            
        if st.button("Find route between these stations", on_click = reset_route):
            rtt_code, linepts, linedists = find_trains_pts(Data, init_date, start_code, end_code)
            st.session_state.linepts = linepts; st.session_state.linedists = linedists
            st.session_state.stat_selected_1 = True

            if st.session_state.linepts is None:
                st.error("No train found travelling between these stations today. Try specifying a train instead?")
                st.stop()

            init_url = "https://www.realtimetrains.co.uk/service/gb-nr:" + rtt_code + '/' + str(init_date)[:10]  + '/detailed#allox_id=0'
       
            #DO need to trim here...
            #start_ind = station_inds[station_names.index(start_name)]
            #end_ind = station_inds[station_names.index(end_name)]

            st.session_state.linepts, st.session_state.linedists = find_line_info(init_url, init = True, unspecified = True)
            #Options for plotting: Generate as a list (useful for later anyway, probably)
            start_ind = st.session_state.linepts.index(start_code); end_ind = st.session_state.linepts.index(end_code)
            
            if start_ind < end_ind:
                st.session_state.linepts = st.session_state.linepts[start_ind:end_ind + 1]
                if st.session_state.linedists is not None:
                    st.session_state.linedists = st.session_state.linedists[start_ind:end_ind + 1]
            else:
                st.session_state.linepts = st.session_state.linepts[end_ind:start_ind + 1][::-1]
                if st.session_state.linedists is not None:
                    st.session_state.linedists = st.session_state.linedists[end_ind:start_ind + 1][::-1]

    if not st.session_state.stat_selected_1:
        st.stop()
        
    if st.session_state.linepts is None:
        st.error("No train found travelling between these stations today. Try specifying a train instead?")
        st.stop()
        
    elif st.session_state.linedists is None:
        st.write("Suitable route found, but with no distance information. Plot y axes may be a little strange.")
    else:
        st.write("Suitable route and distance information found for this choice. If this isn't the route you'd like, specify a train instead.")

    if st.session_state.linedists is not None:
        st.session_state.linedists = st.session_state.linedists - np.min(st.session_state.linedists)
        
    if st.session_state.linepts is None:
        st.stop()

    with st.expander("View all waypoints and distances on this route:"):
        if st.session_state.linedists is not None:
            sanitised_linedists = np.array([round(val, 4) for val in st.session_state.linedists])
            st.write(np.vstack((st.session_state.linepts, sanitised_linedists)).T)
        else:
            st.write(np.array(st.session_state.linepts))
        
    Data.plot_date = st.date_input("Date to plot", value ="today", min_value = uk_tz.localize(datetime.datetime.today()) - datetime.timedelta(days = 7), max_value = uk_tz.localize(datetime.datetime.today()), on_change = reset_trains)
    Data.plot_date = datetime.datetime.combine(Data.plot_date, datetime.datetime.min.time())
    Data.plot_yesterday =  uk_tz.localize(datetime.datetime.today()) - datetime.timedelta(days = 1)

    if st.button("Find all trains on this route on this day", disabled = st.session_state.all_trains != None):
        st.write("Finding all trains...")

        st.session_state.all_trains = find_all_trains(Data)
        st.rerun()    
        
    if st.session_state.all_trains is None:
        st.stop()
    else:
        st.write(str(len(st.session_state.all_trains)), ' trains found')
        
    #Train IDs found. Attempt to find info for them...
    if st.button("Find all train times (may take a minute or two)", disabled = st.session_state.found_alltrains):
        st.write("Finding train times...")
        find_train_data(Data)
        st.rerun()
        
    def reset_time():
        st.session_state.update_time = 0

    def reset_refresh_start():
        st.session_state.update_start = time.time()
        
    class plot_paras():
        def __init__(self):
            pass
        
    if st.session_state.allcalls is None:
        st.stop()
    else:
        st.write("Train data found, with ", str(len(st.session_state.allops)), "trains on this route at some point")

        if len(st.session_state.allops) == 0:
            st.error("No trains found on this route")
            st.stop()
        
        istoday = Data.plot_date.day == uk_tz.localize(datetime.datetime.today()).day
        
        refresh_flag = st.checkbox("Plot live trains (may not work well for long or busy routes)", disabled = not istoday, value = st.session_state.refresh, on_change = reset_refresh_start)

        if time.time() -  st.session_state.update_start > 900. and refresh_flag:   #Stop updating if it's been going on a while (currently 15 mins)
            st.write('**Live plotting stopped due to time limit. Uncheck and check box to restart.**')
            st.write('**If trains fail to update, please start again... This undesirable feature is due to memory limitations.**')
            st.session_state.refresh = False
            refresh_flag = False

        with st.form("Plot stuff"):
            with st.expander("Choose plot parameters"):
                if st.session_state.timeref is None:
                    
                    st.session_state.timeref = datetime.datetime(2000,1,1,datetime.datetime.now().astimezone(uk_tz).hour, datetime.datetime.now().astimezone(uk_tz).minute, 0)
            
                t0 = datetime.datetime(2000,1,1,0,0,0) .astimezone(uk_tz)
                t1 = datetime.datetime(2000,1,1,23,59,0).astimezone(uk_tz)
             
                Paras = plot_paras()
                headtypes = []
                for i in range(len(set(st.session_state.allheads))):
                    if int(list(set(st.session_state.allheads))[i][:1]) not in headtypes:
                        headtypes.append(int(list(set(st.session_state.allheads))[i][:1]))
    
                Paras.plot_up = st.checkbox("Plot trains going up", value = True)
                Paras.plot_down = st.checkbox("Plot trains going down", value = True)
                Paras.plot_rt = st.checkbox("Plot actual times", value = True)
                Paras.plot_wtt = st.checkbox("Plot scheduled times", value = True)
                Paras.reverse = st.checkbox("Reverse y axis", value = False)
    
                #Select operators
                Paras.plot_operators = st.pills("Plot operators:", list(set(st.session_state.allops)), default = list(set(st.session_state.allops)), selection_mode = "multi")
                Paras.plot_heads = st.pills("Plot headcode type:", sorted(headtypes), default = sorted(headtypes), selection_mode = "multi")
                Paras.aspect = st.slider("Aspect ratio", min_value = 0.25, max_value = 2., value = 1.0,step = (0.05), format = "%.2f")
                Paras.write_headcode = st.checkbox("Show headcodes", value = False)
                Paras.write_traincode = st.checkbox("Show RTT codes", value = False)
    
                init_minval = max(t0, st.session_state.timeref.astimezone(None) - datetime.timedelta(hours = 1.5))
                init_maxval = min(t1, st.session_state.timeref.astimezone(None) + datetime.timedelta(hours = 1.5))
                
                init_minval = init_minval.astimezone(uk_tz)
                init_maxval = init_maxval.astimezone(uk_tz)

                trange_min, trange_max = st.slider("Time range (if not showing live trains):", min_value = t0, max_value = t1, value = (init_minval, init_maxval), format = "HH:mm")
                Paras.xmin = trange_min.hour*60 + trange_min.minute; Paras.xmax = trange_max.hour*60 + trange_max.minute
                Paras.xmin = min(Paras.xmin, 24*60 - 30)
                Paras.xmax = max(Paras.xmax, Paras.xmin + 30)
                if istoday:
                    #dot_time = st.slider("Time to plot RT until", min_value = t0, max_value = t1, value = st.session_state.timeref, format = "HH:mm")
                    dot_time = datetime.datetime.now().astimezone(uk_tz)
                    Paras.dot_time = dot_time.hour*60 + dot_time.minute - 1
                else:
                    #dot_time = st.slider("Time to plot RT until", min_value = t0, max_value = t1, value = t1, format = "HH:mm")
                    dot_time = t1
                    Paras.dot_time = dot_time.hour*60 + dot_time.minute
                
            st.form_submit_button("Update Plot", on_click = reset_time)

        if abs(Paras.xmin - max(0, Paras.dot_time - 90)) > 1.0:
            st.session_state.paras_chosen = True
                
        if refresh_flag:
            #Need to update trains then do the above, but specify a load of the parameters
            update_train_data(Data)
            dot_time = datetime.datetime.now().astimezone(uk_tz)
            Paras.dot_time = dot_time.hour*60 + dot_time.minute + dot_time.second/60.0
            Paras.xmin = max(0, Paras.dot_time - 90); Paras.xmax = min(Paras.dot_time + 90, 60*24)
            st.session_state.paras_chosen = False

        #plot_trains(Paras, save = True)   #For use when the bug handler is being unhelpful
        try:
            plot_trains(Paras, save = True)   #Saves to a temporary location by default
        except:
            st.error("Plotting failed for some reason... Sorry. Trying again in a second.")
            time.sleep(0.01)
            st.rerun()
            
        del Paras   #Try to do some clearing up...
        del Data

        fname = './tmp/%s_%s.png' % (st.session_state.linepts[0], st.session_state.linepts[-1])
        fname_local = '%s_%s.png' % (st.session_state.linepts[0], st.session_state.linepts[-1])
        if os.path.exists(fname):
            with open(fname, "rb") as img:
                st.download_button(label="Download high-resolution plot (may not be fast...)", file_name = fname_local,  data=img,mime="image/png")
            os.remove(fname)     
        st.session_state.update_time = time.time()

        if refresh_flag:
            while time.time() - st.session_state.update_time < 30.0:
                time.sleep(1.0)
            st.rerun()
            
        del img
        
if __name__ == "__main__":
    run()









