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
                              title="Set Calibration Parameters",
                              size=(300, 400),
                              style=wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        
        self.panel = wx.Panel(self)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)

        self.add_unit_pane(self.panel, panel_sizer, 'Unit of Measurement:')

        for each in self.density_pane_data():
            self.add_density_pane(self.panel, panel_sizer, *each)
        
        apply = wx.Button(self.panel, -1, 'Save')
        panel_sizer.Add(apply, 0, wx.ALIGN_CENTER)
        panel_sizer.AddSpacer(5)
        self.panel.SetSizerAndFit(panel_sizer)

        self.Bind(wx.EVT_BUTTON, self.controller.on_apply, apply)
        self.Bind(wx.EVT_CLOSE, self.controller.on_close)

    def add_unit_pane(self, panel, panel_sizer, label):
        outer_sb = wx.StaticBox(panel, -1, label)
        sbs = wx.StaticBoxSizer(outer_sb, wx.VERTICAL)

        # Inner 1
        unit_st = wx.StaticText(panel, -1, 'Unit:')
        rb1 = wx.RadioButton(panel, label='in', style=wx.RB_GROUP)
        rb2 = wx.RadioButton(panel, label='cm')
        rb3 = wx.RadioButton(panel, label='mm')

        # Inner 2
        pixels_st = wx.StaticText(panel, -1, '# of Pixels per Unit:')
        pixels_ta = wx.TextCtrl(panel, style=wx.TE_LEFT, value='0')

        # Inner 3
        set = wx.Button(panel, -1, 'Set')

        # Add Inner 1 to Sizer 1
        inner_sb = wx.StaticBox(panel, -1, '')
        sizer_one = wx.StaticBoxSizer(inner_sb, wx.HORIZONTAL)
        sizer_one.Add(unit_st)
        sizer_one.AddSpacer(5)
        sizer_one.Add(rb1)
        sizer_one.Add(rb2)
        sizer_one.Add(rb3)

        # Add Inner 2 to Sizer 2
        sizer_two = wx.StaticBoxSizer(inner_sb, wx.HORIZONTAL)
        sizer_two.Add(pixels_st)
        sizer_two.AddSpacer(5)
        sizer_two.Add(pixels_ta)

        #self.rb1.Bind(wx.EVT_RADIOBUTTON, self.SetVal)
        #self.rb2.Bind(wx.EVT_RADIOBUTTON, self.SetVal)
        #self.rb3.Bind(wx.EVT_RADIOBUTTON, self.SetVal)

        sbs.Add(sizer_one, 1, wx.EXPAND)
        sbs.Add(sizer_two, 1, wx.EXPAND)
        sbs.AddSpacer(5)
        sbs.Add(set, 0, wx.ALIGN_CENTER)

        panel_sizer.Add(sbs, 1, wx.EXPAND)
        panel_sizer.AddSpacer(5)

    def add_density_pane(self, panel, panel_sizer, label, units, default):
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

    def density_pane_data(self):
        return [
                ('Wedge density: ', 'g/cm'+u'\u00B3', '2.790'),
                ('Min wedge thickness: ', 'mm', '1.0'),
                ('Max wedge thickness: ', 'mm', '5.0')
                ]