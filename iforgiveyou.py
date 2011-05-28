#
# (c) 2011 Arjan Scherpenisse <arjan@scherpenisse.net>
# I Forgive You by Esther Verhamme
#

import clutter
import gst
import cluttergst
import random
import glob
import os

from twisted.internet import reactor, protocol
from twisted.internet.serialport import SerialPort

from sparked import application
from sparked.graphics import stage


class Machine(protocol.Protocol):
    """
    Communication with The Machine.

    The Machine consists of a Matrix Orbital VK204-24 USB controller
    which has its GPO ports wired to a RM5 coin acceptor. When the GPO
    ports are high, the machine accepts coins. When a coin is
    accepted, the keypad controller registers a keypress, 0x4B. The
    keypad controller is also wired to another button (0x46) which
    does not do a lot, but is used here to display a "no refund" message.
    """

    def __init__(self, app):
        self.app = app

    def dataReceived(self, data):
        for c in data:
            if ord(c) == 0x4B:
                self.app.coinInserted()
            if ord(c) == 0x46:
                self.app.buttonPressed()


    def startScreen(self):
        self.transport.write(chr(254)+chr(88))
        self.transport.write("\n * INSERT 1 EURO *")


    def sorry(self):
        self.transport.write(chr(254)+chr(88))
        self.transport.write("\n\nSorry, no refund...")


    def playing(self):
        self.transport.write(chr(254)+chr(88))


    def accept(self, accept=True):
        for i in range(6):
            self.transport.write(chr(254)+chr(86+int(accept))+chr(i+1))



class Stage(stage.Stage):
    """
    The graphic display. Has a movie player which plays movies. One
    movie is always fixed,"intro.mov"; the other movie which is played after the intro is a random choice
    from the data folder.
    """

    def __init__(self, app):
        stage.Stage.__init__(self, app)
        self.video = cluttergst.VideoTexture()
        self.add(self.video)

        def onPlayerMessage(bus, message):
            if message.type == gst.MESSAGE_EOS:
                self.app.state.set("start")

        bus = self.video.get_playbin().get_bus()
        bus.add_signal_watch()
        bus.connect("message", onPlayerMessage)
        self.video.set_size(self.get_width(), self.get_height())
        self.set_color(clutter.color_from_string("#000000"))


    def addMonitors(self):
        pass


    def enter_start(self):
        self.video.hide()


    def exit_start(self):
        self.video.show()


    def enter_play_movie(self):
        # random movie
        all = [f for f in glob.glob(self.app.path("data").child("*").path)]
        f = random.choice(all)
        print "playing", f
        self.video.set_uri("file://" + f)
        self.video.set_playing(True)





class Application (application.Application):

    def starting(self):
        self.stage = Stage(self)
        self.machine = Machine(self)
        SerialPort(self.machine, "/dev/serial/by-id/usb-Matrix_Orbital_LK_VK204-24-USB_00000186-if00-port0", reactor, baudrate=19200)


    def enter_start(self):
        self.machine.startScreen()
        self.machine.accept(True)


    def exit_start(self):
        self.machine.accept(False)


    def enter_sorry(self):
        self.machine.sorry()
        self.state.setAfter("start", 2)


    def coinInserted(self):
        if self.state.get != "start":
            return
        self.state.set("play_movie")


    def buttonPressed(self):
        if self.state.get != "start":
            return
        self.state.set("sorry")
