if __name__ == '__main__':
    import sys
    import xdebugtoolkit.cgparser
    import xdebugtoolkit.reader
    import xdebugtoolkit.dot
    import xdebugtoolkit.stylers.default
    parser = xdebugtoolkit.cgparser.XdebugCachegrindFsaParser(sys.argv[1])
    tree = xdebugtoolkit.reader.XdebugCachegrindTreeBuilder(parser).get_tree()
    tree_aggregator = xdebugtoolkit.reader.CallTreeAggregator()
    tree = xdebugtoolkit.reader.CallTreeAggregator().aggregate_call_paths(tree)
    xdebugtoolkit.reader.CallTreeFilter().filter_inclusive_time(tree, 0.15)
    print xdebugtoolkit.dot.DotBuilder().get_dot(tree, xdebugtoolkit.stylers.default.DotNodeStyler)
