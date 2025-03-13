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
from functions import find_line_info, station_name, find_all_trains, find_train_data

import pandas as pd
import numpy as np

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
    
def reset_route():
    st.session_state.all_trains = None
    st.session_state.allcalls = None
    st.session_state.allops = None
    st.session_state.allcalls_rt = None
    st.session_state.allops_rt = None
    st.session_state.allheads = None
    st.session_state.allheads_rt = None
    
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

    select_type = st.pills("Use RTT code or start and end stations?", options = ["RTT Number", "Stations"])
    Data = all_data()
    #Establish the first train to use
    if select_type == "RTT Number":
        rtt_code = st.text_input("Input RTT code (eg. P13795)")
        init_date = st.date_input("Date this train happened", value ="today", min_value = date.today() - timedelta(days = 7), max_value = date.today())
        init_url = "https://www.realtimetrains.co.uk/service/gb-nr:" + rtt_code + '/' + str(init_date) + '/detailed#allox_id=0'
    else:
        st.write("Not done this yet")
        st.stop()
        
    Data.linepts, Data.linedists = find_line_info(Data, init_url, init = True)
    
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

    with st.expander("View all waypoints to plot:"):
        st.write(np.array(Data.linepts))
    
    Data.plot_date = st.date_input("Date to plot", value ="today", min_value = date.today() - timedelta(days = 7), max_value = date.today(), on_change = reset_route)

    if st.button("Find all trains on this route"):
        find_all_trains(Data)
        st.rerun()    
        
    if st.session_state.all_trains is None:
        st.stop()
    else:
        st.write(str(len(st.session_state.all_trains)), ' trains found')
        
    #Train IDs found. Attempt to find info for them...
    if st.button("Find all train info (may take a minute or two with no updates)"):
        st.write("Finding train info... Be patient -- things are happening.")
        find_train_data(Data)
        st.rerun()
        
    if st.session_state.allcalls is None:
        st.stop()
    else:
        st.write("All train data found with ", str(len(st.session_state.allops)), "on the route to some degree")
        st.write("Choose plot parameters:")

if __name__ == "__main__":
    run()









