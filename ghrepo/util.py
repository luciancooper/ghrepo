#!/usr/bin/env python
import pydecorator,os

def iter_reduce(iterable,init=None):
    it = iter(iterable)
    try:
        v0 = next(it) if init is None else init
    except StopIteration:
        return
    for v1 in it:
        yield v0,v1
        v0 = v1


def splitpath(path):
    """Splits a path into all its components"""
    p0,p1,p = (*os.path.split(path),tuple())
    while p1!='':
        p0,p1,p = (*os.path.split(p0),(p1,) + p)
    return p

# ================================ [iso-time] ================================ #

def iso_date(iso):
    return "{}-{}-{}".format(iso[:4],iso[5:7],iso[8:10])

def iso_time(iso):
    return "{}:{}:{}".format(iso[11:13],iso[14:16],iso[17:19])

def cmp_iso(a,b):
    """ Compares two iso8601 format dates. returns [0 : a = b], [-1 : a < b], [1 : a > b] """
    y0,y1 = int(a[:4]),int(b[:4])
    if y0 != y1: return -1 if y0 < y1 else 1
    m0,m1 = int(a[5:7]),int(b[5:7])
    if m0 != m1: return -1 if m0 < m1 else 1
    d0,d1 = int(a[8:10]),int(b[8:10])
    if d0 != d1: return -1 if d0 < d1 else 1
    H0,H1 = int(a[11:13]),int(b[11:13])
    if H0 != H1: return -1 if H0 < H1 else 1
    M0,M1 = int(a[14:16]),int(b[14:16])
    if M0 != M1: return -1 if M0 < M1 else 1
    S0,S1 = int(a[17:19]),int(b[17:19])
    return 1 if S0 > S1 else -1 if S0 < S1 else 0

# ================================ [ls-display] ================================ #

def ls_commit_format_code(code,commit):
    # Repo
    if code == "r": return commit['repo']
    # Date
    if code == "d": return iso_date(commit['date'])
    # Time
    if code == "t": return iso_time(commit['date'])
    # Short Hash
    if code == "h": return commit['hash'][:8]
    # Long Hash
    if code == "H": return commit['hash']
    # First line of message
    if code == "m": return commit['message'].split("\n")[0]
    # Full Message Indented
    if code == "M": return '\n'.join('\t'+x for x in commit['message'].split('\n'))
    raise IndexError("Unrecognized Format Variable '{}'".format(code))

@pydecorator.str
def ls_commit_format(commit,fmt):
    """Returns a string to display"""
    i = 0
    try:
        j = fmt.index("%",i)
        while True:
            if j > i:
                yield fmt[i:j]
            yield ls_commit_format_code(fmt[j+1],commit)
            i = j+2
            j = fmt.index("%",i)
    except ValueError:
        j = len(fmt)
    finally:
        if j > i:
            yield fmt[i:j]


# ================================ [get-filename] ================================ #

def get_commit_format_code(code,commit):
    if code == "r": return commit['repo']
    if code == "d": return iso_date(commit['date'])
    if code == "t": return iso_time(commit['date']).replace(':','.')
    # Short Hash
    if code == "h": return commit['hash'][:8]
    # Long Hash
    if code == "H": return commit['hash']
    if code == "m":
        # normalize message (make it an acceptable file path)
        # TODO - Make platform depenedant
        message = commit['message'].split("\n")[0]
        return message.replace(":","-").replace("/","-")
    raise IndexError("Unrecognized Format Variable '{}'".format(code))

@pydecorator.str
def get_commit_format(commit,fmt):
    """Returns a string usable as a filename"""
    i = 0
    try:
        j = fmt.index("%",i)
        while True:
            if j > i:
                yield fmt[i:j]
            yield get_commit_format_code(fmt[j+1],commit)
            i = j+2
            j = fmt.index("%",i)
    except ValueError:
        j = len(fmt)
    finally:
        if j > i:
            yield fmt[i:j]






# ============================================ cli ============================================ #

# :---------:------:------:------------:----------:
# | Color   | Text |  BG  | BrightText | BrightBG |
# :---------:------:------:------------:----------:
# | Black   |  30  |  40  |    30;1    |   40;1   |
# | Red     |  31  |  41  |    31;1    |   41;1   |
# | Green   |  32  |  42  |    32;1    |   42;1   |
# | Yellow  |  33  |  43  |    33;1    |   43;1   |
# | Blue    |  34  |  44  |    34;1    |   44;1   |
# | Magenta |  35  |  45  |    35;1    |   45;1   |
# | Cyan    |  36  |  46  |    36;1    |   46;1   |
# | White   |  37  |  47  |    37;1    |   47;1   |
# :---------:------:------:------------:----------:

def cli_color(text,*colors):
    return "{}{}\x1b[0m".format("".join("\x1b[{}m".format(c) for c in colors),text)

def cli_warning(message):
    print("\x1b[31mWarning: {}\x1b[0m".format(message),file=sys.stderr)
