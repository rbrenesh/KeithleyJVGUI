from ScopeFoundry import HardwareComponent
import numpy as np
import time
import pyvisa

class InvalidSourceError(Exception):
    pass

class InvalidTerminalError(Exception):
    pass

class InvalidMeasurementError(Exception):
    pass

class InvalidSenseError(Exception):
    pass


class Keithley2600HW(HardwareComponent):

    name = 'Keithley 2600'


    def setup(self):
        
        self.settings.New('Source', dtype=str, choices=[("Voltage","Voltage"),("Current","Current")], initial='Voltage')
        self.settings.New('Measurement', dtype=str, choices=[("Voltage","Voltage"),("Current","Current")], initial='Current')
        self.settings.New('Level', dtype = float, initial = 0, vmin=-50, vmax=50)
        self.settings.New('Output',dtype=str, choices = [('On','On'),('Off','Off')], initial = 'Off')
        self.settings.New('Sense', dtype =str, choices=[('2Wire','2Wire'),('4Wire','4Wire')], initial='2Wire')
        self.settings.New('Measure_Delay', dtype=float, unit='s',si = True)
        self.settings.New('ILimit', dtype=float, unit='A',si = True, initial= 1)
        self.settings.New('VLimit', dtype= float, unit = 'V', si = True, initial = 20)
        self.settings.New('Autorange', dtype=str, choices = [('On','On'),('Off','Off')], initial = 'On')
        self.settings.New('NPLC', dtype = float, initial = 1, vmin=0.01, vmax = 10)
        self.add_operation('Reset', self.reset)
        self.add_operation('Beep', self.beep)

    def connect(self):
        self.rm = pyvisa.ResourceManager()
        self.keithley = self.rm.open_resource('GPIB0::26::INSTR')

        LQ = self.settings.as_dict()


        #Set the read and write functions for every logged quantity
        LQ["Source"].hardware_set_func    = self.set_source
        LQ["Source"].hardware_read_func = self.read_sourceFunc

        LQ["Measurement"].hardware_set_func    = self.set_measureFunc
        LQ["Measurement"].hardware_read_func = self.read_measureFunc

        LQ["Level"].hardware_set_func    = self.set_level
        LQ["Level"].hardware_read_func = self.read_level

        LQ["Autorange"].hardware_set_func    = self.set_autorange
        LQ["Autorange"].hardware_read_func    = self.read_autorange

        LQ["Sense"].hardware_set_func    = self.set_sense
        LQ["Sense"].hardware_read_func    = self.read_sense

        LQ["Output"].hardware_set_func    = self.set_output
        LQ["Output"].hardware_read_func    = self.read_output

        LQ["NPLC"].hardware_set_func    = self.set_NPLC
        LQ["NPLC"].hardware_read_func    = self.read_NPLC

        LQ['Measure_Delay'].hardware_set_func = self.set_delay
        LQ['Measure_Delay'].hardware_read_func = self.read_delay

        LQ["ILimit"].hardware_set_func    = self.set_ilimit
        LQ["ILimit"].hardware_read_func    = self.read_ilimit

        LQ['VLimit'].hardware_set_func = self.set_vlimit
        LQ["VLimit"].hardware_read_func    = self.read_vlimit

        #Reset the Keithley, which also reads all the default values from hardware
        self.reset()

    def set_source(self,func='Voltage'):
        if func == 'Voltage':
            self.keithley.write("smua.source.func = smua.OUTPUT_DCVOLTS ")

            #Maximum and minimum levels from Keithley 2450 manual
            self.settings.Level.vmin = -210
            self.settings.Level.vmax = 210
            self.settings.Level.unit = 'V'
        elif func == 'Current':
            self.keithley.write("smua.source.func = smua.OUTPUT_DCAMPS")

            #Maximum and minimum levels from Keithley 2450 manual
            self.settings.Level.vmin = -1.05
            self.settings.Level.vmax = 1.05
            self.settings.Level.unit = 'A'
        else:
            raise InvalidSourceError('Invalid source function')

    def read_sourceFunc(self):
        func =  str(self.keithley.query("print(smua.source.func)"))
        if func == 'smua.OUTPUT_DCAMPS':
            return 'Current'
        else:
            return 'Voltage'

    def set_measureFunc(self,func='Current'):

        if func == 'Voltage':
            self.keithley.write("display.smua.measure.func = display.MEASURE_DCVOLTS")
        elif func == 'Current':
            self.keithley.write("display.smua.measure.func = display.MEASURE_DCAMPS")
        else:
            raise InvalidMeasurementError('Invalid measurement function')

    def read_measureFunc(self):
        func =  str(self.keithley.query("print(display.smua.measure.func)"))
        if func == 'display.MEASURE_DCVOLTS':
            return 'Voltage'
        else:
            return 'Current'

    def set_level(self,level):

        if self.settings['Source'] =='Voltage':
            self.keithley.write("smua.source.levelv= {:f}".format(level))
        else:
            self.keithley.write("smua.source.leveli= {:f}".format(level))

    def read_level(self):

        if self.settings['Source'] =='Voltage':
            return float(self.keithley.query("print(smua.source.levelv)"))
        else:
            return float(self.keithley.query("print(smua.source.leveli)"))

    def set_ilimit(self,limit):
        self.keithley.write("smua.source.limiti = {:f}".format(limit))

    def read_ilimit(self):
        return float(self.keithley.query("print(smua.source.limiti)"))

    def set_vlimit(self, limit):
        self.keithley.write("smua.source.limitv = {:f}".format(limit))

    def read_vlimit(self):
        vlim = self.keithley.query("print(smua.source.limitv)")
        if vlim == 'nil\n':
            return 210
        else:
            return float(vlim)

    def set_sense(self,m_type):
        if m_type == '2Wire':
            self.keithley.write("smua.sense = smua.SENSE_LOCAL")
        elif m_type == '4Wire':
            self.keithley.write("smua.sense = smua.SENSE_REMOTE")
        else:
            raise InvalidSenseError('Invalid sense type')

    def read_sense(self):
        sense = str(self.keithley.query("print(smua.sense)"))
        if sense == 'smua.SENSE_LOCAL':
            return '2Wire'
        else:
            return '4Wire'


    def set_autorange(self,autorange='On'):
        if self.settings['Source'] =='Voltage':
            if autorange == 'On':
                self.keithley.write("smua.measure.autorangei = smua.AUTORANGE_ON")
            else:
                self.keithley.write("smua.measure.autorangei = smua.AUTORANGE_OFF")
        else:
            if autorange == 'On':
                self.keithley.write("smua.measure.autorangev = smua.AUTORANGE_ON")
            else:
                self.keithley.write("smu.measure.autorangev = smua.AUTORANGE_OFF")

    def read_autorange(self):

        if self.settings['Source'] =='Voltage':
            ans =  str(self.keithley.query("print(smua.measure.autorangei)"))
            if ans == 'smua.AUTORANGE_ON':
                return 'On'
            else:
                return 'Off'
        else:
            ans =  str(self.keithley.query("print(smua.measure.autorangev)"))
            if ans == 'smua.AUTORANGE_ON':
                return 'On'
            else:
                return 'Off'

    def set_NPLC(self,NPLC):
        self.keithley.write("smua.measure.nplc = {:f}".format(NPLC))

    def read_NPLC(self):
        nplc = self.keithley.query("print(smu.source.nplc)")
        if nplc == 'nil\n':
            return float(1)
        else:
            return float(nplc)

    def set_output(self,output):
        if output == 'On':
            self.keithley.write("smua.source.output = smua.OUTPUT_ON")
        else:
            self.keithley.write("smua.source.output = smua.OUTPUT_OFF")

    def read_output(self):
        output = str(self.keithley.query("print(smua.source.output)"))
        if output == 'smua.OUTPUT_ON':
            return 'On'
        else:
            return 'Off'

    def set_delay(self,delay):
        self.keithley.write("smua.source.delay = {:f}".format(delay))

    def read_delay(self):
        ans = self.keithley.query("print(smua.source.delay)")
        if ans=='smua.DELAY_AUTO' or ans =='-1':
            return float(-1)
        elif ans=='smua.DELAY_OFF' or ans =='0':
            return float(0)
        else:
            return float(ans)

    def read_measurement(self):
        if self.settings['Source'] =='Voltage':
            return float(self.keithley.query("print(smua.measure.i())"))
        else:
            return float(self.keithley.query("print(smua.measure.v())"))

    def read_measurement_withTime(self):
        val = self.read_measurement()
        t = time.time()
        return val, t

    def linVSweepMeasureI(self,Vstart,Vstop,pts,delay):
        self.keithley.write('SweepVLinMeasureI(smua, {0:f}, {1:f}, {2:f}, {3:d})'.format(Vstart,Vstop,delay,pts))
        readings = self.keithly.query('printbuffer(1,{:d}, smua.nvbuffer1.readings)'.format(pts)).split(', ')
        return np.array([float(i) for i in readings])

    def clear_buffer(self):
        self.keithley.write("smua.nvbuffer1.clear()")

    def reset(self):
        self.keithley.write("reset()")
        self.read_from_hardware()

    def beep(self, duration=2, freq=2400):
        self.keithley.write('beeper.beep({0:f}, {1:f})'.format(duration,freq))

    def disconnect(self):
        try:
            self.rm.close()
            del self.rm
            del self.keithley
        except AttributeError as e:
            pass
