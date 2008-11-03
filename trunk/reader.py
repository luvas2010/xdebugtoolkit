import sys
import pydot


class RawEntry:

    def __init__(self):
        self.fn = None
        self.fl = None
        self.self_time = None
        self.subcalls = []
        self.summary = None


class RawCall:

    def __init__(self):
        self.cfn = None
        self.position = None
        self.inclusive_time = None


class Call:

    def __init__(self):
        self.fn = None
        self.fl = None
        self.subcalls = []
        self.call_count = 1
        self.self_time = None
        self.inclusive_time = None


class CallTree:

    def __init__(self):
        self.fl_map = None
        self.fl_rev = None
        self.fn_map = None
        self.fn_rev = None
        self.root_node = Call()
        
    def to_string(self):
        ret = []
        
        stack = [self.root_node]
        stack_pos = [0]

        ret.append('  ' * (len(stack) - 1) + '/') 

        while len(stack):
            
            stack.append(stack[-1].subcalls[stack_pos[-1]])
            stack_pos[-1] += 1
            stack_pos.append(0)
            
            ret.append('  ' * (len(stack) - 1) + str(stack[-1].call_count) + ' x ' + self.fn_rev[stack[-1].fn])
                
            # cleanup stack
            while len(stack) and len(stack[-1].subcalls) == stack_pos[-1]:
                del(stack[-1])
                del(stack_pos[-1])
        
        return "\n".join(ret)


class XdebugCachegrindFsaParser:
    """
    A low-level lexer
    """

    # header states
    # -2 got eof or fl, finish parsing
    # -1 error, finish parsing
    # 0 start
    # 1 got version, expecting cmd
    # 2 got cmd, expecting part
    # 3 gor part, expecting events
    # 4 got events, expecting fl or eof
    header_fsm = {
        #    0   1   2   3   4
        0: [ 1, -1, -1, -1, -1], # version
        1: [-1,  2, -1, -1, -1], # cmd
        2: [-1, -1,  3, -1, -1], # part
        3: [-1, -1, -1,  4, -1], # events
        4: [-1, -1, -1, -1, -2], # fl
        5: [-1, -1, -1, -1, -2], # eof
    }

    # body states:
    # -2 got eof, finish parsing
    # -1 error, finish parsing
    # 0 got header line, expectine more header lines or fl or eof
    # 1 got fl, expecting fn
    # 2 got fn, expecting num or summary
    # 3 got num, expecting fl or cfn or eof
    # 4 got cfn, expecting calls
    # 5 got calls, expecting subcall num
    # 6 got subcall num, expecting fl or cfn or eof
    # 7 got summary, expecting num
    body_fsm = {
        #    0   1   2   3   4   5   6   7
        0: [ 0, -1, -1, -1, -1, -1, -1, -1], # header
        1: [ 1, -1, -1,  1, -1, -1,  1, -1], # fl
        2: [-1,  2, -1, -1, -1, -1, -1, -1], # fn
        3: [-1, -1,  3, -1, -1,  6, -1,  3], # num
        4: [-1, -1, -1,  4, -1, -1,  4, -1], # cfn
        5: [-1, -1, -1, -1,  5, -1, -1, -1], # calls
        6: [-1, -1,  7, -1, -1, -1, -1, -1], # summary
        7: [-2, -1, -1, -2, -1, -1, -2, -1], # eof
    }

    def __init__(self, filename):
        self.fh = file(filename, 'rU')
        self.fl_map = {}
        self.fl_inc = 1
        self.fn_map = {}
        self.fn_inc = 1

    def get_header(self):
        self.fh.seek(0)

        state = 0;
        line_no = 0

        while True:
            token = None
            try:
                line = self.fh.next()
                line_no += 1
                if line == '\n':
                    continue
                if line == 'version: 0.9.6\n':
                    token = 0
                if line[0:5] == 'cmd: ':
                    token = 1
                if line == 'part: 1\n':
                    token = 2
                if line == 'events: Time\n':
                    token = 3
                if line[0:3] == 'fl=':
                    token = 4
            except StopIteration:
                token = 5

            try:
                state = self.header_fsm[token][state]
            except:
                state = -1

            if state == -2:
                break

            elif state == -1:
                raise Exception(line_no, line, token)

            elif state == 2:
                cmd = line[5:-1]

        return {
            'cmd': cmd,
        }

    def get_body(self):
        body = []

        self.get_header()

        self.fh.seek(0)

        state = 0;
        line_no = 0

        total_self = 0
        total_calls = 0

        while True:
            token = None
            line = None
            try:
                line = self.fh.next()
                line_no += 1
                if line == '\n':
                    continue
                elif line[0].isdigit():
                    token = 3
                elif line[0:3] == 'fl=':
                    token = 1
                elif line[0:3] == 'fn=':
                    token = 2
                elif line[0:4] == 'cfn=':
                    token = 4
                elif line[0:6] == 'calls=':
                    token = 5
                elif line[0:9] == 'summary: ':
                    token = 6
                elif state == 0:
                    token = 0
            except StopIteration:
                token = 7

            try:
                state = self.body_fsm[token][state]
            except KeyError:
                state = -1

            if state == 1:
                fl = line[3:-1]
                if fl not in self.fl_map:
                    self.fl_map[fl] = self.fl_inc
                    self.fl_inc += 1

                # re-init raw_entry
                raw_entry = RawEntry()
                body.append(raw_entry)

                raw_entry.fl = self.fl_map[fl]

            elif state == 2:
                fn = line[3:-1]
                if fn not in self.fn_map:
                    self.fn_map[fn] = self.fn_inc
                    self.fn_inc += 1

                raw_entry.fn = self.fn_map[fn]

            elif state == 3:
                position, time_taken = map(int, line.split(' '))
                total_self += time_taken
                if fn == '{main}':
                    total_calls += time_taken
                    total_self_before_summary = total_self

            elif state == 4:
                cfn = line[4:-1]
                if cfn not in self.fn_map:
                    self.fn_map[cfn] = self.fn_inc
                    self.fn_inc += 1

                # init raw_call
                raw_call = RawCall()
                raw_entry.subcalls.append(raw_call)

                raw_call.cfn = self.fn_map[cfn]

            elif state == 5:
                calls = line[6:-1]

            elif state == 6:
                position, time_taken = map(int, line.split(' '))
                if fn == '{main}':
                    total_calls += time_taken

                # set raw_call's time and position
                raw_call.position = position
                raw_call.inclusive_time = time_taken

            elif state == 7:
                summary = int(line[9:-1])

            elif state == -2:
                break

            elif state == -1:
                raise Exception(line_no, line, token)

        #print 'summary:    ', summary
        #print 'total_self: ', total_self_before_summary
        #print 'total_calls:', total_calls
        return body


