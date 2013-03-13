###############################################################################
import time
from Tkinter import *
from numpy import array

from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties

from automat.core.plotting.tk_embedded_plots import EmbeddedFigure
################################################################################
DEFAULT_SUPTITLE = "Unknown Sample"
FIGSIZE = (9,5)
LABEL_FONT_SIZE  = 8
LABEL_FONT_PROP  = FontProperties(size=LABEL_FONT_SIZE)
LEGEND_FONT_PROP = FontProperties(size=6)

################################################################################
class DataPlotter(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.figure_widget = EmbeddedFigure(self, figsize=FIGSIZE)
        self.setup()

    def pack(self, **kwargs):
        self.figure_widget.pack(side='right',fill='both', expand='yes')
        Frame.pack(self,**kwargs)

    def setup(self):
        figure = self.figure_widget.get_figure()
        figure.clear()
        self.suptitle = figure.suptitle(DEFAULT_SUPTITLE)
        #temperature plot
        self.plot_ax1 = ax1 = figure.add_subplot(311)
        self.plot_line0, = ax1.plot([],[],'r-', label="measurementA")
        self.plot_line1, = ax1.plot([],[],'b-', label="measurementB")
        self.plot_line2, = ax1.plot([],[],'m-', label="measurementC")
        ax1.set_ylabel("Temperature ($^{\circ}$C)", fontproperties=LABEL_FONT_PROP)
        #setpoint plot
        self.plot_line3, = ax1.plot([],[],'r--', label="setpointA")
        self.plot_line4, = ax1.plot([],[],'b--', label="setpointB")
        #finish formatting the first axes
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 30)
        ax1.get_xaxis().set_ticklabels([])
        ax1.tick_params(axis='both', which='major', labelsize=LABEL_FONT_SIZE)
        ax1.tick_params(axis='both', which='minor', labelsize=LABEL_FONT_SIZE-2)

        #PID output
        self.plot_ax2 = ax2 = figure.add_subplot(312)
        self.plot_line5, = ax2.plot([],[],'r-', label="Chan A")
        self.plot_line6, = ax2.plot([],[],'b-', label="Chan B")
        ax2.set_ylabel("PID Output (duty cycle)", fontproperties=LABEL_FONT_PROP)
        #finish formatting the second axes
        ax2.set_xlim(0, 1)
        ax2.set_ylim(-1.1, 1.1)
        ax2.get_xaxis().set_ticklabels([])
        ax2.tick_params(axis='both', which='major', labelsize=LABEL_FONT_SIZE)
        ax2.tick_params(axis='both', which='minor', labelsize=LABEL_FONT_SIZE-2)
        #Voltage 
        self.plot_ax3 = ax3 = figure.add_subplot(313)
        self.plot_line7, = ax3.plot([],[],'c-')
        #finish formatting the third axes
        #ax3.set_xlabel("Time (seconds)", fontproperties=LABEL_FONT_PROP)
        ax3.set_ylabel("Voltage", fontproperties=LABEL_FONT_PROP)
        ax3.set_xlim(0, 1)
        ax3.set_ylim(-0.5, 0.5)
        ax3.tick_params(axis='both', which='major', labelsize=LABEL_FONT_SIZE)
        ax3.tick_params(axis='both', which='minor', labelsize=LABEL_FONT_SIZE-2) 
        self.figure_widget.update()

    def update(self, data):
        t = array(data['timestamp'])
        if len(t) == 0:  #skip update for empty data
            return
        t -= t[0]
        #Temperature Plot
        #line 0
        y0 = array(data['temperatureA_measured'])
        self.plot_line0.set_xdata(t)
        self.plot_line0.set_ydata(y0)
        #line 1
        y1 = array(data['temperatureB_measured'])
        self.plot_line1.set_xdata(t)
        self.plot_line1.set_ydata(y1)
        #line 2
        y2 = array(data['temperatureC_measured'])
        self.plot_line2.set_xdata(t)
        self.plot_line2.set_ydata(y2)
        #line 3
        y3 = array(data['temperatureA_target'])
        self.plot_line3.set_xdata(t)
        self.plot_line3.set_ydata(y3)
        #line 4
        y4 = array(data['temperatureB_target'])
        self.plot_line4.set_xdata(t)
        self.plot_line4.set_ydata(y4)
        #adjust the plot window
        y_min = min(y0.min(),y1.min(),y2.min(), y3.min(), y4.min())
        y_max = max(y0.max(),y1.max(),y2.max(), y3.max(), y4.max())
        self.plot_ax1.set_ylim(y_min*0.9, y_max*1.1,) 
        self.plot_ax1.set_xlim(0,t[-1]*1.1)
        self.plot_ax1.legend(loc="upper left", prop = LEGEND_FONT_PROP)
        #PID output plot
        y5 = array(data['chanA_output'])
        self.plot_line5.set_xdata(t)
        self.plot_line5.set_ydata(y5)
        y6 = array(data['chanB_output'])
        self.plot_line6.set_xdata(t)
        self.plot_line6.set_ydata(y6)
        self.plot_ax2.set_xlim(0, t[-1]*1.1)
        self.plot_ax2.legend(loc="upper left", prop = LEGEND_FONT_PROP)
        #obtain voltage
        y7 = array(data['voltage'])
        self.plot_line7.set_xdata(t)
        self.plot_line7.set_ydata(y7)
        y_min = y7.min()
        y_max = y7.max()
        if y_min < 0:
            y_min *= 1.1
        else:
            y_min *= 0.9
        if y_max > 0:
            y_max *= 1.1
        else:
            y_max *= 0.9
        self.plot_ax3.set_ylim(y_min, y_max,) 
        self.plot_ax3.set_xlim(0, t[-1]*1.1)
        #done        
        self.figure_widget.update()

    def change_title(self, new_title):
        figure = self.figure_widget.get_figure()       
        figure.texts.remove(self.suptitle)
        self.suptitle = figure.suptitle(new_title)
        self.figure_widget.update()
