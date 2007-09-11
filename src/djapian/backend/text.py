# -*- encoding: utf-8 -*-
"""
This module is useful for those live in latin-based countries (like me in Brazil)
and allow you to index words 'caminhão' as 'caminhao', because users can don't 
write accents

WARING: This was not tested with japanese/chinese/korean/you-understand characters
"""
import re
import string
import logging

from htmlentitydefs import name2codepoint
from base64 import decodestring, encodestring
import cPickle

class Text(object):
    """Parse texts in UTF-8"""
    spaces = string.whitespace+'\0'
    tokens = re.compile('[%s]+'%re.escape(string.punctuation + spaces),re.M|re.S)
    double_space = re.compile(r'\s\s+',re.M|re.S)
    cod_html = re.compile(r'&(\w+);', re.M|re.S)
    cod_unicode_html = re.compile(r'&#(\d+);', re.M|re.S)
    tags = re.compile(r'<[/a-z]+[^>]*>',re.I|re.M|re.S)

    cods = {'\xc2\xa0': ' '}

    no_accents = {192: u'A', 193: u'A', 194: u'A', 195: u'A', 196: u'A', 197: u'A',
                    199: u'C', 200: u'E', 201: u'E', 202: u'E', 203: u'E', 204: u'I',
                    205: u'I', 206: u'I', 207: u'I', 209: u'N', 210: u'O', 211: u'O',
                    212: u'O', 213: u'O', 214: u'O', 216: u'O', 217: u'U', 218: u'U',
                    219: u'U', 220: u'U', 221: u'Y', 224: u'a', 225: u'a', 226: u'a',
                    227: u'a', 228: u'a', 229: u'a', 231: u'c', 232: u'e', 233: u'e',
                    234: u'e', 235: u'e', 236: u'i', 237: u'i', 238: u'i', 239: u'i',
                    241: u'n', 242: u'o', 243: u'o', 244: u'o', 245: u'o', 246: u'o',
                    248: u'o', 249: u'u', 250: u'u', 251: u'u', 252: u'u', 253: u'y',
                    255: u'y'}


    def split(self, text):
        """Return a list with the words of text"""
        return [word for word in self.tokens.split(text) if word != '']

    def strip_tags(self,text):
        """Replace any tag for an space"""
        return self.tags.sub(' ',text)

    def entity_to_char(self, text):
        """Swap accents code in HTML to accents characters"""
        name_func = '(Text.swap_cod_html_to_char) '

        cods = self.cod_html.findall(text)
        cods = set(cods)
        for cod in cods:
            cod_unicode = name2codepoint.get(cod)
            if cod_unicode:
                try:
                    text = text.replace('&%s;'%(cod), unichr(cod_unicode).encode('utf-8'))
                except Exception, msg:
                    logging.error('%sErro ao trocar os chars acentuados em HTML(1): %s'%(name_func, msg))

        cods = self.cod_unicode_html.findall(text)
        cods = set(cods)
        for cod in cods:
            if cod.isdigit():
                try:
                    text = text.replace('&#%s;'%(cod), unichr(int(cod)).encode('utf-8'))
                except Exception, msg:
                    logging.error('%sErro ao trocar os chars acentuados em HTML(2): %s'%(name_func, msg))

        for cod in self.cods:
            text = text.replace(cod, self.cods[cod])

        return text

    swap_cod_html_to_char = entity_to_char

    def to_ascii(self, text):
        """Return 'text' without accents characters"""

        text = text.decode('utf-8', 'ignore') # unicode
        text = text.translate(self.no_accents)
        text = text.encode('utf-8', 'ignore')
        return text

    swap_no_accents = to_ascii

    def remove_punctuaction(self,text):
        text = self.tokens.sub(' ', text)
        text = self.double_space.sub(' ',text)
        return text.strip()

    def set_encode(self, text, encode='iso-8859-1'):
        """Encode the text to utf-8. The default decode is iso-8859-1"""
        name_func = '(Text.set_encode) '

        try:
            text_utf8 = text.decode(encode, 'ignore').encode('utf-8', 'ignore')
        except LookupError, msg:
            logging.error('%sErro ao fazer encoding: %s'%(name_func, msg))
            text_utf8 = text.decode('iso-8859-1', 'ignore').encode('utf-8', 'ignore')

        return text_utf8

def dumps(obj):
    '''Return the encoded-serializated'''
    return encodestring(cPickle.dumps(obj))

def loads(str_):
    '''Return a object deserializate-uncoded'''
    return cPickle.loads(decodestring(str_))
