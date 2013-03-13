################################################################################
class ScriptProgram(object):
    def __init__(self,app):
        self.app = app                
    def send_event(self, event_type, obj = None): 
        self.app._script_event_queue.put((event_type,obj))
    def print_back(self, obj): 
        self.send_event('PRINT',str(obj))
################################################################################
