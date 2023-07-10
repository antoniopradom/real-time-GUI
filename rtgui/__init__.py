import struct
import tkinter as tk
import warnings
from tkinter import ttk

import matplotlib.pyplot as plt
import numpy as np
import pandas
from scipy.spatial.transform import Rotation as rot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D  # <-- Note the capitalization!


class CheckControl(tk.Frame):
    def __init__(self, parent, title, names, cmd=None, color=['red'], defaultVal=None, vertical=True, offset=0):
        """
        creates n checkboxes cluster, where n=len(names)

        :param parent: parent frome
        :type parent: tk.Frame
        :param title: Title to display
        :type title: str
        :param names: List with the name of each checkbox
        :type names: iter
        :param cmd: function to execute when checkbox is selected.
        :type cmd: function
        :param color: color (matplotlib) to use for checkboxes. If only one color provided, all checkboxes use that color
        :type color: iter
        :param defaultVal: Default value of the checkboxes. Can be either an int of a list of length(names)
        :type defaultVal: int, list
        :param vertical: Flag to create a vertical array of checkboxes. If false, the array is horizontal
        :type vertical: bool
        :param offset: offset for the corresponding row or column depending on vertical flag
        :type offset: int
        """
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.titleLabel = ttk.Label(self, text=title)
        j = 0
        if vertical:
            self.titleLabel.grid(row=j, column=offset)
        else:
            self.titleLabel.grid(row=offset, column=j)
            j += 1
        self.vals = []
        self.boxes = []
        self.names = names
        # self.ax = ax
        if len(color) != len(names):
            color = [color[0]] * len(names)
        if defaultVal is None:
            dV = [0] * len(names)
        else:
            if len(defaultVal) is not len(names):
                if len(defaultVal) is 1:
                    dV = defaultVal * len(names)
                else:
                    warnings.warn('Default values should be 1 or equal to the number of names')
                    dV = defaultVal + [''] * (len(names) - len(defaultVal))
            else:
                dV = defaultVal
        if len(color) is not len(names):
            color = color * (len(names) - len(color))
        for i, (n, co, d) in enumerate(zip(names, color, dV)):
            self.vals.append(tk.IntVar())
            self.vals[-1].set(d)
            self.boxes.append(tk.Checkbutton(self, text=n, variable=self.vals[-1], command=cmd, background=co,
                                             foreground='black'))
            if vertical:
                self.boxes[-1].grid(row=i + 1, column=offset)
            else:
                self.boxes[-1].grid(row=offset, column=i + 1)
                j += 1

    def getAllValues(self):
        """
        Returns the values of all boxes in cluster
        """
        v = [val.get() for val in self.vals]
        return v


class ConsoleFrame(tk.Frame):
    def __init__(self, parent, nLines=5, parseCMD=None):
        """
        Creates a console to print strings
        :param parent: tk.Frame to use as parent
        :type parent: tk.Frame
        :param nLines: Max number of lines to display on the console
        :type nLines: int
        :param parseCMD: Function to use to parse the message
        :type parseCMD: function
        """
        tk.Frame.__init__(self, parent)
        self.parseCMD = parseCMD
        self.nLines = nLines
        self.consoleVar = tk.StringVar()
        self.consoleList = []
        tk.Label(self, text='Console').pack(fill=tk.BOTH)
        self.console = tk.Message(self, textvariable=self.consoleVar, relief=tk.SUNKEN)
        self.console.pack()
        tk.Button(self, text='Clear', command=self.clearConsole).pack()

    def __append2console(self, text):
        self.consoleList.append(text)
        if len(self.consoleList) >= self.nLines:
            self.consoleList.pop(0)
        console = ''
        for t in self.consoleList:
            console += t + '\n'
        self.consoleVar.set(console)

    def append(self, text, clear_console=False):
        """
        Add text to console
        :param text: text to append
        :type text: str
        :param clear_console: flag to clear console before appending
        :type clear_console: bool
        """
        if clear_console:
            self.clearConsole()
        self.__append2console(text)
        if self.parseCMD is not None:
            self.parseCMD(text)

    def clearConsole(self):
        """
        Clears console
        """
        self.consoleVar.set('')
        self.consoleList = []


