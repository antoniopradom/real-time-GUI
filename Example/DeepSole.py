import pandas
import time
import numpy as np
from tkinter import messagebox, simpledialog
import tkinter as tk
import rtgui as guT
import matplotlib.image as mpimg
import matplotlib.patches as patches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import struct
import warnings
import rtgui.communication as tu
import threading


class UDPreceiveDS(tu.UDPreceiveProto):
    """
    Object to receive data through UDP
    """

    def __init__(self, leftShoe, rightShoe, console, portN=12345, bufferedData=None, startTime=[0],
                 maxQSize=10):
        """
        :param leftShoe: left shoe object
        :param rightShoe: right shoe object
        :param console: tkInter text to be used as "console"
        :param portN: port number for receiving
        """
        super(UDPreceiveDS, self).__init__(console, portN, bufferedData, maxQSize=maxQSize)
        self.leftShoe = leftShoe
        self.rightShoe = rightShoe
        self.startTime = startTime
        self.th = [threading.Thread() for _ in range(2)]
        # self.maxQSize = maxQSize

    def _parseData(self, unparsed, qSize=1):
        """
        Parses network data and process it accordingly
        :param unparsed:
        :return:
        """
        if unparsed[0] == 1 and unparsed[1] == 2 and unparsed[2] == 3:
            # 3 char for open, uint64 for timestamp, 24 short for values and 3 char for close
            # fmt = '=3c I 13H 4c'
            if qSize > self.maxQSize:
                # print('Q too big')
                return
            fmt = self.rightShoe.fmt
            now = int((time.time() - self.startTime[0]) * 1000)
            p = struct.unpack(fmt, unparsed)
            msg = struct.pack('2I h', now, p[3], p[16])
            if p[17].decode() is 'l':
                self.leftShoe.binaryFile += unparsed
                self.leftShoe.binaryFile2 += msg
                self.leftShoe.appendData(p[4:16], p[3], p[16])
            else:
                self.rightShoe.binaryFile += unparsed
                self.rightShoe.binaryFile2 += msg
                self.rightShoe.appendData(p[4:16], p[3], p[16])
        elif unparsed[0] == 0xF and unparsed[1] == 0xF and unparsed[2] == 0xA:
            # 3 char for open, uint64 for timestamp, 24 short for values and 3 char for close
            fmt = '=3c 3H 4c'
            p = struct.unpack(fmt, unparsed)
        else:
            print(unparsed)
            self.console.set(unparsed.decode("utf-8", "ignore"))

