#!/usr/bin/env python2

"""
Use --help for info.
"""

from os import listdir, getcwd
from os.path import isdir, join, exists
from re import sub
from shutil import move
from sys import argv, stdout


extensions = {'.jpg', '.png', '.gif', '.mp3', '.mp4', '.txt', '.pdf'}


def clean_name(name):
	was_hidden = name.startswith('.')
	name = name.replace('@', '-at-')
	name = sub(r'\s', '_', name)
	name = sub(r'[^a-zA-Z0-9._\-]', '', name)
	name = sub(r'[^a-zA-Z0-9]*$', '', name)
	name = sub(r'^[^a-zA-Z0-9.]*', '', name)
	name = sub(r'\.\.+', '.', name)
	name = sub(r'[_-]*_[_-]+', '-', name)
	name = sub(r'--+', '-', name)
	for ext in extensions:
		if name.lower().endswith(ext) and not name.endswith(ext):
			name = name[:-len(ext)] + ext
	if name.startswith('.') and not was_hidden:
		name = 'f' + name
	return name


def test_clean_name():
	assert clean_name('a b.txt') == 'a_b.txt'
	assert clean_name('a@b.txt') == 'a-at-b.txt'
	assert clean_name('a_--_b') == 'a-b'
	assert clean_name('a--b') == 'a-b'
	assert clean_name('a-  b') == 'a-b'
	assert clean_name('a  -b') == 'a-b'
	assert clean_name('tt-_.') == 'tt'
	assert clean_name('.git') == '.git'
	assert clean_name('file.JPG') == 'file.jpg'
	assert clean_name('file.jpg') == 'file.jpg'
	assert clean_name('file.Jpg') == 'file.jpg'
	assert clean_name('file.PDF') == 'file.pdf'
	assert clean_name('###.PDF') == 'f.pdf'
	assert clean_name('.PDF') == '.pdf'
	assert clean_name('hello___there  w0rld!!.PDF') == 'hello-there-w0rld.pdf'
	print('test completed')


class Stats(object):
	def __init__(self):
		self.total = 0
		self.changed = 0
	def report(self):
		stdout.write('changing {:d} of {:d} files\n'.format(self.changed, self.total))


def fix_dir_rec(do=False):
	stats = Stats()
	fix_files_for_dir(dir=getcwd(), stats=stats, do=do)
	stats.report()


def do_move(dir, old, new, do):
	stdout.write('{:s} -> {:s}\n'.format(old, new))
	if exists(join(dir, new)):
		stdout.write('ERROR: {:s} cannot be moved to {:s} because it exists\n'.format(old, new))
		return
	if do:
		move(join(dir, old), join(dir, new))


def fix_files_for_dir(dir, stats, do):
	for oldname in listdir(dir):
		stats.total += 1
		newname = clean_name(oldname)
		if len(newname) <= 2:
			stdout.write('ERROR: {:s} converted to {:s} is too short\n'.format(oldname, newname))
			continue
		if oldname == newname:
			# print(newname)
			continue
		stats.changed += 1
		do_move(dir, oldname, newname, do=do)
	for name in listdir(dir):
		if isdir(join(dir, name)):
			# print('  dir: ' + dir + '/' + name)
			fix_files_for_dir(join(dir, name), stats, do=do)


if __name__ == '__main__':
	do = '--do' in argv[1:] or '-f' in argv[1:]
	test = '--test' in argv[1:]
	help = '--help' in argv[1:] or '-h' in argv[1:]
	if help:
		stdout.write(
			'\nThis script recursively finds files which have names that contain\n'
			'special characters, spaces or other inconvenient symbols. These\n'
			'are then renamed to stripped versions. Some extensions are also\n'
			'converted to lowercase.\n\n'
			'Example: \'hello___there  w0rld!!.PDF\' becomes \'hello-there-w0rld.pdf\'\n\n'
			'Without any arguments, prints the files to be renamed, without\n'
			'renaming them. Use --do to actually execute.\n\n')
		exit()
	if test:
		test_clean_name()
	if not do:
		stdout.write('dry run; use --do to execute\n')
	fix_dir_rec(do=do)


