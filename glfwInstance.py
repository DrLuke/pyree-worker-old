import glfw

class GlfwInstance():
    """Single GLFW Instance
    One GLFW Instance needs to be spawned for every monitor. It contains the rendering lopp for that monitor."""
    def __init__(self, monitor:glfw._GLFWmonitor):
        pass