'''
    test_Printing.py

    Tests the functionality of WebElements/Printing.py

    Copyright (C) 2013  Timothy Edmund Crosley

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''

from test_WebElement_Base import ElementTester
from WebElements.All import Factory


class TestPageBreak(ElementTester):

    def setup_method(self, method):
        self.element = Factory.build('pagebreak', 'test')


class TestUnPrintable(ElementTester):

    def setup_method(self, method):
        self.element = Factory.build('unprintable', 'test')
