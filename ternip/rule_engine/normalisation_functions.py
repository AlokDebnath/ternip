#!/usr/bin/env python

import calendar
import expressions
import datetime
import dateutil.easter
import re

# Mappings
month_to_num = {
    'jan': 1,
    'feb': 2,
    'mar': 3,
    'apr': 4,
    'may': 5,
    'jun': 6,
    'jul': 7,
    'aug': 8,
    'sep': 9,
    'oct': 10,
    'nov': 11,
    'dec': 12
}

ordinal_to_num = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
    "eleventh": 11,
    "twelfth": 12,
    "thirteenth": 13,
    "fourteenth": 14,
    "fifteenth": 15,
    "sixteenth": 16,
    "seventeenth": 17,
    "eighteenth": 18,
    "nineteenth": 19,
    "twentieth": 20,
    "twenty-first": 21,
    "twenty-second": 22,
    "twenty-third": 23,
    "twenty-fourth": 24,
    "twenty-fifth": 25,
    "twenty-sixth": 26,
    "twenty-seventh": 27,
    "twenty-eighth": 28,
    "twenty-ninth": 29,
    "thirtieth": 30,
    "thirty-first": 31
}

timezones = {
    "E": -5,
    "C": -6,
    "M": -7,
    "P": -8
}

word_to_num = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
    "thousand": 1000,
    "million": 1000000,
    "billion": 1000000000,
    "trillion": 1000000000000
}

decade_nums = {
    "twen": 2,
    "thir": 3,
    "for": 4,
    "fif": 5,
    "six": 6,
    "seven": 7,
    "eigh": 8,
    "nine": 9
}

fixed_holiday_date = {
    "newyear":          "0101",
    "inauguration":     "0120",
    "valentine":        "0214",
    "ground":           "0202",
    "candlemas":        "0202",
    "patrick":          "0317",
    "fool":             "0401",
    "st\.george":       "0423",
    "saintgeorge":      "0423",
    "walpurgisnacht":   "0430",
    "mayday":           "0501",
    "beltane":          "0501",
    "cinco":            "0505",
    "flag":             "0614",
    "baptiste":         "0624",
    "dominion":         "0701",
    "canada":           "0701",
    "independence":     "0704",
    "bastille":         "0714",
    "halloween":        "1031",
    "allhallow":        "1101",
    "allsaints":        "1101",
    "allsouls":         "1102",
    "dayofthedead":     "1102",
    "fawkes":           "1105",
    "veteran":          "1111",
    "christmas":        "1225",
    "xmas":             "1225"
}

# month dow nth
nth_dow_holiday_date = {
    "mlk":          (1, 1, 3),
    "king":         (1, 1, 3),
    "president":    (2, 1, 3),
    "canberra":     (3, 1, 3),
    "mother":       (5, 7, 2),
    "father":       (6, 7, 3),
    "labor":        (9, 1, 1),
    "columbus":     (10, 1, 2),
    "thanksgiving": (11, 4, 4)
}

season = {
    "spring": "SP",
    "summer": "SU",
    "autumn": "FA",
    "fall":   "FA",
    "winter": "WI"
}

# Functions for normalisation rules to use
def normalise_two_digit_year(y):
    if y[0] == "'":
        y = y[1:]
    if int(y) < 39:
        return '%04d' % int(y) + 2000
    elif int(y) < 100:
        return '%04d' % int(y) + 1900
    else:
        return '%04d' % int(y)

