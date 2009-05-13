import cgparser

class AggregatedCall(object):
    
    __slots__ = ('fn', 'fl', 'subcalls', 'call_count',
                 'min_self_time', 'max_self_time', 'sum_self_time',
                 'min_inclusive_time', 'max_inclusive_time', 'sum_inclusive_time')
    
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

    def __str__(self):
        return str({
            'fn': self.fn,
            'fl': self.fl,
            'subcalls': self.subcalls,
            'call_count': self.call_count,
            'min_self_time': self.min_self_time,
            'max_self_time': self.max_self_time,
            'sum_self_time': self.sum_self_time,
            'min_inclusive_time': self.min_inclusive_time,
            'max_inclusive_time': self.max_inclusive_time,
            'sum_inclusive_time': self.sum_inclusive_time,
        })


class CallTree:

    def __init__(self):
        self.max_self_time = 0
        self.max_call_count = 0
        self.total_call_count = 0
        self.root_node = AggregatedCall(None, None)
    
    def get_max_self_time(self): return self.max_self_time
    def get_total_time(self): return self.root_node.sum_inclusive_time
    def get_max_call_count(self): return self.max_call_count
    def get_total_call_count(self): return self.total_call_count
    
    def merge(self, tree):
        # update tree statistics
        self.max_call_count = max(self.max_call_count, tree.max_call_count)
        self.max_self_time = max(self.max_self_time, tree.max_self_time)
        self.total_call_count += tree.total_call_count
        
        # merge foreign root node to self root node
        self.root_node.merge(tree.root_node)
        
        # merge foreigh root node's subcalls
        self.root_node.subcalls += tree.root_node.subcalls
    
    def filter_inclusive_time(self, threshold):
        CallTreeFilter().filter_inclusive_time(self, threshold)
    
    def __str__(self):
        return str({
            'max_self_time': self.max_self_time,
            'max_call_count': self.max_call_count,
            'total_call_count': self.total_call_count,
        })

class XdebugCachegrindTreeBuilder:
    """A tree builder class.
    
    It accepts a parser, uses it to fetch cachegrind's raw structure and
    composes a tree from it.
    """
    
    def __init__(self, parser):
        self.parser = parser

    def get_tree(self):
        body_obj = self.parser.get_body()
        body = body_obj.get_body()

        max_self_time = 0
        nodes = []
        stack = []
        root_node = AggregatedCall(None, None)
        stack.append([0, -1])
        nodes.append(root_node)
        for entry in reversed(body):
            inclusive_time = entry.self_time + sum([x.inclusive_time for x in entry.get_subcalls()])
            
            # update tree-wide max_self_time
            max_self_time = max(max_self_time, entry.self_time)

            node = AggregatedCall(entry.fl, entry.fn);
            node.add_call(entry.fl, entry.fn, entry.self_time, inclusive_time)

            node_id = len(nodes)
            nodes.append(node)

            parent_id, parent_expected_calls = stack[-1]
            parent = nodes[parent_id]

            # add node to it's parent
            # at the moment they are in the reverse order
            parent.subcalls.append(node)

            expected_calls = len(entry.get_subcalls())

            # fill stack
            stack.append((node_id, expected_calls))

            # clean up stack
            j = len(stack) - 1
            while len(nodes[stack[j][0]].subcalls) == stack[j][1]:
                # fix reverse order in filled nodes
                nodes[stack[j][0]].subcalls.reverse()
        
                del stack[j]
                j -= 1

        # reverse the root_node's subcalls separately
        root_node.subcalls.reverse()
        
        # calculate inclusive_time for the root_node separately
        inclusive_time = sum([x.sum_inclusive_time for x in root_node.subcalls])
        root_node.add_call(None, None, 0, inclusive_time)

        tree = CallTree()
        tree.total_call_count = len(body)
        tree.max_call_count = 1
        tree.max_self_time = max_self_time
        tree.root_node = root_node
        return tree


class CallTreeFilter:

    def filter_depth(self, tree, depth):
        stack = [tree.root_node]
        stack_pos = [-1, 0]

        while stack:
            stack.append(stack[-1].subcalls[stack_pos[-1]])
            stack_pos[-1] += 1
            stack_pos.append(0)
            
            if len(stack) == depth:
                stack[-1].subcalls = []
                
            # cleanup stack
            while stack and len(stack[-1].subcalls) == stack_pos[-1]:
                del stack[-1], stack_pos[-1]

    def filter_inclusive_time(self, tree, percent_threshold):
        stack = [tree.root_node]
        stack_pos = [-1, 0]

        while stack:
            parent = stack[-1]
            call = parent.subcalls[stack_pos[-1]]
            if call.sum_inclusive_time > tree.get_total_time() * percent_threshold / 100:
                stack.append(call)
                stack_pos[-1] += 1
                stack_pos.append(0)
            else:
                parent.subcalls[stack_pos[-1]:stack_pos[-1]+1] = []
                
            # cleanup stack
            while stack and len(stack[-1].subcalls) == stack_pos[-1]:
                del stack[-1], stack_pos[-1]
        

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
        
        while stack:
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
            while stack and len(stack[-1].subcalls) == stack_pos[-1]:
                del stack[-1], stack_pos[-1], stack_path[-2:]
                
        new_tree = CallTree()
        new_tree.root_node = new_root_node
        new_tree.max_self_time = max_self_time
        new_tree.total_call_count = tree.total_call_count
        new_tree.max_call_count = max_call_count
        return new_tree
