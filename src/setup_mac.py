import sys
from setuptools import setup, find_packages

# Add images/dependencies that CXV uses here:
DATA_FILES = [ 'images/calibrate.png', 'images/contrast.png', 'images/coral.png',
              'images/cursor_cross.png', 'images/cursor_hand_closed.gif',
              'images/cursor_hand_open.gif', 'images/cursor_hand.png', 'images/density.png',
              'images/info.png', 'images/lock_calibrate.png', 'images/lock_coral.png',
              'images/lock_polyline.png', 'images/open.png', 'images/overlay.png',
              'images/overview.png', 'images/polyline.png', 'images/save.png',
              'images/zoom_in_toolbar.png', 'images/zoom_out_toolbar.png'
               ]
setup(name='Coral X-Ray Viewer',
      app=['main.py'],
      data_files=DATA_FILES,
      setup_requires=['py2app'],
      packages=find_packages())