from mx.TextTools import *

header_table = (
    # version
    (None, Word, 'version: ', MatchFail),
    ('version', AllNotIn, newline, MatchFail),
    (None, AllIn, newline, MatchFail),
    # cmd
    (None, Word, 'cmd: ', MatchFail),
    ('cmd', AllNotIn, newline, MatchFail),
    (None, AllIn, newline, MatchFail),
    # part
    (None, Word, 'part: ', MatchFail),
    ('part', AllNotIn, newline, MatchFail),
    (None, AllIn, newline, MatchFail),
    # events
    (None, Word, 'events: ', MatchFail),
    ('events', AllNotIn, newline, MatchFail),
    (None, AllIn, newline, MatchFail),
)

subcall_table = (
    # cfn
    (None, Word, 'cfn=', MatchFail),
    ('fl', AllNotIn, newline, MatchFail),
    (None, AllIn, newline, MatchFail),
    # calls
    (None, Word, 'calls=1 0 0', MatchFail),
    (None, AllIn, newline, MatchFail),
    # position
    ('position', AllIn, number, MatchFail),
    (None, AllIn, ' ', MatchFail),
    # time
    ('time', AllIn, number, MatchFail),
    (None, AllIn, newline, MatchFail),
)

entry_table = (
    # fl
    (None, Word, 'fl=', MatchFail),
    ('fl', AllNotIn, newline, MatchFail),
    (None, AllIn, newline, MatchFail),
    # fn
    (None, Word, 'fn=', MatchFail),
    ('fn', AllNotIn, newline, MatchFail),
    (None, AllIn, newline, MatchFail),
    # summary
    (None, Word, 'summary: ', +3),
    ('summary', AllNotIn, newline, MatchFail),
    (None, AllIn, newline, MatchFail),
    # position
    ('position', AllIn, number, MatchFail),
    (None, AllIn, ' ', MatchFail),
    # time
    ('time', AllIn, number, MatchFail),
    (None, AllIn, newline, MatchFail),
    # subcalls
    (None, Word, 'cfn=', MatchOk),
    (None, Skip, -len('cfn=')),
    ('subcalls', Table, subcall_table, MatchFail, -2),
)

cg_table = (
    # header
    ('header', Table, header_table, MatchFail),
    # body
    (None, Word, 'fl=', MatchOk),
    (None, Skip, -len('fl=')),
    ('entry', Table, entry_table, MatchFail, -2),
)

if __name__ == '__main__':
    import sys
    import time
    
    contents = open(sys.argv[1]).read()
    timer = time.time()
    result, taglist, nextindex = tag(contents, cg_table)
    print time.time() - timer
    #print_tags(text,taglist)
