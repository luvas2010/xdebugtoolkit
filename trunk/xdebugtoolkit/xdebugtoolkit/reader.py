class AggregatedCall:
    
    def __init__(self, fl, fn):
        self.fn = fn
        self.fl = fl
        self.subcalls = []
        self.call_count = 0
        self.min_self_time = None
        self.max_self_time = None
        self.sum_self_time = 0
        self.min_inclusive_time = None
        self.max_inclusive_time = None
        self.sum_inclusive_time = 0
    
    def add_call(self, fl, fn, self_time, inclusive_time):
        self._merge(fl, fn, 1, self_time, self_time, self_time, inclusive_time, inclusive_time, inclusive_time)

    def merge(self, call):
        if call.call_count > 0:
            self._merge(call.fl, call.fn, call.call_count, call.min_self_time, call.max_self_time, call.sum_self_time, call.min_inclusive_time, call.max_inclusive_time, call.sum_inclusive_time)
            
    def _merge(self, fl, fn, call_count, min_self_time, max_self_time, sum_self_time,
               min_inclusive_time, max_inclusive_time, sum_inclusive_time):
        assert self.fl == fl
        assert self.fn == fn

        self.call_count += call_count
        if self.min_self_time is None:
            self.min_self_time = min_self_time
        else:
            self.min_self_time = min(self.min_self_time, min_self_time)
        self.max_self_time = max(self.max_self_time, max_self_time)
        self.sum_self_time += sum_self_time
        if self.min_inclusive_time is None:
            self.min_inclusive_time = min_inclusive_time
        else:
            self.min_inclusive_time = min(self.min_inclusive_time, min_inclusive_time)
        self.max_inclusive_time = max(self.max_inclusive_time, max_inclusive_time)
        self.sum_inclusive_time += sum_inclusive_time


class CallTree:

    def __init__(self):
        self.fl_map = None
        self.fn_map = None
        self.max_self_time = 0
        self.max_call_count = 0
        self.total_call_count = 0
        self.root_node = AggregatedCall(None, None)
    
    def get_max_self_time(self): return self.max_self_time
    def get_total_time(self): return self.root_node.sum_inclusive_time
    def get_max_call_count(self): return self.max_call_count
    def get_total_call_count(self): return self.total_call_count
    
    def to_string(self):
        fn_rev = self.fn_map.rev()
        
        ret = []
        
        stack = [self.root_node]
        stack_pos = [0]

        ret.append('  ' * (len(stack) - 1) + '/') 
        ret.append('            (self_time = %s, inclusive_time = %s)' % (stack[-1].self_time, stack[-1].inclusive_time))
        ret.append('\n');

        while len(stack):
            
            stack.append(stack[-1].subcalls[stack_pos[-1]])
            stack_pos[-1] += 1
            stack_pos.append(0)
            
            ret.append('  ' * (len(stack) - 1))
            ret.append('%s x ' % stack[-1].call_count)
            ret.append(fn_rev[stack[-1].fn])
            ret.append(' (self_time = %s, inclusive_time = %s)' % (stack[-1].self_time, stack[-1].inclusive_time))
            ret.append('\n');
                
            # cleanup stack
            while len(stack) and len(stack[-1].subcalls) == stack_pos[-1]:
                del(stack[-1])
                del(stack_pos[-1])
        
        return "".join(ret)


class XdebugCachegrindTreeBuilder:
    """A tree builder class.
    
    It accepts a parser, uses it to fetch cachegrind's raw structure and
    composes a tree from it.
    """
    
    def __init__(self, parser):
        self.parser = parser

    def get_tree(self):
        body = self.parser.get_body()

        nodes = []
        stack = []
        root_node = AggregatedCall(None, None)
        stack.append([0, -1])
        nodes.append(root_node)
        i = len(body)
        while i > 0:
            i -= 1
            entry = body[i];

            inclusive_time = entry.self_time + sum([x.inclusive_time for x in entry.subcalls])

            node = AggregatedCall(entry.fl, entry.fn);
            node.add_call(entry.fl, entry.fn, entry.self_time, inclusive_time)

            node_id = len(nodes)
            nodes.append(node)

            parent_id, parent_expected_calls = stack[-1]
            parent = nodes[parent_id]

            # add node to it's parent
            # at the moment they are in the reverse order
            parent.subcalls.append(node)

            expected_calls = len(entry.subcalls)

            # fill stack
            stack.append([node_id, expected_calls])

            # clean up stack
            j = len(stack) - 1
            while len(nodes[stack[j][0]].subcalls) == stack[j][1]:
                # fix reverse order in filled nodes
                nodes[stack[j][0]].subcalls.reverse()
        
                del(stack[j])
                j -= 1

        # reverse the root_node's subcalls separately
        root_node.subcalls.reverse()
        
        # calculate inclusive_time for the root_node separately
        inclusive_time = sum([x.sum_inclusive_time for x in root_node.subcalls])
        root_node.add_call(None, None, 0, inclusive_time)

        tree = CallTree()
        tree.fl_map = self.parser.fl_map
        tree.fn_map = self.parser.fn_map
        tree.total_call_count = len(body)
        tree.max_call_count = 1
        tree.root_node = root_node
        return tree


