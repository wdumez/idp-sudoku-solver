# idp_parse_out


def parse_element(s):
    s = s.strip()
    try:
        return int(s)
    except ValueError:
        unquoted = s.strip("'").strip('"')
        return unquoted

def parse_tuple(tup):
    tup = tup.strip()
    elements = tup.split(',')
    parsed = list(map(parse_element, elements))
    if len(parsed) == 1:
        return parsed[0]
    return tuple(parsed)

def parse_function_tuple(s):
    s = s.strip()
    from_, to = s.split('->')
    return parse_tuple(from_), parse_element(to)

def parse_enumerated(s):
    if '->' in s:
        return parse_function_tuple(s)
    return parse_tuple(s)

def parse_enumeration(s):
    s = s.strip()
    elements = s.split(';')
    parsed = list(map(parse_enumerated, elements))
    if "->" in s: # Function
        return dict(parsed)
    else: # Predicate
        return parsed

def parse_range(s):
    s = s.strip()
    low, up = s.split('..')
    return list(range(int(low),int(up)))

def parse_contents(s):
    stripped = s.strip().lstrip('{').rstrip('}').strip()
    if '..' in stripped:
        return parse_range(stripped)
    return parse_enumeration(stripped)

def parse_assignment(s,wanted):
    name, contents = s.split('=')
    name = name.strip()
    if name in wanted:
        return name, parse_contents(contents)
    else:
        return None, None

def idp_parse(s,wanted):
    lines = s.splitlines()
    first_line = True
    res = {}
    for line in lines:
        line = line.strip()
        if __debug__:
            print(line)
        if first_line:
            first_line = False
            continue
        if line == "" or line.rstrip('}') == "" or "structure" in line:
            continue
        symb, content = parse_assignment(line,wanted)
        if symb:
            res[symb] = content
    return res
