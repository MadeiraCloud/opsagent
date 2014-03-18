'''
Madeira OpsAgent Checksum library

@author: Thibault BRONCHAIN
'''

import os
import hashlib

from opsagent import utils

#label: state type-name (or uuid?)

class Checksum():
    # filepath:reference file  label:checksum file reference  dirname:checksum location
    # checksum filepath -> dirname/label-filename.cksum
    def __init__(self, filepath, label, dirname):
        self.__cksumpath = os.path.join(dirname,
                                        '/',
                                        label.replace('/','-'),
                                        '-',
                                        filepath.replace('/','-'),
                                        '.cksum')
        self.__filepath = filepath
        self.__cksum = None
        try:
            with open(self.__cksumpath,'r') as f:
                self.__cksum = f.read()
        except Exception as e:
            utils.log("DEBUG", "checksum can't be fetched from disk (file %s): %s."%(self.__cksumpath,e),('__init__',self))
        else:
            utils.log("DEBUG", "checksum fetched from disk (file %s): %s."%(self.__cksumpath,self.__cksum),('__init__',self))

    # update checksum if changed, return change state
    # cksum:new checksum (if external)  persist:write on disk  tfirst:return true if no old cksum
    def update(self, cksum=None, persist=True, tfirst=True):
        if not cksum:
            with open(self.__filepath, 'r') as f:
                cksum = hashlib.md5(f.read()).hexdigest()
        utils.log("DEBUG", "Old cksum:%s - New cksum: %s (file: %s)"%(self.__cksum,cksum,self.__filepath),('update',self))
        if cksum != self.__cksum:
            ret = (False if tfirst is False and not self.__cksum else True)
            self.__cksum = cksum
            if persist:
                with open(self.__cksumpath, 'w') as f:
                    f.write(cksum)
                utils.log("DEBUG", "Checksum saved on disk under file: %s"%(self.__cksumpath),('update',self))
            utils.log("INFO", "Change found in file: %s"%(self.__filepath),('update',self))
            utils.log("DEBUG", "Return value: %s"%(ret),('update',self))
            return ret
        utils.log("DEBUG", "No change found in file: %s"%(self.__filepath),('update',self))
        return False

    # check if checksum has changed, return change state
    # cksum:new checksum (if external)  tfirst:return true if no old cksum
    def check(self, cksum=None, tfirst=True):
        return self.update(cksum=cksum,persist=False,tfirst=tfirst)

    # return checksum
    def get(self):
        return self.__cksum

    # reset curent checksum
    # persiste: write on disk
    def reset(self, persist=True):
        if persist:
            open(self.__cksumpath, 'w').close()
        self.__cksum = None
        utils.log("INFO", "Checksum reset (file %s). Write on disk=%s"%(self.__filepath,persist),('reset',self))
