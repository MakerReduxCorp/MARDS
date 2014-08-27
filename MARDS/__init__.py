# MARDS\__init__.py
#
# MARDS data serialization library
#
# Version 0.1.0

from rolne import rolne

import mards_library as ml

def MARDS_to_rolne(doc=None, schema=None, context="doc", tab_strict=False):
    result = rolne()
    error_list = []
    if doc is None:
        return result, error_list
    if schema:
        schema, schema_errors = MARDS_to_rolne(schema, context="schema")
        error_list.extend(schema_errors)
    current = 0
    tab_list = [0]
    pointer_list = range(50)
    pointer_list[0]=result
    last_spot = pointer_list[0]
    #line_tracker = []
    last_nvi = range(50)
    for ctr, line in enumerate(doc.split("\n")):
        #line_tracker.append([])
        (indent, key, value, error) = ml.parse_line(line, tab_list, tab_strict=tab_strict)
        if error:
            t = (context, ctr, error)
            error_list.append(t)
        else:
            if key:
                if indent<current:
                    current = indent
                elif indent==current:
                    pass # do nothing, the operational default works
                elif indent==(current+1):
                    pointer_list[indent] = last_spot
                    current = indent
                else:
                    t = (context, ctr, "tab stop jumped ahead too far")
                    error_list.append(t)
                index = pointer_list[indent].append_index(key, value, seq=str(ctr))
                last_spot = pointer_list[indent][key, value, index]
                last_nvi[indent]=(key, value, index)
                #for r in range(indent+1):
                #    line_tracker[ctr].append(last_nvi[r])
    if schema:
        result, schema_errors = ml.schema_rolne_check(result, schema)
        error_list.extend(schema_errors)
    return result, error_list

# TODO: sit down and figure out loop detection
def _SCHEMA_to_rolne(doc=None):
    schema, error_list = MARDS_to_rolne(doc, context="schema", tab_strict=True)
    copy = schema.copy(seq_prefix="", seq_suffix="")
    # build a list of names from the document and their corresponding locations
    # mark as False if the key is seen twice
    name_seq = {}
    name_recurs = {}
    for key in schema.flattened_list( (), name=True, value=True, seq=True):
        (en, ev, es) = key
        if en=="name":
            if ev in name_seq:
                name_seq[ev]=False
            else:
                name_seq[ev]=es
        elif en in ["treatment", "value", "insert", "required", "default", "ordered", "type", "recurse"]:
            pass
        else:
            t = ("schema", es, "'{}' not a recognized schema element name".format(en))
            error_list.append(t)
            schema.seq_delete(es)
    #schema_list = schema.flattened_list(("insert"), value=True, seq=True)
    #while schema_list:
    #    for (ev, es) in schema_list:
    #        if ev in name_seq:
    #            if name_seq[ev] is False:
    #                t = ("schema", es, "'name {}' found in schema multiple times".format(ev))
    #                error_list.append(t)
    #                schema.seq_delete(es)
    #            else:
    #                prefix = es+"_"
    #                src = name_seq[ev]
    #                schema.seq_replace(es, src, prefix)
    #                #name_recurs[src].append(prefix)
    #        else:
    #            t = ("schema", es, "'name {}' not found in schema".format(ev))
    #            error_list.append(t)
    #            schema.seq_delete(es)
    #    schema_list = schema.flattened_list(("insert"), value=True, seq=True)
    schema_list = schema.flattened_list(("recurse"), value=True, seq=True)
    safety_ctr=0
    while schema_list and safety_ctr<2:
        for (ev, es) in schema_list:
            if ev in name_seq:
                if name_seq[ev] is False:
                    t = ("schema", es, "'name {}' found in schema multiple times".format(ev))
                    error_list.append(t)
                    schema.seq_delete(es)
                else:
                    src = name_seq[ev]
                    #prefix = "r_"+es+"_"+src+"_"
                    prefix = "r_"+src+".1_" # TODO: make the .1 a real counter
                    line = schema.seq_lineage(es)
                    if name_seq[ev] in line:
                        schema.seq_replace(es, copy.ptr_to_seq(src), prefix)
                        print "jr",line
                    else:
                        error_list.append(("schema", es, "'recurse {}' is not recursive".format(ev)))
                        schema.seq_delete(es)
            else:
                t = ("schema", es, "'name {}' not found in schema".format(ev))
                error_list.append(t)
                schema.seq_delete(es)
        schema_list = schema.flattened_list(("recurse"), value=True, seq=True)
        safety_ctr += 1
    return schema, error_list


def MARDS_to_python(doc=None, schema=None, context="doc", tab_strict=False):
    r, error_list = MARDS_to_rolne(doc, schema, context=context, tab_strict=tab_strict)
    if schema:
        schema, schema_errors = MARDS_to_rolne(schema, context="schema")
        error_list.extend(schema_errors)
        result = ml.sub_convert_python(r, schema)
    else:
        result = r.dump()
    return result, error_list


def rolne_to_MARDS(r, tab_size=4, quote_all=True):
    result = ""
    #print r.data
    if r:
        for (rn, rv, rl) in r.data:
            result += rn
            if rv is not None:
                printable = str(rv)
                quote_flag = False
                if '"' in printable:
                    quote_flag = True
                if len(printable) != len(printable.strip()):
                    quote_flag = True
                if quote_flag or quote_all:
                    result += " "+'"'+rv+'"'
                else:
                    result += " "+rv
            result += "\n"
            if rl:
                temp = rolne_to_string(rolne(in_list=rl), tab_size=tab_size, quote_all=quote_all)
                for line in temp.split("\n"):
                    if line:
                        result += " "*tab_size+line
                        result += "\n"
    return result

if __name__ == "__main__":

    if True:

        my_doc = '''
item zing
    size 4
    color red
        intensity 44%
    color yellow
    size 2
item womp
    size 5
    color blue
item bam
item bam
item broom
    size 7
    title "The "big" thing"
zoom_flag
code_seq a
    * r9
    * r3
    * r2
    * r3
code_seq b
    * a
    * b
    * c
    * d
system_title hello
zoom_flag False'''

        schema = '''
ordered False
name blink
    value
        type label
        required
    name rate
    insert item
name item
    treatment unique
    value
        type label
        required
    name size
        treatment one
    name color
        treatment unique
        name intensity
    name title
        required
        treatment concat
        value
            default "unknown"
name zoom_flag
    treatment one
    value
        required
        default True
    name color
name boing
    required
    value
        required
        default joejoe
    recurse boing
name code_seq
    value
        ordered False
    ordered False
    treatment sum
    name *
name system_title
'''

        #print my_doc
        print schema
        x,e = _SCHEMA_to_rolne(schema)
        #x,e = MARDS_to_rolne(my_doc, schema, tab_strict=True)
        #y,e = MARDS_to_rolne(my_doc, schema, tab_strict=True)
        #x,e = MARDS_to_python(my_doc, schema)
        #for ctr, line in enumerate(my_doc.split("\n")):
        #    print ctr, line
        print "FINAL:\n"
        print x._explicit()
        print "ERRORS:\n"
        print repr(e)

    else:
        print "==================================="
        print
        import doctest
        print "Testing begins. Errors found:"
