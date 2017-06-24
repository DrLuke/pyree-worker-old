import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', help='TCP and UDP port used for primary communication', default=31337, type=int)

if __name__ == "__main__":
    pass