def date_to_iso(string):
    """
    A translation of GUTime's Date2ISO function
    """
    
    # disregard tokenisation, if it's there, to make this an easier conversion for GUTime
    string = re.sub(r'<([^~]*)~.+?>', r'\1 ', string)
    
    # Defaults
    d = None
    m = None
    y = None
    h = None
    min = None
    s = None
    fs = None
    zone = None
    
    # Already in ISO format
    match = re.search(r'(\d\d\d\d-?\d\d-?\d\d)(-?(T\d\d(:?\d\d)?(:?\d\d)?([+-]\d{1,4})?))?', re.sub('\s', '', string))
    if match != None:
        d = match.group(1)
        d = re.sub(r'-', r'', d)
        h = match.group(3)
        if h != None:
            h = re.sub(r':', r'', h)
            return d + h
        else:
            return d
    
    # ACE format
    match = re.search(r'(\d\d\d\d\d\d\d\d:\d\d\d\d)', re.sub('\s', '', string))
    if match != None:
        d = match.group(1)
        d = re.sub(r':', r'T', d)
        return d
    
    # some pre-processing
    match = re.search('T\d\d(:?\d\d)?(:?\d\d)?([+-]\d{1,4})?', re.sub('\s', '', string))
    if match != None:
        return re.sub(r':', r'', re.sub('\s', '', string))
    
    # extract date
    if re.search(r'(\d\d?)\s+(' + expressions.MONTHS + r'|' + expressions.MONTH_ABBRS + r'\s*\.?)\s*,?\s+(\d\d(\s|\Z)|\d{4}\b)', string, re.I) != None:
        match = re.search(r'(\d\d?)\s+(' + expressions.MONTHS + r'|' + expressions.MONTH_ABBRS + r'\s*\.?)\s*,?\s+(\d\d(\s|\Z)|\d{4}\b)', string, re.I)
        d = match.group(1)
        m = month_to_num[match.group(2)[:3].lower()]
        y = match.group(5)
        
    elif re.search(r'(' + expressions.MONTHS + r'|' + expressions.MONTH_ABBRS + r'\s*\.?)\s+(\d\d?|' + expressions.ORDINAL_WORDS + r')\b,?\s*(\d\d(\s|\Z)|\d{4}\b)', string, re.I) != None:
        match = re.search(r'(' + expressions.MONTHS + r'|' + expressions.MONTH_ABBRS + r'\s*\.?)\s+(\d\d?|' + expressions.ORDINAL_WORDS + r')\b,?\s*(\d\d(\s|\Z)|\d{4}\b)', string, re.I)
        d = match.group(4)
        dm = re.search(expressions.ORDINAL_WORDS, d)
        if dm != None:
            d = ordinal_to_num[dm.group()]
        m = month_to_num[match.group(1)[:3].lower()]
        y = match.group(6)
    
    elif re.search(r'(\d\d\d\d)(\/|\-)(\d\d?)\2(\d\d?)', re.sub('\s', '', string)) != None:
        match = re.search(r'(\d\d\d\d)(\/|\-)(\d\d?)\2(\d\d?)', re.sub('\s', '', string))
        m = match.group(3)
        d = match.group(4)
        y = match.group(1)
    
    elif re.search(r'(\d\d?)(\/|\-|\.)(\d\d?)\2(\d\d(\d\d)?)', re.sub('\s', '', string)) != None:
        match = re.search(r'(\d\d?)(\/|\-|\.)(\d\d?)\2(\d\d(\d\d)?', re.sub('\s', '', string))
        m = match.group(1)
        d = match.group(3)
        y = match.group(4)
    
    elif re.search(r'(' + expressions.MONTHS + r'|' + expressions.MONTH_ABBRS + r'\.?)\s+(\d\d?).+(\d\d\d\d)\b', string) != None:
        match = re.search(r'(' + expressions.MONTHS + r'|' + expressions.MONTH_ABBRS + r'\.?)\s+(\d\d?).+(\d\d\d\d)\b', string)
        d = match.group(4)
        m = month_to_num[match.group(2)[:3].lower()]
        y = match.group(5)
        if int(y) > 2100 or int(y) < 1900:
            y = None
    
    if y != None:
        # check for European style date
        if int(m) > 12 and int(m) < 31 and int(d) < 12:
            new_d = m
            m = d
            d = new_d
        
        # check for 2 digit year
        y = normalise_two_digit_year(str(y))
        
        iso = "%4d%02d%02d" % (int(y), int(m), int(d))
    
    else:
        iso = "XXXXXXXX"
    
    # Extract time
    match = re.search(r'(\d?\d):(\d\d)(:(\d\d)(\.\d+)?)?(([AP])\.?M\.?)?(([+\-]\d+|[A-Z][SD]T|GMT([+\-]\d+)?))?', re.sub('\s', '', string), re.I)
    if match != None:
        h = match.group(1)
        min = match.group(2)
        s = match.group(4)
        fs = match.group(5)
        ampm = match.group(7)
        zone = match.group(9)
        
        if ampm != None and ampm[0].lower() == 'p':
            h = str(int(h) + 12)
        
        if zone != None:
            zm = re.search(r'(GMT)([+\-]\d+)', zone)
            if zm != None:
                zone = zm.group(2)
            elif zone.lower().contains('gmt'):
                zone = 'Z'
            elif re.search(r'([A-Z])([SD])T', zone) != None:
                zm = re.search(r'([A-Z])([SD])T', zone)
                if zm.group(1) in timezones:
                    zone = timezones[zone]
                    if zm.group(2) == 'd':
                        zone += 1
                    if zone < 0:
                        zone = '-%02d' % (-1 * zone)
                    else:
                        zone = '+%02d' % zone
    elif re.search(r'(\d\d)(\d\d)\s+(h(ou)?r|(on\s+)?\d\d?\/\d)', string, re.I) != None:
        match = re.search(r'(\d\d)(\d\d)\s+(h(ou)?r|(on\s+)?\d\d?\/\d)', string, re.I)
        h = match.group(1)
        min = match.group(2)
    
    if h != None:
        if fs != None:
            fs = re.sub(r'\.', r'', fs)
            iso += 'T%02d:%02d:%02d.%02d' % (int(h), int(min), int(s), int(fs))
        elif s != None:
            iso += 'T%02d:%02d:%02d' % (int(h), int(min), int(s))
        elif min != None:
            iso += 'T%02d:%02d' % (int(h), int(min))
        else:
            iso += 'T%02d' % (int(h))
        
        if zone != None:
            iso += zone.lstrip()
    
    return iso

def date_to_week(y, m, d):
    return datetime.datetime(y, m, d).strftime(r'%YW%W')

