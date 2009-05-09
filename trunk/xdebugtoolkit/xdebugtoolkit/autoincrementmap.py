'''
Created on May 9, 2009

@author: wicked
'''

class AutoIncrementMap(object):
    '''
    classdocs
    '''


    def __init__(self):
        self.data = {}
        self.rev = []
    def __repr__(self):
        return repr(self.data)
    def __len__(self):
        return len(self.data)
    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        else:
            self.data[key] = len(self.data)
            self.rev.append(key)
            return self.data[key]
    def has_key(self, key):
        return self.data.has_key(key)
    def __contains__(self, key):
        return key in self.data
    def merge(self, af):
        for key in af.data:
            self[key]
    def get_by_id(self, id):
        return self.rev[id]