import sys
################################################################################
CRASHDUMP_FILENAME = '.crash_dump.txt~'
################################################################################
class handleCrash(object):
    """Wraps a top-level script function in an error handling routine that 
       for a crash prints an informative message and dumps the exception 
       details to a file. Use as a decorator.
    """
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        try:
            self.func(*args, **kwargs)
        except SystemExit, exc:
            sys.exit(0)
        except:
            error_type, exc, tb = sys.exc_info()
            msg = str(exc)
            print '*'*80
            print "A fatal error has occured: %s" % error_type 
            print msg
            print '*'*80
            print "Writing crash info to '%s'." % CRASHDUMP_FILENAME 
            crashdump_file = open(CRASHDUMP_FILENAME,'w')
            import traceback
            traceback.print_exc(file=crashdump_file)
            crashdump_file.close()
            print "Aborting program."
            print "press 'enter' key to continue..."
            raw_input()
            try:
                sys.exit(exc.err_code)
            except AttributeError:
                sys.exit(1)
