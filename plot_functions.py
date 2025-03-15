# -*- coding: utf-8 -*-
"""
Created on Thu Mar 13 23:22:56 2025

@author: eleph
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
import streamlit as st

def plot_train(call_set, operator, headcode, dot_time, fig, rt_flag = False):
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
        colour = 'orange'
    elif operator == 'LD':
        colour = 'darkblue'
    elif operator == 'GC':
        colour = 'black'
    elif operator == 'GN':
        colour = 'pink'
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
        colour = 'purple'
    elif operator == 'MV':
        colour = 'black'
    elif operator == 'WR':
        colour = 'brown'
    elif operator == 'ME':
        colour = 'yellow'
    elif operator == 'LM':
        colour = 'lightgreen'
    elif operator == 'AW':
        colour = 'lightblue'
    elif operator == 'SE':
        colour = 'blue'
    elif operator == 'ES':
        colour = 'black'
    elif operator == 'SW':
        colour = 'red'
    elif operator == 'LO':
        colour = 'red'
    elif operator == 'SN':
        colour = 'green'
    elif operator == 'GX':
        colour = 'lightblue'
    elif operator == 'LT':
        colour = 'red'
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
    order = 0
    if train_type == 1 or train_type == 9:
        shape = 'D'
        order = 10
        max_speed = 2.0
        min_speed = 0.1
    elif train_type == 2:
        shape = 'o'
        order = 2
        max_speed = 1.5
        min_speed = 0.1

    elif train_type == 5 or train_type == 3:
        shape = 'p'
        order = 5
        if train_type ==5:
            max_speed = 2.0
        else:
            max_speed = 1.5
        min_speed = 0.1

    else:
        shape = 's'
        order = 8
        max_speed = 1.0
        min_speed = 0.2

    def ttox(t):  
        #Converts time into minutes since midnight
        if t >= 0:
            return (t//100)*60 + t - 100*(t//100)
        else:
            return t
        
    def plotbit(xls, yls, bc1, bc2, fig, rt_flag):
        
        #print(tls)
        if rt_flag:
            alpha = 1
            lw = 2.5
        else:
            alpha = 0.1
            lw = 2.5
            
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
            plt.plot(xls,yls, c= colour, linewidth = lw, alpha = alpha, zorder = order)
            if dot:
                plt.scatter(dot_time, yls[0], zorder= 100, c= colour, edgecolor = 'black', s = 50, marker = shape)
        else:
            try:
                yinterp = CubicSpline(xls, yls, bc_type=((bc1 + 1, 0.0), (bc2 + 1, 0.0)))
            except:
                return
            
            yis = yinterp(xis)                
                
            if dot_ind < 0:
                plt.plot(xis, yis, c= colour, linewidth = lw, alpha = alpha, zorder = order)
            else:
                plt.plot(xis[:dot_ind], yis[:dot_ind], c= colour, linewidth = lw, alpha = alpha, zorder = order)

            if dot:
                plt.scatter(dot_time, yinterp(dot_time), zorder = 100, c= colour, edgecolor = 'black', s = 50, marker = shape)

        if printer:
            plt.scatter(xls, yls)
        return
    

    if len(call_set) > 1 and call_set[0][2] > 0:
        if st.session_state.linepts.index(call_set[-1][0]) > st.session_state.linepts.index(call_set[0][0]):
            up = 1
        else:
            up = 0
            
        printer = False
        if operator == "TL":
            if call_set[0][2] > 22 and call_set[0][2] < 24:
            #if call_set[-1][0] == "SVG" and call_set[-1][2] < 500:
                printer = False
                if printer:
                    print(call_set)
                    
        if call_set[0][1] < 0 and call_set[0][2] < 0:
            return
        
        
        #print(call_set)
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
        if len(st.session_state.linedists) == 0:
            st.session_state.linedists = np.arange(len(st.session_state.linepts))
        avg_speed = abs(st.session_state.linedists[st.session_state.linepts.index(call_set[-1][0])] - st.session_state.linedists[st.session_state.linepts.index(call_set[0][0])]) / (end - start) #Avg. speed in miles per minute
        
        #print('Avg. speed', avg_speed)   

        #Run through calls and change if necessary
        #Pretend there are stops if it's slow, and adjust timings to average if too fast
        dists = []; stops = []; xas = []; xds = []
        
        for i in range(len(call_set[:])):
            dists.append(st.session_state.linedists[st.session_state.linepts.index(call_set[i][0])])
            xas.append(ttox(call_set[i][1]))
            xds.append(ttox(call_set[i][2]))

            isstop = 0
            #establish if it is a stop
            if call_set[i][1] > 0.:   #If an arrival time is logged then there was a stop
                isstop = 1
            elif i == 0 and call_set[i][1] == -2:
                isstop = 1
            elif i == len(call_set) - 1 and call_set[i][2] == -2:
                isstop = 1
            stops.append(isstop)
            #If stop is too quick, adjust it. Stops weird things happening with the cubics
            if i > 0:
                if xds[-1] - xds[-2] < 0.1 and xds[-1] > 0:
                    xds[-1] = xds[-2] + abs(dists[-1] - dists[-2])/avg_speed

                elif xas[-1] > 0 and xas[-1] - xds[-2] < 0.1:
                    xas[-1] = xds[-2] + abs(dists[-1] - dists[-2])/avg_speed
                    if xds[-1] < xas[-1]:
                        xds[-1] = xas[-1]
                elif xds[-1] > 0 and (dists[-1] - dists[-2])/(xds[-1] - xds[-2]) > max_speed*1.25:
                    xds[-1] = xds[-2] + abs(dists[-1] - dists[-2])/avg_speed

                elif xas[-1] > 0 and (dists[-1] - dists[-2])/(xas[-1] - xds[-2]) > max_speed*1.25:
                    xas[-1] = xds[-2] + abs(dists[-1] - dists[-2])/avg_speed
                    #print(i,'Too fast 4', call_set[i][0])
                    if xds[-1] < xas[-1]:
                        xds[-1] = xas[-1]
                
            #Establish stops that aren't really but may as well be
            if i > 0:
                if abs(dists[-1] - dists[-2])/(xds[-1] - xds[-2]) < min_speed:
                    #print(i,'Too slow 1', call_set[i][0])
                    stops[-1] = 1
                    stops[-2] = 1
                    #Put in a fake arrival time if necessary
                    if xas[-1] < 0:
                        xas[-1] = xds[-1]
                    if xas[-2] < 0:
                        xas[-2] = xds[-2]
                        
                if xas[-1] > 0:
                    if abs(dists[-1] - dists[-2])/(xas[-1] - xds[-2]) < min_speed:
                        #print(i,'Too slow 2', call_set[i][0])
                        stops[-1] = 1
                        stops[-2] = 1
                        if xas[-1] < 0:
                            xas[-1] = xds[-1]
                        if xas[-2] < 0:
                            xas[-2] = xds[-2]
            
        
        #Now slice in between the stops. Run through and check where they are. 
        #BC flags 0 for default, 1 for enter at speed and 2 for leave at speed
        k1 = 0; k2 = 1; bc1 = 0; bc2 = 0
        if xds[0] >= 0.0 and xas[0] >= 0.0:
            if abs(xds[0] - xas[0]) > 0.1:
                plotbit([xas[0],xds[0]],[dists[0], dists[0]], 0, 0, fig, rt_flag)
                
        while k2 < len(stops):
            if stops[k2] == 1:   #Is a stop, do a plot.
                bc1 = 0; bc2 = 0
                if k1 == 0 and stops[k1] == 0:
                    bc1 = 1
                
                #print(call_set[k2][0], stops[k2], dists[k2], xas[k2], xds[k2], bc1, bc2)

                #print(xds[k1:k2] + [xas[k2]])
                plotbit(xds[k1:k2] + [xas[k2]], dists[k1:k2+1], bc1, bc2, fig, rt_flag)
                k1 = k2 
                
                #Plot line for when train is stationary. Can put end ones on as well?
                if xds[k2] >= 0.0 and xas[k2] >= 0.0:
                    if abs(xds[k2] - xas[k2]) > 0.1:
                        plotbit([xas[k2],xds[k2]],[dists[k2], dists[k2]], 0, 0, fig, rt_flag)
                
            k2 += 1
        if stops[-1] == 0:   #Finish off last bit (though it's in motion)
            k2 = len(stops)
            bc2 = 1
            if k1 == 0 and stops[k1] == 0:
                bc1 = 1
            else:
                bc1 = 0

            plotbit(xds[k1:k2], dists[k1:k2], bc1, bc2, fig, rt_flag)
            #print(bc1, bc2, xds[k1:k2], dists[k1:k2])

    return 




def plot_trains(Paras, counter = -1):
    
    dot_time = Paras.dot_time#xmin + 0.75*(xmax - xmin)
    #This is tricky...
    if len(st.session_state.linedists) > 0:
        yrange = np.max(st.session_state.linedists) - np.min(st.session_state.linedists)
    else:
        yrange = len(st.session_state.linepts)*3   #Times some undetermined factor
        
    fig = plt.figure(figsize = ((Paras.xmax-Paras.xmin)/12.5*Paras.aspect,yrange/10))
    #Establish y axis distances/labels. If no distance data just use integers. 
    #Shame that distance data isn't universal but meh. Could perhaps bodge later?
    yticks = []
    ylabels = []
    
    for i in range(len(st.session_state.linepts)):
        if len(st.session_state.linepts[i]) == 3 and st.session_state.linepts[i][0] != 'X':
            ylabels.append(st.session_state.linepts[i])
            if len(st.session_state.linedists) > 0:
                yticks.append(st.session_state.linedists[i])
            else:
                yticks.append(i)
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
                        plot_train(st.session_state.allcalls[k], st.session_state.allops[k], st.session_state.allheads[k], 1e6, fig, rt_flag = not(Paras.plot_rt))
    if Paras.plot_rt:
        for k in range(len(st.session_state.allcalls_rt)):
            
            if st.session_state.linepts.index(st.session_state.allcalls_rt[k][-1][0]) > st.session_state.linepts.index(st.session_state.allcalls_rt[k][0][0]):
                up = False
            else:
                up = True
    
            start, end = startend(st.session_state.allcalls_rt[k])
            if (up and Paras.plot_up) or (not up and Paras.plot_down):
            #if allops_rt[k] == 'ZZ' and allcalls_rt[k][0][2] > 300 and allcalls_rt[k][0][2] < 330:
                if Paras.xmin < end and Paras.xmax > start:
                    if (st.session_state.allops_rt[k] in Paras.plot_operators) and (int(st.session_state.allheads_rt[k][:1]) in Paras.plot_heads):

                        plot_train(st.session_state.allcalls_rt[k], st.session_state.allops_rt[k], st.session_state.allheads_rt[k], dot_time, fig, rt_flag = True)
            #plot_train(linepts, linedists, allcalls_rt[k], allops_rt[k], allheads_rt[k], dot_time, fig, rt_flag = True)

        
    plt.xlim(Paras.xmin,Paras.xmax)
    plt.ylim(yticks[-1] + 5.0, yticks[0] - 5.0)
    if not Paras.reverse:
        plt.gca().invert_yaxis()

    st.pyplot(fig)
    plt.clf()
    plt.close()
    #plt.close()
    