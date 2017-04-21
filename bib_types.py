# Copyright 2014 Sam Parkinson
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import logging
from gettext import gettext as _

ALL_TYPES = {}
ALL_TYPE_NAMES = []
WEB_TYPES = []


class BibType(object):

    def __init__(self, type, name, items, format_func,
                 web_title=None, web_uri=None):
        self.type = type
        self.name = name
        self.format = format_func
        self.web_title_index = web_title
        self.web_uri_index = web_uri

        items = [tuple(item.strip().split(':')) for item in items.split('|')]
        # Fix issue with URLs having a colon
        self.items = [(item[0], ':'.join(item[1:])) for item in items]

        ALL_TYPES[self.name] = self
        ALL_TYPE_NAMES.append(self.name)

def basic_format(format_string):
    def closure(values):
        return format_string.format(*values)
    return closure

# NOTE: To use the and symbol (`&`), you must type `&amp;`
#       You also need to escape charecters like less than (`<` becomes `&lt;`)
#       and the greater than (`>` becomes `&gt;`)
#
# Format Information:
# The pipe charecter separates a tuple of the bibliography entry and
# placeholder/example.  The tuple is separated by a colon.
# DO NOT TRANSLATE words with an asterisk (`*`) at the start
#
# TODO:
# eBooks from Databases... does anybody have examples?
# Books with more than 2 authors
# CD recordings

BibType('Book', _('Book'),
        _('Last Name:Shoup | First Name Initial:K | Year of Publication:2008 |'
          'Title:Reuse your refuse | Publisher:Wiley |'
          'Place of Publication:Hoboken, N.J'),
        basic_format('{}, {} {}, <i>{}</i>, {}, {}'))
BibType('Book with 2 Authors', _('Book with 2 Authors'),
        _('Author 1 Last Name:Fiell | Author 1 First Name Initial:C |'
          'Author 2 Last Name:Fiell | Author 2 First Name Initial:P |'
          'Year of Publication:2005 | Title:Graphic design now |'
          'Publisher:Taschen | Place of Publication:London'),
        basic_format('{}, {} &amp; {}, {} {}, <i>{}</i>, {}, {}'))
BibType('Book without Author', _('Book without Author'),
        _('Title:Rome | Year of Publication:2008 |'
          'Publisher:Dorling Kindersley | Place of Publication:London'),
        basic_format('<i>{}</i> {}, {}, {}'))
BibType('Book with Editor', _('Book with Editor'),
        _('Editor Last Name:West | Editor First Name Initial:S |'
          'Year of Publication:2005 | Title:Guide to art |'
          'Publisher:Bloomsbury | Place of Publication:London'),
        basic_format('{}, {} (ed.) {}, <i>{}</i>, {}, {}'))


def ebook_format(without_edition, with_edition, index):
    def closure(values):
        if values[index].strip():
            return with_edition.format(*values)
        else:
            del values[index]
            return without_edition.format(*values)
    return closure

BibType('eBook', _('eBook'),
        _('Last Name:Sachar | First Name Initial:L |'
          'Year of Publication:2010 | Edition (if applicable): | Title:Holes |'
          'Publisher:Bloomsbury Publishing | Place of Publication:London |'
          'Accessed:*datenow |'
          'URL:http://books.google.com.au/books?id=vlJw20OoYqUC'),
        ebook_format('{}, {} {}, <i>{}</i>, {}, {}, accessed {}, &lt;{}&gt;',
            '{}, {} {}, {} edn, <i>{}</i>, {}, {}, accessed {}, &lt;{}&gt;',
            3))
BibType('eBook with 2 Authors', _('eBook with 2 Authors'),
        _('Author 1 Last Name:Sharpley | Author 1 First Name Initial:R |'
          'Author 2 Last Name:Telfer | Author 2 First Name Initial:D |'
          'Year of Publication:2002 | Edition (if applicable): | '
          'Title:Tourism and Development: Concepts and Issues |'
          'Publisher:Channel View Publications |'
          'Place of Publication:Bristol | Accessed:*datenow |'
          'URL:https://books.google.com.au/books?id=Wvo1sIjZH3UC'),
        ebook_format('{}, {} &amp; {}, {} {}, <i>{}</i>, {}, {}, '
                     'accessed {}, &lt;{}&gt;',
                     '{}, {} &amp; {}, {} {}, {} edn, <i>{}</i>, {}, {}, '
                     'accessed {}, &lt;{}&gt;',
                     5))
