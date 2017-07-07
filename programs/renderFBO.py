from glfwInstance import PyreeProgram

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import *
from OpenGL.GL import shaders
import OpenGL

import numpy as np
import traceback

class RenderFBO(PyreeProgram):
    def __init__(self):
        # vbo and vao
        self.uvxoffset = 0
        self.uvyoffset = 0

        self.vbo = None
        self.vao = None

        self.updateFBO()

        # shader program
        self.vertexShader = None

        self.fragmentcode = """
        #version 330 core
        in vec3 vertColor;
        in vec2 texCoord;
        layout(location = 0) out vec4 outColor;

        uniform sampler2D fboTex;

        void main()
        {
            outColor = texture(fboTex, texCoord);
        }
        """
        self.fragmentShader = None

        self.shaderProgram = None

        self.updateShaderprogram()     # Generate default shader

    def updateFBO(self):
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

    def updateShaderprogram(self, fragmentcode=None):
        if fragmentcode is not None:
            self.fragmentcode = fragmentcode

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
            self.fragmentShader = shaders.compileShader(self.fragmentcode, GL_FRAGMENT_SHADER)
        except:
            print(traceback.print_exc())

        # Compile vertex shader
        try:
            self.vertexShader = shaders.compileShader(vertexCode, GL_VERTEX_SHADER)
        except:
            print(traceback.print_exc())

        # Create shader program
        if isinstance(self.fragmentShader, int) and isinstance(self.vertexShader, int):
            self.shaderProgram = shaders.compileProgram(self.fragmentShader, self.vertexShader)

    def render(self, runtime, textures):

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        glUseProgram(self.shaderProgram)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, runtime.fbotexture)
        uniformLoc = glGetUniformLocation(self.shaderProgram, "fboTex")
        if not uniformLoc == -1:
            glUniform1i(uniformLoc, 0)

        # TODO: Get master fade from Artnet
        uniformLoc = glGetUniformLocation(self.shaderProgram, "master")
        if not uniformLoc == -1:
            glUniform2f(uniformLoc, 0, 0)

        glBindVertexArray(self.vao)
        tricount = 2
        glDrawArrays(GL_TRIANGLES, 0, tricount * 3)
        glBindVertexArray(0)
