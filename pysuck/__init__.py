PYSUCKSTOP = False

def initialize(args):
    print(str(args))

def sig_handler(signum=None, frame=None):
    if signum is not None:
        print("This picks up a signal")