BibType('eBook without Author', _('eBook without Author'),
        _('Title: You\'ve got what? | Year of Publication:2009 |'
          'Edition (if applicable):4th |'
          'Publisher:Communicable Disease Control Branch, Department of Health'
          '| Place of Publication:Adelaide | Accessed:*datenow |'
          'URL:http://www.publications.health.sa.gov.au/cgi/viewcontent.cgi'
          '?article=1029'),
        ebook_format('<i>{}</i> {}, {}, {}, accessed {}, &lt;{}&gt;',
            '<i>{}</i> {}, {} edn, {}, {}, accessed {}, &lt;{}&gt;',
            2))

BibType('Electronic Encyclopedia', _('Electronic Encyclopedia'),
        _('Title of Article:Earthquake | Year of Publication:2013 |'
          'Title of Encyclopedia:Encyclopaedia Britannica |'
          'Accessed:*datenow | URL:http://www.school.eb.com.au/all/comptons/'
          'article-9274104?query=earthquake'),
        basic_format('\'{}\' {}, in <i>{}</i>, accessed {}, &lt;{}&gt;'))
BibType('Printed Encyclopedia with Author',
        _('Printed Encyclopedia with Author'),
        _('Last Name:Pettus | First Name Initial:A M |'
          'Year of Publication:1998 | Title of Article:Edward Jenne |'
          'Title of Encyclopedia:Biographical encyclopedia of scientists |'
          'Publisher:Marshall Cavendish |'
          'Place of Publication:Tarrytown, N.Y. | Volume Number:3 |'
          'Starting Page:691 | Finishing Page:693'),
        basic_format('{}, {} {}, \'{}\' in <i>{}</i>, {}, {} '
                     'vol. {}, pp. {}-{}'))
BibType('Printed Encyclopedia without Author',
        _('Printed Encyclopedia without Author'),
        _('Title of Article:Germany | Year of Publication:2008 |'
          'Title of Encyclopedia:The World Book | Publisher:World Book |'
          'Place of Publication:Chicago | Volume Number:8 |'
          'Starting Page:146 | Finishing Page:172'),
        basic_format('\'{}\' {} in <i>{}</i>, {}, {} vol. {}, pp. {}-{}'))

def vid_format(string, volumei, issuei, datei):
    def closure(values):
        volume = ' vol. {},'.format(values[volumei]) \
            if values[volumei].strip() else ''
        issue = ' no. {},'.format(values[issuei]) \
            if values[issuei].strip() else ''
        date = ' {},'.format(values[datei]) if values[datei].strip() else ''
        fvalues = values[:volumei] + [volume, issue, date] + values[datei + 1:]
        return string.format(*fvalues)
    return closure

BibType('Magazine or Journal Article with Author',
        _('Magazine or Journal Article with Author'),
        _('Last Name:Carter | First Name Initial:R |'
          'Year of Publication:2014 |'
          'Tite of Article:Take Control of Your Dreams |'
          'Title of Magazine:BBC Focus | Volume (if applicable): |'
          'Issue (if applicable):271 |'
          'Date of Issue (if applicable):August | Starting Page:37 |'
          'Finishing Page:43'),
        vid_format('{}, {} {} \'{}\', <i>{}</i>,{}{}{} pp. {}-{}', 5, 6, 7))
BibType('Magazine or Journal Article without Author',
        _('Magazine or Journal Article without Author'),
        _('Tite of Article:Appliances of Science | Year of Publication:2014 |'
          'Title of Magazine:BBC Focus | Volume (if applicable): |'
          'Issue (if applicable):271 |'
          'Date of Issue (if applicable):August | Starting Page:87 |'
          'Finishing Page:87'),
        vid_format('{}, {} {} \'{}\', <i>{}</i>,{}{}{} pp. {}-{}', 3, 4, 5))

