#!/usr/bin/env python

# file: gridfs_handler.py
# brief: custom API for MongoDB GridFS
# author: caosiyang <csy3228@gmail.com>
# date: 2013/05/30

import os
import sys
import random
import time
from pymongo.mongo_client import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from bson.objectid import ObjectId
from gridfs import GridFS


class GridfsHandler:
    """MongoDB GridFS handler.
    """
    def __init__(self, host, port, dbname, bucketname="fs"):
        """Connect to MongoDB server.
        """
        self.host = host
        self.port = port
        self.dbname = dbname
        self.bucketname = bucketname
        try:
            self.client = MongoClient(host=self.host, port=self.port)
            self.db = Database(self.client, self.dbname)
            self.gridfs = GridFS(self.db, self.bucketname)
        except Exception, e:
            print e
            raise e

    def __del__(self):
        """Close connection.
        """
        self.close()

    def close(self):
        """Close connection.
        """
        if self.client:
            self.client.close()
            self.client = None

    def put(self, filepath):
        """Add a file with specfic filepath.
        Return: code, _id, md5
        code:
            0 - success
           -1 - failed
        """
        try:
            if filepath and os.path.exists(filepath) and os.path.isfile(filepath):
                fd = open(filepath, 'r')
                content = fd.read()
                fd.close()
                id = self._put(filepath, content)
                if id:
                    collname = '%s.files' % self.bucketname
                    coll = Collection(self.db, collname)
                    if coll:
                        doc = coll.find_one({'_id': id}, {'md5': 1})
                        if doc:
                            md5 = doc['md5']
                            return 0, str(id), str(md5)
                        else:
                            print "[ERROR] not found document with id '%s'" % str(id)
                    else:
                        print "[ERROR] not found collection with name '%s'" % collname
                else:
                    print "[ERROR] put file '%s' failed"  % filepath
            else:
                print "[ERROR] not found file '%s'" % filepath
        except Exception, e:
            print e
        return -1, None, None

    def _put(self, filepath, filecontent):
        """Add a file.
        Return: _id
        """
        try:
            id = self.gridfs.put(filecontent, filename=filepath)
            return id
        except Exception, e:
            print e
            return None

    def get(self, filepath):
        """Get the lastest file with specific filepath.
        Return: file content
        """
        try:
            collname = '%s.files' % self.bucketname
            coll = Collection(self.db, collname)
            if coll:
                doc = coll.find_one({'filename': str(filepath)}, sort=[('uploadDate', -1)])
                if doc:
                    id = doc['_id']
                    gout = self.gridfs.get(ObjectId(id))
                    if gout:
                        content = gout.read()
                        gout.close()
                        return content
        except Exception, e:
            print e
            return None

    def delete(self, id):
        """Delete a file with specfic _id.
        Return: True/False
        """
        try:
            self.gridfs.delete(ObjectId(id))
        except Exception, e:
            print e
            raise e


def test():
    h = GridfsHandler("10.10.135.51", 27017, "pic", "fs")
    filepath = './logo001.png'
    retval, id, md5 = h.put(filepath)
    print "[put] retval: %d, id: %s, md5: %s" % (retval, id, md5)
    if retval == 0:
        filecontent = h.get(filepath)
        if filecontent:
            print "[get] content length: %d" % len(filecontent)
    #h.delete(id)
    h.close()


def stability_test():
    fd = open('log', 'a')
    h = GridfsHandler("10.10.135.51", 27017, "pic", "fs")
    for i in range(100000):
        print >> fd, i
        retval, id, md5 = h.put("./logo001.png")
        print >> fd, "retval: %d, id: %s, md5: %s" % (retval, id, md5)
        if id:
            filecontent = h.get(id)
            if filecontent:
                print >> fd, "content length: %d" % len(filecontent)
        fd.flush()
        time.sleep(1)
    h.close()
    fd.close()


if __name__ == "__main__":
    test()