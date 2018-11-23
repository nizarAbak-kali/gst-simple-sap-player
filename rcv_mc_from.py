#!/usr/bin/python3

import socket
import struct
import sys
import time
from threading import Thread

DEBUG = False


class SapReceiver(Thread):

    def __init__(self, m_group='224.2.127.254', server_address=('', 9875)):
        Thread.__init__(self)
        self.multicast_group = m_group
        self.server_address = server_address

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.server_address)

        self.group = socket.inet_aton(self.multicast_group)
        self.mreq = struct.pack('4sL', self.group, socket.INADDR_ANY)
        self.sock.setsockopt(
            socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, self.mreq)

        self.sdp_dict = {}

    def run(self):
        sdp_model = SdpModel()
        change = False
        while True:
            data, address = self.sock.recvfrom(1024)
            ip, port = address
            if DEBUG:
                print('received bytes from:' + str(len(data)) +
                      ", " + ip + "/" + str(port) + "\n")
            type = data[0] & 0x04
            sdp_model.sdp_parser(data[8:].decode())
            if type == 4:
                change = self.remove_sdp_from(sdp_model)
            else:
                change = self.add_new_sdp(sdp_model)
            if change:
                change = False
                if DEBUG:
                    print(self.sdp_dict)
            time.sleep(0.5)

    def add_new_sdp(self, sdp):
        if sdp.session_name not in self.sdp_dict.keys():
            if DEBUG:
                print('T=Announce')
            self.sdp_dict[sdp.session_name] = sdp
            if DEBUG:
                print(str(sdp))
            return True
        return False

    def remove_sdp_from(self, sdp):
        if sdp.session_name in self.sdp_dict.keys():
            if DEBUG:
                print('T=Delete')
            del self.sdp_dict[sdp.session_name]
            return True
        return False


class SdpModel:

    def __init__(self):
        self.ip = ""
        self.port = 5004
        self.session_id = ""
        self.encoding_type = ""
        self.video_prop = ""
        self.payload_type = 96
        self.session_name = ""

    def __str__(self):
        if DEBUG:
            print("to_string")
        string = "ip = " + self.ip + "\n" + \
            "port = " + str(self.port) + "\n" + \
            "session_id = " + self.session_id + "\n" + \
            "encoding_type = " + self.encoding_type + "\n" + \
            "payload_type = " + str(self.payload_type) + "\n" + \
            "session_name = " + self.session_name + "\n" + \
            "video_prop = " + self.video_prop + "\n"
        return string

    def sdp_parser(self, sdp):
        lines = sdp.splitlines()

        for line in lines:
            self.get_session_id(line)
            self.get_session_name(line)
            self.get_video_port(line)
            self.get_mcast_ip(line)
            self.get_encoding_type(line)
            self.get_video_props(line)

    def get_session_id(self, o_line_from_sdp):
        elements = o_line_from_sdp.split(' ')
        if elements[0] == 'o=-':
            self.session_id = elements[1] + elements[2]

    def get_session_name(self, s_line_from_sdp):
        elements = s_line_from_sdp.split('=')
        if elements[0] == 's':
            self.session_name = elements[1]

    def get_video_port(self, m_line_from_sdp):
        elements = m_line_from_sdp.split(' ')
        if elements[0] == 'm=':
            self.port = int(elements[1])
            self.payload_type = int(elements[3])

    def get_mcast_ip(self, c_line_from_sdp):
        elements = c_line_from_sdp.split(' ')
        if elements[0] == 'c=IN':
            self.ip = elements[2].split('/')[0]

    def get_encoding_type(self, a_line_from_sdp):
        elements = a_line_from_sdp.split(' ')
        if elements[0] == 'a=rtpmap:'+str(self.payload_type):
            self.encoding_type = elements[1].split('/')[0]

    def get_video_props(self, a_line_from_sdp):
        elements = a_line_from_sdp.split(' ')
        result = ""
        if elements[0] == 'a=fmtp:'+str(self.payload_type):
            if self.encoding_type == "H264":
                params = elements[1].split('=', 1)[1]
                params = params.replace("=", "\\=")
                params = params.replace(",", "\\,")
                params += '\\"' + params+'\\"'
                result += elements[1].split('=', 1)[0] + '=' + params
            else:
                params = elements[1].split(';')
                new_params = ""
                new_params += ', '.join(x.replace('=', '=(string)')
                                        for x in params)
                result += new_params
        self.video_prop = result

    def get_caps_from_sdp(self):
        string = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)"+self.encoding_type + \
            ", "+self.video_prop+", "+"payload=(int)"+str(self.payload_type)
        return string
