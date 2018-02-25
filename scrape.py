#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import time
import sys
import scrapy
import random
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

min_sec = 1
max_sec = 5

#==============================================================================
# OasthArrivalsScraper ()
#==============================================================================
class OasthArrivalsScraper:

    #==========================================================================
    # __init__ ()
    #==========================================================================
    def __init__(self):
        self.arrivals_option_name = 'Αφίξεις Γραμμών'
        self.bus_name = random.choice([ '02', '08', '10', '11', '14', '17', '27', '31' ]) # aristotelous apo egnatia
#        self.bus_name = random.choice([ '03', '05', '06', '12', '33', '39', '58', '78' ]) # aristotelous apo tsimiski
#        self.bus_name = random.choice([ '02', '08', '10', '11', '14', '31' ]) # aristotelous apo egnatia
        self.bus_stop_name = 'ΠΛΑΤΕΙΑ ΑΡΙΣΤΟΤΕΛΟΥΣ'
        self.printing_interval = 20

        print('bus: %s' % self.bus_name)

        # Initialized our headless browser
        #self.browser = webdriver.PhantomJS()
        #self.browser = webdriver.Firefox()
        self.browser = webdriver.Chrome()
        self.browser.get('http://m.oasth.gr')

    #==========================================================================
    # scrape ()
    #==========================================================================
    def scrape(self):

        time.sleep(random.randint(min_sec, max_sec))

        self.menu_page_click_link(self.arrivals_option_name)

        time.sleep(random.randint(min_sec, max_sec))

        self.arrivals_page_click_bus(self.bus_name)

        time.sleep(random.randint(min_sec, max_sec))

        self.arrivals_bus_page_click_stop(self.bus_stop_name)

        time.sleep(random.randint(min_sec, max_sec))

        if self.no_results_in_page():
            print('No results in page. Please try again.')
            self.browser.close()
            sys.exit(1)

        output_filename = time.strftime('%Y.%m.%d-%H.%M.%S') + '.txt'
        print('Output file: %s' % (output_filename))
        self.output_file = open(output_filename, 'w')

        while True:
            self.print_arrival_times()
            time.sleep(self.printing_interval)

    #==========================================================================
    # menu_page_click_link ()
    #==========================================================================
    def menu_page_click_link(self, menu_option):
        elems = self.get_menu_options()
        option = self.select_option_by_class_and_name(elems, "slideup", menu_option)
        option.click()

    #==========================================================================
    # arrivals_page_click_bus ()
    #==========================================================================
    def arrivals_page_click_bus(self, bus_name):
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
        xpath_template = './/*[@class = "%s" %s]'
        extra_operand = 'and contains(text(), "%s")' % (elem_name)
        xpath = xpath_template % (class_name, extra_operand)

        for elem in elems:
            try:
                found_elem = elem.find_element_by_xpath(xpath)
                return found_elem
            except (NoSuchElementException):
                continue

        extra_operand = ''
        xpath = xpath_template % (class_name, extra_operand)
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
    # no_results_in_page ()
    #==========================================================================
    def no_results_in_page(self):
        if len(self.browser.find_elements_by_xpath('//*[@class="err"]')) > 0:
            return True

        return False

s = OasthArrivalsScraper()
s.scrape()