BibType('Online Magazine or Journal Article with Author',
        _('Online Magazine or Journal Article with Author'),
        _('Last Name:Keneley | First Name Initial:M |'
          'Year of Publication:2004 | Tite of Article:The dying town syndrome:'
          'a survey of urban development in the Western District of Victoria'
          '1830 - 1930 | Title of Magazine:Electronic Journal of Australian'
          'and New Zealand History | Volume (if applicable): |'
          'Issue (if applicable): |'
          'Date of Issue (if applicable):19 February | Accessed:*datenow |'
          'URL:ttp://www.jcu.edu.au/aff/history/articles/keneley3.htm'),
        vid_format('{}, {} {} \'{}\', <i>{}</i>,{}{}{}'
                   ' accessed {}, &lt;{}&gt;', 5, 6, 7))
BibType('Online Magazine or Journal Article without Author',
        _('Online Magazine or Journal Article without Author'),
        _('Tite of Article:Logging off? | Year of Publication:2010 |'
          'Title of Magazine:New Internationalist | Volume (if applicable): |'
          'Issue (if applicable):432 | Date of Issue (if applicable):May |'
          'Accessed:*datenow | URL:http://www.newint.org/columns/currents/2010'
          '/05/01/illegal-logging-madagascar'),
        vid_format('\'{}\', {} <i>{}</i>,{}{}{} pp. {}-{},'
                   ' accessed {}, &lt;{}&gt;', 3, 4, 5))

def page_format(string, starti, endi):
    def closure(values):
        page = 'pp. {}-{}'.format(values[starti], values[endi])
        if values[starti].strip() == values[endi].strip() \
           or not values[endi].strip():
            page = 'p. {}'.format(values[starti])

        values[starti] = page
        del values[endi]
        return string.format(*values)
    return closure

BibType('Newsaper Article with Author',
        _('Newsaper Article with Author'),
        _('Last Name:Bourke | First Name Initial:L |'
          'Year of Publication:2014 |'
          'Title of Article:New push to hit online buys with GST |'
          'Title of Newspaper:The Canberra Times |'
          'Date of Issue:27 December | Starting Page:1 |'
          'Finishing Page:'),
        page_format('{}, {} {} \'{}\', <i>{}</i>, {}, {}', 6, 7))
BibType('Newsaper Article without Author',
        _('Newsaper Article without Author'),
        _('Title of Article:Aspirin put to the test | Year of Publication:2005 |'
          'Title of Newspaper:Advertiser |'
          'Date of Issue:18 January | Starting Page:23 |'
          'Finishing Page:'),
        page_format('\'{}\', {}, <i>{}</i>, {}, {}', 4, 5))

BibType('Online Newsaper Article with Author',
        _('Online Newsaper Article with Author'),
        _('Last Name:Bourke | First Name Initial:L |'
          'Year of Publication:2014 | Title of Article:AirAsia QZ8501: '
          'Australia joins search for missing AirAsia flight |'
          'Title of Newspaper:The Canberra Times |'
          'Date of Issue:29 December | Accessed:*datenow |'
          'URL:http://www.canberratimes.com.au/federal-politics/political-news'
          '/airasia-qz8501-australia-joins-search-for-missing-airasia-flight-'
          '20141229-12exkr.html'),
        basic_format('{}, {} {} \'{}\', <i>{}</i>, {},'
                     ' accessed {}, &lt;{}&gt;'))
BibType('Online Article without Author',
        _('Online Article without Author'),
        _('Title of Article:Google street view broke privacy law |'
          'Year of Publication:2010 |Title of Newspaper:Advertiser |'
          'Date of Issue:9 July | Accessed:*datenow |'
          'URL:http://www.adelaidenow.com.au/google-street-view-broke-'
          'privacy-law/story-e6frea8c-1225890011209'),
        basic_format('\'{}\', {}, <i>{}</i>, {}, accessed {}, &lt;{}&gt;'))

def license_format(string, index=-1):
    def closure(values):
        license = ', License: &lt;{}&gt;'.format(values[index]) \
                  if values[index].strip() else ''
        values[index] = license
        return string.format(*values)
    return closure

