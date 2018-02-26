#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import time
import sys
import scrapy
import argparse
import random
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import codecs

DEFAULT_BUS_NAME = '10'
DEFAULT_BUS_STOP_NAME = 'ΠΛΑΤΕΙΑ ΑΡΙΣΤΟΤΕΛΟΥΣ'
SCRAPE_TYPES = ['buses_arrivals', 'bus_arrivals', 'timetables']

min_sec = 1
max_sec = 1

#==============================================================================
# replace_white_spaces_with_single_space ()
#==============================================================================
def replace_white_spaces_with_single_space(s):
    return ' '.join(s.split())

#==============================================================================
# flatten_list_of_lists ()
#==============================================================================
def flatten_list_of_lists(l):
    return [item for sublist in l for item in sublist]

#==============================================================================
# OasthArrivalsScraper ()
#==============================================================================
class OasthArrivalsScraper:

    #==========================================================================
    # __init__ ()
    #==========================================================================
    def __init__(self):
        self.timetables_option_name = 'Δρομολόγια Γραμμών'
        self.buses_arrival_times_option_name = 'Αφίξεις Γραμμών'
        self.bus_arrival_times_option_name = 'Άφίξη Γραμμής'
        self.printing_interval = 20

        # Initialized our headless browser
        #self.browser = webdriver.PhantomJS()
        #self.browser = webdriver.Firefox()
        self.browser = webdriver.Chrome()
        self.browser.get('http://m.oasth.gr')

        self.curdate = time.strftime('%Y.%m.%d_%H.%M.%S')
        self.output_file = None

    #==========================================================================
    # __del__ ()
    #==========================================================================
    def __del__(self):
        if self.output_file:
            self.output_file.close()
        if self.browser:
            self.browser.close()

    #==========================================================================
    # scrape_arrival_times ()
    #==========================================================================
    def scrape_arrival_times(self, operation, bus_name, bus_stop_name):
        self.operation = operation
        self.bus_name = bus_name
        self.bus_stop_name = bus_stop_name

        time.sleep(random.randint(min_sec, max_sec))
        if self.operation == 'buses_arrivals':
            self.menu_page_click_link(self.buses_arrival_times_option_name)
        elif self.operation == 'bus_arrivals':
            self.menu_page_click_link(self.bus_arrival_times_option_name)
        else:
            raise ValueError('Invalid option "%s"' % self.operation)

        self.bus_selection_page_click_bus(self.bus_name)

        self.arrivals_bus_page_click_stop(self.bus_stop_name)

