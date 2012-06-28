from Controllers import plugin_controller
from yapsy.IPlugin import IPlugin
import math
import numpy as np
import wx

class Filters(IPlugin):
    """ Fast Fourier Transform + Butterworth Highpass filter """

    def __init__(self):
        pass

    def initPlugin(self, overlay_controller, coral_slab, model, progress_bar, overlay):
        self.overlay_controller = overlay_controller    # Overlay Controller
        self.coral_slab = coral_slab                    # The coral slab we're filtering
        self.model = model                              # The model (image)
        self.pb = progress_bar                          # The progress bar to update
        self.overlay_num = overlay                      # The overlay this filter is added to

    def print_information(self):
        print 'Running Butterworth plugin...'
        print '   Applying to overlay ' + str(self.overlay_num)

    def calc_filter(self):
        """ Must provide an implementation for the run method """

        wx.CallAfter(self.pb.update, 'Applying FFT + Butterworth HPF to overlay ' + str(self.overlay_num))
        iht, iwd = self.coral_slab.shape
        #zero pad image to a power of 2 to speed up FFT
        vpad = 2**(int(math.ceil(math.log(iht, 2))))
        hpad = 2**(int(math.ceil(math.log(iwd, 2))))
        fImg = np.zeros(shape=(vpad, hpad), dtype=np.double, order='C')
        fImg[0:iht, 0:iwd] = self.coral_slab
        #FFT
        fImg = np.fft.fftshift(np.fft.fft2(fImg))
        #find center row and column
        cr = fImg.shape[0]/2
        cc = fImg.shape[1]/2
        #compute distance for every pixel from center
        D = np.ones(shape=(vpad, hpad), dtype=np.double, order='C')
        for row in range(iht):
            for col in range(iwd):
                D[row][col] = math.sqrt((col-cc)**2 + (row-cr)**2)
        D[cr][cc] = 0.00000001  # avoid zero-division warning 
        #Create the Butterworth, high-pass filter
        Do = 25
        p = 2
        H = 1/(1 + (Do/D)**(2*p))
        #Highpass filter the source image & strip off the zero-padded regions
        fi = H*fImg
        fi = np.fft.ifftshift(fi)
        fi = np.abs(np.fft.ifft2(fi))
        fi = fi[0:iht, 0:iwd]

        # Create the overlay and append it to the list
        self.overlay_controller.overlays.append(self.coral_slab - fi)
        self.overlay_controller.alphas.append(0)
        
        wx.CallAfter(self.pb.update, 'Completed FFT + Butterworth Highpass Filter')