class XdebugCachegrindTreeBuilder:
    """
    A tree builder class.
    """
    def __init__(self, parser):
        self.parser = parser

    def get_tree(self):
        body = self.parser.get_body()

        fl_map = self.parser.fl_map
        fl_rev = dict([(v, k) for k, v in fl_map.iteritems()])

        fn_map = self.parser.fn_map
        fn_rev = dict([(v, k) for k, v in fn_map.iteritems()])

        nodes = []
        stack = []
        root_node = Call()
        stack.append([0, -1])
        nodes.append(root_node)
        i = len(body)
        while i > 0:
            i -= 1
            node = Call()
            entry = body[i];
            node.fn = entry.fn
            node.fl = entry.fl
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

        root_node.subcalls.reverse()

        tree = CallTree()
        tree.fl_map = fl_map
        tree.fl_rev = fl_rev
        tree.fn_map = fn_map
        tree.fn_rev = fn_rev
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
        

class CallTreeAggregator:
    
    def __init__(self):
        pass
    
    def aggregateCallPaths(self, tree):
        path_map = {}
        
        stack = [tree.root_node]
        stack_pos = [0]
        stack_path = [-1]

        try:
            call = path_map[tuple(stack_path)]
        except KeyError:
            call = Call()
            call.fl = stack[-1].fl
            call.fn = stack[-1].fn
            path_map[tuple(stack_path)] = call
        
        while len(stack):
            stack.append(stack[-1].subcalls[stack_pos[-1]])
            stack_pos[-1] += 1
            stack_pos.append(0)
            
            stack_path.append(stack[-1].fn)
            
            try:
                call = path_map[tuple(stack_path)]
                call.call_count += 1
                
                # TODO: add times
                
            except KeyError:
                call = Call()
                call.fl = stack[-1].fl
                call.fn = stack[-1].fn
                
                # TODO: set times
                
                path_map[tuple(stack_path)] = call
                
                parent_call = path_map[tuple(stack_path[:-1])]
                
                parent_call.subcalls.append(call)
            
            # cleanup stack
            while len(stack) and len(stack[-1].subcalls) == stack_pos[-1]:
                del(stack[-1])
                del(stack_pos[-1])
                del(stack_path[-1])
                
        new_tree = CallTree()
        new_tree.fl_map = tree.fl_map
        new_tree.fl_rev = tree.fl_rev
        new_tree.fn_map = tree.fn_map
        new_tree.fn_rev = tree.fn_rev
        
        new_tree.root_node = path_map[(-1, )]
        return new_tree


