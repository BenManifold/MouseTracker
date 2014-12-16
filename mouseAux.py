#!/usr/local/bin/sage

import cPickle
import sys
import time
import commands
import os
from csv import *
from collections import *
from sage.all import *


LONGMONTHS = {'01':'January', '02':'February', '03':'March', '04':'April', '05':'May', '06':'June', '07':'July',\
          '08':'August', '09':'September', '10':'October', '11':'November', '12':'December'}

SHORTMONTHS = {'01':'Jan', '02':'Feb', '03':'Mar', '04':'Apr', '05':'May', '06':'Jun', '07':'Jul',\
          '08':'Aug', '09':'Sep', '10':'Oct', '11':'Nov', '12':'Dec'}

SHORT_TO_LONG = -1
LONG_TO_SHORT = -2
NUMB_TO_SHORT = -3
NUMB_TO_LONG  = -4
SHORT_TO_NUMB = -5
LONG_TO_NUMB  = -6

KEYS = [ 'Segment ID', 'Joined ID', 'Start Frame', 'Average Area', 'Distance', 'Start X', 'Start Y', 'End X', 'End Y', 'Active Frames', 'Total Frames', 'Speed', 'Start Speed', 'End Speed']

def cvtDate(inDate, method = NUMB_TO_LONG):
    outDate = ''
    if type(inDate) == int:
        inDate = str(inDate)
        
    if method == SHORT_TO_LONG:
        for idx in SHORTMONTHS:
            if inDate.find(SHORTMONTHS[idx]) != -1:
                outDate = inDate.replace(SHORTMONTHS[idx],LONGMONTHS[idx])
                outDate = outDate.replace(" 200", ", 200") 

    elif method == LONG_TO_SHORT:
        for idx in LONGMONTHS:
            if inDate.find(LONGMONTHS[idx]) != -1:
                outDate = inDate.replace(LONGMONTHS[idx],SHORTMONTHS[idx])
                outDate = outDate.replace(", 200", " 200") 

    elif method == NUMB_TO_SHORT:
        year = inDate[:4]
        month = inDate[4:6]
        day = inDate[6:8]
        outDate = SHORTMONTHS[month] + ' ' + str(int(day)) + ' ' + year 

    elif method == NUMB_TO_LONG:
        year = inDate[:4]
        month = inDate[4:6]
        day = inDate[6:8]
        outDate = LONGMONTHS[month] + ' ' + str(int(day)) + ', ' + year

    elif method == SHORT_TO_NUMB:
        tempDate = inDate.split(' ')
        for num, month in SHORTMONTHS.items():
            if month == tempDate[0]:
                tempDate[0] = num    
        outDate = tempDate[-1] + tempDate[0] + '0' + tempDate[-2]

    elif method == LONG_TO_NUMB:
        tempDate = inDate.replace(', 200', ' 200').split(' ')
        for num, month in LONGMONTHS.items():
            if month == tempDate[0]:
                tempDate[0] = num    
        outDate = tempDate[-1] + tempDate[0] + '0' + tempDate[-2]

    else:
        return 'Invalid conversion method.'

    return outDate

def loadCsv(filename):
    csv = DictReader(open(filename, "rb"), dialect='excel-tab')
    keys = csv.fieldnames
    csvDict = OrderedDict()
    for row in csv:
        csvDict[row['Date']] = row

    return keys, csvDict
    
def saveCsv(filename, keys, csvDict):
    csv = DictWriter(open(filename, 'wb'), keys, dialect='excel-tab', quoting = QUOTE_ALL, extrasaction='ignore')
    csv.writeheader()
    for idx in csvDict:
        csv.writerow(csvDict[idx])


def loadFile(filename, method = "rb"):
    input_file = open(filename, method)
            
    if method == "rb":
        data = cPickle.load(input_file)
    else:
        data = input_file.read()
        
    input_file.close()
    return data

def savePickle(filename, data):
    output = open(filename, "wb")
    cPickle.dump(data, output,2)
    output.close()


def cfor(first,test,update):
    while test(first):
        yield first
        first = update(first)

class print_no_cr():
    """
    Print things to stdout on one line dynamically
    """

    def __init__(self,data):

        sys.stdout.write("\r\x1b"+data.__str__())
        sys.stdout.flush()
