import logging
import os

import pysuck

def remove_file(path: str):
    """Wrapper function so any file removal is logged"""
    logging.debug("Deleting file %s", path)
    os.remove(path)