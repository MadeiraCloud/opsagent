'''
Madeira OpsAgent Checksum library

@author: Thibault BRONCHAIN
'''

import os
import hashlib

#label: state type-name

class Checksum():
    # filename:reference file  label:checksum file reference  dirname:checksum location
    # checksum filepath -> dirname/label-filename.cksum
    def __init__(self, filepath, label, dirname):
        self.__cksumpath = os.path.join(dirname,
                                        '/',
                                        label.replace('/','-'),
                                        '-',
                                        filepath.replace('/','-'),
                                        '.cksum')
        self.__filepath = filename
        self.__cksum = None
        try:
            with open(self.__cksumpath,'r') as f:
                self.__cksum = f.read()
        except Exception: pass

    # update checksum if changed, return change state
    # cksum:new checksum (if external)  persist:write on disk  tfirst:return true if no old cksum
    def update(self, cksum=None, persist=True, tfirst=True):
        if not cksum:
            with open(self.__filepath, 'r') as f:
                cksum = hashlib.md5(f.read()).hexdigest()
        if cksum != self.__cksum or (not cksum):
            ret=(False if not cksum and tfirst=False else True)
            self.__cksum = cksum
            if persist:
                with open(self.__cksumpath, 'w') as f:
                    f.write(cksum)
            return ret
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
