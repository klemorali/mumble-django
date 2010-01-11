# -*- coding: utf-8 -*-

"""
 *  Copyright (C) 2010, mbonetti <http://code.google.com/u/mbonetti/>
 *
 *  Permission is hereby granted, free of charge, to any person obtaining a copy
 *  of this software and associated documentation files (the "Software"), to deal
 *  in the Software without restriction, including without limitation the rights
 *  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 *  copies of the Software, and to permit persons to whom the Software is
 *  furnished to do so, subject to the following conditions:
 *
 *  The above copyright notice and this permission notice shall be included in
 *  all copies or substantial portions of the Software.
 *
 *  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 *  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 *  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 *  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 *  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 *  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 *  THE SOFTWARE.
"""

from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
import re
from django.template import Node

register = template.Library()
rx = re.compile(r'(%(\([^\s\)]*\))?[sd])')

def format_message(message):
    return mark_safe(rx.sub('<code>\\1</code>', escape(message).replace(r'\n','<br />\n')))
format_message=register.filter(format_message)


def lines_count(message):
    return 1 + sum([len(line)/50 for line in message.split('\n')])
lines_count=register.filter(lines_count)

def mult(a,b):
    return int(a)*int(b)
mult=register.filter(mult)

def minus(a,b):
    try:
        return int(a) - int(b)
    except:
        return 0
minus=register.filter(minus)
    

def gt(a,b):
    try:
        return int(a) > int(b)
    except:
        return False
gt=register.filter(gt)


def is_fuzzy(message):
    return message and hasattr(message, 'flags') and 'fuzzy' in message.flags
is_fuzzy = register.filter(is_fuzzy)

class RosettaCsrfTokenPlaceholder(Node):
    def render(self, context):
        return mark_safe(u"<!-- csrf token placeholder -->")

def rosetta_csrf_token(parser, token):
    try:
        from django.template.defaulttags import csrf_token
        return csrf_token(parser,token)
    except ImportError:
        return RosettaCsrfTokenPlaceholder()
rosetta_csrf_token=register.tag(rosetta_csrf_token)
