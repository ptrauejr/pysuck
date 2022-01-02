import logging
import os
import sqlite3
import sys
import threading
import time
import zlib

import pysuck
from pysuck.constants import DB_NAME
from pysuck.decorators import synchronized
from pysuck.filesystem import remove_file

DB_LOCK = threading.RLock()

def convert_search(search):
    """Convert classic wildcard to SQL wildcard"""
    if not search:
        # Default value
        search = ""
    else:
        # Allow * for wildcard matching and space
        search = search.replace("*", "%").replace(" ", "%")

class DB:
    """Class to access the database
    Each class-instance will create an access channel that
    can be used in one thread.
    Each thread needs its own class-instance"""

    # These class attributes will be accessed directly because
    # they need to be shared by all instances
    db_path = None
    done_cleaning = False

    @synchronized(DB_LOCK)
    def __init__(self):
        """Determine database path and create conection"""
        self.con = self.c = None
        if not DB.db_path:
            DB.db_path = os.path.join(args.db, DB_NAME)
        self.connect()

    def connect(self):
        """Create a connection to the database"""
        create_table = not os.path.exists(DB.db_path)
        self.con = sqlite3.connect(DB.db_path)
        self.con.row_factor = sqlite3.Row
        self.c = self.con.cursor()
        if create_table:
            self.create_db()
        elif not DB.done_cleaning:
            # Run VACUUM on sqlite
            # When an object (table, index, or trigger) is dropped from the database, it leaves behind empty space
            # http://www.sqlite.org/lang_vaccum.html
            DB.done_cleaning = True
            self.execute("VACUUM")

    def execute(self, command, args=(), save=False):
        """Wrapper for executing SQL commands"""
        for tries in range(5, 0, -1):
            try:
                if args and isinstance(args, tuple):
                    self.c.execute(command, args)
                else:
                    self.c.execute(command)
                if save:
                    self.con.commit()
                return True
            except:
                error = str(sys.exc_info()[1])
                if tries >= 0 and "is locked" in error:
                    logging.debug("Database locked, wait and retry")
                    time.sleep(0.5)
                    continue
                elif "readonly" in error:
                    logging.error("Cannot write to History database, check access rights!")
                    # Report back success, because there's no recovery possible
                    return True
                elif "not a database" in error or "malformed" in error or "duplicate column name" in error:
                    logging.error("Damaged Hisotry database, created empty replacement")
                    logging.info("Traceback: ", exc_info=True)
                    self.close()
                    try:
                        remove_file(DB.db_path)
                    except:
                        pass
                    self.connect()
                    # Return False in case of "duplicate column" error
                    # because the column addition in connect() must be terminated
                    return "duplicate column name" not in error
                else:
                    logging.error("SQL Command failed, see log")
                    logging.info("SQL: %s", command)
                    logging.info("Argumnets: %s", repr(args))
                    logging.info("Traceback: ", exc_info=True)
                    try:
                        self.con.rollback()
                    except:
                        logging.debug("Rollback Failed: ", exc_info=True)
        return False

    def create_db(self):
        """Create a new (empty) database file"""
        self.execute(
            """
                CREATE TABLE "post" (
                    "id" INTEGER PRIMARY KEY,
                    "completed" INTEGER NOT NULL,
                    "msgid" TEXT NOT NULL,
                    "status" INTEGER NOT NULL
                )
            """
        )
        self.execute(
            """
                CREATE UNIQUE INDEX idx_post_msgid on posts(msgid)
            """
        )
        self.execute(
            """
                CREATE TABLE "group" (
                    "id" INTEGER PRIMARY KEY,
                    "name" TEXT NOT NULL,
                    "high_mark" INTEGER NOT NULL,
                    "enabled" INTEGER NOT NULL
                )
            """
        )
        self.execute(
            """
                CREATE UNIQUE INDEX "idx_group_name" on group(name)
            """
        )
        self.execute(
            """
                CREATE INDEX "idx_group_enabled" on group("enabled")
            """
        )
        self.execute(
            """
                CREATE TABLE "message" (
                    "id" INTEGER PRIMARY KEY,
                    "post_id" INTEGER NOT NULL,
                    "group_id" INTEGER NOT NULL
                )
            """
        )

        self.execute("PRAGMA user_version = 1;")

    def close(self):
        """Close database connection"""
        try:
            self.c.close()
            self.con.close()
        except:
            logging.error("Failed to close database, see log")
            logging.info("Traceback: ", exc_info=True)