def date_to_dow(y, m, d):
    """
    Gets the day of week for a date. Sunday is 0.
    """
    # Python uses Monday week start, so wrap around
    w = calendar.weekday(y, m, d) + 1
    if w == 7:
        w = 0
    return w

def absolute_date_to_iso(string):
    v = None
    d = None
    match = re.search(r'(\d{4}|\'\d\d)', string, re.I)
    y = int(normalise_two_digit_year(match.group(1)))
    before = string[:match.start()]
    
    match = re.search(r'\b(' + expressions.MONTHS + r'|' + expressions.MONTH_ABBRS + r')\b', before, re.I)
    m = month_to_num[match.group(1)[:3].lower()]
    
    match = re.search(r'(' + expressions.ORDINAL_WORDS + r'|' + expressions.ORDINAL_NUMS + r')\s+week(end)?\s+(of|in)', before, re.I)
    if match != None:
        wk_match = re.search(r'\d+', match.group(1))
        if wk_match != None:
            wk = int(wk_match.group(0))
        else:
            wk = ordinal_to_num[match.group(1).lower()]
        
        if re.search(r'weekend', string, re.I) != None:
            d = wk * 7 - 5
        else:
            d = wk * 7 - 3
        
        v = date_to_week(y, m, d)
        
        if re.search(r'weekend', string, re.I):
            v += 'WE'
    
    elif re.search(r'(\d\d?)', before) != None:
        match  = re.search(r'(\d\d?)', before)
        d = int(match.group(1))
    
    elif re.search(expressions.ORDINAL_WORDS, before, re.I) != None:
        match = re.search(expressions.ORDINAL_WORDS, before, re.I)
        d = ordinal_to_num[match.group(1).lower()]
    
    elif re.search(r'\bides\b', before, re.I) != None:
        match = re.search(r'\bides\b', before, re.I)
        if m == 3 or m == 5 or m == 7 or m == 10:
            d = 15
        else:
            d = 13
    
    elif re.search(r'\bnones\b', before, re.I) != None:
        match = re.search(r'\bnones\b', before, re.I)
        if m == 3 or m == 5 or m == 7 or m == 10:
            d = 7
        else:
            d = 5
    
    if v == None:
        if d != None:
            if re.search(r'the\s+week\s+(of|in)', string, re.I):
                v = date_to_week(y, m, d)
            else:
                v = "%4d%02d%02d" % (y, m, d)
        else:
            v = "%4d%02d" % (y, m)

def offset_from_date(v, offset, gran='D'):
    if len(v) >= 4:
        y = v[:4]
    else:
        y = None
    
    if len(v) >= 6:
        m = v[4:6]
    else:
        m = None
    
    if len(v) >= 8:
        d = v[6:8]
    else:
        d = None
    
    if len(v) >= 11:
        h = v[9:11]
    else:
        h = None
    
    if len(v) >= 13:
        min = v[11:13]
    else:
        min = None
    
    dt = datetime.datetime(y, m, d, h, min, s)
    
    if gran == 'TM':
        # minutes
        dt += datetime.timedelta(minutes=offset)
        return dt.strftime('%Y%m%dT%H%M')
    elif gran == 'TH':
        # hours
        dt += datetime.timedelta(hours=offset)
        return dt.strftime('%Y%m%dT%H%M')
    elif gran == 'D':
        # days
        dt += datetime.timedelta(days=offset)
        return dt.strftime('%Y%m%d')
    elif gran == 'W':
        # weeks
        dt += datetime.timedelta(weeks=offset)
        return dt.strftime('%YW%W')
    elif gran == 'M':
        # months - timedelta rather annoyingly doesn't support months, so we
        # need to do a bit more work here
        m += offset
        if m > 12:
            year += int(m/12)
            m = m % 12
        elif m < 0:
            y += int(m/12) - 1
            m = m % 12
        
        if m == 0:
            m = 12
            y -= 1
        
        dt = datetime.datetime(y, m, 1)
        return dt.strftime('%Y%m')
    elif gran == 'Y':
        # years - again, need to do a bit more work
        if d == 29 and m == 2 and not calendar.isleap(y + offset):
            # eugh, mucking about with a date that's not going to be in the
            # target year - fall back
            d = 28
        y += offset
        dt = datetime.datetime(y, m, d, h, min, s)
        return dt.strftime('%Y')

def easter_date(y):
    """
    Return the date of Easter for that year
    """
    return dateutil.easter.easter(int(y)).strftime('%Y%m%d')

def nth_dow_to_date(m, dow, n, y):
    """
    Figures out the date of the nth day-of-week in the month m and year y,
    
    e.g., 2nd Wednesday in July 2010:
          nth_dow_to_date(7, 3, 2, 2010)
    
    Conversion from GUTime
    """
    
    if dow == 7:
        dow = 0
    
    first_dow = date_to_dow(y, m, 1) # the dow of the first of the month
    shift = dow - first
    if shift < 0:
        shift += 7
    
    return shift + (7 * n) - 6