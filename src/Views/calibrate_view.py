#########################################################
# CXV - Coral X-Ray Viewer
#
# @author:    Luke Mueller
# @contact:   muellelj@eckerd.edu or lmueller62@gmail.com
#
# @author:    Adam Childs
# @contact:   adchilds@eckerd.edu
#
# @copyright: owned and maintained by the
#             US Geological Survey (USGS),
#             Department of Interior (DOI)
#########################################################
import wx

class View(wx.MiniFrame):
    
    def __init__(self, controller, unit='cm', ppu='',
                 dens=2.79, min_thick=1.0, max_thick=5.0):
        self.controller = controller
        self.unit_selected = unit
        self.pixels_per_unit = ppu
        self.wedge_density = dens
        self.min_wedge_thickness = min_thick
        self.max_wedge_thickness = max_thick
        
        self.density_panel = None # Holds our density parameter widgets
        self.tc1 = None # Holds our pixels_per_unit value
        self.dens = None
        self.min = None
        self.max = None
        
        wx.MiniFrame.__init__(self,
                              parent=None,
                              title="Set Calibration Parameters",
                              size=(300, 300),
                              style=wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        
        panel = wx.Panel(self)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(self.add_unit_pane(panel, panel_sizer), 0, wx.EXPAND)
        panel_sizer.AddSpacer(5)
        panel_sizer.Add(self.add_density_pane(panel, panel_sizer), 0, wx.EXPAND)
        panel_sizer.AddSpacer(5)
        save_button = wx.Button(panel, 0, 'Save')
        panel_sizer.Add(save_button, 0, wx.CENTER)
        panel.SetSizerAndFit(panel_sizer)


        self.Bind(wx.EVT_BUTTON, self.controller.on_apply, save_button)
        self.Bind(wx.EVT_CLOSE, self.controller.on_close)

    def density_pane_data(self):
        return [
                ('Wedge density: ', 'g/cm'+u'\u00B3', str(self.wedge_density)),
                ('Min wedge thickness: ', 'mm', str(self.min_wedge_thickness)),
                ('Max wedge thickness: ', 'mm', str(self.max_wedge_thickness))
                ]

    def add_density_pane(self, panel, panel_sizer):
        """ Creates the Density Parameters panel """
        self.density_panel = wx.StaticBox(panel, -1, 'Density Parameters')
        density_panel_sizer = wx.StaticBoxSizer(self.density_panel, wx.VERTICAL)

        # Create a horizontal row of widgets
        i = 0
        for each in self.density_pane_data():
            sb = wx.StaticBox(panel, -1, '')
            sbs = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
            st = wx.StaticText(panel, -1, each[0], size=(110, -1))

            if i == 0:
                self.dens = wx.TextCtrl(panel, -1, str(self.controller.density), size=(100, -1), style=wx.TE_RIGHT)
            elif i == 1:
                self.min = wx.TextCtrl(panel, -1, str(self.controller.min_thickness), size=(100, -1), style=wx.TE_RIGHT)
            else:
                self.max = wx.TextCtrl(panel, -1, str(self.controller.max_thickness), size=(100, -1), style=wx.TE_RIGHT)

            st2 = wx.StaticText(panel, -1, each[1])
            
            sbs.Add(st)
            sbs.AddSpacer(5)

            if i == 0:
                sbs.Add(self.dens)
            elif i == 1:
                sbs.Add(self.min)
            else:
                sbs.Add(self.max)

            sbs.AddSpacer(5)
            sbs.Add(st2)
            
            density_panel_sizer.Add(sbs, 1, wx.EXPAND)
            density_panel_sizer.AddSpacer(5)
            i += 1

        return density_panel_sizer

    def add_unit_pane(self, panel, panel_sizer):
        """ Creates the Unit Measurement panel """
        unit_panel = wx.StaticBox(panel, -1, 'Unit of Measurement')
        unit_panel_sizer = wx.StaticBoxSizer(unit_panel, wx.VERTICAL)

        # Create horizontal row of widgets 1
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)

        st1 = wx.StaticText(panel, label='UNIT:', size=(110, -1))
        self.unit_choices = ['in (INCHES)',
                            'cm (CENTIMETERS)',
                            'mm (MILLIMETERS)'
                            ]
        unit_cb = wx.ComboBox(panel, -1, '100%',
                                         choices=self.unit_choices,
                                         style=wx.CB_DROPDOWN|wx.CB_READONLY)

        if self.unit_selected == 'in':
            unit_cb.SetValue(self.unit_choices[0])
        elif self.unit_selected == 'cm':
            unit_cb.SetValue(self.unit_choices[1])
        else:
            unit_cb.SetValue(self.unit_choices[2])

        unit_cb.Bind(wx.EVT_COMBOBOX, self.on_unit_choice)

        hbox1.Add(st1)
        hbox1.AddSpacer(5)
        hbox1.Add(unit_cb)

        # Create horizontal row of widgets 2
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)

        self.st2 = wx.StaticText(panel, label='Pixels per unit (mm):', size=(110, -1))
        self.tc1 = wx.TextCtrl(panel, style=wx.TE_RIGHT)

        if self.controller.pixels_per_unit is not '':
            self.tc1.SetValue(str(self.controller.pixels_per_unit))
        else:
            self.tc1.SetValue(str(self.pixels_per_unit))

        st3 = wx.StaticText(panel, -1, 'px')

        hbox2.Add(self.st2)
        hbox2.AddSpacer(5)
        hbox2.Add(self.tc1)
        hbox2.AddSpacer(5)
        hbox2.Add(st3)

        # Create horizontal row of widgets 3
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        set_button = wx.Button(panel, -1, 'Set')
        #set_button.SetToolTip(wx.ToolTip('Click two points that represent one unit'))
        self.Bind(wx.EVT_BUTTON, self.controller.on_set_pixel_unit, set_button)
        hbox3.Add(set_button)

        # Add all other sizers to the main unit_panel_sizer
        unit_panel_sizer.Add(hbox1)
        unit_panel_sizer.AddSpacer(5)
        unit_panel_sizer.Add(hbox2)
        unit_panel_sizer.AddSpacer(5)
        unit_panel_sizer.Add(hbox3, 0, wx.CENTER)

        # Return the unit_panel_sizer
        return unit_panel_sizer

    def on_unit_choice(self, event):
        """ Fired when the user selects a unit of measurement to use from
        the dropdown combobox.
        """
        print self.unit_choices[event.GetSelection()]
        self.unit_selected = self.unit_choices[event.GetSelection()]
        self.st2.SetLabel('Pixels per unit (' + self.unit_choices[event.GetSelection()][:2] + '):')