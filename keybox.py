#!/usr/bin/python3
"""Keybox

Usage:
    keybox.py [-hv] [-r REMOTE] [-l LOCAL] [DATABASE]

Options:
    -h --help                       show this message
    -r REMOTE, --remote REMOTE      rclone remote directory
    -l LOCAL, --local LOCAL         local directory

    DATABASE                        database name

"""

import subprocess
import os
import sys
import hashlib
from datetime import datetime
from docopt import docopt

DATABASE_DEFAULT = "passwords.kdbx"
LOCAL_DIR_DEFAULT  = os.environ['HOME'] + "/keepass"
REMOTE_DIR_DEFAULT = "remote:keepass"

def dropboxHash(fname):
    """Implemetation of Dropbox hashing algorithm"""
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

def syncDir(source, dest):
    """Runs rclone synchronization from source to dest"""

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

def getRemoteStats(remoteDir):
    """Retreive a dict with the stats of the remote directory"""

    statOrder = ["path", "time", "size", "hash"]
    args = [
        "rclone",
        "lsf",
        "--hash",
        "DropboxHash",
        "--format",
        "ptsh",
        "--separator",
        "|",
        remoteDir
    ]

    proc = subprocess.run(args, capture_output=True, text=True)

    if proc.returncode is not 0:
        print(proc.stderr)
        exit(1)

    result = proc.stdout.strip().split("|")

    remoteStats = dict(zip(statOrder, result))

    return remoteStats

def processArgs():
    """Retrieve command line arguments and set local vars, using defaults if needed"""

    args = docopt(__doc__)

    remote = local = database = None

    for key, val in args.items():
        if key == '--remote':
            remote = val or REMOTE_DIR_DEFAULT
        elif key == '--local':
            local = val or LOCAL_DIR_DEFAULT
        elif key == 'DATABASE':
            database = val or DATABASE_DEFAULT

    return (remote, local, database)


def main():
    """Main method"""

    remote, local, database = processArgs()
    rmt = getRemoteStats(remote)

    remoteTime = datetime.strptime(rmt["time"], "%Y-%m-%d %H:%M:%S").timestamp()
    remoteHash = rmt["hash"]

    localTime = os.lstat(local  + '/' + database).st_mtime
    localHash = dropboxHash(local  + '/' + database)

    if not remoteHash == localHash:
        if remoteTime > localTime:
            if syncDir(remote, local):
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

    if syncDir(local, remote):
        print("Synchronized to remote")
    else:
        print("Could not synchronize files!")

# execute script
if __name__ == "__main__":
    main()
