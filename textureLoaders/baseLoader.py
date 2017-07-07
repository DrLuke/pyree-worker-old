import glfw

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import *
from OpenGL.GL import shaders
import OpenGL

import PIL
from PIL import Image, ImageFont, ImageDraw

import os

import numpy as np

class VideoLoader():
    pass

    def loadTexture(self, path):
        newTextureID = None
        try:
            if path is not None and os.path.exists(path) and os.path.isfile(path):
                if os.path.exists(path + ".npy") and os.path.exists(path + ".size.npy"):
                    img_data = np.load(path + ".npy")
                    img_size = np.load(path + ".size.npy")
                else:
                    img = Image.open(path)
                    img = img.convert('RGBA').transpose(PIL.Image.FLIP_TOP_BOTTOM)
                    img_data = np.array(list(img.getdata()), 'B')
                    np.save(path, img_data)
                    img_size = np.array([img.size[0], img.size[1]])
                    np.save(path + ".size", img_size)
                newTextureID = glGenTextures(1)
                glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
                glBindTexture(GL_TEXTURE_2D, newTextureID)
                glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
                glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
                glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img_size[0], img_size[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
                glGenerateMipmap(GL_TEXTURE_2D)
        except:
            print("Texture load failed: %s" % path)
            newTextureID = None

        return newTextureID