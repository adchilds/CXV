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
import dicom
import numpy as np
import ctypes
import os

class Model():

    def __init__(self):
        """Model attributes"""
        self.ds = None
        self.image_array = None
        self.path = None

    def load_dicom_image(self, path):
        """Loads DICOM file and return the image associated with it"""
        self.path = path
        self.ds = dicom.read_file(self.path)
        return self.ds.pixel_array.astype(np.double)

    def allocate_array(self, shape):
        """Allocates array using Python C API function PyMem_Malloc"""
        y, x, z = shape
        num_of_elements = y * x * z
        size_of_element = ctypes.sizeof(ctypes.c_double)    # 8 bytes on all platforms
        ptr = ctypes.pythonapi.PyMem_Malloc(num_of_elements*size_of_element)
        ptr = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_double*num_of_elements))
        rgba = np.ctypeslib.as_array(ptr.contents)
        rgba = rgba.reshape(y, x, z)
        return (rgba, ptr)

    def deallocate_array(self, ptr):
        """Deallocates array using Python C API function PyMem_Free"""
        ctypes.pythonapi.PyMem_Free(ptr)

    def rotate_image(self, img):
        """ Rotates the given image by 90 degrees (counter-clockwise)
        
        @var img - The image array to rotate
        """
        return np.rot90(img)

    def normalize_intensity(self, img):
        """Normalizes raw intensity values to real values between 0.0 and 1.0"""
        img -= img.min()
        img /= img.max()
        return img

    def invert_grayscale(self, img):
        """Use inverted grayscale mapping"""
        img = 1 - img
        return img

    def set_display_data(self, rgba, data, alpha):
        """Sets values in data to the RGBA bands of rgba with specified alpha mask"""
        rgba[:,:,0] = data  # R
        rgba[:,:,1] = data  # G
        rgba[:,:,2] = data  # B
        rgba[:,:,3] = alpha # A
        return rgba

    def get_image(self):
        """Returns raw RGBA array from memory"""
        return self.image_array

    def get_image_shape(self):
        """Returns the shape of the dicom pixel array"""
        return self.ds.pixel_array.shape

    def get_dicom_path(self):
        """Returns the full path of the current DICOM file"""
        return self.path

    def get_image_name(self):
        """Returns the DICOM file name"""
        return self.path.split(os.sep)[-1]

    def print_data_usage(self):
        """Prints the size of the image in memory (MB)"""
        print 'image_array:', self.image_array.nbytes/1000000, 'MB @', id(self.image_array)

    def get_meta_description(self, data_element):
        """Returns description of a meta data element"""
        return data_element.description()

    def get_meta_value(self, data_element):
        """Returns value of a meta data element"""
        return data_element._get_repval()