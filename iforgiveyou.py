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

    def __init__(self, app):
        stage.Stage.__init__(self, app)
        self.video = cluttergst.VideoTexture()
        self.add(self.video)

        def onPlayerMessage(bus, message):
            if message.type == gst.MESSAGE_EOS:
                if self.app.state.get == "play_intro":
                    self.app.state.set("play_movie")
                elif self.app.state.get == "play_movie":
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


    def enter_play_intro(self):
        self.video.set_size(self.get_width(), self.get_height())
        self.video.set_uri("file://" + self.app.path("data").child("intro.mov").path)
        self.video.set_playing(True)


    def enter_play_movie(self):
        # random movie
        all = [f for f in glob.glob(self.app.path("data").child("*").path) if os.path.basename(f) != "intro.mov"]
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


    def enter_play_intro(self):
        self.machine.playing()


    def coinInserted(self):
        if self.state.get != "start":
            print "Huh, not in start?"
            return
        self.state.set("play_intro")


    def buttonPressed(self):
        if self.state.get != "start":
            return
        self.state.set("sorry")