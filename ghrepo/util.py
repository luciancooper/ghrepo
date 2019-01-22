#!/usr/bin/env python
import pydecorator

def format_isotime(d):
    year,month,day,hour,minute = d[:4],d[5:7],d[8:10],d[11:13],d[14:16]
    # second = d[17:19]
    return "{}-{}-{}_{}-{}".format(year,month,day,hour,minute)


def _isotime_time(d):
    return "{}.{}.{}".format(d[11:13],d[14:16],d[17:19])

def _isotime_date(d):
    return "{}-{}-{}".format(d[:4],d[5:7],d[8:10])


def _normalize_message(message):
    message = message.split("\n")[0]
    return message.replace(":","-").replace("/","-")

def _format_commit_extract(code,commit):
    if code == "r":
        return commit['repo']
    if code == "d":
        return _isotime_date(commit['date'])
    if code == "t":
        return _isotime_time(commit['date'])
    if code == "h":
        # Short Hash
        return commit['hash'][:8]
    if code == "H":
        # Long Hash
        return commit['hash']
    if code == "M":
        return _normalize_message(commit['message'])
    raise IndexError("Unrecognized Format Variable '{}'".format(code))
    
@pydecorator.str
def format_commit_str(commit,fmt):
    i = 0
    try:
        j = fmt.index("%",i)
        while True:
            if j > i:
                yield fmt[i:j]
            yield _format_commit_extract(fmt[j+1],commit)
            i = j+2
            j = fmt.index("%",i)
    except ValueError:
        j = len(fmt)
    finally:
        if j > i:
            yield fmt[i:j]