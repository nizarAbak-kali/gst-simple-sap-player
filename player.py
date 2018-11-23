#!/usr/bin/env python3

from rcv_mc_from import SapReceiver, SdpModel
from gi.repository import Gst, GObject, Gtk
import os
import time

import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')


class GTK_Main(object):

    def __init__(self):
        # SAP PART
        self.session_name_changed = False
        self.sap_rcv = SapReceiver()

        self.sap_rcv.start()
        # IHM PART
        window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        window.set_title("Simple test Player")
        window.set_default_size(200, 200)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        vbox = Gtk.VBox()
        window.add(vbox)
        hbox = Gtk.HBox()
        vbox.pack_start(hbox, False, False, 0)

        self.entry = Gtk.ListStore(str)

        while len(self.sap_rcv.sdp_dict.keys()) == 0:
            print ("waiting ....")
            time.sleep(1)
            pass

        time.sleep(1)

        name_list = list(self.sap_rcv.sdp_dict.keys())

        print(name_list)
        self.current_session_name = name_list[0]

        name_combo = Gtk.ComboBoxText()
        name_combo.set_entry_text_column(0)
        name_combo.connect("changed", self.on_name_combo_changed)
        for i in name_list:
            name_combo.append_text(i)
        hbox.pack_start(name_combo, False, False, 0)

        self.button = Gtk.Button("Start")
        vbox.pack_start(self.button, False, False, 0)
        self.button.connect("clicked", self.start)

        self.button = Gtk.Button("Stop")
        hbox.pack_start(self.button, False, False, 0)
        self.button.connect("clicked", self.stop)

        self.label = Gtk.Label('lol')
        self.label.set_line_wrap(True)
        vbox.pack_start(self.label, False, False, 0)

        self.movie_window = Gtk.DrawingArea()
        vbox.add(self.movie_window)
        window.show_all()

        # GSTREAMER PART
        self.start_pipeline()
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)

    def on_name_combo_changed(self, combo):
        text = combo.get_active_text()
        print("selected : ", text)
        self.current_session_name = text
        self.session_name_changed = True

    def start_pipeline(self):
        sdp = self.sap_rcv.sdp_dict[self.current_session_name]
        self.label.set_text(str(sdp))
        gst_command = 'udpsrc' +\
            ' address='+sdp.ip + \
            ' port='+str(sdp.port) +\
            ' multicast-iface=eth0' + \
            ' caps="' + sdp.get_caps_from_sdp()+'" '

        if sdp.encoding_type == "RAW":
            gst_command += " ! rtpvrawdepay ! glimagesink sync = false"
        else:
            gst_command += " ! rtph264depay ! h264parse ! avdec_h264 ! glimagesink sync = false"
        self.pipeline = Gst.parse_launch(gst_command)
        self.pipeline.set_state(Gst.State.PLAYING)

    def start(self, w):
        if self.session_name_changed:
            self.pipeline.set_state(Gst.State.NULL)
            self.start_pipeline()
            self.session_name_changed = False
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop(self, w):
        self.pipeline.set_state(Gst.State.NULL)

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.pipeline.set_state(Gst.State.NULL)
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print("Error: %s" % err, debug)
            self.pipeline.set_state(Gst.State.NULL)


Gst.init(None)
GTK_Main()
GObject.threads_init()
Gtk.main()

print("finish!")
