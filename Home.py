# Copyright 2018-2022 Streamlit Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st
from streamlit.logger import get_logger

import datetime
from functions import find_line_info, station_name, station_code, find_all_trains, find_train_data, find_trains_pts
from plot_functions import plot_trains
import time
import os
import io

import pandas as pd
import numpy as np
import time as time_module

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
if "allcalls_rt" not in st.session_state:
    st.session_state.allcalls_rt = None
if "allops_rt" not in st.session_state:
    st.session_state.allops_rt = None
if "allheads" not in st.session_state:
    st.session_state.allheads = None
if "allheads_rt" not in st.session_state:
    st.session_state.allheads_rt = None
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

def reset_trains():
    st.session_state.all_trains = None
    st.session_state.allcalls = None
    st.session_state.allops = None
    st.session_state.allcalls_rt = None
    st.session_state.allops_rt = None
    st.session_state.allheads = None
    st.session_state.allheads_rt = None
    st.session_state.found_alltrains = False
    
if not os.path.exists('./tmp/'):
    os.mkdir('./tmp/')
    
def run():
    st.set_page_config(
        page_title="Home",
        page_icon="🏠",
    )

    st.write("# Train Location Plotting")

    #st.sidebar.success("Select a demo above.")

    st.markdown(
        """
        Making line plots of train positions, using live data from RealTimeTrains.
        Choose what to plot either by specifying a train on a certain date, or two stations which have trains running between them.
        'Live' features to follow when I can figure out a way of speeding certain things up.
        """
    )

    select_type = st.pills("Specify stations or specific train using RTT number?", options = ["Stations", "RTT Number"], default = "Stations")
    
    @st.cache_data
    def get_data():
        Data = all_data()
        return Data
        
    Data = get_data()
    #Establish the first train to use
    if select_type == "RTT Number":
        rtt_code = st.text_input("Input RTT code (eg. P13795)")
        if rtt_code == '':
            st.stop()
        init_date = st.date_input("Date this train happened", value ="today", min_value = datetime.date.today() - datetime.timedelta(days = 7), max_value = datetime.date.today(), on_change = reset_route)
        init_url = "https://www.realtimetrains.co.uk/service/gb-nr:" + rtt_code + '/' + str(init_date) + '/detailed#allox_id=0'
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
        init_date = datetime.date.today()

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

            init_url = "https://www.realtimetrains.co.uk/service/gb-nr:" + rtt_code + '/' + str(init_date) + '/detailed#allox_id=0'
       
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
        st.write("Suitable route and distance information found for this choice.")

    if st.session_state.linedists is not None:
        st.session_state.linedists = st.session_state.linedists - np.min(st.session_state.linedists)
        
    if st.session_state.linepts is None:
        st.stop()

    with st.expander("View all waypoints on this route:"):
        if st.session_state.linedists is not None:
            st.write(np.vstack((st.session_state.linepts, st.session_state.linedists)).T)
        else:
            st.write(np.array(st.session_state.linepts))
        
    Data.plot_date = st.date_input("Date to plot", value ="today", min_value = datetime.date.today() - datetime.timedelta(days = 7), max_value = datetime.date.today(), on_change = reset_trains)
    
    if st.button("Find all trains on this route on this day", disabled = st.session_state.all_trains != None):
        st.write("Finding all trains...")

        st.session_state.all_trains = find_all_trains(Data)
        st.rerun()    
        
    if st.session_state.all_trains is None:
        st.stop()
    else:
        st.write(str(len(st.session_state.all_trains)), ' trains found')
        
    #Train IDs found. Attempt to find info for them...
    if st.button("Find all train info (may take a minute or two)", disabled = st.session_state.found_alltrains):
        st.write("Finding train info...")
        find_train_data(Data)
        st.rerun()
        
    class plot_paras():
        def __init__(self):
            pass
        
    if st.session_state.allcalls is None:
        st.stop()
    else:
        st.write("Train data found, with ", str(len(st.session_state.allops)), "trains on this route at some point")
        with st.form("Plot stuff"):
            with st.expander("Choose plot parameters"):
                if st.session_state.timeref is None:
                    st.session_state.timeref = datetime.datetime(2000,1,1,datetime.datetime.now().hour, datetime.datetime.now().minute, 0)
            
                t0 = datetime.datetime(2000,1,1,0,0,0) 
                t1 = datetime.datetime(2000,1,1,23,59,0)
             
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
    
                init_minval = max(t0, st.session_state.timeref - datetime.timedelta(hours = 2))
                init_maxval = min(t1, st.session_state.timeref + datetime.timedelta(hours = 2))
                trange_min, trange_max = st.slider("Time range:", min_value = t0, max_value = t1, value = (init_minval, init_maxval), format = "HH:mm")

                Paras.xmin = trange_min.hour*60 + trange_min.minute; Paras.xmax = trange_max.hour*60 + trange_max.minute
                if Data.plot_date == datetime.date.today():
                    dot_time = st.slider("Time to plot RT until", min_value = t0, max_value = t1, value = st.session_state.timeref, format = "HH:mm")
                else:
                    dot_time = st.slider("Time to plot RT until", min_value = t0, max_value = t1, value = t1, format = "HH:mm")
                Paras.dot_time = dot_time.hour*60 + dot_time.minute
                
            st.form_submit_button("Update Plot")

        plot_trains(Paras, save = True)   #Saves to a temporary location by default
        fname = './tmp/%s_%s.png' % (st.session_state.linepts[0], st.session_state.linepts[-1])
        fname_local = '%s_%s.png' % (st.session_state.linepts[0], st.session_state.linepts[-1])
        with open(fname, "rb") as img:
            st.download_button(label="Download high-resolution plot (may not be fast...)", file_name = fname_local,  data=img,mime="image/png")
        os.system('rm -r %s' % fname)        
    
if __name__ == "__main__":
    run()









