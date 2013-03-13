###############################################################################
# "pyTEIS Peltier Test" Application
###############################################################################
from pyTEIS.apps.lib.errors import handleCrash
CONFIG_FILENAME = "peltier_test.cfg"


@handleCrash
def main():
    ############################################################################
    # Imports
    ############################################################################
    #standard
    import os, sys, glob, warnings
    from optparse import OptionParser
    #3rd party

    #Automat framework provided
    from automat.core.hwcontrol.config.configuration import Configuration   
    #pyTEIS framework provided
    from pyTEIS import pkg_info
    #application local
    from lib.application.application import Application
    from lib.gui.gui import GUI
    
    ############################################################################
    #parse commandline options
    OP = OptionParser()
    OP.add_option("--no-detach",dest="detach",default=True,
                  action = 'store_false',
                  help="stay bound to the current terminal session"
                 )
    OP.add_option("--shell",dest="shell",default=False,
                  action = 'store_true',
                  help="run the interactive shell rather than the GUI"
                 )
    opts, args = OP.parse_args()
    #load the configuration
    config_dirpath = pkg_info.platform['config_dirpath']
    config_filepath = os.path.sep.join((config_dirpath, CONFIG_FILENAME))
    config = Configuration(config_filepath)    
    #initialize the control application
    app = Application(config)
    #start the graphical interface
    gui = GUI(app)
    #give the app the ability to print to the GUI's textbox
    app.setup_textbox_printer(gui.print_to_text_display)
    #detach
    if opts.shell:
        app.start_shell("Application Shell:")
    else:
        if opts.detach:
            #detach the process from its controlling terminal
            from automat.system_tools.daemonize import detach
            app.print_comment("Process Detached.")
            app.print_comment("You may now close the terminal window...")
            detach()
        #launch the gui interface
        gui.launch()
    #return all good
    return 0

if __name__ == "__main__":
    main()
