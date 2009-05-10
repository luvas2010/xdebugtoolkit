if __name__ == '__main__':
    import sys
    from cgparser import XdebugCachegrindFsaParser
    from reader import CallTree, CallTreeAggregator, CallTreeFilter, XdebugCachegrindTreeBuilder
    from dot import DotBuilder
    from stylers.default import DotNodeStyler
    
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-t', '--threshold', dest='threshold',
                      action="store", type="float", default=1,
                      help='remove fast tails that took less then this percent of total execution time. Default is %default%.')
    (options, args) = parser.parse_args(sys.argv[1:])
    if len(args) == 0:
        parser.error('incorrect number of arguments')
    
    merged_tree = CallTree()
    tree_aggregator = CallTreeAggregator()

    for file in args:
        parser = XdebugCachegrindFsaParser(file)
        tree = XdebugCachegrindTreeBuilder(parser).get_tree()
        merged_tree.merge(tree)
        merged_tree = tree_aggregator.aggregate_call_paths(merged_tree)

    merged_tree.filter_inclusive_time(options.threshold)
    print DotBuilder().get_dot(merged_tree, DotNodeStyler)
