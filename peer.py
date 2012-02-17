##
#  Very early version of the chatter thing.
#
#  Author: Prashant vasudevan
#  
#
##


from socket import *
import fcntl
import struct
import sys, os
import select

MSG_SIZE = 100
ADDR_SIZE = 20
broadcast_addr = '255.255.255.255'
TYPE_STR, TYPE_NAME, TYPE_BROADCAST = 0, 1, 2

def get_ip_address(ifname, s):
    #s = socket(AF_INET, SOCK_DGRAM)
    return inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15]))[20:24])


def pack(type, msg):
    return str(type) + msg

def unpack(msg):
    return int(msg[0]), msg[1:]
    

my_port = 4000
my_sock = socket(AF_INET, SOCK_DGRAM)
my_sock.bind(('', my_port))
my_addr = get_ip_address('eth0', my_sock)


broad_sock = socket(AF_INET, SOCK_DGRAM)
broad_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1) 

my_name = raw_input('Enter Name: ')

broad_sock.sendto(pack(TYPE_BROADCAST, my_name), (broadcast_addr, my_port))
broad_sock.close()

pipein, pipeout = os.pipe()

pid = os.fork()

if pid == 0:
    people = {}
    while 1:
        msg, (addr, port) = my_sock.recvfrom(MSG_SIZE)                 #port MUST be same as my_port
        if addr == my_addr:
            continue
        
        msg_type, msg_data = unpack(msg)
        if msg_type in [TYPE_NAME, TYPE_BROADCAST] and addr not in people.keys():
        
            people[addr] = msg_data
            
            os.write(pipeout, (addr+':').ljust(ADDR_SIZE, '0'))

            if msg_type == TYPE_BROADCAST:
                my_sock.sendto(pack(TYPE_NAME, my_name), (addr, my_port))
            print '<%s has joined>' % msg_data
        
        elif msg_type == TYPE_STR:
            
            if addr not in people.keys():
                print 'Unknown person.'
            else:
                print '%s: %s' % (people[addr], msg_data)
    
        #my_sock.sendto(msg, (addr, port))
else:
    addrs = []
    #fcntl.fcntl(pipein, fcntl.F_SETFL, os.O_NONBLOCK)
    while 1:
        msg = raw_input()
        
        ready = select.select([pipein], [], [], 0.01)
        while ready[0] != []:
            addr = os.read(pipein, ADDR_SIZE)
            addrs.append(addr.split(':')[0])
            #print 'addr:', addr

            ready = select.select([pipein], [], [], 0.01)

        #print msg, addrs
        for addr in addrs:
            my_sock.sendto(pack(TYPE_STR, msg), (addr, my_port))

my_sock.close()
