#########################################################
# CXV - Coral X-Ray Viewer
#
# @author:    Adam Childs
# @contact:   adchilds@eckerd.edu
#
# @copyright: owned and maintained by the
#             US Geological Survey (USGS),
#             Department of Interior (DOI)
#########################################################
from Controllers import xml_controller
from Views import overlay_view
from lib import progress_bar
from yapsy.PluginManager import PluginManager
import numpy as np
import os
import threading
import wx

class Controller(threading.Thread):
    """ The plugin_controller allows the user to write their
    own Python scripts for the manipulation of the images, via
    image manipulation algorithms. This class facilitates the
    loading of the files, the running of the scripts, etc.
    """

    def __init__(self, pb, overlay_controller, dicom_controller, model):
        threading.Thread.__init__(self)
        self.pb = pb
        self.controller = overlay_controller
        self.dicom_controller = dicom_controller
        self.model = model
        self.start()

    def run(self):
        """ Runs the given algorithms """
        
        wx.CallAfter(self.pb.update, 'Retrieving coral region')
        # Load in original dicom pixel data and normalize
        coral_slab = self.model.ds.pixel_array.astype(np.double)
        coral_slab = self.model.normalize_intensity(coral_slab)
        # Cut down dicom pixel data to user defined coral slab region
        x, y, dx, dy = self.dicom_controller.coral_slab
        coral_slab = coral_slab[y:dy, x:dx]
        
        # Get the default plugin directory, using XML
        path = os.path.expanduser('~')
        xml = xml_controller.Controller(path + '\.cxvrc.xml')
        xml.load_file()

        if os.path.exists(os.path.expanduser('~') + os.sep + "plugins"):
            default_dir = os.path.expanduser('~') + os.sep + "plugins"
        else:
            default_dir = self.dicom_controller.view.get_main_dir() + os.sep + "plugins"

        if xml.get_plugin_directory() == "":
            directory = [default_dir]
        else:
            directory = [default_dir, xml.get_plugin_directory()]

        # Load the plugins from the default plugin directory.
        manager = PluginManager()
        manager.setPluginPlaces(directory)
        manager.setPluginInfoExtension('plugin')
        manager.collectPlugins()
    
        # Loop over all plugins that have been found
        count = 0;
        for plugin in manager.getAllPlugins():
            # Initialize the plugin so that we can call it's methods
            plugin.plugin_object.initPlugin(self.controller, coral_slab, self.model, self.pb, count)

            # Print a little information about the plugin (DEBUG)
            plugin.plugin_object.print_information()

            # Run the plugin's algorithm
            plugin.plugin_object.calc_filter()

            # Update count so that the next filter will be added to the next overlay
            count += 1

        # Add the original coral_slab to the overlay
        self.controller.overlays.append(coral_slab)
        self.controller.alphas.append(100)
        wx.CallAfter(self.controller.add_overlay)

        # Update the progress bar to let the user know we've finished
        # running the algorithms
        wx.CallAfter(self.pb.finish, 'Finishing up')

        # Display the filters
        if self.controller.show:
            # Get the size of alphas (number of filters) minus one.
            # The last alpha should be 0. Set all the alphas to the same
            # value (except for the last one), so divide 100 by the number
            # of alphas minus one.
#            value = 100 / (len(self.controller.alphas) - 1)
            value = 0
            for i in range(len(self.controller.alphas) - 1):
                self.controller.alphas[i] = int(value)

            # Set the last one to 0 ourselves just to make sure
            self.controller.alphas[len(self.controller.alphas) - 1] = 100

            wx.CallAfter(self.controller.display)
            wx.CallAfter(self.controller.view.Show)
        else:
            wx.CallAfter(self.controller.display)

    def calc_filter(self):
        raise NotImplementedError( "Algorithm needs to be implemented!" )