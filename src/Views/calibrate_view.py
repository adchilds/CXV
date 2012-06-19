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
    
    def __init__(self, controller):
        self.controller = controller
        
        wx.MiniFrame.__init__(self,
                              parent=None,
                              title="Density Parameters",
                              size=(300, 200),
                              style=wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        
        self.panel = wx.Panel(self)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        
        for each in self.pane_data():
            self.add_pane(self.panel, panel_sizer, *each)
        
        apply = wx.Button(self.panel, -1, 'Apply')
        panel_sizer.Add(apply, 0, wx.ALIGN_CENTER)
        panel_sizer.AddSpacer(5)
        self.panel.SetSizerAndFit(panel_sizer)
        self.panel.SetSizerAndFit(panel_sizer)
        
        self.Bind(wx.EVT_BUTTON, self.controller.on_apply, apply)
        self.Bind(wx.EVT_CLOSE, self.controller.on_close)
        
    def add_pane(self, panel, panel_sizer, label, units, default):
        sb = wx.StaticBox(panel, -1, '')
        sbs = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        st = wx.StaticText(panel, -1, label, size=(110, -1))
        tc = wx.TextCtrl(panel, -1, default, size=(100, -1))
        st2 = wx.StaticText(panel, -1, units)
        
        sbs.Add(st)
        sbs.AddSpacer(5)
        sbs.Add(tc)
        sbs.AddSpacer(5)
        sbs.Add(st2)
        
        panel_sizer.Add(sbs, 1, wx.EXPAND)
        panel_sizer.AddSpacer(5)
        
    def pane_data(self):
        return [
                ('Wedge density: ', 'g/cm'+u'\u00B3', '2.790'),
                ('Min wedge thickness: ', 'mm', '1.0'),
                ('Max wedge thickness: ', 'mm', '5.0')
                ]