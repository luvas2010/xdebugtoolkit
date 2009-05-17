'''
Created on May 16, 2009

@author: wicked
'''
import unittest
from cgparser import *
from reader import *


class Test(unittest.TestCase):
    
    #filename = 'fixtures/cachegrind.out.2776'
    filename = 'fixtures/1241577166_325172.cg'
    
    def setUp(self):
        self.parser = XdebugCachegrindFsaParser(self.filename)
        self.tree_builder = XdebugCachegrindTreeBuilder(self.parser)

    def testGetTree(self):
        tree = self.tree_builder.get_tree()
        print tree
        self.assertEquals(tree.get_max_self_time(), 23525)
        self.assertEquals(tree.get_total_time(), 23798)
        self.assertEquals(tree.get_max_call_count(), 1)
        self.assertEquals(tree.get_total_call_count(), 14)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()