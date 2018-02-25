#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import time
import sys
import scrapy
import random
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

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
        self.arrivals_option_name = 'Αφίξεις Γραμμών'
#        self.bus_name = random.choice([ '02', '08', '10', '11', '14', '17', '27', '31' ]) # aristotelous apo egnatia
#        self.bus_name = random.choice([ '03', '05', '06', '12', '33', '39', '58', '78' ]) # aristotelous apo tsimiski
        self.bus_name = random.choice([ '02', '08', '10', '11', ]) # aristotelous apo egnatia
        self.bus_stop_name = 'ΠΛΑΤΕΙΑ ΑΡΙΣΤΟΤΕΛΟΥΣ'
        self.printing_interval = 1

        print('bus: %s' % self.bus_name)

        # Initialized our headless browser
        #self.browser = webdriver.PhantomJS()
        #self.browser = webdriver.Firefox()
        self.browser = webdriver.Chrome()
        self.browser.get('http://m.oasth.gr')

        output_filename = time.strftime('%Y.%m.%d-%H.%M.%S')
        self.output_file = open(output_filename, 'w')

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

        while True:
            self.print_arrival_times()
            time.sleep(self.printing_interval)

    #==========================================================================
    # menu_page_click_link ()
    #==========================================================================
    def menu_page_click_link(self, menu_option):
        self.page_click_link('slideup', menu_option, '.')

    #==========================================================================
    # arrivals_page_click_bus ()
    #==========================================================================
    def arrivals_page_click_bus(self, bus_name):
        self.page_click_link('sp1', bus_name, '..')

    #==========================================================================
    # arrivals_bus_page_click_stop ()
    #==========================================================================
    def arrivals_bus_page_click_stop(self, stop_name):
        self.page_click_link('spt', stop_name, '.')

    #==========================================================================
    # page_click_link ()
    #==========================================================================
    def page_click_link(self, class_name, elem_name, relative_elem_to_click_xpath):
        xpath_template  = '//div[@class="cacher" and (not(@style) or not(contains(@style,"display: none")))]'
        xpath_template += '/div[@class="holder"]'
        xpath_template += '/div[contains(@class,"menu")]'
        # select the first menu, e.g. in case of stop selection, there
        # is the outward journey menu and return journey menu.
        xpath_template += '[1]'
        xpath_template += '/h3'
        xpath_template += '//*[@class="%s" %s ]'
        try:
            extra_operand = 'and contains(text(), "%s")' % (elem_name)
            xpath = xpath_template % (class_name, extra_operand)
            elem = self.browser.find_element_by_xpath(xpath)
        except (NoSuchElementException):
            extra_operand = ''
            xpath = xpath_template % (class_name, extra_operand)
            elems = self.browser.find_elements_by_xpath(xpath)
            print('No element "%s". Please check again the name is one of the following:' % (elem_name))
            for elem in elems:
                print(elem.get_attribute('innerHTML'))
            sys.exit(1)

        elem_to_click = elem.find_element_by_xpath(relative_elem_to_click_xpath)
        elem.click()

    #==========================================================================
    # print_arrival_times ()
    #==========================================================================
    def print_arrival_times(self):

        path = '//*[@id="hh"]/div[5]/div[4]/div/h3'
        arrivals_info = []
        arrivals = self.browser.find_elements_by_xpath(path)
        for arrival in arrivals:
            try:
                bus_info_elem = arrival.find_element_by_class_name('sp1')
                arrival_time_elem = arrival.find_element_by_class_name('sptime')
                bus_info = bus_info_elem.get_attribute('innerHTML')
                arrival_time = arrival_time_elem.get_attribute('innerHTML')
                arrivals_info.append([bus_info, arrival_time])
            except (StaleElementReferenceException):
                continue

        timestamp = int(time.time())
        for arrival_info in arrivals_info:
            [bus_info, arrival_time] = arrival_info

            bus_info = bus_info.replace(u"ΟΧΗΜΑ", ":")
            [line_number, line_name, vehicle_number] = [ v.strip() for v in bus_info.split(":") ]
            arrival_time = int(arrival_time.strip(" '"))

            print(time.strftime('%d-%m-%Y %H:%M:%S :'), end='')
            print("%4s (%04s) %-40s : %3d" % (line_number, vehicle_number, line_name, arrival_time))
            print("%d,%s,%s,%d" % (timestamp, line_number, vehicle_number, arrival_time), file=self.output_file)

        if len(arrivals):
            print('')

        self.output_file.flush()


s = OasthArrivalsScraper()
s.scrape()
