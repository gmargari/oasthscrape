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

DEFAULT_BUS_NAME = '10'
DEFAULT_BUS_STOP_NAME = 'ΠΛΑΤΕΙΑ ΑΡΙΣΤΟΤΕΛΟΥΣ'
SCRAPE_TYPES = ['arrivals', 'timetables']

min_sec = 1
max_sec = 1

#==============================================================================
# OasthArrivalsScraper ()
#==============================================================================
class OasthArrivalsScraper:

    #==========================================================================
    # __init__ ()
    #==========================================================================
    def __init__(self):
        self.arrival_times_option_name = 'Αφίξεις Γραμμών'
        self.timetables_option_name = 'Δρομολόγια Γραμμών'
        self.printing_interval = 20

        # Initialized our headless browser
        #self.browser = webdriver.PhantomJS()
        #self.browser = webdriver.Firefox()
        self.browser = webdriver.Chrome()
        self.browser.get('http://m.oasth.gr')

        self.curdate = time.strftime('%Y.%m.%d_%H.%M.%S')

    #==========================================================================
    # scrape_arrival_times ()
    #==========================================================================
    def scrape_arrival_times(self, bus_name, bus_stop_name):
        self.bus_name = bus_name
        self.bus_stop_name = bus_stop_name

        time.sleep(random.randint(min_sec, max_sec))
        self.menu_page_click_link(self.arrival_times_option_name)

        time.sleep(random.randint(min_sec, max_sec))
        self.bus_selection_page_click_bus(self.bus_name)

        time.sleep(random.randint(min_sec, max_sec))
        self.arrivals_bus_page_click_stop(self.bus_stop_name)

        time.sleep(random.randint(min_sec, max_sec))
        if self.err_in_page():
            print('No results in page. Please try again.')
            self.browser.close()
            sys.exit(1)

        self.open_output_file('arrivals')

        while True:
            self.print_arrival_times()
            time.sleep(self.printing_interval)

    #==========================================================================
    # open_output_file ()
    #==========================================================================
    def open_output_file(self, file_type):
        if file_type == 'arrivals':
            output_filename = 'arrivals-%s-%s-%s.txt' % (self.bus_name.replace(' ','_'), self.bus_stop_name.replace(' ','_'), self.curdate)
        elif file_type == 'timetables':
            output_filename = 'timetables-%s.txt' % (self.bus_name.replace(' ','_') )
        else:
            print('Unknown file type "%s"' % (file_type))
            sys.exit(1)

        self.output_file = open(output_filename, 'w')
        print('Output file: %s' % (output_filename))

    #==========================================================================
    # menu_page_click_link ()
    #==========================================================================
    def menu_page_click_link(self, menu_option):
        elems = self.get_menu_options()
        option = self.select_option_by_class_and_name(elems, "slideup", menu_option)
        option.click()

    #==========================================================================
    # bus_selection_page_click_bus ()
    #==========================================================================
    def bus_selection_page_click_bus(self, bus_name):
        elems = self.get_menu_options()
        option = self.select_option_by_class_and_name(elems, "sp1", bus_name)
        option.click()

    #==========================================================================
    # arrivals_bus_page_click_stop ()
    #==========================================================================
    def arrivals_bus_page_click_stop(self, stop_name):
        elems = self.get_menu_options()
        option = self.select_option_by_class_and_name(elems, "spt", stop_name)
        option.click()

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
    # select_option_by_class_and_name ()
    #==========================================================================
    def select_option_by_class_and_name(self, elems, class_name, elem_name):
        if class_name:
            xpath = './/*[@class = "%s"]' % (class_name)
        else:
            xpath = './/*'

        for elem in elems:
            try:
                xpath_copy = xpath + '[contains(text(), "%s")]' % (elem_name)
                found_elem = elem.find_element_by_xpath(xpath_copy)
                return found_elem
            except (NoSuchElementException):
                continue

        print('No element "%s". Please check again the name is one of the following:' % (elem_name))
        for elem in elems:
            print(elem.find_element_by_xpath(xpath).get_attribute('innerHTML'))

    #==========================================================================
    # print_arrival_times ()
    #==========================================================================
    def print_arrival_times(self):
        arrivals_info = []
        elems = self.get_menu_options()
        for arrival in elems:
            try:
                bus_info_elem = arrival.find_element_by_class_name('sp1')
                arrival_time_elem = arrival.find_element_by_class_name('sptime')
                bus_info = bus_info_elem.get_attribute('innerHTML')
                arrival_time = arrival_time_elem.get_attribute('innerHTML')
                arrivals_info.append([bus_info, arrival_time])
            except (StaleElementReferenceException):
                print('Stale element exception, will retry in next interval')
                time.sleep(random.randint(min_sec, max_sec))
                return

        timestamp = int(time.time())
        for arrival_info in arrivals_info:
            [bus_info, arrival_time] = arrival_info

            bus_info = bus_info.replace(u"ΟΧΗΜΑ", ":")
            [line_number, line_name, vehicle_number] = [ v.strip() for v in bus_info.split(":") ]
            arrival_time = int(arrival_time.strip(" '"))

            print(time.strftime('%d-%m-%Y %H:%M:%S :'), end='')
            print("%4s (%04s) %-40s : %3d" % (line_number, vehicle_number, line_name, arrival_time))
            print("%d,%s,%s,%d" % (timestamp, line_number, vehicle_number, arrival_time), file=self.output_file)

        if len(arrivals_info):
            print('')

        self.output_file.flush()


    #==========================================================================
    # err_in_page ()
    #==========================================================================
    def err_in_page(self):
        if len(self.browser.find_elements_by_xpath('//*[@class="err"]')) > 0:
            return True

        return False

    #==========================================================================
    # scrape_timetables ()
    #==========================================================================
    def scrape_timetables(self, bus_name):
        self.bus_name = bus_name

