from ScopeFoundry import HardwareComponent
import pyvisa

class InvalidSourceError(Exception):
    pass

class InvalidTerminalError(Exception):
    pass

class InvalidMeasurementError(Exception):
    pass

class InvalidSenseError(Exception):
    pass


class Keithley2450HW(HardwareComponent):

    name = 'Keithley 2450'


    def setup(self):
        
        self.settings.New('Source', dtype=str, choices=[("Voltage","Voltage"),("Current","Current")], initial='Voltage')
        self.settings.New('Measurement', dtype=str, choices=[("Voltage","Voltage"),("Current","Current")], initial='Current')
        self.settings.New('Level', dtype = float, initial = 0, vmin=-50, vmax=50)
        self.settings.New('Output',dtype=str, choices = [('On','On'),('Off','Off')], initial = 'Off')
        self.settings.New('Terminals', dtype =str, choices=[('Front','Front'),('Rear','Rear')], initial='Rear')
        self.settings.New('Sense', dtype =str, choices=[('2Wire','2Wire'),('4Wire','4Wire')], initial='2Wire')
        self.settings.New('Measure_Delay', dtype=float, unit='s',si = True)
        self.settings.New('ILimit', dtype=float, unit='A',si = True, initial= 1)
        self.settings.New('VLimit', dtype= float, unit = 'V', si = True, initial = 20)
        self.settings.New('Autorange', dtype=str, choices = [('On','On'),('Off','Off')], initial = 'On')
        self.settings.New('AutoDelay', dtype=str, choices = [('On','On'),('Off','Off')])
        self.settings.New('NPLC', dtype = float, initial = 1, vmin=0.01, vmax = 10)
        self.add_operation('Reset', self.reset)
        self.add_operation('Beep', self.beep)

    def connect(self):
        self.rm = pyvisa.ResourceManager()
        self.keithley = self.rm.open_resource('GPIB0::18::INSTR')

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

        LQ["Terminals"].hardware_set_func    = self.set_terminals
        LQ["Terminals"].hardware_read_func    = self.read_terminals

        LQ["Output"].hardware_set_func    = self.set_output
        LQ["Output"].hardware_read_func    = self.read_output

        LQ["NPLC"].hardware_set_func    = self.set_NPLC
        LQ["NPLC"].hardware_read_func    = self.read_NPLC

        LQ['Measure_Delay'].hardware_set_func = self.set_delay
        LQ['Measure_Delay'].hardware_read_func = self.read_delay

        LQ['AutoDelay'].hardware_set_func = self.set_autodelay
        LQ['AutoDelay'].hardware_read_func = self.read_autodelay

        LQ["ILimit"].hardware_set_func    = self.set_ilimit
        LQ["ILimit"].hardware_read_func    = self.read_ilimit

        LQ['VLimit'].hardware_set_func = self.set_vlimit
        LQ["VLimit"].hardware_read_func    = self.read_vlimit

        #Reset the Keithley, which also reads all the default values from hardware
        self.reset()

        self.settings['ILimit'] = 1
        self.settings['Sense'] = '2Wire'

    def set_source(self,func='Voltage'):
        if func == 'Voltage':
            self.keithley.write("smu.source.func = smu.FUNC_DC_VOLTAGE")

            #Maximum and minimum levels from Keithley 2450 manual
            self.settings.Level.vmin = -210
            self.settings.Level.vmax = 210
            self.settings.Level.unit = 'V'
        elif func == 'Current':
            self.keithley.write("smu.source.func = smu.FUNC_DC_CURRENT")

            #Maximum and minimum levels from Keithley 2450 manual
            self.settings.Level.vmin = -1.05
            self.settings.Level.vmax = 1.05
            self.settings.Level.unit = 'A'
        else:
            raise InvalidSourceError('Invalid source function')

    def read_sourceFunc(self):
        self.keithley.write("mfunc = smu.source.func")
        func =  str(self.keithley.query("print(source)"))
        if func == 'smu.FUNC_DC_CURRENT':
            return 'Current'
        else:
            return 'Voltage'

    def set_measureFunc(self,func='Current'):

        if func == 'Voltage':
            self.keithley.write("smu.measure.func = smu.FUNC_DC_VOLTAGE")
        elif func == 'Current':
            self.keithley.write("smu.measure.func = smu.FUNC_DC_CURRENT")
        else:
            raise InvalidMeasurementError('Invalid measurement function')

    def read_measureFunc(self):
        self.keithley.write("mfunc = smu.measure.func")
        func =  str(self.keithley.query("print(mfunc)"))
        if func == 'smu.FUNC_DC_CURRENT':
            return 'Current'
        else:
            return 'Voltage'

    def set_level(self,level):
        self.keithley.write("smu.source.level= {:f}".format(level))

    def read_level(self):
        self.keithley.write("level = smu.source.level")
        return float(self.keithley.query("print(level)"))

    def set_ilimit(self,limit):
        self.keithley.write("smu.source.ilimit.level = {:f}".format(limit))

        if self.settings['Source'] =='Current':
            self.settings.Level.vmax = limit

    def read_ilimit(self):
        self.keithley.write("ilimit = smu.source.ilimit.level")
        return float(self.keithley.query("print(ilimit)"))

    def set_vlimit(self, limit):
        self.keithley.write("smu.source.vlimit.level = {:f}".format(limit))

        if self.settings['Source'] =='Voltage':
            self.settings.Level.vmax = limit

    def read_vlimit(self):
        self.keithley.write("vlimit = smu.source.vlimit.level")
        vlim = self.keithley.query("print(vlimit)")
        if vlim == 'nil\n':
            return 210
        else:
            return float(vlim)

    def set_sense(self,m_type):
        if m_type == '2Wire':
            self.keithley.write("smu.measure.sense=smu.SENSE_2WIRE")
        elif m_type == '4Wire':
            self.keithley.write("smu.measure.sense=smu.SENSE_4WIRE")
        else:
            raise InvalidSenseError('Invalid sense type')

    def read_sense(self):
        self.keithley.write("sensing = smu.source.sense")
        sense = str(self.keithley.query("print(sensing)"))
        if sense == 'smu.SENSE_2WIRE':
            return '2Wire'
        else:
            return '4Wire'

    def set_terminals(self,terminal):
        if terminal == 'Front':
            self.keithley.write("smu.measure.terminals = smu.TERMINALS_FRONT")
        elif terminal == 'Rear':
            self.keithley.write("smu.measure.terminals = smu.TERMINALS_REAR")
        else:
            raise InvalidTerminalError('Invalid terminal')

    def read_terminals(self):
        self.keithley.write("terminals = smu.source.sense")
        terminals = str(self.keithley.query("print(terminals)"))
        if terminals == 'smu.TERMINALS_FRONT':
            return 'Front'
        else:
            return 'Rear'

    def set_autorange(self,autorange='On'):
        if autorange == 'On':
            self.keithley.write("smu.measure.autorange = smu.ON")
        else:
            self.keithley.write("smu.measure.autorange = smu.OFF")

    def read_autorange(self):
        self.keithley.write("autorange = smu.source.autorange")
        ans =  str(self.keithley.query("print(autorange)"))
        if ans == 'smu.ON':
            return 'On'
        else:
            return 'Off'

    def set_NPLC(self,NPLC):
        self.keithley.write("smu.measure.nplc = {:f}".format(NPLC))

    def read_NPLC(self):
        self.keithley.write("nplc = smu.measure.nplc")
        nplc = self.keithley.query("print(nplc)")
        if nplc == 'nil\n':
            return float(1)
        else:
            return float(nplc)

    def set_output(self,output):
        if output == 'On':
            self.keithley.write("smu.source.output=smu.ON")
        else:
            self.keithley.write("smu.source.output=smu.OFF")

    def read_output(self):
        output = str(self.keithley.query("print(smu.source.output)"))
        if output == 'smu.ON':
            return 'On'
        else:
            return 'Off'

    def set_delay(self,delay):
        self.keithley.write("smu.source.delay = {:f}".format(delay))

    def read_delay(self):
        return float(self.keithley.query("print(smu.source.delay)"))

    def read_autodelay(self):
        self.keithley.write("state = smu.source.autodelay")
        state = str(self.keithley.query("print(state)"))

        if state == 'smu.ON':
            return 'On'
        else:
            return 'Off'

    def set_autodelay(self,state):
        if state =='On':
            self.keithley.write('smu.source.autodelay = smu.ON')
        else:
            self.keithley.write('smu.source.autodelay = smu.OFF')

    def read_measurement(self):
        return float(self.keithley.query("print(smu.measure.read())"))

    def read_measurement_withTime(self):
        self.keithley.write("amp, sec, fracSec = smu.measure.readwithtime()")
        amp = self.keithley.query("print(amp)")
        sec = self.keithley.query("print(sec)")
        fracSec = self.keithley.query("print(fracSec)")
        print(float(sec)+float(fracSec))
        return float(amp), float(sec)+float(fracSec)

    def clear_buffer(self):
        self.keithley.write("defbuffer1.clear()")

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
