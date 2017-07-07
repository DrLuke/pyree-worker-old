import argparse
import time

import glfw

from glfwInstance import GlfwInstance
from programs.defaultProgram import DefaultProgram
from programs.renderFBO import RenderFBO

import socket
from select import select
import json
import os

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', help='TCP and UDP port used for primary communication', default=31337, type=int)

class Manager:
    """Bodge class to go with bodge UI"""
    def __init__(self, inst):
        self.inst = inst
        self.fboprog = RenderFBO()
        self.program = DefaultProgram()

        self.inst.programs = [self.program, self.fboprog]

        self.tcpPort = 31337
        self.tcpsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcpsocket.bind(("localhost", self.tcpPort))

        self.tcpsocket.listen(10)

        self.controllerConn = None
        self.controllerAddr = None
        self.outbuf = ""  # IO buffer for controller

        self.inbuf = ""

    def loop(self):
        # Check for incoming connections
        rlist, wlist, elist = select([self.tcpsocket], [], [], 0)
        for sock in rlist:
            if sock is self.tcpsocket:
                conn, addr = self.tcpsocket.accept()
                if self.controllerConn is None:  # We have no controller? Great, this is our controller now.
                    self.controllerConn = conn
                    self.controllerAddr = addr
                else:  # Tell the other side we already have a controller, then close the connection
                    rlist, wlist, elist = select([], [conn], [], 0)
                    if conn in wlist:
                        conn.send(b"REJECTED: Already got controller")  # TODO: Invent proper json error message

                    conn.close()

        rlist = []
        if self.controllerConn:
             rlist = [self.controllerConn]

        rlist, wlist, elist = select(rlist, [], [], 0)
        if self.controllerConn in rlist:
            incomingData = self.controllerConn.recv(4096)
            if not incomingData:  # AKA connection is dead
                print("Connection from " + str(self.controllerAddr) + " died.")
                self.controllerConn.close()
                self.controllerConn = None
                self.controllerAddr = None
            else:
                try:
                    self.inbuf += bytes.decode(incomingData)
                except UnicodeDecodeError:
                    print("-------------\nReceived garbled unicode: %s\n-------------" % incomingData)

        self.parseInbuf()

        self.inst.loop()


    def parseInbuf(self):
        if self.inbuf and "\n" in self.inbuf:
            splitbuf = self.inbuf.split("\n")  # Split input buffer on newlines
            self.parseMessage(splitbuf[0])  # Parse everything until the first newline
            self.inbuf = str.join("\n", splitbuf[1:])  # Recombine all other remaining messages with newlines
            self.parseInbuf()  # Work recursively until no messages are left

    def parseMessage(self, msg):
        print(msg)
        try:
            decoded = json.loads(msg)
        except json.JSONDecodeError:
            return

        type = decoded["type"]
        if type == "program":
            self.handleProgram(decoded)
        elif type == "texture":
            self.handleTexture(decoded)

    def handleProgram(self, msg):
        """
        {
          type: "program",
          A: "",
          B: "",
          C: "",
          D: "",
          delete: false
        }
        """
        self.program.fragmentPathA = msg["A"]
        self.program.fragmentPathB = msg["B"]

    def handleTexture(self, msg):
        pass    # TODO: implement lol


if __name__ == "__main__":
    glfw.init()

    a = GlfwInstance(glfw.get_monitors()[0])
    a.createWindow()

    b = Manager(a)

    gtime = glfw.get_time()
    while 1:  # Limit framerate to 100 frames
        dt = glfw.get_time() - gtime
        b.loop()
        time.sleep(max(0.01 - dt, 0))
        gtime = glfw.get_time()


"""
{
  type: "program",
  A: "",
  B: "",
  C: "",
  D: "",
  delete: false
}
"""

""" TEXTURE COMMAND JSON
{
  type: "texture",
  id: 0,
  start: 0,
  length: 0,
  texbank: 0,
  delete: false
}
"""