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

from datetime import timedelta, date
from functions import find_line_info, station_name, station_code, find_all_trains, find_train_data, find_trains_pts
from plot_functions import plot_trains
import time

import pandas as pd
import numpy as np
import time as time_module

LOGGER = get_logger(__name__)

class all_data():
    #Contains some things
    def __init__(self):
        self.stations = pd.read_csv("stations.csv")
        
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
if "linepts" not in st.session_state:
    st.session_state.linepts = None
if "linedists" not in st.session_state:
    st.session_state.linedists = None
    
    
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
        Then time and things should follow relatively easily.
        """
    )

    select_type = st.pills("Specify stations or specific train using RTT number?", options = ["Stations", "RTT Number"], default = "Stations")
    Data = all_data()
    #Establish the first train to use
    if select_type == "RTT Number":
        rtt_code = st.text_input("Input RTT code (eg. P13795)")
        if rtt_code == '':
            st.stop()
        init_date = st.date_input("Date this train happened", value ="today", min_value = date.today() - timedelta(days = 7), max_value = date.today())
        init_url = "https://www.realtimetrains.co.uk/service/gb-nr:" + rtt_code + '/' + str(init_date) + '/detailed#allox_id=0'
        Data.linepts, Data.linedists = find_line_info(Data, init_url, init = True, unspecified = False)
        
        #Options for plotting: Generate as a list (useful for later anyway, probably)
        station_names = []; station_inds = []
        for si, stat in enumerate(Data.linepts):
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
            Data.linepts = Data.linepts[start_ind:end_ind + 1]
            Data.linedists = Data.linedists[start_ind:end_ind + 1]
        else:
            Data.linepts = Data.linepts[end_ind:start_ind + 1][::-1]
            Data.linedists = Data.linedists[end_ind:start_ind + 1][::-1]
        st.session_state.linepts = Data.linepts; st.session_state.linedists = Data.linedists

    else:
        cols = st.columns(2)
        init_date = date.today()

        with cols[0]:
            start_name = st.selectbox("Start station", Data.stations["stationName"], index = 1690, on_change = reset_route, key = 24556567)
            start_code = station_code(Data,start_name)
        with cols[1]:
            end_name = st.selectbox("End station", Data.stations["stationName"], index = 2620, on_change = reset_route, key = 4568934)
            end_code = station_code(Data,end_name)
            
        if st.button("Find suitable route", on_click = reset_route):
            rtt_code, linepts, linedists = find_trains_pts(Data, init_date, start_code, end_code)
            st.session_state.linepts = linepts; st.session_state.linedists = linedists

            if len(st.session_state.linepts) == 0:
                st.error("No train found travelling between these stations. Try reversing the order maybe?")
                st.stop()
            elif len(st.session_state.linepts) == 0:
                st.write("Suitable route found, but with no distance information. Plots may look a little off.")
            else:
                st.write("Suitable route and distance information found for this choice.")
            init_url = "https://www.realtimetrains.co.uk/service/gb-nr:" + rtt_code + '/' + str(init_date) + '/detailed#allox_id=0'
       
            #DO need to trim here...
            #start_ind = station_inds[station_names.index(start_name)]
            #end_ind = station_inds[station_names.index(end_name)]

            Data.linepts, Data.linedists = find_line_info(Data, init_url, init = True, unspecified = True)
            #Options for plotting: Generate as a list (useful for later anyway, probably)
            start_ind = Data.linepts.index(start_code); end_ind = Data.linepts.index(end_code)
            if start_ind < end_ind:
                Data.linepts = Data.linepts[start_ind:end_ind + 1]
                Data.linedists = Data.linedists[start_ind:end_ind + 1]
            else:
                Data.linepts = Data.linepts[end_ind:start_ind + 1][::-1]
                Data.linedists = Data.linedists[end_ind:start_ind + 1][::-1]
            st.session_state.linepts = Data.linepts; st.session_state.linedists = Data.linedists

    with st.expander("View all waypoints on this route:"):
        st.write(np.array(st.session_state.linepts))
    
    if st.session_state.linepts is None:
        st.stop()
        
    if len(st.session_state.linepts) == 0:
        st.stop()
        
    Data.linepts = st.session_state.linepts; Data.linedists = st.session_state.linedists
    Data.plot_date = st.date_input("Date to plot", value ="today", min_value = date.today() - timedelta(days = 7), max_value = date.today())
    
    if st.button("Find all trains on this route"):
        st.write("Finding all trains on this route on the selected day.")

        st.session_state.all_trains = find_all_trains(Data)
        st.rerun()    
        
    if st.session_state.all_trains is None:
        st.stop()
    else:
        st.write(str(len(st.session_state.all_trains)), ' trains found')
        
    #Train IDs found. Attempt to find info for them...
    if st.button("Find all train info (may take a minute or two)"):
        st.write("Finding train info...")
        find_train_data(Data)
        st.rerun()
        
    class plot_paras():
        def __init__(self):
            pass
        
            
    if st.session_state.allcalls is None:
        st.stop()
    else:
        st.write("All data found, with ", str(len(st.session_state.allops)), "trains on this route to some degree")
        with st.expander("Choose plot parameters:"):
            if st.session_state.timeref is None:
                today = date.today()
                st.session_state.timeref = time_module.time() - time_module.mktime(today.timetuple())
            current_time = st.session_state.timeref/60
            
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
            Paras.aspect = st.slider("Aspect ratio", min_value = 0.5, max_value = 2., value = 1.0,step = (0.05))

            trange_min, trange_max = st.slider("Time range (hours):", min_value = 0., max_value = 24., value = (max(0., current_time/60. - 2.), min(24., current_time/60. + 2.)),step = (1/12))
            Paras.xmin = trange_min*60; Paras.xmax = trange_max*60
            Paras.dot_time = st.slider("Time to plot RT until (hours)", min_value = 0., max_value = 24., value = current_time/60 - 0.1,step = (1/12))*60

        plot_trains(Paras, counter = -1)

if __name__ == "__main__":
    run()









