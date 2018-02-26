#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
from datetime import datetime, timedelta
import calendar

def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)

if len(sys.argv) != 4:
    print('Syntax: %s <arrivals file> <timetables file> <day type>' % sys.argv[0])
    sys.exit(1)

arrivals_filename = sys.argv[1]
timetables_filename = sys.argv[2]
day_type = sys.argv[3]

with open(timetables_filename) as timetables_f:
    lines = [ l.strip() for l in timetables_f.readlines() ]
    for line in lines:
        values = line.split()
        if values[0] == day_type:
            times = values[1:]
            times_hh_mm = map(lambda x: x.split(":"), times)
            times_minutes = map(lambda hh_mm: int(hh_mm[0])*60 + int(hh_mm[1]), times_hh_mm)
            mapped = zip(times, times_minutes)
#            print("%s" % '\n'.join([ "%s => %s" % (m[0], m[1]) for m in mapped ]))

#sys.exit(0)

prev_timestamp = 0
vehicles = []
prev_vehicles = []
with open(arrivals_filename) as arrivals_f:
    lines = [ l.strip() for l in arrivals_f.readlines() ]
    for line in lines:
        values = line.split(',')
        timestamp = int(values[0])
        line_number = values[1]
        vehicle_number = values[2]
        arrival_time = int(values[3])

        date = datetime.utcfromtimestamp(timestamp)
        local_date = utc_to_local(date)

        vehicles.append((line_number, vehicle_number))

        if prev_timestamp and timestamp != prev_timestamp:
            new_vehicles = []
            for v in vehicles:
                if v not in prev_vehicles:
                    new_vehicles.append(v)

            prev_vehicles = list(vehicles)
            vehicles = []

            if new_vehicles:
                print('')
                print('New vehicles:')
                for v in new_vehicles:
                    print("\t%3s - %s" % (v[0], v[1]))


            print('-----------------------')

        print(local_date.strftime('%d-%m-%Y %H:%M:%S'), end='')
        print("   %3s (%s) %d'" % (line_number, vehicle_number, arrival_time))

        prev_timestamp = timestamp
