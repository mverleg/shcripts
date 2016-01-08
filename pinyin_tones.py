# -*- coding: utf-8 -*-

"""
	Add tone marks to Pinyin-with-numbers
	
	Adapted from http://stackoverflow.com/a/21488584/723090.
	
		python pinyin_tones.py hi3hao3
		# hǐhǎo
"""

import re
from sys import argv


pinyinToneMarks = {
	u'a': u'āáǎà', u'e': u'ēéěè', u'i': u'īíǐì',
	u'o': u'ōóǒò', u'u': u'ūúǔù', u'ü': u'ǖǘǚǜ',
	u'A': u'ĀÁǍÀ', u'E': u'ĒÉĚÈ', u'I': u'ĪÍǏÌ',
	u'O': u'ŌÓǑÒ', u'U': u'ŪÚǓÙ', u'Ü': u'ǕǗǙǛ'
}


def convert_pinyin_callback(m):
	tone=int(m.group(3)) % 5
	r = m.group(1).replace(u'v', u'ü').replace(u'V', u'Ü')
	""" For multple vowels, use first one if it is a/e/o, otherwise use second one. """
	pos = 0
	if len(r) > 1 and not r[0] in 'aeoAEO':
		pos = 1
	if tone != 0:
		r = r[0:pos]+pinyinToneMarks[r[pos]][tone-1] + r[pos+1:]
	return r + m.group(2)


def convert_pinyin(s):
	return re.sub(ur'([aeiouüvÜ]{1,3})(n?g?r?)([012345])', convert_pinyin_callback, s, flags=re.IGNORECASE)


if __name__ == '__main__':
	if argv[1:]:
		original = u' '.join(argv[1:])
		print convert_pinyin(original)
	else:
		try:
			import pygtk
			pygtk.require('2.0')
			import gtk
		except ImportError as err:
			print('{0:s}\n\nneed gtk to read clipboard'.format(str(err)))
		clipboard = gtk.clipboard_get()
		original = clipboard.wait_for_text()
		new = convert_pinyin(original)
		clipboard.set_text(new)
		clipboard.store()
		print '[clipboard updated] %s' % new


