'''
Created on May 9, 2009

@author: wicked
'''
import unittest
from autoincrementmap import AutoIncrementMap

class Test(unittest.TestCase):


    def testStore(self):
        map = AutoIncrementMap()
        id = map.store('a')
        self.assertEquals(id, 0)
        id = map.store('b')
        self.assertEquals(id, 1)


    def testStoreArrayAccess(self):
        map = AutoIncrementMap()
        id = map['a']
        self.assertEquals(id, 0)
        id = map['b']
        self.assertEquals(id, 1)

    def testZeroLen(self):
        map = AutoIncrementMap()
        self.assertEquals(len(map), 0)
        
    def testIncrementingLen(self):    
        map = AutoIncrementMap()
        map.store('a')
        self.assertEquals(len(map), 1)
        map.store('b')
        self.assertEquals(len(map), 2)
        
    def testNonIncrementingLen(self):    
        map = AutoIncrementMap()
        map.store('a')
        map.store('b')
        self.assertEquals(len(map), 2)
        map.store('a')
        map.store('b')
        self.assertEquals(len(map), 2)        
    
    def testContains(self):
        map = AutoIncrementMap()
        self.assertFalse('a' in map)
        self.assertFalse('b' in map)
        map.store('a')
        self.assertTrue('a' in map)
        self.assertFalse('b' in map)

    def testHasKey(self):
        map = AutoIncrementMap()
        self.assertFalse(map.has_key('a'))
        self.assertFalse(map.has_key('b'))
        map.store('a')
        self.assertTrue(map.has_key('a'))
        self.assertFalse(map.has_key('b'))
        
    def testGet(self):
        map = AutoIncrementMap()
        map.store('a')
        map.store('b')
        self.assertEquals(map.store('a'), 0)
        self.assertEquals(map.store('b'), 1)
        
    def testGetById(self):
        map = AutoIncrementMap()
        map.store('a')
        map.store('b')
        self.assertEquals(map.get_by_id(0), 'a')
        self.assertEquals(map.get_by_id(1), 'b')
        
    def testGetByIdFails(self):
        map = AutoIncrementMap()
        self.assertRaises(IndexError, map.get_by_id, 0)
        
    def testMerge(self):
        map1 = AutoIncrementMap()
        map1.store('a1')
        map1.store('b1')
        map2 = AutoIncrementMap()
        map2.store('b1')
        map2.store('a2')
        map2.store('b2')
        map1.merge(map2)
        
        self.assertEquals(len(map1), 4)
        
        self.assertTrue('a1' in map1)
        self.assertTrue('b1' in map1)
        self.assertTrue('a2' in map1)
        self.assertTrue('b2' in map1)

        self.assertEquals(map1.store('b2'), 3)
        self.assertEquals(map1.store('a2'), 2)
        self.assertEquals(map1.store('b1'), 1)
        self.assertEquals(map1.store('a1'), 0)

    def testIterate(self):
        map = AutoIncrementMap()
        map.store('a')
        map.store('b')
        test = []
        for i in map:
            test.append(i)
        self.assertEquals(test, ['a', 'b'])
    
    def testComprehension(self):
        map = AutoIncrementMap()
        map.store('a')
        map.store('b')
        test = [i for i in map]
        self.assertEquals(test, ['a', 'b'])
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testLen']
    unittest.main()