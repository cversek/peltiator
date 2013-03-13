import time
from threading import Timer

def loop(period, duration, callback):
    t0 = time.time()
    while (time.time()-t0) < duration:
        timer = Timer(period, callback)
        timer.start() 
        timer.join()


class Scheduler(object):
    def __init__(self,prog, sampling_period, sampling_duration):
        self.prog = prog
        self.sampling_period = sampling_period
        self.sampling_duration = sampling_duration

    def update_loop(self, sampling_period = None, sampling_duration = None):
        if sampling_period is None:
            sampling_period = self.sampling_period
        if sampling_duration is None:
            sampling_duration = self.sampling_duration
        update_callback = lambda: self.prog.send_event("UPDATE")
        loop(period=sampling_period, duration=sampling_duration, callback=update_callback)
        
    def run_gradient_schedule(self,gradients, sampling_period = None, sampling_duration = None):
        self.prog.print_back("running gradient schedule: %r" % list(gradients))
        self.prog.print_back("sampling every %0.1f seconds for a duration of %0.1f seconds" % (self.sampling_period,self.sampling_duration))
        for grad in gradients:
            self.prog.print_back("setting gradient: %0.2f" % grad)
            self.prog.app.change_gradient_setpoint(grad)        
            self.update_loop(sampling_period=sampling_period,sampling_duration=sampling_duration)
