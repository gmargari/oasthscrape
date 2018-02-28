#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
from datetime import datetime, timedelta
import calendar
import bisect
from pprint import pprint

bus_from_timetable = None
bus_from_arrival = None

#==============================================================================
# main ()
#==============================================================================
def main():
    if len(sys.argv) != 3:
        print('Syntax: %s <arrivals file> <timetables file>' % sys.argv[0])
        sys.exit(1)

    arrival_times_filename = sys.argv[1]
    timetables_filename = sys.argv[2]

    timetable = load_timetable(timetables_filename)
    bus_start_times = load_arrival_times(arrival_times_filename)
    compare_bus_start_times_and_timetable(bus_start_times, timetable)

#==============================================================================
# load_timetable ()
#==============================================================================
def load_timetable(timetables_filename):
    global bus_from_timetable
    global bus_from_arrival

    with open(timetables_filename) as f:
        daytype_timetable = {}
        for line in [ l.strip() for l in f.readlines() ]:

            # Comment line
            if line.startswith('#'):
                values = [ v.strip() for v in line.split() ]
                if values[1] == 'Filetype:':
                    filetype = values[2]
                    assert filetype == 'timetables'
                elif values[1] == 'Bus:':
                    bus_from_timetable = values[2]
                else:
                    raise ValueError('Invalid option %s' % values[1])

            # Timetable line
            elif len(line):
                values = [ v.strip() for v in line.split(',') ]
                daytype = values[0]
                times = values[1:]
                times_hh_mm = map(lambda x: x.split(':'), times)
                times_minutes = []
                for hh_mm in times_hh_mm:
                    # An hh_mm may be of the form "14:05(02A)"
                    if len(hh_mm[1]) > 2:
                        print('Warning: ignoring time "%s"' % ':'.join(hh_mm))
                    else:
                        hh = int(hh_mm[0])
                        mm = int(hh_mm[1])
                        times_minutes.append(hh*60 + mm)

                daytype_timetable[daytype] = times_minutes

        assert bus_from_timetable != None
        if bus_from_arrival != None and bus_from_arrival != bus_from_timetable:
            print('Error: Arrivals bus: %s, timetable bus: %s' % (bus_from_arrival, bus_from_timetable))
            sys.exit(1)

        return daytype_timetable

#==============================================================================
# load_arrival_times ()
#==============================================================================
def load_arrival_times(arrivals_filename):
    global bus_from_timetable
    global bus_from_arrival

    with open(arrivals_filename) as f:
        bus_start_times = []
        prev_timestamp = 0
        vehicles = []
        prev_vehicles = []
        for line in [ l.strip() for l in f.readlines() ]:

            # Comment line
            if line.startswith('#'):
                values = [ v.strip() for v in line.split() ]
                if values[1] == 'Filetype:':
                    filetype = values[2]
                    assert filetype == 'bus_arrivals' or filetype == 'buses_arrivals'
                elif values[1] == 'Bus:':
                    bus_from_arrival = values[2]
                elif values[1] == 'Stop:':
                    stop = values[2]
                else:
                    raise ValueError('Invalid option %s' % values[1])

            # Timetable line
            elif len(line):
                if filetype == 'bus_arrivals':
                    values = line.split(',')
                    timestamp = int(values[0])
                    vehicle = values[1]
                    arrival_time = int(values[2])

                    date = datetime.utcfromtimestamp(timestamp)
                    local_date = utc_to_local(date)
                    vehicles.append(vehicle)

                    if prev_timestamp and timestamp != prev_timestamp:
                        for vehicle in vehicles:
                            if prev_vehicles and vehicle not in prev_vehicles:
                                bus_start_times.append([local_date, vehicle])

                        prev_vehicles = vehicles
                        vehicles = []

                    prev_timestamp = timestamp
                else:
                    raise ValueError('Filetype %s not supported yet' % filetype)

        assert bus_from_arrival != None
        if bus_from_timetable != None and bus_from_arrival != bus_from_timetable:
            print('Error: Arrivals bus: %s, timetable bus: %s' % (bus_from_arrival, bus_from_timetable))
            sys.exit(1)

        return bus_start_times

#==============================================================================
# compare_bus_start_times_and_timetable ()
#==============================================================================
def compare_bus_start_times_and_timetable(bus_start_times, timetable):

    # TODO: take care of timebale times that wrap around e.g. 78N
    # that continues after 00:00 so is not sorted

    # TODO: dynamically select day type based on date below
    daytype = 'ΚΑΘΗΜΕΡΙΝΗ'
    day_timetable = timetable[daytype]
    #print(len(day_timetable))
    #sys.exit(0)

    for [date, vehicle] in bus_start_times:
        hour = date.hour
        minute = date.minute
        second = date.second

        minute_of_day = hour*60 + minute
        closest_time = closest_time_from_timetable(day_timetable, minute_of_day)

        #print("%s %s" % (date.strftime('%d-%m-%Y %H:%M:%S'), vehicle))
        print("(%s) %02d:%02d:%02d - %02d:%02d (+%d)" % \
          (vehicle, hour, minute, second, \
          closest_time/60, closest_time%60,
          minute_of_day - closest_time))

#==============================================================================
# closest_time_from_timetable ()
#==============================================================================
def closest_time_from_timetable(timetable, minute_of_day):
    return timetable[bisect.bisect(timetable, minute_of_day) - 1]

#==============================================================================
# utc_to_local ()
#==============================================================================
def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)

if __name__ == "__main__":
    main()
