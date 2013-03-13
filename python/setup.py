"""   
desc:  Setup script for 'peltiator' package.
auth:  Craig Wm. Versek (cversek@physics.umass.edu)
date:  2012-03-13
notes: install with "sudo python setup.py install"
"""
import platform, os, shutil


PACKAGE_METADATA = {
    'name'         : 'peltiator',
    'version'      : 'dev',
    'author'       : "Craig Versek",
}
    
PACKAGE_SOURCE_DIR = 'src'
MAIN_PACKAGE_DIR   = 'peltiator'
MAIN_PACKAGE_PATH  = os.path.abspath(os.sep.join((PACKAGE_SOURCE_DIR,MAIN_PACKAGE_DIR)))

INSTALL_REQUIRES = []

LINUX_CONFIG_DIR = '/etc/peltiator'

def ask_yesno(prompt, default='y'):
    while True:
        full_prompt = prompt + "([y]/n): "
        val = raw_input(full_prompt)
        if val == "":
            val = default
        if val in ['y','Y']:
            return True
        elif val in ['n','N']:
            return False

###############################################################################
# verify dependencies

def check_pyserial():
    try:
        print "Checking for pyserial...",
        import serial
        print " found"
        return True
    except ImportError:
        print "\n\tWarning: pyserial has not been installed."
        val = ask_yesno("Should setuptools try to download an install this package?")
        if val:
            INSTALL_REQUIRES.append('pyserial')
        return False
 

###############################################################################
# MAIN
###############################################################################
if __name__ == "__main__":
    print "*"*80
    #check the system 
    system = platform.system()
    print "Detected system: %s" % system 
    print "Running compatibility check:"
    if system == 'Linux':
        #FIXME - this is a hack to get python path working with 'sudo python setup.py...'
        import sys
        major, minor, _,_,_ = sys.version_info
        sys.path.append("/usr/local/lib/python%d.%d/site-packages" % (major,minor))
        #END FIXME
        check_pyserial()
    elif system == 'Darwin':
        check_pyserial()
    elif system == 'Windows':
        check_pyserial()

    #gather platform specific data
    platform_data = {}   
    platform_data['system'] = system
    config_dirpath = None
    if system == 'Linux' or system == 'Darwin':
        config_dirpath = LINUX_CONFIG_DIR
        if not os.path.isdir(config_dirpath):
            print "creating config directory: %s" % config_dirpath
            os.mkdir(config_dirpath)
        else:
            print "config directory already exists: %s" % config_dirpath
    elif system == 'Windows':
        from win32com.shell import shellcon, shell
        appdata_path   = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
        config_dirpath = appdata_path

    platform_data['config_dirpath'] = config_dirpath

    #autogenerate the package information file
    pkg_info_filename   = os.sep.join((MAIN_PACKAGE_PATH,'pkg_info.py'))
    print "Writing the package info file: %s" % pkg_info_filename
    pkg_info_file       = open(pkg_info_filename,'w')
    pkg_info_file.write("metadata = %r\n" % PACKAGE_METADATA)
    pkg_info_file.write("platform = %r"   % platform_data)
    pkg_info_file.close()

    raw_input("press 'Enter' to continue...")
    print "*"*80

    ##the rest is controlled by setuptools
    #from ez_setup import use_setuptools
    #use_setuptools()

    from setuptools import setup, find_packages

    # run the setup script
    setup(
        
          #packages to install
          package_dir  = {'':'src'},
          packages     = find_packages('src'),
          
          #non-code files
          package_data     =   {'': ['*.yaml','*.yml']},

          #dependencies
          install_requires = INSTALL_REQUIRES,
          extras_require = {
                            'Plotting': ['matplotlib >= 0.98'],
                           },
          dependency_links = [
                              #'http://sourceforge.net/project/showfiles.php?group_id=80706', #matplotlib
                             ],
          #scripts and plugins
          entry_points = {
                          'gui_scripts': [
                               'peltier_test = pyTEIS.apps.peltier_test.main:main',
                           ],
                          'console_scripts': [
                           ]
                         },
          **PACKAGE_METADATA 
    )
