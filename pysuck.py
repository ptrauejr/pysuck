#!/usr/bin/env python3

import argparse
import signal

import pysuck

def main():
    """Gets command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="turn on debugging", action="store_true")
    parser.add_argument("--ssl", help="Use ssl for pull server", action="store_true")
    parser.add_argument("--pullserver", help="Server for news pull", default="news")
    parser.add_argument("--pulluser", help="User for use on the pull server", default=None)
    parser.add_argument("--pullpassword", help="Password for use on the pull server", default=None)
    parser.add_argument("--db", help="Path for Database and temporary files", default=None)

    """Parse arguments"""
    args = parser.parse_args()

    # Initialize app
    pysuck.initialize(args)




if __name__ == '__main__':
    # Catch signals for quitting properly
    signal.signal(signal.SIGINT, pysuck.sig_handler)
    signal.signal(signal.SIGTERM, pysuck.sig_handler)

    main()
