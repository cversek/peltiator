import socket

DEFAULT_IP_ADDRESS =  "128.119.56.100"
DEFAULT_PORT            = 1234
DEFAULT_RECV_BUFF_SIZE  = 1024
DEFAULT_EOL             = '\n'


class GPIBController(object):
    def __init__(self, 
                 ip_address,
                 port       = DEFAULT_PORT, 
                 eol        = DEFAULT_EOL
                ):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((ip_address,port))
        self.ip_address = ip_address
        self.port       = port
        self.eol = eol
        #set the controller to turn off the read-after-write mode
        self.send("++auto 0")

    def get_addr(self):
        cmd = "++addr"
        return int(self.exchange(cmd))

    def get_eos(self):
        cmd = "++eos"
        return int(self.exchange(cmd))
    
    def set_addr(self, addr):
        cmd = "++addr %d" % addr
        self.send(cmd)

    def set_eos(self, eos):
        cmd = "++eos %d"  % eos
        self.send(cmd)
    
    def send(self, cmd):
        self._sock.send(cmd + self.eol)
        
    def read(self, recv_buff_size = DEFAULT_RECV_BUFF_SIZE):
        self.send("++read")
        resp = self._sock.recv(recv_buff_size)
        return resp

    def exchange(self, cmd, recv_buff_size = DEFAULT_RECV_BUFF_SIZE):
        self.send(cmd)
        resp = self.read(recv_buff_size = recv_buff_size)
        return resp

    def dump_errors(self):
        cmd = "SYSTEM:ERROR?"
        err_list = []        
        while True:
            resp = self.exchange(cmd)
            errno, msg = resp.split(',')
            errno = int(errno)
            if errno == 0:
                break
            else:
                err_list.append((errno,msg))
        return err_list

DEFAULT_EOS_MODE = 2
        
class GPIBInstrument(object):
    def __init__(self, gpib_controller, gpib_address, eos_mode = DEFAULT_EOS_MODE):
        self.gpib_controller = gpib_controller
        self.gpib_address    = gpib_address
        self.eos_mode        = eos_mode
    def activate(self):
        self.gpib_controller.set_addr(self.gpib_address)
        self.gpib_controller.set_eos(self.eos_mode)
    def send(self, cmd):
        self.activate()
        self.gpib_controller.send(cmd)
    def read(self, recv_buff_size = DEFAULT_RECV_BUFF_SIZE):
        self.activate()
        return self.gpib_controller.read(recv_buff_size = recv_buff_size)
    def exchange(self, cmd, recv_buff_size = DEFAULT_RECV_BUFF_SIZE):
        self.send(cmd)
        resp = self.read(recv_buff_size = recv_buff_size)
        return resp
    

###############################################################################
#  TEST CODE
###############################################################################
if __name__ == "__main__":
    c = GPIBController()
    #we are talking to the Agilent 3641A power supply
    c.set_addr(5)
    c.set_eos(2)

