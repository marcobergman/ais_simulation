#!/usr/bin/env python
import wx
import socket
import time
import ais_simulation

simulation = ais_simulation.Simulation()

class UI(wx.Frame):

    def __init__(self, parent, title):
        super(UI, self).__init__(parent, title = title, size=(460,150))

        self.InitUI()
        self.Centre()
        self.Show()

    def InitUI(self):

        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(0,0)

        ## Set up Statictext
        text1 = wx.StaticText(panel, label = "filename")
        sizer.Add(text1, pos = (0, 0), flag = wx.ALL, border = 3)


        ## Setup up controls
        filename = wx.TextCtrl(panel, value="ais_simulation.xml")
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

        buttonStart.Bind(wx.EVT_BUTTON, simulation.startBoats)
        buttonPause.Bind(wx.EVT_BUTTON, simulation.pauseBoats)
        buttonResume.Bind(wx.EVT_BUTTON, simulation.resumeBoats)
        buttonStop.Bind(wx.EVT_BUTTON, simulation.stopBoats)

        buttonMinus10.Bind(wx.EVT_BUTTON, simulation.steerBoat)
        buttonMinus1.Bind(wx.EVT_BUTTON, simulation.steerBoat)
        buttonPlus1.Bind(wx.EVT_BUTTON, simulation.steerBoat)
        buttonPlus10.Bind(wx.EVT_BUTTON, simulation.steerBoat)

        panel.SetSizerAndFit(sizer)


simulation.loadBoats("ais_simulation.xml")

app = wx.App()
UI(None, title = 'AIS Simulator')
app.MainLoop()

