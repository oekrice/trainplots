# -*- coding: utf-8 -*-
"""
Created on Thu Mar 13 23:22:56 2025

@author: eleph
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
import streamlit as st
from matplotlib.collections import LineCollection

def plot_train(call_set, operator, headcode, dot_time, fig, alllines, allcolors, rt_flag = False):
    #Adds an individual train to the plot
    colour = 'black'
    if operator == 'GR':
        colour = 'red'
    elif operator == 'TP':
        colour = 'turquoise'
    elif operator == 'XC':
        colour = 'brown'
    elif operator == 'NT':
        colour = 'purple'
    elif operator == 'ZZ':
        colour = 'darkgoldenrod'
    elif operator == 'LD':
        colour = 'darkblue'
    elif operator == 'GC':
        colour = 'black'
    elif operator == 'GN':
        colour = 'lightblue'
    elif operator == 'HT':
        colour = 'green'
    elif operator == 'EM':
        colour = 'purple'
    elif operator == 'TL':
        colour = 'grey'
    elif operator == 'LE':
        colour = 'lightgreen'
    elif operator == 'SR':
        colour = 'blue'
    elif operator == 'CS':
        colour = 'brown'
    elif operator == 'VT':
        colour = 'grey'
    elif operator == 'MV':
        colour = 'black'
    elif operator == 'WR':
        colour = 'brown'
    elif operator == 'ME':
        colour = 'yellow'
    elif operator == 'LM':
        colour = 'mediumseagreen'
    elif operator == 'AW':
        colour = 'red'
    elif operator == 'SE':
        colour = 'blue'
    elif operator == 'ES':
        colour = 'black'
    elif operator == 'SW':
        colour = 'red'
    elif operator == 'LO':
        colour = 'orange'
    elif operator == 'SN':
        colour = 'green'
    elif operator == 'GX':
        colour = 'lightblue'
    elif operator == 'LT':
        colour = 'blue'
    elif operator == 'LS':
        colour = 'brown'
    elif operator == 'GW':
        colour = 'darkgreen'
    elif operator == 'LR':
        colour = 'orange'
    elif operator == 'XR':
        colour = 'purple'
    elif operator == 'HX':
        colour = 'blue'
    if operator == 'ZZ' and not rt_flag:
        return
        #colour = 'black'
    #Determine shape from headcode
    train_type = int(headcode[0])
    if train_type == 1 or train_type == 9:
        shape = 'D'
        max_speed = 2.0
        min_speed = 0.5
    elif train_type == 2:
        shape = 'o'
        max_speed = 1.5
        min_speed = 0.5

    elif train_type == 5 or train_type == 3:
        shape = 'p'
        if train_type == 5:
            max_speed = 2.0
        else:
            max_speed = 1.5
        min_speed = 0.5

    else:
        shape = 's'
        max_speed = 1.0
        min_speed = 0.5

    def ttox(t):  
        #Converts time into minutes since midnight
        if t >= 0:
            return (t//100)*60 + t - 100*(t//100)
        else:
            return t
        
    def plotbit(xls, yls, bc1, bc2, fig, rt_flag, alllines, allcolors):
        
        res = max(10, 4*int((xls[-1] - xls[0])))   #Points to interpolate in time (smoooooth)
        
        #Check in bounds.
        dot = False; dot_ind = -1
        if dot_time < xls[0]:
            return 
        elif dot_time < xls[-1]:
            xis = np.linspace(xls[0], xls[-1], res*5)
            dot_ind = int(res*5*(dot_time - xls[0])/(xls[-1] - xls[0]))
            dot = True
        else:
            xis = np.linspace(xls[0], xls[-1], res)

        if len(yls) == 2 and yls[1] == yls[0]:   #Train is stationary
            if dot:
                xls[-1] = dot_time
            #plt.plot(xls,yls, c= colour, linewidth = lw, alpha = alpha, zorder = order)
            alllines.append(np.column_stack((xls, yls))); allcolors.append(colour)
            if dot:
                plt.scatter(dot_time, yls[0], zorder= 100, c= colour, edgecolor = 'black', s = 50, marker = shape)
        else:
            try:
                yinterp = CubicSpline(xls, yls, bc_type=((bc1 + 1, 0.0), (bc2 + 1, 0.0)))
            except:
                return
            
            yis = yinterp(xis)                
                
            if dot_ind < 0:
                #plt.plot(xis, yis, c= colour, linewidth = lw, alpha = alpha, zorder = order)
                alllines.append(np.column_stack((xis, yis))); allcolors.append(colour)
            else:
                #plt.plot(xis[:dot_ind], yis[:dot_ind], c= colour, linewidth = lw, alpha = alpha, zorder = order)
                alllines.append(np.column_stack((xis[:dot_ind], yis[:dot_ind]))); allcolors.append(colour)

            if dot:
                plt.scatter(dot_time, yinterp(dot_time), zorder = 100, c= colour, edgecolor = 'black', s = 50, marker = shape)

        return
    

    if len(call_set) > 1 and call_set[0][2] > 0:
                                
        if call_set[0][1] < 0 and call_set[0][2] < 0:
            return
        
        
        def startend(calls):
            #Gives start and end time for the set of calls
            start = calls[0][2]%100 + 60*(calls[0][2]//100) 
            if calls[-1][1] >= 0:
                end = calls[-1][1]%100 + 60*( calls[-1][1]//100)
            else:
                end = calls[-1][2]%100 + 60*( calls[-1][2]//100)
            return start,end

        #Establish new method of plotting things
        start, end = startend(call_set)
        
        if start == end:
            #Not sure what's happened here, just ignore
            return
        
        if  st.session_state.linedists is None:
            #linedists_plot = np.arange(len(st.session_state.linepts))
            linedists_plot = st.session_state.linetimes
        else:
            linedists_plot = st.session_state.linedists
        avg_speed = abs(linedists_plot[st.session_state.linepts.index(call_set[-1][0])] - linedists_plot[st.session_state.linepts.index(call_set[0][0])]) / (end - start) #Avg. speed in miles per minute
        
        #Run through calls and change if necessary
        #Pretend there are stops if it's slow, and adjust timings to average if too fast
        dists = []; stops = []; xas = []; xds = []
        
        for i in range(len(call_set[:])):
            dists.append(linedists_plot[st.session_state.linepts.index(call_set[i][0])])
            xas.append(ttox(call_set[i][1]))
            xds.append(ttox(call_set[i][2]))

            isstop = 0
            #establish if it is a stop
            if call_set[i][1] > 0.:   #If an arrival time is logged then there was a stop
                isstop = 1
            elif i == 0 and call_set[i][1] == -2:   #Train starts here
                isstop = 1
            elif i == len(call_set) - 1 and call_set[i][2] == -2:   #Train ends here
                isstop = 1
            stops.append(isstop)

            #Establish stops that aren't really but may as well be
            if i > 0:
                if xds[-1] != xds[-2]: #Would give divzero error -- don't want that (sort out in a minute)   
                    #Choose what to do based on stops around the fact                
                    if abs(dists[-1] - dists[-2])/(xds[-1] - xds[-2]) < min_speed:
                        if st.session_state.diag_flag:
                            print('too slow 1')
                        #Too slow between successive departures/passes
                        if stops[-2] == 0:
                            stops[-1] = 1
                            xas[-1] = xds[-2] + abs(dists[-1] - dists[-2])/max(avg_speed, min_speed*2)
                        else:
                            xds[-2] = xas[-1] - abs(dists[-1] - dists[-2])/max(avg_speed, min_speed*2)
                        #stops[-2] = 1
                        #Put in a fake arrival time if necessary
                        if xas[-1] < 0:
                            xas[-1] = xds[-1]
                        if xas[-2] < 0:
                            xas[-2] = xds[-2]
                         
                if xas[-1] != xds[-2]: #Would give divzero error -- don't want that (sort out in a minute)   

                    if xas[-1] > 0:
                        if st.session_state.diag_flag:
                            print('too slow 2')

                        #Too slow between a departure and next arrival
                        if abs(dists[-1] - dists[-2])/(xas[-1] - xds[-2]) < min_speed:
                            
                            if stops[-2] == 0:
                                stops[-1] = 1
                                xas[-1] = xds[-2] + abs(dists[-1] - dists[-2])/max(avg_speed, min_speed*2)
                            else:
                                xds[-2] = xas[-1] - abs(dists[-1] - dists[-2])/max(avg_speed, min_speed*2)

                            if xas[-1] < 0:
                                xas[-1] = xds[-1]
                            if xas[-2] < 0:
                                xas[-2] = xds[-2]

            #If stop is too quick, adjust it. Stops weird things happening with the cubics
            if i > 0:
                if xds[-1] - xds[-2] < 0.1 and xds[-1] > 0:  #Sucessive departures too close
                    xds[-1] = xds[-2] + abs(dists[-1] - dists[-2])/max_speed

                elif xas[-1] > 0 and xas[-1] - xds[-2] < 0.1:   #Next arrival too close to departure
                    xas[-1] = xds[-2] + abs(dists[-1] - dists[-2])/max_speed
                    if xds[-1] < xas[-1]:
                        xds[-1] = xas[-1]

                elif xds[-1] > 0 and ((dists[-1] - dists[-2])/(xds[-1] - xds[-2])) > max_speed*1.25:  #Departs next too fast
                    xds[-1] = xds[-2] + abs(dists[-1] - dists[-2])/max_speed

                elif xas[-1] > 0 and ((dists[-1] - dists[-2])/(xas[-1] - xds[-2])) > max_speed*1.25:  #Arrives there too fast
                    xas[-1] = xds[-2] + abs(dists[-1] - dists[-2])/max_speed
                    if xds[-1] < xas[-1]:
                        xds[-1] = xas[-1]
                
            
        
        #Now slice in between the stops. Run through and check where they are. 
        #BC flags 0 for default, 1 for enter at speed and 2 for leave at speed
        k1 = 0; k2 = 1; bc1 = 0; bc2 = 0
        if xds[0] >= 0.0 and xas[0] >= 0.0:   #Starts with the train stopped -- plot as a straight line
            if abs(xds[0] - xas[0]) > 0.1:  #
                plotbit([xas[0],xds[0]],[dists[0], dists[0]], 0, 0, fig, rt_flag, alllines, allcolors)
                
        while k2 < len(stops):
            if stops[k2] == 1:   #Is a stop, do a plot.
                bc1 = 0; bc2 = 0
                if k1 == 0 and stops[k1] == 0:
                    bc1 = 1
                
                plotbit(xds[k1:k2] + [xas[k2]], dists[k1:k2+1], bc1, bc2, fig, rt_flag, alllines, allcolors)
                k1 = k2 
                
                #Plot line for when train is stationary. Can put end ones on as well?
                if xds[k2] >= 0.0 and xas[k2] >= 0.0:
                    if abs(xds[k2] - xas[k2]) > 0.1:
                        plotbit([xas[k2],xds[k2]],[dists[k2], dists[k2]], 0, 0, fig, rt_flag, alllines, allcolors)
                
            k2 += 1
            
        if stops[-1] == 0:   #Finish off last bit (though it's in motion)

            k2 = len(stops)
            bc2 = 1
            if k1 == 0 and stops[k1] == 0:   #Train NEVER stops
                bc1 = 1
            else:
                bc1 = 0   #Starts stopped

            plotbit(xds[k1:k2], dists[k1:k2], bc1, bc2, fig, rt_flag, alllines, allcolors)
            #print(bc1, bc2, xds[k1:k2], dists[k1:k2])

    return 




def plot_trains(Paras, counter = -1, save = False):
    
    dot_time = Paras.dot_time#xmin + 0.75*(xmax - xmin)
    #This is tricky...
    if st.session_state.linedists is not None:
        yrange = np.max(st.session_state.linedists) - np.min(st.session_state.linedists)
    else:
        yrange = len(st.session_state.linepts)*3   #Times some undetermined factor
        
    ysize = max(5, yrange/10)
    xsize = max(7.5, (Paras.xmax-Paras.xmin)/12.5)
    fig = plt.figure(figsize = (xsize*Paras.aspect,ysize))
    #Establish y axis distances/labels. If no distance data just use integers. 
    #Shame that distance data isn't universal but meh. Could perhaps bodge later?
    yticks = []
    ylabels = []
    
    if  st.session_state.linedists is None:
        #linedists_plot = np.arange(len(st.session_state.linepts))
        linedists_plot = st.session_state.linetimes
    else:
        linedists_plot = st.session_state.linedists

    for i in range(len(st.session_state.linepts)):
        if len(st.session_state.linepts[i]) == 3 and st.session_state.linepts[i][0] != 'X':
            ylabels.append(st.session_state.linepts[i])
            yticks.append(linedists_plot[i])
            #plt.plot([-60,25*60], [linedists[i], linedists[i]], c= 'grey', alpha = 1.0, linewidth = 1.0)    
            
    plt.gca().set_yticks(yticks)
    # Set ticks labels for x-axis
    plt.gca().set_yticklabels(ylabels, fontsize = 8.0)   
    
    tlabels = []
    
    if False:  #Plot hours
        plt.gca().set_xticks(np.linspace(0,1440,25))

        for i in range(25):
            tlabels.append('%d:00' % i)
    else:
        plt.gca().set_xticks(np.linspace(0,1440,4*24+1))

        for i in range(24):
            tlabels.append('%02d:00' % i)
            for j in range(3):
                tlabels.append('%02d:%02d' % (i, j * 15 + 15))
        tlabels.append('%02d:00' % 0)

    plt.gca().set_xticklabels(tlabels, rotation='vertical')
    
    def startend(calls_test):
        #Gives start and end time for the set of calls
        start = calls_test[0][2]%100 + 60*(calls_test[0][2]//100) 
        if calls_test[-1][2] == -2:
            end = calls_test[-1][1]%100 + 60*( calls_test[-1][1]//100)
        else:
            end = calls_test[-1][2]%100 + 60*( calls_test[-1][2]//100)
        return start,end
        
    alllines = []; allcolors = []
    if Paras.plot_wtt:
        for k in range(len(st.session_state.allcalls)):
            
            if st.session_state.linepts.index(st.session_state.allcalls[k][-1][0]) > st.session_state.linepts.index(st.session_state.allcalls[k][0][0]):
                up = False
            else:
                up = True
                
            start, end = startend(st.session_state.allcalls[k])
            
            if (up and Paras.plot_up) or (not up and Paras.plot_down):
                if Paras.xmin < end and Paras.xmax > start:
                    if st.session_state.allops[k] in Paras.plot_operators and int(st.session_state.allheads[k][:1]) in Paras.plot_heads:
                        plot_train(st.session_state.allcalls[k], st.session_state.allops[k], st.session_state.allheads[k], 1e6, fig, alllines, allcolors, rt_flag = not(Paras.plot_rt))
    
        if not(Paras.plot_rt):
            line_collection = LineCollection(alllines, colors=allcolors, linewidths=2.5, alpha = 1.0)
        else:
            line_collection = LineCollection(alllines, colors=allcolors, linewidths=2.5, alpha = 0.1)
        plt.gca().add_collection(line_collection)

    alllines = []; allcolors = []
    if Paras.plot_rt:
        #print('_________________________-')
        for k in range(len(st.session_state.allcalls_rt)):
            st.session_state.diag_flag = False
            start = 'TRHFGDFGB'
            mint = 1520; maxt = 1530
            if st.session_state.allcalls_rt[k][0][0] == start:
                if st.session_state.allcalls_rt[k][0][2] > mint and st.session_state.allcalls_rt[k][0][2] < maxt:
                    print(st.session_state.allcalls_rt[k])
                    st.session_state.diag_flag = True
            
            if st.session_state.linepts.index(st.session_state.allcalls_rt[k][-1][0]) > st.session_state.linepts.index(st.session_state.allcalls_rt[k][0][0]):
                up = False
            else:
                up = True
    
            start, end = startend(st.session_state.allcalls_rt[k])
            

            if (up and Paras.plot_up) or (not up and Paras.plot_down):
            #if allops_rt[k] == 'ZZ' and allcalls_rt[k][0][2] > 300 and allcalls_rt[k][0][2] < 330:
                if Paras.xmin < end and Paras.xmax > start:
                    if (st.session_state.allops_rt[k] in Paras.plot_operators) and (int(st.session_state.allheads_rt[k][:1]) in Paras.plot_heads):

                        plot_train(st.session_state.allcalls_rt[k], st.session_state.allops_rt[k], st.session_state.allheads_rt[k], dot_time, fig, alllines, allcolors, rt_flag = True)
        line_collection = LineCollection(alllines, colors=allcolors, linewidths=2.5, alpha = 1.0)
        plt.gca().add_collection(line_collection)
            #plot_train(linepts, linedists, allcalls_rt[k], allops_rt[k], allheads_rt[k], dot_time, fig, rt_flag = True)

        
    plt.xlim(Paras.xmin,Paras.xmax)
    tickrange = yticks[-1] - yticks[0]
    plt.ylim(yticks[-1] + tickrange*0.1, yticks[0] - tickrange*0.1)
    if Paras.reverse:
        plt.gca().invert_yaxis()

    st.pyplot(fig)
    if save:
        plt.savefig('./tmp/%s_%s.png' % (st.session_state.linepts[0], st.session_state.linepts[-1]), dpi = 150)
    plt.clf()
    plt.close()
    #plt.close()
    
