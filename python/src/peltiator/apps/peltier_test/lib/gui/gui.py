###############################################################################
#Standard Python provided
import os, sys, time, signal, datetime, warnings, threading, traceback
from Queue import Queue, Empty
#3rd party packages
from Tkinter import *
#from tkinter.filedialog import askopenfilename
import Pmw
from FileDialog import FileDialog, SaveFileDialog
import numpy
#Automat framework provided
from automat.core.gui.text_widgets import TextDisplayBox
#pyTEIS framework provided
from pyTEIS.apps.lib.thread2 import Thread as KillableThread
#application local
from data_plotter import DataPlotter
###############################################################################
# Module Constants
WINDOW_TITLE            = "pyTEIS Peltier Test"
WAIT_DELAY              = 100 #milliseconds
TEXT_BUFFER_SIZE        = 10*2**20 #ten megabytes
DATA_UPDATE_PERIOD        = 100  #milliseconds
PLOT_UPDATE_PERIOD        = 1000 #milliseconds
SCRIPT_LOOP_UPDATE_PERIOD = 10   #milliseconds

TEXT_DISPLAY_HEIGHT = 10

###############################################################################
def IgnoreKeyboardInterrupt():
    """
    Sets the response to a SIGINT (keyboard interrupt) to ignore.
    """
    return signal.signal(signal.SIGINT,signal.SIG_IGN)

def NoticeKeyboardInterrupt():
    """
    Sets the response to a SIGINT (keyboard interrupt) to the
    default (raise KeyboardInterrupt).
    """
    return signal.signal(signal.SIGINT, signal.default_int_handler)

