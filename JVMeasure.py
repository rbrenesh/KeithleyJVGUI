from ScopeFoundry import Measurement, h5_io
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from qtpy import QtWidgets,QtCore
from PyQt5 import QtGui
import pyqtgraph as pg
import numpy as np
import time
from datetime import datetime
import os
import re
# from .XAutoPanTool import XAutoPanTool


class JVMeasure(Measurement):


    name = "JV Measurement"

    hardware_requirements = ['Keithley 2450']

    measurement_sucessfully_completed = QtCore.Signal(())

    def setup(self):
        self.ui = load_qt_ui_file(sibling_path(__file__, 'JVMeasurement_ui.ui'))
        self.settings.New('Measurement', dtype= str, initial='JV Measurement', choices = ('JV Measurement','Current Tracking', 'Voltage Tracking'))
        self.settings.New('start_voltage',dtype=float,initial=0, unit='V', si= True)
        self.settings.New('end_voltage',dtype=float,initial=1, unit='V', si= True)
        self.settings.New('npoints',dtype=int,initial=101, vmin=1)
        self.settings.New('constant_v',dtype=float,initial=0, unit='V', si= True)
        self.settings.New('itrack_delay',dtype=float,initial=0.1, unit='s', si= True)
        self.settings.New('constant_i',dtype=float,initial=0, unit='A', si= True)
        self.settings.New('vtrack_delay',dtype=float,initial=0.1, unit='s', si= True)

        self.counter = 0
        self.display_update_period = 0.1 #seconds

        initial_save_dir = 'C:\\Users\\solaradmin\\Desktop\\Solar Data\\Miscellaneous'
        self.app.settings.save_dir.default_dir = initial_save_dir
        self.app.settings.save_dir.update_value(new_val=initial_save_dir)

        self.keithley  = self.app.hardware['Keithley 2450']

        # self.threadpool = QtCore.QThreadPool()

        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.settings.progress.connect_to_widget(self.ui.progressBar)

        #connect settings to buttons
        self.settings.Measurement.connect_to_widget(self.ui.measurement_comboBox)
        self.ui.measurement_comboBox.currentIndexChanged.connect(self.measurement_change)
        self.settings.start_voltage.connect_to_widget(self.ui.startV_doubleSpinBox)
        self.settings.end_voltage.connect_to_widget(self.ui.endV_doubleSpinBox)
        self.settings.npoints.connect_to_widget(self.ui.npoints_spinBox)
        self.keithley.settings.Measure_Delay.connect_to_widget(self.ui.JVdelaytime_doubleSpinBox)
        self.settings.itrack_delay.connect_to_widget(self.ui.delay_itrack_doubleSpinBox)
        self.settings.vtrack_delay.connect_to_widget(self.ui.delay_vtrack_doubleSpinBox)
        self.set_progress(0)

    def measurement_change(self):
        pass

    def lock_start_button(self):
        self.op_buttons['start'].setEnabled(False)
        self.ui.start_pushButton.setEnabled(False)
        self.ui.measurement_comboBox.setEnabled(False)

        for lqname in "Measurement start_voltage end_voltage npoints constant_v itrack_delay constant_i vtrack_delay".split():
            self.settings.as_dict()[lqname].change_readonly(True)

        self.keithley.settings.as_dict()['Measure_Delay'].change_readonly(True)

    def unlock_start_button(self):
        self.op_buttons['start'].setEnabled(True)
        self.ui.start_pushButton.setEnabled(True)
        self.ui.measurement_comboBox.setEnabled(True)

        for lqname in "Measurement start_voltage end_voltage npoints constant_v itrack_delay constant_i vtrack_delay".split():
            self.settings.as_dict()[lqname].change_readonly(False)

        self.keithley.settings.as_dict()['Measure_Delay'].change_readonly(False)

    def fileExists(self,fname):
        return os.path.isfile(fname)

    def save_file(self):
        dirname = self.app.settings['save_dir']
        sample_filename = self.app.settings['sample']
        counter_sample_filename = sample_filename+'_'+str(self.counter)

        if sample_filename=='':
            self.counter = 0
            now = datetime.now()
            dt_string = now.strftime("%Y%m%d_%Hh%Mm%Ss")
            data_filename = os.path.join(dirname,dt_string)

        #increase filename counter if filename already exists
        elif self.fileExists(os.path.join(dirname,sample_filename)) or self.fileExists(os.path.join(dirname,counter_sample_filename)):
            self.counter += 1
            data_filename = os.path.join(dirname,sample_filename+'_'+str(self.counter))

        else:
            self.counter=0
            data_filename = os.path.join(dirname,sample_filename)


        # save data depending on the type of measurement
        if self.settings['Measurement'] == 'JV Measurement':
            np.savetxt(data_filename+'.txt',np.vstack((self.vlist,np.array(self.data))).T)

        elif self.settings['Measurement'] == 'Current Tracking':
            np.savetxt(data_filename+'.txt',np.vstack((np.array(self.tlist)-self.tlist[0],np.array(self.data))).T)

        else:
            np.savetxt(data_filename+'.txt',np.vstack((np.array(self.tlist)-self.tlist[0],np.array(self.data))).T)

    def pre_run(self):
        self.lock_start_button()
        S = self.settings 
        self.vlist = np.linspace(S['start_voltage'],S['end_voltage'],S['npoints'])
        self.tlist = []
        self.data = []

    def post_run(self):
        self.unlock_start_button()
        self.set_progress(0)

    def run(self):
        S = self.settings

        while not self.interrupt_measurement_called:

            if self.settings['Measurement'] == 'JV Measurement':
                
                #need to call this in case someone does a tracking measurement and doesn't change the JV delay value
                self.keithley.set_delay(self.ui.JVdelaytime_doubleSpinBox.value())


                self.keithley.clear_buffer()
                self.keithley.set_output('On')

                #delay time is automatically set on the Keithley when any of the delay time spinboxes are changed, so no need for a time.sleep() function call
                for i,v in enumerate(self.vlist):
                    self.keithley.set_level(v)
                    self.data.append(self.keithley.read_measurement())
                    self.set_progress(i/S['npoints']*100)

                self.keithley.set_output('Off')
                self.keithley.clear_buffer()

                break


            elif self.settings['Measurement'] == 'Current Tracking':
                self.set_progress(50)
                self.keithley.set_level(S['constant_v'])
                temp_dat, t = self.keithley.read_measurement_withTime()

                self.tlist.append(t)
                self.data.append(temp_dat)

                time.sleep(S['itrack_delay'])

            else:
                self.set_progress(50)
                self.keithley.set_level(S['constant_i'])

                temp_dat, t = self.keithley.read_measurement_withTime()

                self.tlist.append(t)
                self.data.append(temp_dat)

                time.sleep(S['vtrack_delay'])

        self.save_file()


    def setup_figure(self):

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        self.graph_layout = pg.GraphicsLayoutWidget(border=(0,0,0))

        #Create infinite vertical and horizontal lines
        self.vline = pg.InfiniteLine(pos = 0 ,angle = 90, movable = False)
        self.hline = pg.InfiniteLine(pos = 0, angle = 0, movable = False)

        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        
        self.jv_plot = self.graph_layout.addPlot()
        self.jv_plot.getViewBox().setMouseMode(pg.ViewBox.RectMode)

        #Add infinite vertical and horizontal lines to plot (for easy JV curve viewing)
        self.jv_plot.addItem(self.vline)
        self.jv_plot.addItem(self.hline)
        self.jv_plot_line = self.jv_plot.plot()
        self.jv_plot.enableAutoRange()

    def update_display(self):

        try:

            if self.settings['Measurement'] == 'JV Measurement':
                self.jv_plot_line.setData(self.vlist[:np.size(self.data)],self.data)
            else:
                self.jv_plot_line.setData(np.array(self.tlist)-self.tlist[0],self.data)

        except (AttributeError, IndexError) as e:
            pass





