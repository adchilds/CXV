from Controllers import plugin_controller
from yapsy.IPlugin import IPlugin
import math
import numpy as np
import wx

class Filters(IPlugin):
    """ Test filter """

    def __init__(self):
        pass

    def initPlugin(self, overlay_controller, coral_slab, model, progress_bar, overlay):
        self.overlay_controller = overlay_controller    # Overlay Controller
        self.coral_slab = coral_slab                    # The coral slab we're filtering
        self.model = model                              # The model (image)
        self.pb = progress_bar                          # The progress bar to update
        self.overlay_num = overlay                      # The overlay this filter is added to

    def print_information(self):
        print 'Running Test plugin...'
        print '   Applying to overlay ' + str(self.overlay_num)

    def calc_filter(self):
        """ Must provide an implementation for the run method """
        wx.CallAfter(self.pb.update, 'Applying Test Filter to overlay ' + str(self.overlay_num))
        self.overlay_controller.overlays.append(self.coral_slab)
        self.overlay_controller.alphas.append(0)
        wx.CallAfter(self.pb.update, 'Completed Test Filter')