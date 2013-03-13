###############################################################################
# IMPORTS
###############################################################################
#Standard Python
#import os, sys, time, datetime, Queue, threading
import os, sys, imp, time, warnings, threading
from collections import OrderedDict
from Queue import Queue, Empty
#3rd Party
import yaml, IPython, numpy
#Automat framework provided
from automat.core.hwcontrol.config.configuration import Configuration
#pyTEIS framework provided
from pyTEIS import pkg_info
from pyTEIS.apps.lib.thread2 import Thread as KillableThread
#application local
from script_program import ScriptProgram

###############################################################################
# CONSTANTS
###############################################################################
INTRO_MSG_TEMPLATE = """
*******************************************************************************
PyTEIS Peltier Test %(version)s
    author: Craig Versek (cversek@gmail.com)
*******************************************************************************
"""

###############################################################################
# FUNCTIONSthreading
###############################################################################
def stream_print(text, 
                 stream = sys.stdout,
                 eol = '\n', 
                 prefix = None
                ):
        if prefix:
            stream.write(prefix)
        stream.write(text)
        if eol:
            stream.write(eol)
        stream.flush()
###############################################################################
# CLASSES
########################################threading#######################################
class Application(object):
    def __init__(self,
                 config, 
                 intro_msg       = None, 
                 output_stream   = sys.stdout,
                 error_stream    = sys.stderr,
                 textbox_printer = lambda text: None,
                ):
        self.config = config
        self.output_stream   = output_stream
        self.error_stream    = error_stream
        self.textbox_printer = textbox_printer
        self.user_ns  = {}
        #print the introductory message
        if intro_msg is None:
            intro_msg = INTRO_MSG_TEMPLATE % {'version' :pkg_info.metadata['version']}
        self.print_comment(intro_msg)
        self._init_metadata()        
        self._init_data()
        self._init_devices()
        self._init_script_thread()

    def _init_metadata(self):
        md = OrderedDict()
        md['sample_name'] = ""
        md['start_timestamp'] = time.time()
        self.metadata = md

    def _init_data(self):
        self.data = OrderedDict((("timestamp",[]),
                                 ("temperatureA_target",[]),
                                 ("temperatureB_target",[]),
                                 ("temperatureA_measured",[]),
                                 ("temperatureB_measured",[]),
                                 ("temperatureC_measured",[]),
                                 ("chanA_output",[]),
                                 ("chanB_output",[]),
                                 ("voltage",[]),
                               ))

    def _init_devices(self):
        self.peltier_pid = self.config.load_device('peltier_pid')
        self.dmm = self.config.load_device('dmm')
        self.dmm.initialize()
        self.dmm.setup_measurement('V dc')
        self.oven = self.config.load_device('oven')

    def _init_script_thread(self):
        self._script_thread = None
        self._script_event_queue  = Queue()
        self._script_failure_event = threading.Event()

    def setup_textbox_printer(self, textbox_printer):
        self.textbox_printer = textbox_printer

    def print_comment(self, text, eol = '\n', comment_prefix = '#'):
        lines = text.split(eol)
        buff = eol.join([ comment_prefix + line for line in lines])
        stream_print(buff, stream = self.output_stream, eol = eol)
        #also print to the textbox if available
        self.textbox_printer(buff)

    def start_shell(self, msg = ""):
        status_msg = []
        status_msg.append(msg)
        
        #load convenient modules
        self.user_ns['time'] = time
        
        #pass reference to this application instance
        self.user_ns['app'] = self
        
        #complete the status message
        status_msg.append('')
        status_msg.append("-- Hit Ctrl-D to exit. --")
        status_msg = '\n'.join(status_msg) 
        #start the shell
        # directly open the shell
        IPython.embed( user_ns=self.user_ns, banner2=status_msg)

    def run_script(self,filepath):
        self.print_comment("Running script '%s'..." % filepath)   
        def task():
            prog = ScriptProgram(app=self)
            try:
                basepath, filename = os.path.split(filepath)
                mod_name, _ = os.path.splitext(filename)
                filename, pathname, description = imp.find_module(mod_name,[basepath])
                mod = imp.load_module(mod_name,filename,pathname,description)
                mod.main(prog)
            except SystemExit:
                prog.send_event('ABORTED') 
            except:
                prog.send_event('ERROR', sys.exc_info())
        
        self._script_thread = KillableThread(target=task)
        self._script_thread.daemon = True # make thread a daemon so it will not block on program exit
        self._script_thread.start()  #launch thread!
             
    def clear_data(self):
        self._init_data()

    def close(self):
        pass

    def __del__(self):
        self.close()

    def update_data(self, verbose = True):
        if verbose:
            self.print_comment("Status update:")
        try:
            record = self.peltier_pid.get_status()
            record['voltage'] = self.dmm.read()
            for key, val in record.items():
                try:
                    if verbose:                
                        self.print_comment("\t%s: %s" % (key,val))
                    self.data[key].append(val)
                except KeyError:
                    pass
        except IOError, exc:
            msg = str(exc)
            self.print_comment("\t***error*** %s" % msg)        
        return self.data
    
    def send_command_to_peltier_pid(self, cmd):
        cmd.rstrip("\n\r ")
        #self.print_comment("Sending command: %s" % cmd)
        resp = self.peltier_pid.send_command(cmd)
        #self.print_comment("Got response: %s" % resp)
        return resp

    def change_gradient_setpoint(self, grad):
        self.send_command_to_peltier_pid("GRAD %0.2f" % grad)

    def change_setpointA(self, temp):
        self.send_command_to_peltier_pid("TEMP_A %0.2f" % temp)
  
    def change_setpointB(self, temp):
        self.send_command_to_peltier_pid("TEMP_B %0.2f\n" % temp)
        
    def export_data(self, filename):
        base, ext = os.path.splitext(filename)
        if ext == ".csv":
            delimiter      = ", "
            comment_prefix = "#"
            newline        = "\n"
            #write metadata
            with open(filename, 'w') as f:
                for key, val in self.metadata.items():
                    line = delimiter.join((comment_prefix,str(key),str(val)))                       
                    f.write(line + newline)
            #write data in append mode
            colnames_array = numpy.array(self.data.keys()).reshape((1,-1))
            data_array     = numpy.array(self.data.values()).transpose()
            output_array   = numpy.vstack((colnames_array, data_array))
            with open(filename, 'a') as f:
                numpy.savetxt(f, output_array, delimiter=delimiter, fmt='%s', newline=newline)
        else:
            self.print_comment("Warning: file extension '%s' not understood" % ext)         

    

################################################################################
#  TEST CODE
################################################################################
if __name__ == "__main__":
    CONFIG_FILENAME = "peltier_test.cfg"
    #load the configuration
    config_dirpath = pkg_info.platform['config_dirpath']
    config_filepath = os.path.sep.join((config_dirpath, CONFIG_FILENAME))
    config = Configuration(config_filepath) 
    app = Application(config=config)
    app.start_shell(msg="*** TEST CODE ***")