class CallTreeFilter:

    def filter_depth(self, tree, depth):
        stack = [tree.root_node]
        stack_pos = [-1, 0]

        while len(stack):
            stack.append(stack[-1].subcalls[stack_pos[-1]])
            stack_pos[-1] += 1
            stack_pos.append(0)
            
            if len(stack) == depth:
                stack[-1].subcalls = []
                
            # cleanup stack
            while len(stack) and len(stack[-1].subcalls) == stack_pos[-1]:
                del(stack[-1])
                del(stack_pos[-1])

    def filter_inclusive_time(self, tree, percent_threshold):
        stack = [tree.root_node]
        stack_pos = [-1, 0]

        while len(stack):
            parent = stack[-1]
            call = parent.subcalls[stack_pos[-1]]
            if call.sum_inclusive_time > tree.get_total_time() * percent_threshold / 100:
                stack.append(call)
                stack_pos[-1] += 1
                stack_pos.append(0)
            else:
                parent.subcalls[stack_pos[-1]:stack_pos[-1]+1] = []
                
            # cleanup stack
            while len(stack) and len(stack[-1].subcalls) == stack_pos[-1]:
                del(stack[-1])
                del(stack_pos[-1])
        

class CallTreeAggregator:
    
    def __init__(self):
        pass
    
    def aggregate_call_paths(self, tree):
        max_self_time = 0
        max_call_count = 0
        path_map = {}
        
        stack = [tree.root_node]
        stack_pos = [0]
        stack_path = [-1, -1]

        # create a new aggregated call
        new_root_node = AggregatedCall(stack[-1].fl, stack[-1].fn)
        path_map[tuple(stack_path)] = new_root_node

        new_root_node.merge(stack[-1])
        
        while len(stack):
            stack.append(stack[-1].subcalls[stack_pos[-1]])
            stack_pos[-1] += 1
            stack_pos.append(0)
            
            stack_path.extend((stack[-1].fl, stack[-1].fn))
            
            try:
                call = path_map[tuple(stack_path)]
            except KeyError:
                # create a new aggregated call 
                call = AggregatedCall(stack[-1].fl, stack[-1].fn)
                path_map[tuple(stack_path)] = call
                
                # and append it to it's parent
                parent_call = path_map[tuple(stack_path[:-2])]
                parent_call.subcalls.append(call)

            call.merge(stack[-1])

            # update max_subcall_count and max_self_time
            max_call_count = max(max_call_count, call.call_count)
            max_self_time = max(max_self_time, call.sum_self_time)

            # cleanup stack
            while len(stack) and len(stack[-1].subcalls) == stack_pos[-1]:
                del(stack[-1])
                del(stack_pos[-1])
                del(stack_path[-2:])
                
        new_tree = CallTree()
        new_tree.root_node = new_root_node
        new_tree.fl_map = tree.fl_map
        new_tree.max_self_time = max_self_time
        new_tree.total_call_count = tree.total_call_count
        new_tree.max_call_count = max_call_count
        new_tree.fn_map = tree.fn_map
        return new_tree


if __name__ == '__main__':
    import sys
    parser = XdebugCachegrindFsaParser(sys.argv[1])
    tree = XdebugCachegrindTreeBuilder(parser).get_tree()
    #CallTreeFilter().filter_depth(tree, 6)
    tree_aggregator = CallTreeAggregator()
    tree = CallTreeAggregator().aggregate_call_paths(tree)
    CallTreeFilter().filter_inclusive_time(tree, 0.15)
    #print tree.to_string()
    print DotBuilder().get_dot(tree, DotNodeStyler)
