'''
Created on May 9, 2009

@author: wicked
'''

class AutoIncrementMap(object):
    '''
    AutoIncrementMap is a structure for storing some data records
    with auto-increment ids. It handles fast mapping in both
    directions. Auto-increments works when you try
    to fetch an id for a record which hasn't been put into the
    structure yet, and will assign a new id to that record. If you
    then try to fetch the id once again, you'll just get the same
    id one more time.
    
    NB: an id assigned to the first records is 0
    
    The get_by_id() method is used for reverse mapping: id -> record.
    Auto-increment is naturally doesn't work in this case.
    
    Please check the package's unit test for examples. 
    '''


    def __init__(self):
        self.data = {}
        self.rev = []
    def __repr__(self):
        return repr(self.data)
    def __len__(self):
        return len(self.data)
    def __getitem__(self, key):
        return self.store(key)
    def has_key(self, key):
        return self.data.has_key(key)
    def __contains__(self, key):
        return key in self.data
    def merge(self, af):
        for key in af.data:
            self[key]
    def get_by_id(self, id):
        return self.rev[id]
    def __iter__(self):
        return iter(self.rev)
    def store(self, key):
        if key in self.data:
            return self.data[key]
        else:
            self.data[key] = len(self.data)
            self.rev.append(key)
            return self.data[key]