# pydot is very slooooooow
#class DotBuilder:
#
#    def get_dot(self, tree):
#        graph = pydot.Dot(rankdir='TB', ordering='out', graph_type='digraph')
#        graph.set_edge_defaults(labelfontsize='12')
#        graph.set_node_defaults(shape='box', style='filled')
#
#        stack = [tree.root_node]
#        stack_pos = [-1, 0]
#        
#        self_id = '/'.join(map(str, stack_pos[0:-1]));
#        graph.add_node(pydot.Node(self_id))
#        
#        while len(stack):
#            stack.append(stack[-1].subcalls[stack_pos[-1]])
#            stack_pos[-1] += 1
#            stack_pos.append(0)
#            
#            parent_id = '/'.join(map(str, stack_pos[0:-2]));
#            self_id = '/'.join(map(str, stack_pos[0:-1]));
#            graph.add_node(pydot.Node(self_id, label='"' + tree.fn_rev[stack[-1].fn] + '"'))
#            graph.add_edge(pydot.Edge(parent_id, self_id, label=str(stack[-1].call_count) + 'x'))
#
#            # cleanup stack
#            while len(stack) and len(stack[-1].subcalls) == stack_pos[-1]:
#                del(stack[-1])
#                del(stack_pos[-1])
#
#        return graph.to_string()


class DotBuilder2:

    def get_dot(self, tree):
        graph = []
        
        graph.append('digraph G { \n')
        graph.append('ordering=out; \n')
        graph.append('rankdir=TB; \n')
        graph.append('edge [labelfontsize=12]; \n')
        graph.append('node [shape=box, style=filled]; \n')
        
        stack = [tree.root_node]
        stack_pos = [-1, 0]
        
        self_id = '/'.join(map(str, stack_pos[0:-1]));
        graph.append('"%s" \n' % (self_id, ))
        
        while len(stack):
            stack.append(stack[-1].subcalls[stack_pos[-1]])
            stack_pos[-1] += 1
            stack_pos.append(0)
            
            parent_id = '/'.join(map(str, stack_pos[0:-2]));
            self_id = '/'.join(map(str, stack_pos[0:-1]));
            graph.append('"%s" [label="%s"]; \n' % (self_id, tree.fn_rev[stack[-1].fn]))
            graph.append('"%s" -> "%s" [label="%s"]; \n' % (parent_id, self_id, str(stack[-1].call_count) + 'x'))

            # cleanup stack
            while len(stack) and len(stack[-1].subcalls) == stack_pos[-1]:
                del(stack[-1])
                del(stack_pos[-1])

        graph.append("} \n")

        return "".join(graph)


if __name__ == '__main__':
    parser = XdebugCachegrindFsaParser(sys.argv[1])
    tree = XdebugCachegrindTreeBuilder(parser).get_tree()
    CallTreeFilter().filter_depth(tree, 4)
    tree_aggregator = CallTreeAggregator()
    tree = CallTreeAggregator().aggregateCallPaths(tree)
    #print tree.to_string()
    print DotBuilder2().get_dot(tree)