###############################################################################
class GUI(object):
    def __init__(self, application):
        self.app = application
        self.app.print_comment("Starting GUI interface:")
        self.app.print_comment("please wait while the application loads...")
        self._mode = "standby"
        self._update_counter = 0
        self.data = None
        #build the GUI interface as a seperate window
        win = Tk()
        Pmw.initialise(win) #initialize Python MegaWidgets
        win.withdraw()
        win.wm_title(WINDOW_TITLE)
        win.focus_set() #put focus on this new window
        self.win = win
        #handle the user hitting the 'X' button
        self.win.protocol("WM_DELETE_WINDOW", self._close)
        #build the left panel
        left_frame = Frame(win)
        
        button_bar = Frame(left_frame)
        self.start_loop_button       = Button(button_bar,text="Start Loop"  ,command = self.start_loop)
        self.stop_loop_button        = Button(button_bar,text="Stop Loop"   ,command = self.stop_loop, state='disabled')
        self.chanA_pid_mode_button   = Button(button_bar,text="Chan A PID = ON",command = self.toggle_chanA_pid_mode, relief = "sunken")
        self.chanB_pid_mode_button   = Button(button_bar,text="Chan B PID = ON",command = self.toggle_chanB_pid_mode, relief = "sunken")        
        self.send_command1_button    = Button(button_bar,text="Send Command to TEIS"  ,command = self.send_command_to_peltier_pid)        
        self.run_script_button       = Button(button_bar,text="Run Script"  ,command = self.run_script)
        self.abort_script_button     = Button(button_bar,text="Abort Script",command = self.abort_script, state='disabled')
        self.setpointGRAD_button     = Button(button_bar,text="Set Gradient",command = lambda: self.change_setpoint(mode='GRAD'))
        self.setpointA_button        = Button(button_bar,text="Set Temp. A" ,command = lambda: self.change_setpoint(mode='TEMP_A'))
        self.setpointB_button        = Button(button_bar,text="Set Temp. B" ,command = lambda: self.change_setpoint(mode='TEMP_B'))
        self.clear_button            = Button(button_bar,text="Clear Data"  ,command = self.clear_data)
        self.export_button           = Button(button_bar,text="Export Data" ,command = self.export_data)        

        button_pack_opts = {'side':'top','fill':'x', 'expand':'yes', 'anchor':'nw'}
        self.start_loop_button.pack(**button_pack_opts)
        self.stop_loop_button.pack(**button_pack_opts) 
        self.chanA_pid_mode_button.pack(**button_pack_opts)
        self.chanB_pid_mode_button.pack(**button_pack_opts)
        self.send_command1_button.pack(**button_pack_opts)
        self.run_script_button.pack(**button_pack_opts)
        self.abort_script_button.pack(**button_pack_opts)         
        self.setpointGRAD_button.pack(**button_pack_opts)
        self.setpointA_button.pack(**button_pack_opts)
        self.setpointB_button.pack(**button_pack_opts)
        self.clear_button.pack(**button_pack_opts)
        self.export_button.pack(**button_pack_opts)
        button_bar.pack(side='top', fill='x', expand='no', anchor='nw')
        left_frame.pack(side='left', fill='both', padx=10)
       
        #build the middle panel
        mid_panel = Frame(win)
        self.data_plotter  = DataPlotter(mid_panel)
        self.text_display  = TextDisplayBox(mid_panel,text_height=TEXT_DISPLAY_HEIGHT, buffer_size = TEXT_BUFFER_SIZE)
        
        self.data_plotter.pack(fill='both',expand='yes')
        self.text_display.pack(fill='both',expand='yes')
        mid_panel.pack(fill='both', expand='yes',side='left')

        #build the right panel
        right_panel = Frame(win)
        self.sample_name_entry = Pmw.EntryField(right_panel,
                                                labelpos = 'w',
                                                label_text = 'Sample Name',
                                                command = self.change_sample_name)
        self.sample_name_entry.pack()
        right_panel.pack(side='right', fill='both', padx=10)
        #make a dialog window for sending a command
        self.command_dialog = Pmw.Dialog(parent = win, buttons = ('OK', 'Cancel'), defaultbutton = 'OK')
        self.command_dialog.withdraw()
        self.command_entry = Pmw.EntryField(self.command_dialog.interior(),
                                            labelpos = 'w',
                                            label_text = 'Command:',
                                           )

        self.command_entry.pack()
        #make a dialog window for changing setpoint
        self.change_setpoint_dialog = Pmw.Dialog(parent = win, buttons = ('OK', 'Cancel'), defaultbutton = 'OK')
        self.change_setpoint_dialog.withdraw()
        self.change_setpoint_entry = Pmw.EntryField(self.change_setpoint_dialog.interior(),
                                                    labelpos = 'w',
                                                    label_text = 'Setpoint Value:',
                                                    validate = "real")

        self.change_setpoint_entry.pack()
       
    def launch(self):
        #run the GUI handling loop
        IgnoreKeyboardInterrupt()
        self.win.deiconify()
        #loop until killed
        self.win.mainloop()
        NoticeKeyboardInterrupt()

    def update_data(self):
        self.data = self.app.update_data()
           
    def update_plot(self):
        self.data_plotter.update(self.data)
        
    def start_loop(self):
        self.start_loop_button.config(state='disabled')
        self.stop_loop_button.config(state='normal')
        self._mode = "loop"
        self._loop_data_update()
        self._loop_plot_update()

    def _loop_data_update(self):
        if self._mode == "loop":
            self.update_data()
            self.win.after(DATA_UPDATE_PERIOD, self._loop_data_update)
    
    def _loop_plot_update(self):
        if self._mode == "loop":
            self.update_plot()
            self.win.after(PLOT_UPDATE_PERIOD, self._loop_plot_update)
    
    def stop_loop(self):
        self.stop_loop_button.config(state='disabled')
        self.start_loop_button.config(state='normal')
        self._mode = "standby"
    
    def toggle_chanA_pid_mode(self):
        relief = self.chanA_pid_mode_button.cget('relief')
        if relief == 'raised':
            self.chanA_pid_mode_button.config(text="Chan A PID = ON", relief='sunken')
            self.app.print_comment("Toggling Channel A PID state -> 'on'")
            self.app.peltier_pid.set_pid_control_mode(chan='A', mode = 'on')
        elif relief == 'sunken':
            self.chanA_pid_mode_button.config(text="Chan A PID = OFF", relief='raised')
            self.app.print_comment("Toggling Channel A PID state -> 'off'")
            self.app.peltier_pid.set_pid_control_mode(chan='A', mode = 'off')
    
    def toggle_chanB_pid_mode(self):
        relief = self.chanB_pid_mode_button.cget('relief')
        if relief == 'raised':
            self.chanB_pid_mode_button.config(text="Chan B PID = ON", relief='sunken')
            self.app.print_comment("Toggling Channel B PID state -> 'on'")
            self.app.peltier_pid.set_pid_control_mode(chan='B', mode = 'on')
        elif relief == 'sunken':
            self.chanB_pid_mode_button.config(text="Chan B PID = OFF", relief='raised')
            self.app.print_comment("Toggling Channel B PID state -> 'off'")
            self.app.peltier_pid.set_pid_control_mode(chan='B', mode = 'off')

    def send_command_to_peltier_pid(self):
        #self.command_entry.focus_set()
        result = self.command_dialog.activate()
        if result == "OK":
            cmd = self.command_entry.getvalue()
            resp = self.app.send_command_to_peltier_pid(cmd)
            
        

    def run_script(self):
        self.stop_loop()
        
        fdlg = FileDialog(self.win,title="Run Script")
        input_dir = "/home/cversek/gitwork/umass-physics/teis/python/src/pyTEIS/scripts/" #FIXME #os.getcwd()
        filepath = fdlg.go(dir_or_file = input_dir, 
                           pattern="*.py",  
                          )
        if filepath:
            self.disable_controls()
            self.abort_script_button.config(state='normal')
            self._mode = "scripting"
            self.app.run_script(filepath)
            self._script_loop() 
        

    def _script_loop(self):
        if self._mode == "scripting":
            while not self.app._script_event_queue.empty():
                event_type, obj = self.app._script_event_queue.get()
                if event_type == "PRINT":
                    self.app.print_comment(obj)
                elif event_type == "UPDATE_DATA":
                    self.update_data()
                elif event_type == "UPDATE_PLOT":
                    self.update_plot()
                elif event_type == "UPDATE":
                    self.update_data()
                    self.update_plot()
                elif event_type == "CLEAR_DATA":
                    self.clear_data()
                elif event_type == "ERROR":
                    exc_type, exc, tb = obj
                    msg = traceback.format_exception(exc_type, exc, tb)
                    msg = "".join(msg)
                    self.app.print_comment("Caught Error in Script: %s" % msg)
                    msg = "%s\nCheck the console for the traceback" % (exc,)                    
                    Pmw.MessageDialog(parent = self.win, 
                                      title = 'Script Error',
                                      message_text = msg,
                                      iconpos = 'w',
                                      icon_bitmap = 'error',buttons = ('OK',)
                                      )
                elif event_type == "ABORTED":
                    self.app.print_comment("Script aborted.")
                else:
                    self.app.print_comment("Got unknown event '%s' with obj=%r" % (event_type,obj))
            if self.app._script_thread.is_alive():
                self.win.after(SCRIPT_LOOP_UPDATE_PERIOD, self._script_loop)
            else:
                self.app.print_comment("Script finished.")
                self.enable_controls()
                self._mode = "standby"
    
    def abort_script(self):
        self.app._script_thread.terminate()
        self.app._script_thread.join()
        self.abort_script_button.config(state='disabled')
        self.enable_controls()
        
    def disable_controls(self):
        #disable all controls
        self.start_loop_button.config(state='disabled')
        self.chanA_pid_mode_button.config(state='disabled')
        self.chanB_pid_mode_button.config(state='disabled')
        self.send_command1_button.config(state='disabled')
        self.run_script_button.config(state='disabled')
        self.setpointGRAD_button.config(state='disabled')
        self.setpointA_button.config(state='disabled')
        self.setpointB_button.config(state='disabled')
        self.clear_button.config(state='disabled')
        self.export_button.config(state='disabled')
   
    def enable_controls(self):
        #enable most controls
        self.start_loop_button.config(state='normal')
        self.chanA_pid_mode_button.config(state='normal')
        self.chanB_pid_mode_button.config(state='normal')
        self.send_command1_button.config(state='normal')
        self.run_script_button.config(state='normal')
        self.setpointGRAD_button.config(state='normal')
        self.setpointA_button.config(state='normal')
        self.setpointB_button.config(state='normal')
        self.clear_button.config(state='normal')
        self.export_button.config(state='normal')
    
    def print_to_text_display(self, text, eol='\n'):
        self.text_display.print_text(text, eol=eol)

    def warn(self, msg):
        warnings.warn(msg)
        self.app.print_comment("Warning: %s" % msg)

    def change_setpoint(self, mode):
        result = self.change_setpoint_dialog.activate()
        if result == "OK":
            temp = self.change_setpoint_entry.getvalue()
            temp = float(temp)
            if mode == 'GRAD':
                self.app.change_gradient_setpoint(temp)
            elif mode == 'TEMP_A':
                self.app.change_setpointA(temp)
            elif mode == 'TEMP_B':
                self.app.change_setpointB(temp)
    
    def clear_data(self):
        self.app.metadata['start_timestamp'] = time.time()
        self.app._init_data()
        self.data_plotter.setup()

    def change_sample_name(self):
        sample_name = self.sample_name_entry.getvalue()
        self.app.metadata['sample_name'] = sample_name
        self.data_plotter.change_title(new_title = sample_name)    

    def export_data(self):
        self.app.print_comment("exporting data...")
        data     = self.app.data
        metadata = self.app.metadata
        d = datetime.datetime.fromtimestamp(metadata['start_timestamp'])
        d = d.strftime("%Y-%m-%d")        
        default_filename = "%s_%s_peltier_test.csv" % (d,metadata['sample_name'])
        fdlg = SaveFileDialog(self.win,title="Export Data")
        output_dir = os.getcwd()
        filename = fdlg.go(dir_or_file = output_dir, 
                           pattern="*.csv", 
                           default=default_filename, 
                           key = None
                          )
        if filename:
            self.app.export_data(filename)

    def _close(self):
        self.win.destroy()