class PlotPanel(tk.Frame):
    def __init__(self, parent, title, titles, names, plotColor, timestamp, allValsList, color=None, number2Plot=500,
                 shareAxis=None, showTime=False, useScale=True, figsize=(5, 2), useCheckFn=False):
        """
        This widget has checkboxes with variables and a matplot figure the label goes to the left
        :param parent: parent frome
        :type parent: tk.Frame
        :param title: Title of the widget
        :type title: str
        :param titles: List with title of each of the checkbox control widget
        :type titles: list
        :param names: A list of list containing the name of each signal to plot
        :type names: list
        :param plotColor: Colors to be used for the plots
        :type plotColor: list
        :param timestamp: timestamps list
        :type timestamp: list
        :param allValsList: List with the values of the signals to plot
        :type allValsList: list
        :param color: Color to use for the widget
        :type color: str
        :param number2Plot: How many data points to plot from the list. The widget will plot the last n values
        :type number2Plot: int
        :param shareAxis: A matplotlib axes that will share the scale
        :type shareAxis: Axes
        :param showTime: Flag to show the timestamp value on the widget
        :type showTime: bool
        :param useScale: Flag to normalize all the values between the min and max value. This flag will ignore all units
        :type useScale: bool
        :param figsize: Size of the figure
        :type figsize: tuple
        :param useCheckFn: Function for the check control
        :type useCheckFn: function
        """

        tk.Frame.__init__(self, parent)
        self.title = title
        self.useScale = useScale
        self.showTime = showTime
        self.s = number2Plot
        self.count = 0
        self.parent = parent
        self.timestamp = timestamp
        self.all = allValsList
        self.names = names
        # titleLabelFrame = tk.Frame(self,background=color)
        # self.titleLabel = ttk.Label(self, text=title, background=color)
        self.consoleVar = tk.StringVar()
        self.titleLabel = tk.Message(self, textvariable=self.consoleVar, background=color, foreground='white')
        if self.showTime:
            self.consoleVar.set(title + '\n 0.0 s')
        else:
            self.consoleVar.set(title)
        # titleLabelFrame.grid()
        self.titleLabel.pack(side=tk.LEFT, fill=tk.Y)
        # self.titleLabel.grid(row=0,column=0)
        self.checkFrame = tk.Frame(self)
        self.checkFrame.pack(side=tk.LEFT)
        # self.checkFrame.grid(row=0,column=1)
        self.checks = []
        self.f = plt.figure(figsize=figsize, dpi=100)
        # self.f = plt.figure(figsize=(5, 5), dpi=100)
        self.axis = self.f.add_subplot(111, sharex=shareAxis, sharey=shareAxis)
        self.canvas = FigureCanvasTkAgg(self.f, self)
        self.canvas.draw()
        # self.axis = self.f.gca(projection='3d')
        self.plotColor = plotColor
        for t, n, c in zip(titles, names, self.plotColor):
            if useCheckFn:
                self.checks.append(
                    CheckControl(self.checkFrame, t, n, self.axis, color=c, cmd=self.plotControlFromChecks))
            else:
                self.checks.append(CheckControl(self.checkFrame, t, n, self.axis, color=c))
            # self.checks[-1].grid(row=0,column=len(self.checks))
            self.checks[-1].pack(side=tk.LEFT)

        # self.axis.plot([1,2,3,4,5,6,7,8],[5,6,1,3,8,9,3,5])

        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # self.canvas.get_tk_widget().grid(row=0,column=2)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        # self.canvas._tkcanvas.grid()
        self.canvas._tkcanvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def plotControlFromChecks(self):
        """
        This function plots all the values that have an active checkbox
        """
        #
        self.axis.clear()
        useScale = self.useScale
        s = self.s
        i = 0
        if self.showTime:
            if type(self.timestamp[0]) is list:
                t = self.timestamp[0][-1] / 1000.0
            else:
                t = self.timestamp[-1] / 1000.0
            self.consoleVar.set(self.title + '\n %.1fs' % t)
        for ch, col in zip(self.checks, self.plotColor):
            vals = ch.getAllValues()
            for v, c1 in zip(vals, col):
                if v == 1:
                    if type(self.timestamp[0]) is list:

                        t = np.array(self.timestamp[i][-s:]) / 1000.0
                        # print(t.shape)
                    else:
                        t = np.array(self.timestamp[-s:]) / 1000.0
                    y = np.array(self.all[i])
                    if y.size > t.size:
                        y = y[:t.size]
                    if y.size < t.size:
                        t = t[:y.size]
                    # divAux = FACTOR
                    # ymin = SCALE_MIN
                    if useScale:
                        ymin = y.min()
                        divAux = y.max() - y.min()
                    else:
                        ymin = 0.0
                        divAux = 1.0
                    # divAux = 0
                    if divAux == 0:
                        divAux = 1
                    try:
                        self.axis.plot(t, (y[-s:] - ymin) / divAux, color=c1)
                    except ValueError:
                        a = 1
                i = i + 1
        if useScale:
            self.axis.set_ylim(-0.1, 1.1)
        self.canvas.draw()

    def plotControlFromChecksTime(self, tV, extraT=2):
        """
        This function plots all the values that have an active checkbox and display the timestamp
        :param tV: time to show in seconds
        :type tV: float
        :param extraT: extra time (empty) to show for visualization
        :type float
        """
        if len(self.all[0]) < 2:
            return
        useScale = self.useScale
        self.axis.clear()
        i = 0
        if self.showTime:
            if type(self.timestamp[0]) is list:
                t = self.timestamp[0][-1] / 1000.0
                # print(t.shape)
            else:
                t = self.timestamp[-1] / 1000.0
            self.consoleVar.set(self.title + '\n %.1fs' % t)
        # t = np.array(t1) / 1000
        for ch, col in zip(self.checks, self.plotColor):
            vals = ch.getAllValues()
            for v, c1 in zip(vals, col):
                if v == 1:
                    # plot that var
                    if len(self.all[i]) < 2:
                        continue
                    if type(self.timestamp[0]) is list:
                        dt = self.timestamp[i][-1] - self.timestamp[i][-2]
                        s = int(tV * 1000 // dt)
                        t = np.array(self.timestamp[i][-s:]) / 1000
                        # print(s)
                    else:
                        dt = self.timestamp[-1] - self.timestamp[-2]
                        s = int(tV * 1000 // dt)
                        t = np.array(self.timestamp[-s:]) / 1000
                    y = np.array(self.all[i])
                    if y.size > t.size:
                        y = y[:t.size]
                    if y.size < t.size:
                        t = t[:y.size]
                    if useScale:
                        ymin = y.min()
                        divAux = y.max() - y.min()
                    else:
                        ymin = 0.0
                        divAux = 8000.0
                    # divAux = 0
                    if divAux == 0:
                        divAux = 1
                    try:
                        self.axis.plot(t, (y[-s:] - ymin) / divAux, color=c1)
                    except ValueError:
                        a = 1
                i = i + 1
        if useScale:
            self.axis.set_ylim(-0.1, 1.1)
        x_lim = self.axis.get_xlim()
        self.axis.set_xlim(x_lim[0], x_lim[1] + extraT)
        # self.axis.set_ylim(-200, 2200)
        self.canvas.draw()


class PlotPanelTimer(tk.Frame):
    def __init__(self, parent, label, **kwargs):
        """
        Timer used by PlotPanel
        :param parent: parent frome
        :type parent: tk.Frame
        :param label: Label  to use with the timer
        :type label: str
        """
        super(PlotPanelTimer, self).__init__(parent, **kwargs)
        self._consoleVar = tk.StringVar()
        self._titleLabel = tk.Message(self, textvariable=self._consoleVar)
        self._titleLabel.pack()
        self.label = label
        self.setNewTime(0.0)

    def setNewTime(self, newT):
        """
        Sets new time
        :param newT: new time to display
        :type newT: float
        """
        self._consoleVar.set('%s: %.1fs' % (self.label, newT))


class PlotPanelPandas(PlotPanel):
    def __init__(self, parent, title, titles, names, plotColor, timestamp, allValsPandas, color=None,
                 number2Plot=500, shareAxis=None, showTime=False, useScale=True, multiplier=10,
                 timerFrame=None):
        """
        This widget has checkboxes with variables and a matplot figure the label goes to the left
        :param parent: parent frome
        :type parent: tk.Frame
        :param title: Title of the widget
        :type title: str
        :param titles: List with title of each of the checkbox control widget
        :type titles: list
        :param names: A list of list containing the name of each signal to plot
        :type names: list
        :param plotColor: Colors to be used for the plots
        :type plotColor: list
        :param timestamp: timestamps list
        :type timestamp: list
        :param allValsPandas: Pandas DataFrame containing the values
        :type allValsPandas: pandas.DataFrame
        :param color: Color to use for the widget
        :type color: str
        :param number2Plot: How many data points to plot from the list. The widget will plot the last n values
        :type number2Plot: int
        :param shareAxis: A matplotlib axes that will share the scale
        :type shareAxis: Axes
        :param showTime: Flag to show the timestamp value on the widget
        :type showTime: bool
        :param useScale: Flag to normalize all the values between the min and max value. This flag will ignore all units
        :type useScale: bool
        :param multiplier: To improve performance, use this value to only refresh the plot every multiplier times
        :type multiplier: int
        :param timerFrame: timerFrame to use to display the time
        :type timerFrame: PlotPanelTimer
        """
        super(PlotPanelPandas, self).__init__(self, parent, title, titles, names, plotColor, timestamp, allValsPandas,
                                              color=color, number2Plot=number2Plot, shareAxis=shareAxis,
                                              showTime=showTime, useScale=useScale)
        self.button = ButtonPanel(self, [['Reset Scale']], [[self.resetScale]])
        self.button.pack()
        self.maxValsAux = None
        self.minValsAux = None
        self.dt = 0
        self.multiplier = multiplier
        self.counter = multiplier
        self.timerFrame = timerFrame

    def plotControlFromChecks(self):
        warnings.warn('Please do not use this funciton with plotPanelPandas')

    def resetScale(self):
        """
        Resets the scale of the plot
        """
        self.maxValsAux = None

    def plotControlFromChecksTime(self, tV, extraT=2.0, preprocess=None):
        """
        This function plots all the values that have an active checkbox and display the timestamp
        :param tV: time to show in seconds
        :type tV: float
        :param extraT: extra time (empty) to show for visualization
        :type float
        :param preprocess: Function to use to preprocess the signals
        :type preprocess: function
        """
        # this function will plot all the values from all
        if self.all.shape[0] is 0:
            return
        if self.counter != 0:
            self.counter -= 1
            return
        # print(self.counter)
        self.counter = self.multiplier
        # i = 0

        # def _plotThread(self, tV, extraT, preprocess):
        dt = 1000.0 / np.diff(self.all.index.values).mean()
        if np.isnan(dt):
            return
        self.dt = dt
        if self.showTime:
            t = self.all.index[-1] / 1000.0
            # print(self.all.columns)
            s_val = self.all['sync'].values[-1] == 1
            self.consoleVar.set(self.title + '\n %.1fs\n%.1fHz\n Sync: %d' % (t, dt, s_val))
            if self.timerFrame is not None:
                self.timerFrame.setNewTime(t)
        vals = np.array([ch.getAllValues() for ch in self.checks]).flatten()
        if np.all(vals == 0):
            return
        self.axis.cla()

        # I'll plot only the new 500 values

        # t = np.array(t1) / 1000
        # timeS = int((self.all.index[-1] - tV * 1000 ) // self.all.index.get_values().mean())
        # # print(tV * 1000)
        # windowVals = self.all.iloc[-timeS:, :].copy() / 4096

        windowVals = self.all.iloc[-int(tV * dt):, :].copy()
        if preprocess is not None:
            for k, fn in zip(*preprocess):
                windowVals[k] = fn(windowVals[k])
        if self.useScale:
            if self.maxValsAux is None:
                self.maxValsAux = pandas.Series(np.zeros_like(windowVals.max()), index=windowVals.max().index)
                self.minValsAux = self.maxValsAux.copy() + 4096
            else:
                self.maxValsAux.loc[windowVals.max() > self.maxValsAux] = windowVals.max().loc[
                    windowVals.max() > self.maxValsAux]
                self.minValsAux.loc[windowVals.min() < self.minValsAux] = windowVals.min().loc[
                    windowVals.min() < self.minValsAux]
            divAux = self.maxValsAux - self.minValsAux
            divAux[divAux == 0] = 1
            windowVals = (windowVals - self.minValsAux) / (divAux)
        # print(dt)
        # print(windowVals.shape[0])
        windowVals.index /= 1000.0
        for ch, col, colNames in zip(self.checks, self.plotColor, self.names):
            vals = ch.getAllValues()
            for v, c1, na in zip(vals, col, colNames):
                if na not in windowVals.columns:
                    continue
                if v == 1:
                    # print(na)
                    # try:
                    windowVals[na].plot(ax=self.axis, color=c1)
                    # self.axis.plot(t, (y[-s:] - ymin) / divAux, color=c1)
                    # except TypeError:
                    #     a = 1
                # i = i + 1
        self.axis.set_ylim(-0.1, 1.1)
        x_lim = self.axis.get_xlim()
        self.axis.set_xlim(x_lim[0], x_lim[1] + extraT)
        # self.axis.set_ylim(-200, 2200)
        self.canvas.draw()


class PlotPanel3D(tk.Frame):
    def __init__(self, parent, title, titles, names, plotColor, angleValsList, figsize=(5, 5), color=None,
                 rotationOrder='ZYX', degrees=False):
        """
        This widget create a 3D axes and plots a coordinates system rotation given euler angles
        :param parent: parent frame
        :type parent: tk.Frame
        :param title: Title of the frame
        :type title: str
        :param titles: Title of each angle group
        :type titles: list
        :param names: name of each angle
        :type names: list
        :param plotColor: Color to use for systems
        :type plotColor: list
        :param angleValsList: List with the angle values
        :type angleValsList: list
        :param figsize: Size of the figure
        :type figsize: tuple
        :param color:
        :param rotationOrder: order of rotation using scipy standard
        :type rotationOrder: str
        :param degrees: If true angleValList is in degrees and not radians
        :type degrees: bool
        """

        tk.Frame.__init__(self, parent)
        self._rotationOrder = rotationOrder
        self._degrees = degrees
        self.all = angleValsList
        self.parent = parent
        self.titleLabel = ttk.Label(self, text=title, background=color)
        self.titleLabel.pack(side=tk.LEFT, fill=tk.Y)
        self.checkFrame = tk.Frame(self)
        self.checkFrame.pack(side=tk.LEFT)
        self.checks = []
        self.f = plt.figure(figsize=figsize)
        # self.axis = self.f.gca(projection='3d')
        self.axis = Axes3D(self.f)
        self.plotColor = plotColor
        for t, n, c in zip(titles, names, self.plotColor):
            self.checks.append(CheckControl(self.checkFrame, t, n, self.axis, color=c, cmd=self.plotControlFromChecks))
            # self.checks[-1].grid(row=0,column=len(self.checks))
            self.checks[-1].pack(side=tk.LEFT)

        self.canvas = FigureCanvasTkAgg(self.f, self)
        # self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        # self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.Hs = []
        self.systs = []
        for j in range(len(names)):
            self.Hs.append(np.identity(4))
            # self.Hs[-1][0, 3] = j
            self.systs.append(AxesSystemPlotter(self.axis))
            self.systs[-1].rotateAndPlotSystem(H=self.Hs[-1])
        self.canvas.draw()

    def plotControlFromChecks(self):
        self.axis.clear()

        i = 0
        # t = np.array(t1) / 1000
        for ch, col in zip(self.checks, self.plotColor):
            vals = ch.getAllValues()
            for v, c1 in zip(vals, col):
                if v == 1:
                    # Get the values of rotation
                    if len(self.all[i][0]) is 0:
                        self.systs[i].rotateAndPlotSystem(H=self.Hs[i], clearAx=False)
                        continue
                    # self.all is a list of list with [rx, ry, rz]
                    eu = [x[-1] for x in self.all[i]]
                    self.Hs[i][:3, :3] = rot.from_euler(self._rotationOrder, eu, degrees=self._degrees).as_matrix()
                    self.systs[i].rotateAndPlotSystem(H=self.Hs[i], clearAx=False)

                i = i + 1

        self.axis.set_xlim(-2, 2)
        self.axis.set_ylim(-2, 2)
        self.axis.set_zlim(-2, 2)
        self.canvas.draw()


class PlotPanel3DPandas(tk.Frame):
    def __init__(self, parent, title, titles, names, plotColor, allValsPandas, angle_column_names,
                 figsize=(5, 5), color=None, rotationOrder='ZYX', degrees=False):
        """
        This widget create a 3D axes and plots a coordinates system rotation given euler angles
        :param parent: parent frame
        :type parent: tk.Frame
        :param title: Title of the frame
        :type title: str
        :param titles: Title of each angle group
        :type titles: list
        :param names: name of each angle
        :type names: list
        :param plotColor: Color to use for systems
        :type plotColor: list
        :param allValsPandas: Dataframe with the angle values
        :type allValsPandas: pandas.DataFrame
        :param angle_column_names: name of the columns containing the angle values in the correct order
        :type angle_column_names: list
        :param figsize: Size of the figure
        :type figsize: tuple
        :param color:
        :param rotationOrder: order of rotation using scipy standard
        :type rotationOrder: str
        :param degrees: If true angleValList is in degrees and not radians
        :type degrees: bool
        """
        # this widget has checkboxes with variables and a matplot figure
        # the label goes to the left
        tk.Frame.__init__(self, parent)
        self._rotationOrder = rotationOrder
        self._degrees = degrees
        self._angle_column_names = angle_column_names
        self.all = allValsPandas
        self.parent = parent
        self.titleLabel = ttk.Label(self, text=title, background=color)
        self.titleLabel.pack(side=tk.LEFT, fill=tk.Y)
        self.checkFrame = tk.Frame(self)
        self.checkFrame.pack(side=tk.LEFT)
        self.checks = []
        self.f = plt.figure(figsize=figsize)
        # self.axis = self.f.gca(projection='3d')
        self.axis = Axes3D(self.f)
        self.plotColor = plotColor
        for t, n, c in zip(titles, names, self.plotColor):
            self.checks.append(CheckControl(self.checkFrame, t, n, self.axis, color=c, cmd=self.plotControlFromChecks))
            # self.checks[-1].grid(row=0,column=len(self.checks))
            self.checks[-1].pack(side=tk.LEFT)

        self.canvas = FigureCanvasTkAgg(self.f, self)
        # self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        # self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.Hs = []
        self.systs = []
        for j in range(len(names)):
            self.Hs.append(np.identity(4))
            # self.Hs[-1][0, 3] = j
            self.systs.append(AxesSystemPlotter(self.axis))
            self.systs[-1].rotateAndPlotSystem(H=self.Hs[-1])
        self.canvas.draw()

    def plotControlFromChecks(self):
        # this function will plot all the values from all
        self.axis.clear()

        i = 0
        # t = np.array(t1) / 1000
        for ch, col in zip(self.checks, self.plotColor):
            vals = ch.getAllValues()
            for v, c1 in zip(vals, col):
                if v == 1:
                    # Get the values of rotation
                    if self.all[i].shape[0] is 0:
                        self.systs[i].rotateAndPlotSystem(H=self.Hs[i], clearAx=False)
                        continue
                    eu = self.all.loc[self._angle_column_names].values[-1]
                    self.Hs[i][:3, :3] = rot.from_euler(self._rotationOrder, eu, degrees=self._degrees).as_matrix()
                    self.systs[i].rotateAndPlotSystem(H=self.Hs[i], clearAx=False)

                i = i + 1

        self.axis.set_xlim(-2, 2)
        self.axis.set_ylim(-2, 2)
        self.axis.set_zlim(-2, 2)
        self.canvas.draw()


class InputWithButton(tk.Frame):
    def __init__(self, parent, label, buttonLabel, buttonCmd, browseTitle, browseFiletypes, defaultVal='',
                 dialogType=0):
        """
        This widget creates a file browser widget with a text field, a browse button, and a custom button
        :param parent: parent frame
        :type parent: tk.Frame
        :param label: Label for the widget
        :type label: str
        :param buttonLabel: Label for the custom button
        :type buttonLabel: str
        :param buttonCmd: Command to execute when the button is pressed
        :type buttonCmd: function
        :param browseTitle: Title to show on the browse window
        :type browseTitle: str
        :param browseFiletypes: Types that are accepted using tk standard
        :type browseFiletypes: list
        :param defaultVal: Default path
        :type defaultVal: str
        :param dialogType: use 0 for askopenfilename, 1 for asksaveasfilename, 2 for askdirectory
        :type dialogType: int
        """
        tk.Frame.__init__(self, parent)
        self._dialogType = dialogType
        tk.Label(self, text=label, width=10).grid(row=0, column=0)
        self._browseTitle = browseTitle
        self._browseFiletypes = browseFiletypes
        self.val = tk.StringVar()
        tk.Entry(self, textvariable=self.val, width=80).grid(row=0, column=1)
        self.val.set(defaultVal)
        # frBot = tk.Frame(self)
        self._cmd = buttonCmd
        self.exButton = tk.Button(self, text=buttonLabel, command=self._exeCMD, bg='yellow')
        self.exButton.grid(row=0, column=3)
        tk.Button(self, text='Browse', command=self._browseCMD).grid(row=0, column=2)
        # self.statusIm = tk.Label(self, background='yellow', width=3)
        # self.statusIm.grid(row=0, column=4)
        self.getValue = self.val.get

    def _exeCMD(self):
        self._cmd(self.getValue())
        self.changeButtonColor('g')

    def _browseCMD(self):
        root = tk.Tk()
        if self._dialogType == 0:
            fileN = tk.filedialog.askopenfilename(parent=root, title=self._browseTitle, filetypes=self._browseFiletypes)
        elif self.dialogType == 1:
            fileN = tk.filedialog.asksaveasfilename(parent=root, title=self._browseTitle, filetypes=self._browseFiletypes,
                                                    defaultextension=self._browseFiletypes[0][1][1:])
        else:
            fileN = tk.filedialog.askdirectory(parent=root, title=self._browseTitle)
        root.withdraw()
        if fileN is None:
            return 0
        self.val.set(fileN)
        # self.exButton.config(bg='yellow')
        self._exeCMD()

    def changeButtonColor(self, typeE):
        """
        Changes the color of the button
        :param typeE: 3 options:
        Error, Warn, Good
        :type typeE: str
        """
        if typeE is 'Error':
            c = 'red'
        elif typeE is 'Warn':
            c = 'yellow'
        else:
            c = 'green'
        self.exButton.config(bg=c)


class ButtonPanel(tk.Frame):
    def __init__(self, parent, labels, cmds, width=20):
        """
        Creates a group of buttons
        :param parent: parent frame
        :type parent: tk.Frame
        :param labels: Labels of the buttons. List of lists, the first dimension correspond to rows, second to columns.
        These labels are also used as identifiers within the object
        :type labels: list
        :param cmds: commands to execute when the buttons are pressed. Has to be the same dimension as labels
        :type cmds: list
        :param width: width of the buttons
        :type width: int
        """
        tk.Frame.__init__(self, parent)
        self.buttons = {}
        for row, (ls, cs) in enumerate(zip(labels, cmds)):
            for col, (l, c) in enumerate(zip(ls, cs)):
                self.buttons[l] = tk.Button(self, text=l, command=c, width=width)
                self.buttons[l].grid(row=row, column=col)

    def enableDisableButtons(self, labels, states):
        """
        Enables of disables button using labels
        :param labels: Name/Names to change the state
        :type labels: str, list
        :param states: State/States to change
        :type states: bool, list
        """
        if type(labels) is not list:
            self.buttons[labels]["state"] = states
        else:
            if type(states) is not list:
                states = [states] * len(labels)

            for l, s in zip(labels, states):
                self.buttons[l]["state"] = s


class StringInputs(tk.Frame):
    def __init__(self, parent, names, vertical=True, defaultVals=None, dtype=np.int, process_function=None):
        """
        Creates a widget with an array of string inputs
        :param parent: Parent frame
        :type parent: tk.Frame
        :param names: Name of the input fields
        :type names: list
        :param vertical: Flag if the array should be vertical
        :type vertical: bool
        :param defaultVals: Default values of the fields
        :type defaultVals: list
        :param dtype: dtype of the fields
        :type dtype: class
        :param process_function: function to use to process the string
        :type process_function: function
        """
        tk.Frame.__init__(self, parent)
        # self.root = tk.Toplevel(self)
        self.vals = None
        self.valR = []
        self.dtype = dtype
        # names = ['Freq']
        self.allNames = names
        self._process_function = process_function
        if defaultVals is None:
            dV = [''] * len(names)
        else:
            if len(defaultVals) is not len(names):
                if len(defaultVals) is 1:
                    dV = defaultVals * len(names)
                else:
                    warnings.warn('Default values should be 1 or equal to the number of names')
                    dV = defaultVals + [''] * (len(names) - len(defaultVals))
            else:
                dV = defaultVals
        for i, (n, d) in enumerate(zip(names, dV)):
            if vertical:
                # label
                tk.Label(self, text=n).grid(row=0, column=i + 1)
                # box 1
                self.valR.append(tk.StringVar())
                tk.Entry(self, textvariable=self.valR[-1], validate='focusout').grid(row=1, column=i + 1)
            else:
                # label
                tk.Label(self, text=n).grid(row=i + 1, column=0)
                # box 1
                self.valR.append(tk.StringVar())
                tk.Entry(self, textvariable=self.valR[-1], validate='focusout').grid(row=i + 1, column=0)
            self.valR[-1].set(d)
        # root.quit()

    def readValues(self):
        """
        Reads the values in the array and returns a numpy array
        :return: np.ndarray
        """
        self.vals = [[] for _ in self.allNames]
        for i, r in enumerate(self.valR):
            if self._process_function:
                self.vals[i] = self._process_function(r.get())
            else:
                self.vals[i] = r.get()
        return np.array(self.vals)


class AxesSystemPlotter(object):
    def __init__(self, ax):
        """
        Plots a rotation system
        :param ax: axis containing the plot
        :type ax: matplotlib.axis
        """
        self.axis = ax
        self.xi = np.array([1.0, 0.0, 0.0, 1.0])
        self.yi = np.array([0.0, 1.0, 0.0, 1.0])
        self.zi = np.array([0.0, 0.0, 1.0, 1.0])

    def rotateAndPlotSystem(self, H=None, clearAx=False):
        """
        Information about the system axes
        :param H: homogenous transformation
        :type H: np.ndarray
        :param clearAx: Flag to clear the axis before plotting
        """
        if H is None:
            H = np.identity(4)
        xSpace = np.matmul(H, self.xi)[:-1]
        ySpace = np.matmul(H, self.yi)[:-1]
        zSpace = np.matmul(H, self.zi)[:-1]
        o = H[:-1, -1]
        if clearAx:
            self.axis.clear()
        for v, c in zip([xSpace, ySpace, zSpace], ['red', 'green', 'blue']):
            self.axis.quiver(*o, *v, length=1.0, color=c)


class InputsMatrix(tk.Frame):
    def __init__(self, parent, defaultVals, inputWidth, parseFN=int, **kwargs):
        """
        Creates a widget with an array of string inputs
        :param parent: Parent frame
        :type parent: tk.Frame
        :param defaultVals: Default values of the fields
        :type defaultVals: pandas.DataFrame
        :param inputWidth: width of the fields
        :type inputWidth: int
        :param parseFN: Function used to parse the functions
        :type parseFN: function
        """
        super(InputsMatrix, self).__init__(parent, **kwargs)
        self.parseFN = parseFN
        self.values = defaultVals.copy()
        rowNames = defaultVals.index.values
        colNames = defaultVals.columns.values
        self.strVals = []
        for i, rN in enumerate(rowNames):
            tk.Label(self, text=rN).grid(row=i + 1, column=0)
            for j, cN in enumerate(colNames):
                tk.Label(self, text=cN).grid(row=0, column=j + 1)
                self.strVals.append(tk.StringVar(self))
                tk.Entry(self, textvariable=self.strVals[-1], width=inputWidth).grid(row=i + 1, column=j + 1)
                self.strVals[-1].set(defaultVals.loc[rN, cN])

    def getValues(self):
        """
        Gets the values from the fields
        :return: the values on the fields
        :rtype: pandas.DataFrame
        """
        c = 0
        for j in self.values.index.values:
            for i in self.values.columns.values:
                try:
                    self.values.loc[j, i] = self.parseFN(self.strVals[c].get())
                except ValueError:
                    self.values.loc[j, i] = self.parseFN(0)
                c += 1
        return self.values
