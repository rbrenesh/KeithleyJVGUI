#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 18:41:28 2018

@author: rbrenes
"""

from ScopeFoundry import BaseMicroscopeApp
import qdarkstyle

class KeithleyJVApp(BaseMicroscopeApp):

    # this is the name of the microscope that ScopeFoundry uses 
    # when storing data
    name = 'Keithley JV'
    
    # You must define a setup function that adds all the 
    #capablities of the microscope and sets default settings
    def setup(self):
        
        #Add App wide settings
        
        #Add hardware components
        print("Adding Hardware Components")
        from Keithley2450HW import Keithley2450HW
        from Keithley2600HW import Keithley2600HW
        self.add_hardware(Keithley2450HW(self))
        self.add_hardware(Keithley2600HW(self))

        #Add measurement components
        print("Create Measurement objects")

        # Connect to custom gui
        from JVMeasure import JVMeasure
        self.add_measurement(JVMeasure(self))

        
        # load side panel UI
        
        # show ui
        self.ui.show()
        self.ui.activateWindow()


if __name__ == '__main__':
    import sys
    
    app = KeithleyJVApp(sys.argv)
    #Uncomment line below for dark mode
    # app.qtapp.setStyleSheet(qdarkstyle.load_stylesheet())
    sys.exit(app.exec_())
