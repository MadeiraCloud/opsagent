'''
VisualOps agent Checksum library
(c) 2014 - MadeiraCloud LTD.

@author: Thibault BRONCHAIN
'''

import os
import hashlib
import urllib2

from opsagent import utils

#label: state type-name (or uuid?)

URI_TIMEOUT=600

class Checksum():
    # filepath:reference file  label:checksum file reference  dirname:checksum location
    # checksum filepath -> dirname/label-filename.cksum
    def __init__(self, filepath, label, dirname, uri=None):
        self.__cksumpath = os.path.join(dirname,
                                        ("%s-%s.cksum"%(label,filepath)).replace('/','-'))
        self.__filepath = filepath
        self.__cksum = None
        self.__uri = uri
        try:
            with open(self.__cksumpath,'r') as f:
                self.__cksum = f.read()
        except Exception as e:
            utils.log("DEBUG", "checksum can't be fetched from disk (file %s): %s"%(self.__cksumpath,e),('__init__',self))
        else:
            utils.log("DEBUG", "checksum fetched from disk (file %s): %s"%(self.__cksumpath,self.__cksum),('__init__',self))

    # calculates checksums by chunk
    def __md5sum(self, f):
        md5 = hashlib.md5()
        for chunk in iter(lambda: f.read(128 * md5.block_size), b''):
            md5.update(chunk)
        return md5.hexdigest()

    # update checksum if changed, return change state
    # cksum:new checksum (if external)  persist:write on disk  tfirst:return true if no old cksum
    def update(self, cksum=None, persist=True, edit=True, tfirst=True):
        if not cksum:
            try:
                if self.__uri:
                    f = urllib2.urlopen(self.__uri, timeout=URI_TIMEOUT)
                else:
                    f = open(self.__filepath, 'rb')
                cksum = self.__md5sum(f)
                try:
                    f.close()
                except Exception: pass
            except Exception as e:
                utils.log("DEBUG", "Can't hash file %s: %s"%(self.__filepath,e),('__init__',self))
                cksum = None
        utils.log("DEBUG", "Old cksum:%s - New cksum: %s (file: %s)"%(self.__cksum,cksum,self.__filepath),('update',self))
        if cksum != self.__cksum:
            ret = (False if tfirst is False and not self.__cksum else True)
            if edit:
                self.__cksum = cksum
            if persist and edit:
                with open(self.__cksumpath, 'w') as f:
                    f.write((cksum if cksum else ""))
                utils.log("DEBUG", "Checksum saved on disk under file: %s"%(self.__cksumpath),('update',self))
            utils.log("INFO", "Change found in file: %s"%(self.__filepath),('update',self))
            utils.log("DEBUG", "Return value: %s"%(ret),('update',self))
            return ret
        utils.log("DEBUG", "No change found in file: %s"%(self.__filepath),('update',self))
        return False

    # check if checksum has changed, return change state
    # cksum:new checksum (if external)  tfirst:return true if no old cksum
    def check(self, cksum=None, tfirst=True):
        return self.update(cksum=cksum,persist=False,edit=False,tfirst=tfirst)

    # return checksum
    def get(self):
        return self.__cksum

    def filepath(self):
        return self.__filepath

    # reset curent checksum
    # persiste: write on disk
    def reset(self, persist=True):
        if persist:
            open(self.__cksumpath, 'w').close()
        self.__cksum = None
        utils.log("INFO", "Checksum reset (file %s). Write on disk=%s"%(self.__filepath,persist),('reset',self))


## Example1: watch
#cs = Checksum(watch,sid,self.__config['global']['watch'])
#if cs.update():
#    #file has changed
#    parameter["watch"] = True
#
## Example2: use external cksum (*pseudo code*)
#cs = Checksum(archive_path,unique_label,archive_cksum_path)
#if cs.check(cksum=newcksum):
#    while cs.get() != newcksum:
#        download(archive_uri)
#        cs.update()
