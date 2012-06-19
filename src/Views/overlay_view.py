#########################################################
# CXV - Coral X-Ray Viewer
#
# @author:    Luke Mueller
# @contact:   muellelj@eckerd.edu or lmueller62@gmail.com
#
# @copyright: owned and maintained by the
#             US Geological Survey (USGS),
#             Department of Interior (DOI)
#########################################################
import wx

class View(wx.MiniFrame):
    
    def __init__(self, controller, dicom_view):
        self.controller = controller
        self.dicom_view = dicom_view
        
        wx.MiniFrame.__init__(self,
                              parent=None,
                              title="Overlay",
                              size=(200, 300),
                              style=wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        self.ids = []
        panel = wx.Panel(self)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.AddSpacer(5)
        
        for each in self.pane_data():
            i = self.pane_data().index(each)
            self.add_pane(panel, panel_sizer, i, *each)
        
        apply = wx.Button(panel, -1, 'Apply')
        text = wx.StaticText(panel, -1, 'Overlays can\'t exceed 100%')
        panel_sizer.Add(apply, 0, wx.ALIGN_CENTER)
        panel_sizer.AddSpacer(5)
        panel_sizer.Add(text, 0, wx.ALIGN_CENTER)
        panel.SetSizerAndFit(panel_sizer)
        
        self.Bind(wx.EVT_BUTTON, self.controller.display, apply)
        self.Bind(wx.EVT_CLOSE, self.on_close, self)
        self.Bind(wx.EVT_MOVE, self.dicom_view.controller.cleanup)
        
    def add_pane(self, panel, sizer, i, label, enabled):
        cb_id = wx.NewId()
        tc_id = wx.NewId()
        s_id = wx.NewId()
        self.ids.append((cb_id, tc_id, s_id))
        
        sb = wx.StaticBox(panel, -1, label)
        sbs = wx.StaticBoxSizer(sb, wx.VERTICAL)
        sbs.AddSpacer(5)
        
        bs1 = wx.BoxSizer(wx.HORIZONTAL)
        cb = wx.CheckBox(panel, cb_id, ' Show')
        cb.SetValue(enabled)
        self.Bind(wx.EVT_CHECKBOX, self.controller.find_items, cb)
        bs1.Add(cb)
        sbs.Add(bs1)
        sbs.AddSpacer(10)
            
        bs2 = wx.BoxSizer(wx.HORIZONTAL)
        st = wx.StaticText(panel, -1, 'Opacity: ')
        tc = wx.TextCtrl(panel, tc_id, '50%', size=(60,-1), style=wx.TE_PROCESS_ENTER)
        tc.Enable(enabled)
        self.Bind(wx.EVT_TEXT_ENTER, self.controller.find_items, tc)
        bs2.AddMany([st, tc])
        sbs.Add(bs2)
        sbs.AddSpacer(10)
        
        bs3 = wx.BoxSizer(wx.HORIZONTAL)
        s = wx.Slider(panel, s_id, 50, 0, 100)
        s.Enable(enabled)
        self.Bind(wx.EVT_SLIDER, self.controller.find_items, s) 
        bs3.Add(s, 1, wx.EXPAND)
        sbs.Add(bs3, 1, wx.EXPAND)
        
        sizer.Add(sbs, 1, wx.EXPAND)
        sizer.AddSpacer(10)
        
    def pane_data(self):
        return [
                ('FFT + Butterworth HPF', True),
                ('Sobel Filter', True)
                #('Base Image', False)
                ]
        
    def create_statusbar(self):
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(1)
        self.statusbar.SetStatusText('Overlays can\'t exceed 100%', 0)
        self.statusbar.SetStatusStyles([wx.SB_FLAT])
        
    def on_close(self, event):
        self.Hide()