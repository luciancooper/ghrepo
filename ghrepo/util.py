#!/usr/bin/env python


def format_isotime(d):
    year,month,day,hour,minute = d[:4],d[5:7],d[8:10],d[11:13],d[14:16]
    # second = d[17:19]
    return "{}-{}-{}_{}-{}".format(year,month,day,hour,minute)

