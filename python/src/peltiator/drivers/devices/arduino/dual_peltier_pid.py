"""
   dual_peltier_pid - interface to Arduino based dual peltier device PID controller             
"""
###############################################################################
#Dependencies
import time
#Automat framework provided
from automat.core.hwcontrol.devices.device import Device 
from automat.core.hwcontrol.communication.serial_mixin import SerialCommunicationsMixIn
#3rd Party
import yaml
###############################################################################
#Module constants
YAML_DOC_START = "---"
YAML_DOC_END   = "..."

###############################################################################
# INTERFACE


class Interface(Device, SerialCommunicationsMixIn):
    def __init__(self, port, **kwargs):
        #initialize serial communication
        SerialCommunicationsMixIn.__init__(self, port, **kwargs)
    # Implementation of the Instrument Interface
    def initialize(self):
        self._send("GRAD 0.0")
        #time.sleep(1.0)
    def identify(self):
        idn = self._exchange("*IDN?")
        return idn
    #Cleanup
    def shutdown(self):
        "leave the ststem in a safe state"
        self._send("GRAD 0.0")
    #--------------------------------------------------------------------------
    # Implementation 
    def send_command(self,cmd):
        self.ser.flushInput()
        self.ser.flushOutput()
        self._send(cmd)        
        buff = []
        while True:
            time.sleep(0.01)
            line = self._read(strip_EOL = False)
            if not line:
                return "".join(buff)
            buff.append(line)

    def set_pid_control_mode(self, chan, mode):
        if mode is True:
            mode = 'on'
        elif mode is False:
            mode = 'off'        
        cmd = "PID_%s %s" % (chan,mode)
        self._send(cmd)

    def get_status(self):
        self.ser.flushInput()
        self.ser.flushOutput()
        self.ser.write("STATUS?\n")
        time.sleep(0.1)
        buff = []
        line = self.ser.readline()
#        if not line.startswith(YAML_DOC_START):
#            raise IOError, "expected a YAML document start tag '%s', instead got:\n%r" % (YAML_DOC_START, line)
        buff.append(line)
        while True:
            line = self.ser.readline()
            buff.append(line)
            if line == "":
                raise IOError, "'get_status' timed out after %f seconds" % self.ser.timeout
            elif line.startswith(YAML_DOC_END):
                yaml_doc = "".join(buff)
                #try:
                record = yaml.load(yaml_doc)
                #except yaml.S
                record['timestamp'] = time.time()
                return record
        
        
def get_interface(**kwargs):
    iface = Interface(**kwargs)
    return iface
###############################################################################
# TEST CODE
###############################################################################
if __name__ == "__main__":
    p = Interface("/dev/tty.usbmodem26231")