class smartShoe(object):
    """
    This object contains all the data collected by the shoes
    """

    def __init__(self, isLeft, keepAll=True, sizeBuf=1000):
        """
        Bool isLeft: if True shoe is treated as Left (Master)
        Bool keepAll: if True all values are kept as lists, else only a buffer of sizeBuf values are kept
        """
        self.keepAll = keepAll
        self.sizeBuf = sizeBuf
        self.binaryFile = bytes(0)
        self.binaryFile2 = bytes(0)
        self.fmt = '<3c I 13h 4c'
        self.isLeft = isLeft
        self.pressDisplay = None
        self.plotP = None
        self.now = time.time()
        self.timestamp = []
        self.pToe = []
        self.pBall = []
        self.pHeel = []

        # acc
        self.ax = []
        self.ay = []
        self.az = []

        # gx
        self.gx = []
        self.gy = []
        self.gz = []

        # Euler
        self.roll = []
        self.pitch = []
        self.yaw = []
        self.phase = []
        self.sync = []
        self.euAngles = [self.pitch,
                         self.yaw,
                         self.roll]
        self.EUorder = ['EUy', 'EUz', 'EUx']
        self.all = [self.pToe,
                    self.pBall,
                    self.pHeel,
                    self.ax,
                    self.ay,
                    self.az,
                    self.gx,
                    self.gy,
                    self.gz,
                    self.roll,
                    self.pitch,
                    self.yaw]
        self.names = ['pToe', 'pBall', 'pHeel', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 'EUy', 'EUz', 'EUx']
        self.namesWrong = ['pToe', 'pBall', 'pHeel', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 'EUx', 'EUy', 'EUz']
        self.normalValues = [[None, None] for _ in self.names]
        self.dataFrame = pandas.DataFrame(columns=self.names + ['sync'] + ['timestamp'])
        self.syncFound = None
        self.appendCounter = 0

    def resetShoe(self):
        self.now = time.time()
        self.timestamp = []
        self.pToe = []
        self.pBall = []
        self.pHeel = []

        # acc
        self.ax = []
        self.ay = []
        self.az = []

        # gx
        self.gx = []
        self.gy = []
        self.gz = []

        # Euler
        self.roll = []
        self.pitch = []
        self.yaw = []
        self.phase = []
        self.sync = []
        self.euAngles = [self.pitch,
                         self.yaw,
                         self.roll]
        self.EUorder = ['EUy', 'EUz', 'EUx']
        self.all = [self.pToe,
                    self.pBall,
                    self.pHeel,
                    self.ax,
                    self.ay,
                    self.az,
                    self.gx,
                    self.gy,
                    self.gz,
                    self.roll,
                    self.pitch,
                    self.yaw]

        self.normalValues = [[None, None] for _ in self.names]
        self.dataFrame.drop(self.dataFrame.index, inplace=True)
        self.appendCounter = 0
        self.syncFound = None
        self.binaryFile2 = bytes(0)

    def updateVars(self):
        self.pToe = self.all[0]
        self.pBall = self.all[1]
        self.pHeel = self.all[2]
        self.ax = self.all[3]
        self.ay = self.all[4]
        self.az = self.all[5]
        self.gx = self.all[6]
        self.gy = self.all[7]
        self.gz = self.all[8]
        self.mx = self.all[9]
        self.my = self.all[10]
        self.mz = self.all[11]

    def saveBinaryFile(self, fileN):
        if self.isLeft:
            fileN += '_L.bin'
            fileN2 = fileN + '_t_L.bin'
        else:
            fileN += '_R.bin'
            fileN2 = fileN + '_t_R.bin'

        with open(fileN, 'wb') as f:
            f.write(self.binaryFile)

        with open(fileN2, 'wb') as f:
            f.write(self.binaryFile2)

    def makeBinaryFileAgain(self):
        fmt = self.fmt
        fmt2 = fmt[1:] + ' '
        totalPacks = len(self.timestamp)
        allFmt = fmt + ' ' + fmt2 * (totalPacks - 1)
        if self.isLeft:
            side = 'l'
        else:
            side = 'r'
        # create all packet file
        pAllList = (
            [bytes([0x1]), bytes([0x2]), bytes([0x3])] + list(vals) + [side.encode()] + [bytes([0xA]), bytes([0xB]),
                                                                                         bytes([0xC])] for vals in
            zip(self.timestamp,
                self.pToe, self.pBall, self.pHeel,
                self.ax, self.ay, self.az,
                self.gx, self.gy, self.gz,
                self.roll, self.pitch, self.yaw,
                self.sync))
        pAll = [item for sublist in pAllList for item in sublist]
        self.binaryFile = struct.pack(allFmt, *pAll)

    def getPressVal(self, a):
        """
        :list a: list of pressure values
        :return: last registered pressure value of a
        """
        f = lambda x: (x[-1] - min(x)) / (max(x) - min(x))
        if len(a) == 0 or (max(a) - min(a)) == 0:
            return 0
        else:
            return f(a)

    def appendData(self, data, t, sync, append2list=False):
        if not append2list:
            if np.isnan(t):
                return
            self.dataFrame.loc[t, 'sync'] = sync
            self.dataFrame.loc[t, self.names] = data
            self.dataFrame.loc[t, ['ax', 'ay', 'az', 'gx', 'gy', 'gz', 'EUx', 'EUy', 'EUz']] *= 1.0 / 8000.0
            self.dataFrame.loc[t, 'timestamp'] = t
            if not self.keepAll and self.dataFrame.shape[0] > self.sizeBuf:
                self.dataFrame.drop(index=self.dataFrame.index[0], inplace=True)
        else:
            if self.keepAll:
                self._appendDataAll(data, t, sync)
            else:
                self._appendDataBuff(data, t, sync)

    def _appendDataAll(self, data, t, sync):
        """
        :param data: list of values to append, they need to be in the same order as self.all
        :param t: timestamp when data was collected
        :param sync: 0 or 1 if a signal was received
        :return: nothing
        """
        self.timestamp.append(t)
        self.sync.append(sync)
        for d, v in zip(data, self.all):
            v.append(d)

    def _appendDataBuff(self, data, t, sync):
        """
        :param data: list of values to append, they need to be in the same order as self.all
        :param t: timestamp when data was collected
        :param sync: 0 or 1 if a signal was received
        :return: nothing
        """
        self.timestamp.append(t)
        self.sync.append(sync)
        popEle = len(self.timestamp) > self.sizeBuf
        if popEle:
            self.timestamp.pop(0)
            self.sync.pop(0)
        for d, v in zip(data, self.all):
            v.append(d)
            if popEle:
                v.pop(0)

    def createPandasDataFrame(self, useSync=False, returnObj=False, freq=None, oldShoe=False, filter=False):
        if len(self.ax) is 0:
            self.dataFrame = pandas.DataFrame(columns=self.names + ['sync'])
            warnings.warn("Shoe object is empty, hence dataFrame is empty", DeprecationWarning)
        else:
            if freq is not None or oldShoe:
                t, d = self.makeMatrix(freq=freq, cutAtSync=useSync, normal=False, filter=filter, oldShoe=oldShoe)
                if oldShoe:
                    self.names = ['EUx', 'EUy', 'EUz', 'ax', 'ay', 'az', 'pBall', 'pHeel']
                self.dataFrame = pandas.DataFrame(data=d,
                                                  columns=self.names,
                                                  index=t)
            else:
                d = np.array(self.all).T
                t = np.array(self.timestamp) / 1000
                tS = 0
                if useSync:
                    s = np.where(np.array(self.sync) == 1)[0]
                    if len(s) is 0:
                        warnings.warn('Sync not found')
                        self.syncFound = False
                        tS = self.timestamp[0]
                    else:
                        tS = self.timestamp[s[0]] / 1000
                        d = d[s, :]
                        t = t[s]
                        self.syncFound = True
                # divide by 8000, 8000 is the scale factor we are using for

                self.dataFrame = pandas.DataFrame(data=d,
                                                  columns=self.namesWrong,
                                                  index=(t - tS))
                self.dataFrame.loc[:, ['ax', 'ay', 'az', 'gx', 'gy', 'gz', 'EUx', 'EUy', 'EUz']] *= 1.0 / 8000

                self.dataFrame = self.dataFrame[self.names]

        if returnObj:
            return self.dataFrame.copy()

    def plotValue(self, valNames, **kwargs):
        if self.dataFrame is None:
            self.createPandasDataFrame()
        if type(valNames) is not list:
            valNames = [valNames]
        for valName in valNames:
            if valName not in self.names:
                raise ValueError(
                    'Desired sensor not in shoe, received: %s, valid names are: %s' % (valName, self.names))

            self.dataFrame.plot(y=valName, **kwargs)

    def createListsFromBinary(self):
        bytes_read = self.binaryFile
        fmt2 = self.fmt[1:] + ' '
        fileSize = len(bytes_read)
        packetSize = struct.calcsize(self.fmt)
        totalPacks = fileSize // packetSize
        allFmt = self.fmt + ' ' + fmt2 * (totalPacks - 1)
        pAll = struct.unpack(allFmt, bytes_read)
        nVariables = len(self.all)
        # divide the list into chunks of nVariables, i.e. samples
        self.timestamp = [pAll[i + 3] for i in range(0, len(pAll), nVariables + 1)]
        self.sync = [pAll[i + 16] for i in range(0, len(pAll), nVariables + 1)]
        for j in range(len(self.all)):
            self.all[j][:] = [pAll[i + j + 4] for i in range(0, len(pAll), nVariables + 1)]