WEB_TYPES.extend([ \
    BibType('Image with Creator (Real Name)',
            _('Image with Creator (Real Name)'),
            _('Last Name:Ganguly | First Name Initial:B | Year Created:2010 |'
              'Title or Description:Chicken Egg without Eggshell | Format:Photo |'
              'Sponsor or Orginisation:Wikimedia Commons | Accessed:*datenow |'
              'URL:http://commons.wikimedia.org/wiki/File:Chicken_Egg_without_'
              'Eggshell_5859.jpg | License URL (if available):http://commons.'
              'wikimedia.org/wiki/'
              'Commons:GNU_Free_Documentation_License,_version_1.2'),
            license_format('{}, {} {}, <i>{}</i>, {}, {},'
                           ' accessed {}, &lt;{}&gt;{}'),
            web_title=3, web_uri=7),
    BibType('Image with Creator (Screen Name)',
            _('Image with Creator (Screen Name)'),
            _('Screen Name or User Name:Dschwen | Year Created:2009 |'
              'Title or Description:Looking north from Chicago \'L\' station |'
              'Format:Photo | Sponsor or Orginisation:Wikimedia Commons |'
              'Accessed:*datenow | URL:http://commons.wikimedia.org/wiki/File:'
              'CTA_Night.jpg | License URL (if available):http://creativecommons.'
              'org/licenses/by-sa/4.0/deed.en'),
            license_format('{} {}, <i>{}</i>, {}, {}, accessed {}, &lt;{}&gt;{}'),
            web_title=2, web_uri=6),
    BibType('Image without Creator', _('Image without Creator'),
            _('Title or Description:OLPC XO Laptop with Screen Twisted |'
              'Year Created:n.d. | Format:Photo |'
              'Sponsor or Orginisation:One Laptop Per Child |'
              'Accessed:*datenow | URL:http://one.laptop.org/sites/default/files/'
              'hardware-left-side-view.png | License URL (if available):'),
            license_format('<i>{}</i> {}, {}, {}, accessed {}, &lt;{}&gt;{}'),
            web_title=0, web_uri=5),
    BibType('Website with Author', _('Website with Author'),
            _('Last Name:Lesinski | First Name Initial:K | Last Update:2014 |'
              'Title of Webpage:MozJPEG 3.0 |'
              'Sponsor or Orginisation:Performance Calendar | Accessed:*datenow |'
              'URL:http://calendar.perfplanet.com/2014/mozjpeg-3-0/'),
            basic_format('{}, {} {}, <i>{}</i>, {}, accessed {}, &lt;{}&gt;'),
            web_title=3, web_uri=6),
    BibType('Website by Organisation', _('Website by Organisation'),
            _('Name of Organisation:Sugar Labs | Last Update:2010 |'
              'Title of Webpage:Sugar Labs-learning software for children |'
              'Sponsor or Orginisation:Sugar Labs |'
              'Accessed:*datenow | URL:http://sugarlabs.org/'),
            basic_format('{} {}, <i>{}</i>, {}, accessed {}, &lt;{}&gt;'),
            web_title=2, web_uri=5),
    BibType('Website without Author', _('Website without Author'),
            _('Title of Webpage:Avocado Jackpot | Year Created:2014 |'
              'Sponsor or Orginisation:Reddit | Accessed:*datenow |'
              'URL:http://www.reddit.com/r/food/comments/2qnbpc/avocado_jackpot/'),
            basic_format('<i>{}</i> {}, {}, accessed {}, &lt;{}&gt;'),
            web_title=0, web_uri=4) \
])

def place_format(string, index):
    def closure(values):
        place = ', {}'.format(values[index]) if values[index].strip() else ''
        values[index] = place
        return string.format(*values)
    return closure

BibType('Film', _('Film'),
        _('Title:Toy Story 2 | Year Created:1999 | Format:DVD |'
          'Distributor:Buena Vista Home Entertainment |'
          'Place (if available): | Special Credits or Other Information: A '
          'Pixar Animation Studios Film'),
        place_format('<i>{}</i> {}, {}, {}{}. {}', 4))
BibType('Television Program (Single)', _('Television Program (Single)'),
        _('Title:Ten Bucks A Liter | Year of Broadcast:2013 | Format:iview |'
          'Television Channel:ABC | Place (if available): |'
          'Date of Broadcast:1 August'),
        place_format('<i>{}</i> {}, {}, {}{}, {}', 4))
BibType('Television Program (Part of Series)',
        _('Television Program (Part of Series)'),
        _('Episode Title:Radio Goodies | Year of Broadcast:1970 |'
          'Series Title: The Goodies | Format:DVD |'
          'Television Channel:BBC | Place (if available): |'
          'Date of Broadcast:20 December'),
        place_format('<i>{}</i> {}, {}, {}, {}{}, {}', 5))
