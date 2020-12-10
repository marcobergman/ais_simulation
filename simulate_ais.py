#!/usr/bin/env python
import wx
import socket
import time
import ais_simulation
import threading

simulation = ais_simulation.Simulation()

DEFAULT_FILENAME = "ais_simulation.gpx"

class SimulatorFrame(wx.Frame):

    def __init__(self, parent, title):
        super(SimulatorFrame, self).__init__(parent, title = title, size=(490,180))

        self.InitUI()
        self.Centre()
        self.Show()

    def InitUI(self):

        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(0,0)

        ## Set up Statictext
        text1 = wx.StaticText(panel, label = "filename")
        sizer.Add(text1, pos = (0, 0), flag = wx.ALL, border = 3)
        text2 = wx.StaticText(panel, label = "true wind")
        sizer.Add(text2, pos = (3, 0), flag = wx.ALL, border = 3)
        text3 = wx.StaticText(panel, label = "current")
        sizer.Add(text3, pos = (4, 0), flag = wx.ALL, border = 3)
        text4 = wx.StaticText(panel, label = "speedup")
        sizer.Add(text4, pos = (0, 3), flag = wx.ALL, border = 3)
        

        ## Setup up controls
        filename = wx.TextCtrl(panel, value=DEFAULT_FILENAME)
        sizer.Add(filename, pos = (0,1), flag = wx.EXPAND|wx.ALL, span=(1,2))
        def OnChange_filename(event):
             buttonStart.filename = filename.GetValue()
        self.Bind(wx.EVT_TEXT, OnChange_filename, filename)

        # Set up buttons
        buttonStart = wx.Button(panel, label = "Start" )
        sizer.Add(buttonStart, pos = (1, 0), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)
        buttonStart.filename = filename.GetValue()

        buttonPause = wx.Button(panel, label = "Pause" )
        sizer.Add(buttonPause, pos = (1, 2), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)

        buttonResume = wx.Button(panel, label = "Resume" )
        sizer.Add(buttonResume, pos = (1, 3), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)

        buttonStop = wx.Button(panel, label = "Stop" )
        sizer.Add(buttonStop, pos = (1, 4), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)

        buttonMinus10 = wx.Button(panel, label = "-10" )
        sizer.Add(buttonMinus10, pos = (2, 0), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)
        buttonMinus10.steerValue=-10

        buttonMinus1 = wx.Button(panel, label = "-1" )
        sizer.Add(buttonMinus1, pos = (2, 1), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)
        buttonMinus1.steerValue=-1

        buttonPlus1 = wx.Button(panel, label = "+1" )
        sizer.Add(buttonPlus1, pos = (2, 3), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)
        buttonPlus1.steerValue=1

        buttonPlus10 = wx.Button(panel, label = "+10" )
        sizer.Add(buttonPlus10, pos = (2, 4), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)
        buttonPlus10.steerValue=10

        buttonSetWind = wx.Button(panel, label = "Set wind")
        sizer.Add(buttonSetWind, pos = (3, 4), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)

        buttonSetCurrent = wx.Button(panel, label = "Set current")
        sizer.Add(buttonSetCurrent, pos = (4, 4), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)
        
        textSpeedup = wx.TextCtrl(panel, value="60", size=(70,10))
        sizer.Add(textSpeedup, pos = (0, 4), flag = wx.EXPAND|wx.ALL, border = 3)
        def OnChange_speedup(event):
            simulation.setSpeedup(float(textSpeedup.GetValue()))
        textSpeedup.Bind(wx.EVT_TEXT, OnChange_speedup, textSpeedup)
        
        textTwd = wx.TextCtrl(panel, value="225", size=(70,10))
        sizer.Add(textTwd, pos = (3, 1), flag = wx.EXPAND|wx.ALL, border = 3)
        textTws = wx.TextCtrl(panel, value="15", size=(70,20))
        sizer.Add(textTws, pos = (3, 2), flag = wx.EXPAND|wx.ALL, border = 3)
        textTwv = wx.TextCtrl(panel, value="10", size=(70,20))
        sizer.Add(textTwv, pos = (3, 3), flag = wx.EXPAND|wx.ALL, border = 3)

        textCurD = wx.TextCtrl(panel, value="270", size=(70,10))
        sizer.Add(textCurD, pos = (4, 1), flag = wx.EXPAND|wx.ALL, border = 3)
        textCurS = wx.TextCtrl(panel, value="2.0", size=(70,20))
        sizer.Add(textCurS, pos = (4, 2), flag = wx.EXPAND|wx.ALL, border = 3)
        textCurV = wx.TextCtrl(panel, value="0", size=(70,20))
        sizer.Add(textCurV, pos = (4, 3), flag = wx.EXPAND|wx.ALL, border = 3)

        buttonStart.Bind(wx.EVT_BUTTON, simulation.startBoats)
        buttonPause.Bind(wx.EVT_BUTTON, simulation.pauseBoats)
        buttonResume.Bind(wx.EVT_BUTTON, simulation.resumeBoats)
        buttonStop.Bind(wx.EVT_BUTTON, simulation.stopBoats)

        buttonMinus10.Bind(wx.EVT_BUTTON, simulation.steerBoat)
        buttonMinus1.Bind(wx.EVT_BUTTON, simulation.steerBoat)
        buttonPlus1.Bind(wx.EVT_BUTTON, simulation.steerBoat)
        buttonPlus10.Bind(wx.EVT_BUTTON, simulation.steerBoat)
        
        def OnChange_wind(event):
             buttonSetWind.twd = textTwd.GetValue()
             buttonSetWind.tws = textTws.GetValue()
             buttonSetWind.twv = textTwv.GetValue()
        self.Bind(wx.EVT_TEXT, OnChange_wind, textTwd)
        self.Bind(wx.EVT_TEXT, OnChange_wind, textTws)
        self.Bind(wx.EVT_TEXT, OnChange_wind, textTwv)
        buttonSetWind.Bind(wx.EVT_BUTTON, simulation.setTrueWind)
        OnChange_wind(None)

        def OnChange_current(event):
             buttonSetCurrent.curd = textCurD.GetValue()
             buttonSetCurrent.curs = textCurS.GetValue()
             buttonSetCurrent.curv = textCurV.GetValue()
             simulation.setTrueCurrent
        self.Bind(wx.EVT_TEXT, OnChange_current, textCurD)
        self.Bind(wx.EVT_TEXT, OnChange_current, textCurS)
        self.Bind(wx.EVT_TEXT, OnChange_current, textCurV)
        buttonSetCurrent.Bind(wx.EVT_BUTTON, simulation.setTrueCurrent)
        OnChange_current(None)

        panel.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_CLOSE, self.OnExitApp)
        
        text5 = wx.StaticText(panel)
        sizer.Add(text5, pos = (2, 2), flag = wx.ALL, border = 3)
        
        def updateHeading(self):
            heading = simulation.getHeading()
            text5.SetLabel(heading)
        
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, updateHeading, self.timer)
        self.timer.Start(1000)
        
    def OnExitApp(self, event):
        print ('--- Window closed')
        simulation.stopBoats(event)
        simulation.wrapup()
        self.Destroy()
        



simulation.loadBoats(DEFAULT_FILENAME)
print("--- Initial positioning of boats")
simulation.showBoats()

app = wx.App()
myFrame = SimulatorFrame(None, title = 'AIS Simulator')
app.MainLoop()