class ShoePressDisp(tk.Frame):
    class fakeRec(object):
        def __init__(self):
            a = 1

        def remove(self):
            pass

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        # img are 700x500
        self.rImg = mpimg.imread('./right.png')
        self.lImg = mpimg.imread('./left.png')
        f = plt.figure(figsize=(3.7, 2), dpi=100)
        # f = plt.figure.Figure(figsize=(3.7, 2), dpi=100)
        self.axisL = f.add_subplot(121)
        # self.axisL.axis('equal')
        self.axisL.axis('off')
        self.axisR = f.add_subplot(122)
        self.axisR.axis('off')
        self.canvas = FigureCanvasTkAgg(f, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas._tkcanvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.axisR.imshow(self.rImg)
        self.axisL.imshow(self.lImg)
        self.rects = [ShoePressDisp.fakeRec() for _ in range(3)]
        self.updateVal = tk.IntVar()
        self.updateVal.set(1)
        self.check = tk.Checkbutton(self, text='Update Pressure', variable=self.updateVal, foreground='black')
        self.check.pack()
        self.oldValues = [1.0, 1.0, 1.0]
        self.updatePlot(0.0, 0.0, 0.0)
        self.updatePlot(0.0, 0.0, 0.0, axLeft=False)

    def updatePlot(self, toe=1, ball=1, heel=1, axLeft=True, useAlpha=True):
        # toe is 0 - 200
        # ball is 201 - 400
        # heel is 500 - 700
        # axLeft = True is left
        # axLeft = False is right

        # for a,im in zip([self.axisL,self.axisR],[self.lImg,self.rImg]):
        if self.updateVal.get() == 0 or all([x == y for x, y in zip(self.oldValues, [toe, ball, heel])]):
            return
        self.oldValues = [toe, ball, heel]
        if axLeft:
            a = self.axisL
            im = self.lImg
        else:
            a = self.axisR
            im = self.rImg
        # a.clear()
        [p.remove() for p in reversed(self.rects)]
        if useAlpha:
            toeRec = patches.Rectangle((0, 0), 400, 200, fill=True, color='r', alpha=(1 - toe), zorder=-1)
            ballRec = patches.Rectangle((0, 200), 400, 200, fill=True, color='r', alpha=(1 - ball), zorder=-1)
            heelRec = patches.Rectangle((0, 400), 400, 300, fill=True, color='r', alpha=(1 - heel), zorder=-1)
        else:
            toeRec = patches.Rectangle((0, 0), 400, 200, fill=True, color=str(1 - toe), zorder=-1)
            ballRec = patches.Rectangle((0, 200), 400, 200, fill=True, color=str(1 - ball), zorder=-1)
            heelRec = patches.Rectangle((0, 400), 400, 300, fill=True, color=str(1 - heel), zorder=-1)
        self.rects = [toeRec, ballRec, heelRec]
        for re in self.rects:
            a.add_patch(re)
        # a.imshow(im)
        # a.axis('off')
        self.canvas.draw()
class ControlFunctionsContainer(object):
    def __init__(self, labels, main):
        self.STREAM_IP_ADDRESS = '192.168.0.255'
        self.buttons = None
        self.labels = labels
        self.main = main
        self.theSend = main.theSend
        self.isRecord = True
        self.isStream = True
        self.isPredict = True
        self.fileName = 'file%d' % (int(time.time()))

    class motorControl(tk.Toplevel):
        def __init__(self, parent):
            tk.Toplevel.__init__(self, parent)
            self.vals = None
            fr = tk.Frame(self)
            fr.pack()
            tk.Label(fr, text='R').grid(row=1)
            tk.Label(fr, text='L').grid(row=2)
            self.valR = []
            self.valL = []
            names = ['M Ball', 'L Ball', 'Heel', 'Noise', 'Min Freq', 'Max Freq', 'Use log scale']
            self.allNames = names
            okCMD = self.register(self.validateVal)
            vld = (okCMD, '%P')
            for i, n in enumerate(names):
                # label
                tk.Label(fr, text=n).grid(row=0, column=i + 1)
                # box 1
                self.valR.append(tk.StringVar())
                tk.Entry(fr, textvariable=self.valR[-1], validate='focusout', validatecommand=vld).grid(row=1,
                                                                                                        column=i + 1)
                self.valR[-1].set('0')
                # box 2
                self.valL.append(tk.StringVar())
                tk.Entry(fr, textvariable=self.valL[-1], validate='focusout', validatecommand=vld).grid(row=2,
                                                                                                        column=i + 1)
                self.valL[-1].set('0')
            frBot = tk.Frame(self)
            tk.Button(frBot, text='OK', command=self.okB).pack(side=tk.LEFT)
            tk.Button(frBot, text='Cancel', command=self.cancelB).pack(side=tk.LEFT)
            frBot.pack()
            self.protocol("WM_DELETE_WINDOW", self.cancelB)
            self.transient(parent)
            self.grab_set()
            parent.wait_window(self)

        def validateVal(self, value):
            try:
                if value:
                    v = int(value)
                    return True
            except ValueError:
                return False

        def okB(self):
            self.vals = np.zeros((len(self.allNames), 2), dtype=np.int8)
            for i, (r, l) in enumerate(zip(self.valR, self.valL)):
                self.vals[i, :] = np.array([int(r.get()), int(l.get())], dtype=np.int8)

            self.destroy()

        def cancelB(self):
            self.vals = None
            self.destroy()

    class FreqChange(tk.Toplevel):
        def __init__(self, parent):
            tk.Toplevel.__init__(self, parent)
            self.vals = None
            fr = tk.Frame(self)
            fr.pack()
            self.valR = []
            names = ['Freq']
            self.allNames = names
            okCMD = self.register(self.validateVal)
            vld = (okCMD, '%P')
            for i, n in enumerate(names):
                # label
                tk.Label(fr, text=n).grid(row=0, column=i + 1)
                # box 1
                self.valR.append(tk.StringVar())
                tk.Entry(fr, textvariable=self.valR[-1], validate='focusout', validatecommand=vld).grid(row=1,
                                                                                                        column=i + 1)
                self.valR[-1].set('100')
            self.che = guT.CheckControl(self, '', ['Save params'], ax=None, defaultVal=[1])
            self.che.pack()
            frBot = tk.Frame(self)
            tk.Button(frBot, text='OK', command=self.okB).pack(side=tk.LEFT)
            tk.Button(frBot, text='Cancel', command=self.cancelB).pack(side=tk.LEFT)
            frBot.pack()
            self.protocol("WM_DELETE_WINDOW", self.cancelB)
            self.transient(parent)
            self.grab_set()
            parent.wait_window(self)
            # root.quit()

        def validateVal(self, value):
            try:
                if value:
                    v = int(value)
                    return True
            except ValueError:
                return False

        def okB(self):
            self.vals = np.zeros((len(self.allNames) + 1), dtype=np.int8)
            for i, r in enumerate(self.valR):
                self.vals[i] = int(r.get())
            self.vals[-1] = self.che.getAllValues()[0]
            self.destroy()

        def cancelB(self):
            self.vals = None
            self.destroy()

    class assignControl(tk.Toplevel):
        def __init__(self, parent):
            tk.Toplevel.__init__(self, parent)
            self.vals = None
            fr = tk.Frame(self)
            fr.pack()
            tk.Label(fr, text='R').grid(row=1)
            tk.Label(fr, text='L').grid(row=2)
            self.valR = []
            self.valL = []
            names = ['M Ball', 'L Ball', 'Heel', 'Noise', 'Min Freq', 'Max Freq', 'Use log scale']
            self.allNames = names
            okCMD = self.register(self.validateVal)
            vld = (okCMD, '%P')
            for i, n in enumerate(names):
                # label
                tk.Label(fr, text=n).grid(row=0, column=i + 1)
                # box 1
                self.valR.append(tk.StringVar())
                tk.Entry(fr, textvariable=self.valR[-1], validate='focusout', validatecommand=vld).grid(row=1,
                                                                                                        column=i + 1)
                self.valR[-1].set('0')
                # box 2
                self.valL.append(tk.StringVar())
                tk.Entry(fr, textvariable=self.valL[-1], validate='focusout', validatecommand=vld).grid(row=2,
                                                                                                        column=i + 1)
                self.valL[-1].set('0')
            frBot = tk.Frame(self)
            tk.Button(frBot, text='OK', command=self.okB).pack(side=tk.LEFT)
            tk.Button(frBot, text='Cancel', command=self.cancelB).pack(side=tk.LEFT)
            frBot.pack()
            self.protocol("WM_DELETE_WINDOW", self.cancelB)
            self.transient(parent)
            self.grab_set()
            parent.wait_window(self)
            # root.quit()

        def validateVal(self, value):
            try:
                if value:
                    v = int(value)
                    return True
            except ValueError:
                return False

        def okB(self):
            self.vals = np.zeros((len(self.allNames), 2), dtype=np.int8)
            for i, (r, l) in enumerate(zip(self.valR, self.valL)):
                self.vals[i, :] = np.array([int(r.get()), int(l.get())], dtype=np.int8)

            self.destroy()

        def cancelB(self):
            self.vals = None
            self.destroy()

    def sendPing(self):
        cmd = guT.createCMD(1)
        self.theSend.send(cmd, addr=(self.STREAM_IP_ADDRESS, 12354))

    def changeFreq(self):
        self.mW = self.FreqChange(self.main.root)
        if self.mW.vals is None:
            print('Cancel was pressed')
        else:
            # send motor cmd
            print(self.mW.vals)
            cmd = guT.createCMD(14, te=self.mW.vals)
            self.theSend.send(cmd, addr=(self.STREAM_IP_ADDRESS, 12354))

    def reassign(self):
        cmd = guT.createCMD(5, [108, 1])
        # cmd = guT.createCMD(14, 10)
        # self.theSend.send(cmd, addr=(self.LEFT_IP_ADDRESS, 12354))
        self.theSend.send(cmd, addr=(self.RIGHT_IP_ADDRESS, 12354))

    def recordCmd(self):
        if self.isRecord:
            n = 2
            self.buttons['Start Recording']["text"] = "Stop recording"
            self.main.leftShoe.binaryFile = bytes(0)
            self.main.rightShoe.binaryFile = bytes(0)
            self.buttons['Start Recording'].config(bg='green')
            cmd = guT.createCMD(n)
            self.theSend.send(cmd, addr=(self.STREAM_IP_ADDRESS, 12354))
        else:
            n = 3
            self.buttons['Start Recording']["text"] = "Start recording"
            self.buttons['Start Recording'].config(bg='yellow')
            cmd = guT.createCMD(n)
            self.theSend.send(cmd, addr=(self.STREAM_IP_ADDRESS, 12354))
            self.saveDataCmd()
        self.isRecord = not self.isRecord

        self.streamCmd()

    def streamCmd(self):
        if self.isStream:
            n = 6
        else:
            n = 7
        self.isStream = not self.isStream
        cmd = guT.createCMD(n)
        self.theSend.send(cmd, addr=(self.STREAM_IP_ADDRESS, 12354))

    def reNameCmd(self):
        name = simpledialog.askstring('Name for log file', 'Name')
        if name is None:
            return
        print(name)
        self.fileName = '%s%d' % (name, int(time.time()))
        cmd = guT.createCMD(4, te=name)
        self.theSend.send(cmd, addr=(self.STREAM_IP_ADDRESS, 12354))

    def sendMotorCmd(self):
        self.mW = self.motorControl(self.main.root)
        if self.mW.vals is None:
            print('Cancel was pressed')
        else:
            # send motor cmd
            print(self.mW.vals)
            cmd = guT.createCMD(8, te=np.squeeze(self.mW.vals[:, 1]))
            self.theSend.send(cmd, addr=(self.main.console.ipAddress['l'], 12354))
            cmd = guT.createCMD(8, te=np.squeeze(self.mW.vals[:, 0]))
            self.theSend.send(cmd, addr=(self.main.console.ipAddress['r'], 12354))

    def getPressCmd(self):
        cmd = guT.createCMD(9)
        self.theSend.send(cmd, addr=(self.main.console.ipAddress['l'], 12354))
        time.sleep(1)
        self.theSend.send(cmd, addr=(self.main.console.ipAddress['r'], 12354))

    def readBinaryCmd(self):
        shoes = []
        fSave = tk.filedialog.asksaveasfile(self.main.root)
        if fSave is None:
            return shoes
        np.save(fSave, shoes)

    def saveDataCmd(self):
        fSave = tk.filedialog.asksaveasfilename()
        if fSave is None:
            return 0
        ss = [self.main.leftShoe, self.main.rightShoe]
        sided = [True, False]
        for s, sid in zip(ss, sided):
            s.saveBinaryFile(fSave)

    def enterSafeMode(self):
        cmd = guT.createCMD(10)
        self.theSend.send(cmd, addr=(self.STREAM_IP_ADDRESS, 12354))

    def resetShoes(self):
        cmd = guT.createCMD(11)
        self.theSend.send(cmd, addr=(self.STREAM_IP_ADDRESS, 12354))

    def updateParams(self):
        pass


class RealTimeConsole(guT.ConsoleFrame):
    def __init__(self, parent, nLines=5):
        guT.ConsoleFrame.__init__(self, parent, nLines=nLines, parseCMD=self.parseMSG)
        self.ipAddress = {'IP_BASE': '192.168.0.', 'r': '192.168.0.103', 'l': '192.168.0.102'}
        self.recordings = {'r': False, 'l': False}

    def parseMSG(self, text):
        self.__changeIP(text)
        self.__checkRecording(text)

    def __changeIP(self, text):
        serchStr = 'Hello from'
        if serchStr in text:
            newIP = text[11:14]
            lab = text[16]
            self.ipAddress[lab] = self.ipAddress['IP_BASE'] + newIP

    def __checkRecording(self, text):
        serchStr = 'Recording'
        if serchStr in text:
            lab = text[-1]
            self.recordings[lab] = 'Started' in text


def wrap(angles):
    return (angles + np.pi) % (2 * np.pi) - np.pi


class realTimeApp(object):
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('DeepSole System, Real Time')
        self.root.iconbitmap(r'./GUI/deepsole.ico')
        # objects
        self.theSend = tu.UDPsend()
        self.refreshTime = 10  # ms
        self.visualizeTime = 8  # s
        self.rightShoe = smartShoe(False, keepAll=False)
        self.leftShoe = smartShoe(True, keepAll=False)
        bottomFrame = tk.Frame(self.root)
        self.console = RealTimeConsole(bottomFrame)
        self.theRec = UDPreceiveDS(self.leftShoe, self.rightShoe, self.console)
        self.model = None
        self.batchSize = 10
        # GUI
        titles = ['Press', 'Acc', 'Gyro', 'Euler', 'Phase']
        names = [self.rightShoe.names[3*j:3*j+3] for j in range(4)]
        # names = [['Toe ', 'Ball ', 'Heel'], ['ax', 'ay', 'az'], ['gx', 'gy', 'gz'], ['ro', 'pi', 'ya']]
        plotColor = [['fuchsia', 'orange', 'purple'],
                     ['Chartreuse', 'darkgreen', 'chocolate'],
                     ['coral', 'brown', 'crimson'],
                     ['blue', 'teal', 'cyan']]

        self.allValsR = [j for j in self.rightShoe.all]
        self.allValsL = [j for j in self.leftShoe.all]
        self.timestampR = [self.rightShoe.timestamp for _ in self.rightShoe.all]
        self.timestampL = [self.leftShoe.timestamp for _ in self.leftShoe.all]
        self.scalePlots = True
        topFrame = tk.Frame(self.root)
        topFrame.pack(fill=tk.BOTH, expand=tk.YES)
        topFrameL = tk.Frame(topFrame)
        topFrameR = tk.Frame(topFrame)
        topFrameR.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.BOTH)
        topFrameL.pack(side=tk.LEFT, expand=tk.YES, fill=tk.BOTH)
        self.rPlot = guT.PlotPanelPandas(topFrameL, 'R', titles, names, plotColor, self.timestampR,
                                         self.rightShoe.dataFrame, color='red', number2Plot=500, showTime=True,
                                         useScale=self.scalePlots)
        self.rPlot.pack(fill=tk.BOTH, expand=tk.YES)
        self.lPlot = guT.PlotPanelPandas(topFrameL, 'L', titles, names, plotColor, self.timestampL,
                                         self.leftShoe.dataFrame, color='blue', number2Plot=500, showTime=True,
                                         useScale=self.scalePlots)
        self.lPlot.pack(fill=tk.BOTH, expand=tk.YES)
        self.filesFrame = tk.Frame(topFrameL)
        # 3d plots of orientation
        self.plot3DPanel = guT.PlotPanel3DPandas(topFrameR, 'Side', ['Left', 'Right'], [['Plot'], ['Plot']],
                                                 [['red'], ['blue']],
                                                 [self.leftShoe.dataFrame, self.rightShoe.dataFrame],
                                                 [['EUy', 'EUz', 'EUx'], ['EUy', 'EUz', 'EUx']],
                                                 figsize=(5, 5))
        self.plot3DPanel.pack(fill=tk.BOTH, expand=tk.YES)
        self.model = None
        self.shoeParams = None
        self.subID = 0
        self.freq = 100.0

        labels = [['Ping', 'Change Freq'],
                  ['Start Recording', 'Change Name'],
                  ['Motor CMD'],
                  ['Save file', 'Update Params'],
                  ['Flash FW', 'Reset Shoes']]
        self.theCom = ControlFunctionsContainer(labels, self)
        bottomFrame.pack()
        buttonsCMDs = [[self.theCom.sendPing, self.theCom.changeFreq],
                       [self.theCom.recordCmd, self.theCom.reNameCmd],
                       [self.theCom.sendMotorCmd],
                       [self.theCom.saveDataCmd, self.theCom.updateParams],
                       [self.theCom.enterSafeMode, self.theCom.resetShoes]]
        self.control = guT.ButtonPanel(bottomFrame, labels, buttonsCMDs, width=25)
        self.theCom.buttons = self.control.buttons
        self.control.grid(row=0, column=0)
        self.pressDisp = ShoePressDisp(bottomFrame)
        self.pressDisp.grid(row=0, column=1)

        self.console.grid(row=0, column=2)
        self.oldTimeR = 0
        self.oldTimeL = 0

    def updatePlots(self):
        fn = lambda x: wrap(x/8000)
        self.rPlot.plotControlFromChecksTime(self.visualizeTime, extraT=1.0, preprocess=[['EUy', 'EUz', 'EUx'],
                                                                                         [fn]])
        self.lPlot.plotControlFromChecksTime(self.visualizeTime, extraT=1.0, preprocess=[['EUy', 'EUz', 'EUx'],
                                                                                         [fn]])
        self.plot3DPanel.plotControlFromChecks()
        for pPlot, isL in zip([self.rPlot, self.lPlot], [False, True]):
            if pPlot.maxValsAux is None:
                continue
            windowVals = pPlot.all.iloc[-2:, :].copy()
            divAux = pPlot.maxValsAux - pPlot.minValsAux
            divAux[divAux == 0] = 1
            windowVals = (windowVals-pPlot.minValsAux) / (divAux)
            # 'pToe', 'pBall', 'pHeel'
            self.pressDisp.updatePlot(toe=np.clip(windowVals['pToe'].values[-1], 0, 1),
                                      ball=np.clip(windowVals['pBall'].values[-1], 0, 1),
                                      heel=np.clip(windowVals['pHeel'].values, 0, 1)
                                      [-1], axLeft=isL)


        if not self.theCom.isRecord:
            self.theCom.buttons['Start Recording']["text"] = "[%.1fHz]Stop recording[%.1fHz]" % (self.lPlot.dt,
                                                                                                 self.rPlot.dt)

    def exportCMD(self, exportFlag=True):
        if self.yPred is None:
            e = self.predictCMD()
            if e:
                return True
        yRshoe, yLshoe = self.yPred
        if self.mat is None:
            laps = None
        else:
            laps = self.mat.lap
        self.shoeParams = pandas.DataFrame()
        root = tk.Tk()
        filePath = tk.filedialog.asksaveasfilename(parent=root, title='Save Paramaters as',
                                                   filetypes=(
                                                       ("Excel files", ("*.xls", "*.xlsx")), ("all files", "*.*")))
        root.withdraw()
        if filePath is None:
            return
        writer = pandas.ExcelWriter(filePath, engine='xlsxwriter')
        self.shoeParams.to_excel(writer)
        writer.save()
        writer.close()

    def exportRaw(self):
        if self.leftShoe is None or self.rightShoe is None:
            messagebox.showinfo('Cannot load file', 'Shoe object cannot be empty, please load file')
        sub = tu.ShoeSubject(self.leftShoe, self.rightShoe, self.subID, matInfo=self.mat)
        labels = ['Save Pickle', 'Save Matlab', 'Save Excel']
        buttonsCMDs = [sub.savePickle, sub.saveMatlab, sub.saveExcel]
        root = tk.Tk()
        control = guT.ButtonPanel(root, labels, buttonsCMDs)
        control.pack()

    def loopFunctions(self):
        self.updatePlots()
        self.root.after(self.refreshTime, self.loopFunctions)

    def startApp(self):
        self.startReceive()
        self.loopFunctions()
        self.root.protocol("WM_DELETE_WINDOW", self.stopApp)
        self.root.mainloop()

    def stopApp(self):
        self.root.destroy()

    def startReceive(self):
        self.theRec.startThread()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app = realTimeApp()
    app.startApp()

