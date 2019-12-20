#!/usr/bin/python3
"""Keybox

Usage:
    keybox.py [-hv] [-r REMOTE] [-l LOCAL] DATABASE

Options:
    -h --help  show this message
    -v --verbose  show extended output
    -r REMOTE, --remote REMOTE  rclone remote directory
    -l --local LOCAL        local directory

    DATABASE                database name

"""

import subprocess
import os
import sys
import hashlib
import argparse
from datetime import datetime
from docopt import docopt


DATABASE_NAME = "ewilson.kdbx"
REMOTE_DIR = "dropbox:keepass"
LOCAL_DIR  = os.environ['HOME'] + "/keepass"

"""
Implemetation of Dropbox hashing algorithm
"""
def hash(fname):
    method = hashlib.sha256()
    bstring = b''
    with open(fname, 'rb') as f:
        block = f.read(4194304)
        m = method.copy()
        m.update(block)
        bstring += m.digest()

    method.update(bstring)
    result = method.hexdigest()
    return result

"""
Runs rclone synchronization from source to dest
"""
def syncDir(source, dest):
    args = [
        "rclone",
        "sync",
        source,
        dest
    ]

    proc = subprocess.run(args, capture_output=True)
    if proc.returncode is not 0:
        return False
    return True

"""
Retreive a dict with the stats of the remote directory
"""
def getRemoteStats():
    statOrder = ["path", "time", "size", "hash"]
    args = [
        "rclone",
        "lsf",
        "--hash",
        "DropboxHash",
        "-F",
        "ptsh",
        "-s",
        "|",
        REMOTE_DIR
    ]

    proc = subprocess.run(args, capture_output=True, text=True)

    if proc.returncode is not 0:
        print(remoteStatCall.stderr)
        exit(1)

    result = proc.stdout.strip().split("|")

    remoteStats = dict(zip(statOrder, result))

    return remoteStats

"""
Main method
"""
def main():

    args = docopt(__doc__)

    rmt = getRemoteStats()

    remoteTime = datetime.strptime(rmt["time"], "%Y-%m-%d %H:%M:%S").timestamp()
    remoteHash = rmt["hash"]

    localTime = os.lstat(LOCAL_DIR  + '/' + DATABASE_NAME).st_mtime
    localHash = hash(LOCAL_DIR  + '/' + DATABASE_NAME)

    if not remoteHash == localHash:
        if remoteTime > localTime:
            if syncDir(REMOTE_DIR, LOCAL_DIR):
                print("Synchronized from remote")
            else:
                print("Could not sync files!")
        elif remoteTime < localTime:
            print("Local database is newer, will sync on exit")
        else:
            print("Files are in sync")
    else:
        print("Files are in sync")

    subprocess.run(["keepassxc"], capture_output=True)

    if syncDir(LOCAL_DIR, REMOTE_DIR):
        print("Synchronized to remote")
    else:
        print("Could not synchronize files!")

# execute script
if __name__ == "__main__":
    main()
