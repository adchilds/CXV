from Controllers import xml_controller
import os
import wx
import wx.lib.filebrowsebutton as filebrowse

class BrowseDialog(wx.Dialog):
    """ This class is used for displaying a wx.Dialog()
    that prompts the user to supply a default directory
    where their plugins may be found.
    """

    def __init__(self, parent, title):
        super(BrowseDialog, self).__init__(parent=parent, title=title)

        # Added to avoid unnecessary call to dbbCallback()
        self.directory = ""
        self.hack = False

        # Load the XML file so that we can access some data.
        # It should have already been created. If not, dicom_controller
        # should have taken care of that by now.
        path = os.path.expanduser('~')
        self.xml = xml_controller.Controller(path + '\.cxvrc.xml')
        self.xml.load_file()
        self.plugin_directory = self.xml.get_plugin_directory()

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        sb = wx.StaticBox(panel)
        sbs = wx.StaticBoxSizer(sb, orient=wx.VERTICAL)
        self.dbb = filebrowse.DirBrowseButton(
            panel, -1, size=(450, -1), changeCallback = self.on_browse_callback)
        self.dbb.SetValue(self.plugin_directory, self.on_browse_callback)
        sbs.Add(self.dbb)

        panel.SetSizer(sbs)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, label='Ok')
        closeButton = wx.Button(self, label='Close')
        hbox2.Add(okButton)
        hbox2.Add(closeButton, flag=wx.LEFT, border=5)

        vbox.Add(panel, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        vbox.Add(hbox2, flag= wx.ALIGN_RIGHT|wx.TOP|wx.BOTTOM|wx.RIGHT, border=5)

        self.SetSizer(vbox)
        self.Fit()

        okButton.Bind(wx.EVT_BUTTON, self.on_ok)
        closeButton.Bind(wx.EVT_BUTTON, self.on_close)

    def on_browse_callback(self, event): 
        if self.hack:
            self.hack = False
        else:
            self.directory = event.GetString()

    def on_ok(self, event):
        # Set the <plugin_directory> in the xml config file
        self.xml.set_plugin_directory(self.directory)

        # Fire the on_close event. We don't need this open anymore.
        print 'Plugin directory set to:', self.xml.get_plugin_directory()
        self.on_close(event)

    def on_close(self, event):
        self.Destroy()