#        if self.err_in_page():
#            print('No results in page. Please try again.')
#            sys.exit(1)

        while True:
            self.print_arrival_times(operation)
            time.sleep(self.printing_interval)

    #==========================================================================
    # open_output_file ()
    #==========================================================================
    def open_output_file(self):
        header = "# Filetype: %s\n" % self.operation
        if 'arrivals' in self.operation:
            filename = '%s-%s-%s-%s.txt' % (self.operation, self.bus_name.replace(' ','_'), self.bus_stop_name.replace(' ','_'), self.curdate)
            header += "# Bus: %s\n" % self.bus_name
            header += "# Stop: %s\n" % self.bus_stop
        elif self.operation == 'timetables':
            filename = '%s-%s.txt' % (self.operation, self.bus_name.replace(' ','_'))
            header += "# Bus: %s\n" % self.bus_name
        else:
            raise ValueError('Invalid option "%s"' % file_type)

        self.output_file = codecs.open(filename, 'w', 'utf-8')
        print(header, file=self.output_file, end='')
        print('Output file: %s' % (filename))

    #==========================================================================
    # menu_page_click_link ()
    #==========================================================================
    def menu_page_click_link(self, menu_option):
        self.click_option_by_class_and_name("slideup", menu_option)

    #==========================================================================
    # bus_selection_page_click_bus ()
    #==========================================================================
    def bus_selection_page_click_bus(self, bus_name):
        self.click_option_by_class_and_name("sp1", bus_name)

    #==========================================================================
    # arrivals_bus_page_click_stop ()
    #==========================================================================
    def arrivals_bus_page_click_stop(self, stop_name):
        option = self.click_option_by_class_and_name("spt", stop_name)

    #==========================================================================
    # timetable_day_type_page_click_type ()
    #==========================================================================
    def timetable_day_type_page_click_type(self, day_type):
        option = self.click_option_by_class_and_name("", day_type)

    #==========================================================================
    # click_option_by_class_and_name ()
    #==========================================================================
    def click_option_by_class_and_name(self, class_name, elem_name):
        if class_name:
            xpath = './/*[@class = "%s"]' % (class_name)
        else:
            xpath = './/*'

        elems = self.get_menu_options()
        for elem in elems:
            try:
                xpath_copy = xpath + '[contains(text(), "%s")]' % (elem_name)
                found_elem = elem.find_element_by_xpath(xpath_copy)
                if found_elem:
                    found_elem.click()
                    # Wait a bit for the link to load
                    time.sleep(random.randint(min_sec, max_sec))
                    return

            except (NoSuchElementException):
                continue

        print('No element "%s". Please check again the name is one of the following:' % (elem_name))
        for elem in elems:
            print(elem.find_element_by_xpath(xpath).text)
        sys.exit(1)

    #==========================================================================
    # get_menu_options ()
    #==========================================================================
    def get_menu_options(self):
        xpath  = '//div[@class = "cacher" and (not(@style) or not(contains(@style, "display: none")))]'
        xpath += '/div[@class = "holder"]'
        xpath += '/div[contains(@class, "menu")]'
        # select the first 'menu' div, e.g. in case of stop selection
        # there is the outward journey menu and return journey menu.
        xpath += '[1]'
        xpath += '/h3'

        elems = self.browser.find_elements_by_xpath(xpath)
        return elems

    #==========================================================================
    # print_arrival_times ()
    #==========================================================================
    def print_arrival_times(self, operation):
        if not self.output_file:
          self.open_output_file()

        tuples = []
        elems = self.get_menu_options()
        for elem in elems:
            try:
                s = replace_white_spaces_with_single_space(elem.text)
                tuple = self.split_based_on_operation(s, operation)
                tuples.append(tuple)
            except (StaleElementReferenceException):
                print('Stale element exception, will retry in next interval')
                time.sleep(random.randint(min_sec, max_sec))
                return

        timestamp = int(time.time())
        for tuple in tuples:
            print("%d,%s" % (timestamp, ','.join(tuple)), file=self.output_file)
            print(time.strftime('%d-%m-%Y %H:%M:%S : '), end='')
            print("%s" % ' - '.join(tuple))

        if len(tuples):
            print('')

        self.output_file.flush()

    #==========================================================================
    # split_based_on_operation ()
    #==========================================================================
    def split_based_on_operation(self, s, operation):
        if operation == 'buses_arrivals':
            # "12:ΚΤΕΛ-ΚΑΤΩ ΤΟΥΜΠΑ ΟΧΗΜΑ 0909 ΑΦΙΞΗ ΣΕ 3'" => ["12", "ΚΤΕΛ-ΚΑΤΩ ΤΟΥΜΠΑ", "0909", "3"]
            [line_no, rest] = [ v.strip() for v in s.split(':') ]
            [line_name, rest] = [ v.strip() for v in rest.split(u'ΟΧΗΜΑ') ]
            [vehicle_no, minutes] = [ v.strip(" '") for v in rest.split(u'ΑΦΙΞΗ ΣΕ') ]
            tuple = [line_no, line_name, vehicle_no, minutes]
        elif operation == 'bus_arrivals':
            # "0781 ΑΦΙΞΗ ΣΕ 6'" => ["0781", "6"]
            [vehicle_no, minutes] = [ v.strip(" '") for v in s.split(u'ΑΦΙΞΗ ΣΕ') ]
            tuple = [vehicle_no, minutes]
        else:
            raise ValueError('Invalid option %s' % operation)

        return tuple

    #==========================================================================
    # scrape_timetables ()
    #==========================================================================
    def scrape_timetables(self, operation, bus_name):
        self.operation = operation
        self.bus_name = bus_name

        self.menu_page_click_link(self.timetables_option_name)
        self.bus_selection_page_click_bus(self.bus_name)

        elems = self.get_menu_options()
        for day_type in [ e.text for e in elems ]:
            self.timetable_day_type_page_click_type(day_type)
            self.print_timetables(day_type)
            self.browser.back()

    #==========================================================================
    # print_timetables ()
    #==========================================================================
    def print_timetables(self, day_type):
        if not self.output_file:
          self.open_output_file()

        elems = self.get_menu_options()

        print('=== %s ===' % (day_type))
        print('%s ' % (day_type), file=self.output_file, end='')

        print('%s' % '\n'.join([ e.text for e in elems]))
        print('%s' % ' '.join([ e.text for e in elems]), file=self.output_file)

    #==========================================================================
    # err_in_page ()
    #==========================================================================
    def err_in_page(self):
        if len(self.browser.find_elements_by_xpath('//*[@class="err"]')) > 0:
            return True

        return False

#===============================================================================
# create_arg_parser ()
#===============================================================================
def create_arg_parser():
    formatter = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=100, width=200)
    parser = argparse.ArgumentParser(formatter_class=formatter)
    parser.add_argument('o', metavar='OPERATION', help='Options: %s' % ', '.join(SCRAPE_TYPES), choices=SCRAPE_TYPES, type=str)
    parser.add_argument('-b', '--bus_name', metavar='BUS_NAME', help="Bus name", default=DEFAULT_BUS_NAME, type=str)
    parser.add_argument('-s', '--bus_stop', metavar='BUS_STOP', help="Bus stop", default=DEFAULT_BUS_STOP_NAME, type=str)

    return parser

#===============================================================================
# main ()
#===============================================================================
def main():

    parser = create_arg_parser()
    if (len(sys.argv) == 1):
        parser.print_help()
        sys.exit(1)

    # Parse arguments
    args = parser.parse_args()
    operation = args.o
    if 'arrivals' in operation:
        bus_name = args.bus_name
        bus_stop = args.bus_stop
    elif operation == 'timetables':
        bus_name = args.bus_name

    # Scrape page
    scraper = OasthArrivalsScraper()
    if 'arrivals' in operation:
        scraper.scrape_arrival_times(operation, bus_name, bus_stop)
    elif operation == 'timetables':
        scraper.scrape_timetables(operation, bus_name)

if __name__ == "__main__":
    main()
