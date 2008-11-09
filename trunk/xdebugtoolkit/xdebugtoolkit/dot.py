class DotBuilder:

    def get_dot(self, tree, node_styler_class):
        node_styler = node_styler_class(tree.get_max_self_time(),
            tree.get_total_time(), tree.get_max_call_count(),
            tree.get_total_call_count())
        fn_rev = tree.fn_map.rev()
        for i in fn_rev:
            if fn_rev[i].startswith('php::'):
                fn_rev[i] = fn_rev[i][5:]
            if fn_rev[i].startswith('require::'):
                fn_rev[i] = fn_rev[i][9:]
            if fn_rev[i].startswith('require_once::'):
                fn_rev[i] = fn_rev[i][14:]
            if fn_rev[i].startswith('include::'):
                fn_rev[i] = fn_rev[i][9:]
            if fn_rev[i].startswith('include_once::'):
                fn_rev[i] = fn_rev[i][14:]
            if len(fn_rev[i]) > 30:
                fn_rev[i] = fn_rev[i][0:12] + '...' + fn_rev[i][-15:]
        graph = []
        
        graph.append('digraph G { \n')
        #graph.append('ordering=out; \n') # dot fails if rankdir=LR and ordering=out
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
            color = "#%02x%02x%02x" % node_styler.colorize(stack[-1])
            if stack[-1].call_count == 1:
                graph.append('"%s" [label="%s\\n%sms" color="%s"]; \n' % (self_id, fn_rev[stack[-1].fn], stack[-1].sum_self_time/1000, color))
                graph.append('"%s" -> "%s" [label="%sms"]; \n' % (parent_id, self_id, stack[-1].sum_inclusive_time/1000))
            else:
                graph.append('"%s" [label="%s\\n%sx\[%sms..%sms] = %sms" color="%s"]; \n' % (self_id, fn_rev[stack[-1].fn], stack[-1].call_count, stack[-1].min_self_time/1000, stack[-1].max_self_time/1000, stack[-1].sum_self_time/1000, color))
                graph.append('"%s" -> "%s" [label="%sx\[%sms..%sms] = %sms"]; \n' % (parent_id, self_id, stack[-1].call_count, stack[-1].min_inclusive_time/1000, stack[-1].max_inclusive_time/1000, stack[-1].sum_inclusive_time/1000))

            # cleanup stack
            while len(stack) and len(stack[-1].subcalls) == stack_pos[-1]:
                del(stack[-1])
                del(stack_pos[-1])

        graph.append("} \n")

        return "".join(graph)