#        time.sleep(random.randint(min_sec, max_sec))
        self.menu_page_click_link(self.timetables_option_name)

        time.sleep(random.randint(min_sec, max_sec))
        self.bus_selection_page_click_bus(self.bus_name)

        self.open_output_file('timetables')

        time.sleep(random.randint(min_sec, max_sec))
        elems = self.get_menu_options()
        for day_type in [ e.text for e in elems ]:
            time.sleep(random.randint(min_sec, max_sec))
            self.timetable_day_type_page_click_type(day_type)

            time.sleep(random.randint(min_sec, max_sec))
            self.print_timetables(day_type)

            self.browser.back()

    #==========================================================================
    # timetable_day_type_page_click_type ()
    #==========================================================================
    def timetable_day_type_page_click_type(self, day_type):
        elems = self.get_menu_options()
        option = self.select_option_by_class_and_name(elems, "", day_type)
        option.click()

    #==========================================================================
    # print_timetables ()
    #==========================================================================
    def print_timetables(self, day_type):
        print('=== %s ===' % (day_type))
        print('=== %s ===' % (day_type), file=self.output_file)

        elems = self.get_menu_options()
        for elem in elems:
            print(elem.text)
            print(elem.text, file=self.output_file)

#        time.sleep(random.randint(min_sec, max_sec))
#        self.arrivals_bus_page_click_stop(self.bus_stop_name)


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
    if operation == 'arrivals':
        bus_name = args.bus_name
        bus_stop = args.bus_stop
    elif operation == 'timetables':
        bus_name = args.bus_name

    # Scrape page
    scraper = OasthArrivalsScraper()
    if operation == 'arrivals':
        scraper.scrape_arrival_times(bus_name, bus_stop)
    elif operation == 'timetables':
        scraper = OasthArrivalsScraper()
        scraper.scrape_timetables(bus_name)

if __name__ == "__main__":
    main()
