from glfwInstance import PyreeProgram

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import *
from OpenGL.GL import shaders
import OpenGL

import numpy as np
import traceback

import os, time

class DefaultProgram(PyreeProgram):
    def __init__(self):
        # vbo and vao
        self.uvxoffset = 0
        self.uvyoffset = 0

        self.vbo = None
        self.vao = None

        self.updateVBO()

        # shader program
        self.vertexShader = None

        self.defaultFragmentcode = """
        #version 330 core
        in vec3 vertColor;
        in vec2 texCoord;
        layout(location = 0) out vec4 outColor;

        void main()
        {
            outColor = vec4(vertColor.r, vertColor.g, vertColor.b, 1.0);
        }
        """
        self.fragmentShaderA = None
        self.fragmentShaderB = None

        self.fragmentCodeA = self.defaultFragmentcode
        self.fragmentCodeB = self.defaultFragmentcode

        self.fragmentPathA = ""
        self.lastReadA = 0
        self.fragmentPathB = ""
        self.lastReadB = 0

        self.shaderProgramA = None
        self.shaderProgramB = None

        self.fboB = None

        self.fbotextureB = None

        self.checkCounter = 0

        self.width = -1
        self.height = -1

        self.updateShaderprogramA()     # Generate default shader
        self.updateShaderprogramB()  # Generate default shader

    def updateVBO(self):
        vertices = np.array([
            # X     Y     Z    R    G    B    U    V
            [1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0 + self.uvxoffset, 1.0 + self.uvyoffset],  # Top right
            [-1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0 + self.uvxoffset, 1.0 + self.uvyoffset],  # Top Left
            [1.0, -1.0, 0.0, 1.0, 0.0, 1.0, 1.0 + self.uvxoffset, 0 + self.uvyoffset],  # Bottom Right
            [-1.0, -1.0, 0.0, 1.0, 1.0, 0.0, 0 + self.uvxoffset, 0 + self.uvyoffset],  # Bottom Left
            [1.0, -1.0, 0.0, 1.0, 0.0, 1.0, 1.0 + self.uvxoffset, 0 + self.uvyoffset],  # Bottom Right
            [-1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0 + self.uvxoffset, 1.0 + self.uvyoffset]  # Top Left
        ], 'f')

        # Generate vertex buffer object and fill it with vertex data from above
        if self.vbo is None:
            self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        if self.vao is None:
            # Generate vertex array object and pass vertex data into it
            self.vao = glGenVertexArrays(1)
            glBindVertexArray(self.vao)

            # XYZ
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * vertices.itemsize, None)
            glEnableVertexAttribArray(0)

            # RGB
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 8 * vertices.itemsize,
                                  ctypes.c_void_p(3 * vertices.itemsize))
            glEnableVertexAttribArray(1)

            # UV
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 8 * vertices.itemsize,
                                  ctypes.c_void_p(6 * vertices.itemsize))
            glEnableVertexAttribArray(2)

            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glBindVertexArray(0)

    def genFramebuffers(self, width, height):
        if self.width != width or self.height != height:
            self.width = width
            self.height = height

            if self.fboB is not None:  # Delete old framebuffer object
                glDeleteFramebuffers([self.fboB])
            if self.fbotextureB is not None:  # Delete old framebuffer texture
                glDeleteTextures([self.fbotextureB])

            ### B
            self.fboB = glGenFramebuffers(1)
            glBindFramebuffer(GL_FRAMEBUFFER, self.fboB)
            self.fbotextureB = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.fbotextureB)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA,
                         GL_UNSIGNED_BYTE, None)

            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

            glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.fbotextureB, 0)

    def updateShaderprogramA(self, fragmentcode=None):
        if fragmentcode is not None:
            self.fragmentCodeA = fragmentcode

        vertexCode = """
        #version 330 core
        layout (location = 0) in vec3 position;
        layout (location = 1) in vec3 color;
        layout (location = 2) in vec2 texcoord;
        out vec3 vertColor;
        out vec2 texCoord;
        void main()
        {
            gl_Position = vec4(position.x, position.y, position.z, 1.0);
            vertColor = color;
            texCoord = texcoord;
        }
        """

        # Compile fragment shader
        try:
            self.fragmentShaderA = shaders.compileShader(self.fragmentCodeA, GL_FRAGMENT_SHADER)
        except:
            print(traceback.print_exc())

        # Compile vertex shader
        try:
            self.vertexShader = shaders.compileShader(vertexCode, GL_VERTEX_SHADER)
        except:
            print(traceback.print_exc())

        # Create shader program
        if isinstance(self.fragmentShaderA, int) and isinstance(self.vertexShader, int):
            self.shaderProgramA = shaders.compileProgram(self.fragmentShaderA, self.vertexShader)

    def updateShaderprogramB(self, fragmentcode=None):
        if fragmentcode is not None:
            self.fragmentCodeB = fragmentcode

        vertexCode = """
        #version 330 core
        layout (location = 0) in vec3 position;
        layout (location = 1) in vec3 color;
        layout (location = 2) in vec2 texcoord;
        out vec3 vertColor;
        out vec2 texCoord;
        void main()
        {
            gl_Position = vec4(position.x, position.y, position.z, 1.0);
            vertColor = color;
            texCoord = texcoord;
        }
        """

        # Compile fragment shader
        try:
            self.fragmentShaderB = shaders.compileShader(self.fragmentCodeB, GL_FRAGMENT_SHADER)
        except:
            print(traceback.print_exc())

        # Compile vertex shader
        try:
            self.vertexShader = shaders.compileShader(vertexCode, GL_VERTEX_SHADER)
        except:
            print(traceback.print_exc())

        # Create shader program
        if isinstance(self.fragmentShaderB, int) and isinstance(self.vertexShader, int):
            self.shaderProgramB = shaders.compileProgram(self.fragmentShaderB, self.vertexShader)

    def checkFragmentcode(self):
        if os.path.exists(self.fragmentPathA) and os.path.isfile(self.fragmentPathA):
            if os.path.getmtime(self.fragmentPathA) > self.lastReadA:
                self.lastReadA = os.path.getmtime(self.fragmentPathA)
                with open(self.fragmentPathA, "r") as f:
                    self.updateShaderprogramA(f.read())
        else:
            self.lastReadA = 0

        if os.path.exists(self.fragmentPathB) and os.path.isfile(self.fragmentPathB):
            if os.path.getmtime(self.fragmentPathB) > self.lastReadB:
                self.lastReadB = os.path.getmtime(self.fragmentPathB)
                with open(self.fragmentPathB, "r") as f:
                    self.updateShaderprogramB(f.read())
        else:
            self.lastReadB = 0

    def render(self, runtime, textures):
        self.genFramebuffers(runtime.width, runtime.height)

        if self.checkCounter >= 40:
            self.checkFragmentcode()
            self.checkCounter = 0
        else:
            self.checkCounter += 1

        for buf in [(self.shaderProgramB, self.fboB), (self.shaderProgramA, runtime.fbo)]:
            glBindFramebuffer(GL_FRAMEBUFFER, buf[1])

            glUseProgram(buf[0])

            # Pass previous frame to shader
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.fbotextureB)
            uniformLoc = glGetUniformLocation(buf[0], "bufA")
            if not uniformLoc == -1:
                glUniform1i(uniformLoc, 0)

            if 1 in textures:
                glActiveTexture(GL_TEXTURE1)
                glBindTexture(GL_TEXTURE_2D, textures[1].getTexture())
                uniformLoc = glGetUniformLocation(buf[0], "tex1")
                if not uniformLoc == -1:
                    glUniform1i(uniformLoc, 0)

            if 2 in textures:
                glActiveTexture(GL_TEXTURE2)
                glBindTexture(GL_TEXTURE_2D, textures[2].getTexture())
                uniformLoc = glGetUniformLocation(buf[0], "tex2")
                if not uniformLoc == -1:
                    glUniform1i(uniformLoc, 0)

            if 3 in textures:
                glActiveTexture(GL_TEXTURE3)
                glBindTexture(GL_TEXTURE_2D, textures[3].getTexture())
                uniformLoc = glGetUniformLocation(buf[0], "tex3")
                if not uniformLoc == -1:
                    glUniform1i(uniformLoc, 0)
            else:
                glActiveTexture(GL_TEXTURE5)
                glBindTexture(GL_TEXTURE_2D, self.fbotextureB)
                uniformLoc = glGetUniformLocation(buf[0], "bufB")
                if not uniformLoc == -1:
                    glUniform1i(uniformLoc, 0)

            # Uniforms
            uniformLoc = glGetUniformLocation(buf[0], "t")
            if not uniformLoc == -1:
                glUniform2f(uniformLoc, runtime.time, runtime.deltatime)

            uniformLoc = glGetUniformLocation(buf[0], "res")
            if not uniformLoc == -1:
                glUniform2f(uniformLoc, runtime.width, runtime.height)

            # TODO: Get beat signal from artnet
            uniformLoc = glGetUniformLocation(buf[0], "beat")
            if not uniformLoc == -1:
                glUniform4f(uniformLoc, 0, 0, 0, 0)

            glBindVertexArray(self.vao)
            tricount = 2
            glDrawArrays(GL_TRIANGLES, 0, tricount * 3)
            glBindVertexArray(0)







