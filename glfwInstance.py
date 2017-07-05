import glfw

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import *
from OpenGL.GL import shaders
import OpenGL

class GlfwInstance():
    """Single GLFW Instance
    One GLFW Instance needs to be spawned for every monitor. It contains the rendering lopp for that monitor."""
    def __init__(self, monitor:glfw._GLFWmonitor):
        self.monitor = monitor
        self.window = None

        # Runtime
        self.runtime = GlfwInstance.runtime()

        self.programs = []

    class runtime:
        """Helper class that keeps track of some runtime variables"""
        def __init__(self):
            self.width = 1
            self.height = 1

            self.time = glfw.get_time()
            self.deltatime = 0.01    # Just some good starting value that isn't 0

            self.frameBuffer = None

    def createWindow(self):
        self.window = glfw.create_window(500, 500, "Pyree Worker （´・ω・ `)", None, None)

        self.runtime.width, self.runtime.height = glfw.get_window_size(self.window)

        # glfw.set_window_size(self.window, self.videomode[0][0], self.videomode[0][1])

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        glfw.make_context_current(self.window)

        glfw.set_framebuffer_size_callback(self.window, self.framebufferSizeCallback)

        self.genFramebuffer()

    def closeWindow(self):
        # TODO: More housekeeping needed, or is that it?
        glfw.destroy_window(self.window)

    def framebufferSizeCallback(self, window, width, height):
        glViewport(0, 0, width, height) # Set viewport to fullscreen
        self.runtime.width = width
        self.runtime.height = height

        self.genFramebuffer()   # Re-Generate Framebuffer with new size

    def genFramebuffer(self):
        if self.runtime.fbo is not None:    # Delete old framebuffer object
            glDeleteFramebuffers([self.runtime.fbo])
        if self.runtime.fbotexture is not None: # Delete old framebuffer texture
            glDeleteTextures([self.runtime.fbotexture])

        self.runtime.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.runtime.fbo)
        self.runtime.fbotexture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.runtime.fbotexture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.runtime.width, self.runtime.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.runtime.fbotexture, 0)

    def loop(self):
        # execute programs in order of list
        self.runtime.width, self.runtime.height = glfw.get_window_size(self.window)     # TODO: Needed?

        glfw.make_context_current(self.window)
        glfw.poll_events()

        # Clear screen
        glBindFramebuffer(GL_FRAMEBUFFER, 0)    # Bind main framebuffer
        glClearColor(0.2, 0.3, 0.3, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)    # TODO: Needed?

        # Update time variables
        self.runtime.deltatime = glfw.get_time() - self.runtime.time
        self.runtime.time = glfw.get_time()

        for program in self.programs:
            program.render()

        glfw.swap_buffers(self.window)

class PyreeProgram:
    """Program that is run on workers and hopefully draws pretty things"""
    def __init__(self):
        pass

    def __del__(self):
        pass

    def render(self, runtime: GlfwInstance.runtime, resources: list):
        pass


