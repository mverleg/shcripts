
from os.path import basename
from sys import argv, stderr
from json import loads

if len(argv) < 2:
	stderr.write('please provide the path to a json file\n')
	exit(1)

if len(argv) < 3:
	stderr.write('you can provide keys/indices to explore the json data\n')


def node(data, keys, levels):
	for key in keys:
		if isinstance(data, dict):
			cnt = len(data)
			try:
				data = data[key]
				levels.append('{' + key + '/' + str(cnt) + '}')
			except:
				levels.append('{' + key + '/' + str(cnt) + '} !! NO KEY')
				break
		elif isinstance(data, list):
			cnt = len(data)
			try:
				index = int(key)
			except:
				levels.append('!! USE NR [' + key + '/' + str(cnt) + ']')
			else:
				try:
					data = data[index]
					levels.append('[' + str(index) + '/' + str(cnt) + ']')
				except:
					levels.append('[' + str(index) + '/' + str(cnt) + '] !! NO INDX')
					break
		else:
			stderr.write('can\'t navigate deeper at {0}\n'.format(key))
			break
	return data


def deep_preview(item):
	if isinstance(item, dict):
		things = list(shallow_preview(val) for key, val in list(item.items())[:6])
		return '{dict/' + str(len(item)) + ': ' + ', '.join(things) + (', ...' + str(len(item) - 6) + ' more...]' if len(item) > 6 else '}')
	elif isinstance(item, list):
		things = list(shallow_preview(thing) for thing in item[:6])
		return '[list/' + str(len(item)) + ': ' + ', '.join(things) + (', ...' + str(len(item) - 6) + ' more...]' if len(item) > 6 else ']')
	return shallow_preview(item)


def shallow_preview(item):
	if isinstance(item, dict):
		return '{dict/' + str(len(item)) + '}'
	elif isinstance(item, list):
		return '[list/' + str(len(item)) + ']'
	elif isinstance(item, str):
		if len(item) > 30:
			return('"' + item[:19] + '...' + item[-6:] + '"')
		return item
	return str(item)


def show(data):
	if isinstance(data, dict):
		print('{dictionary} with ' + str(len(data)) + ' items')
		for key, val in list(data.items())[:50]:
			print('  {0} :\t{1}'.format(key, deep_preview(val)))
		if len(data) > 50: print('... and ' + str(len(data) - 50) + ' more ...')
	elif isinstance(data, list):
		print('[list] with {0} items'.format(len(data)))
		for index, val in enumerate(data[:50]):
			print('  {0} :\t{1}'.format(index, deep_preview(val)))
		if len(data) > 50: print('... and ' + str(len(data) - 50) + ' more ...')
	else:
		print(data)

if len(argv) < 2 or argv[1] == '-h':
	print('JSON explorer; can output json data structures, zoomed to a particular sub-element.')
	print('First argument should be the path to the json file.')
	print('Further arguments can be indices to zoom into the structure.')
	print('E.g. json_explorer.py file.json "conf" "apps" "3" would print the contents of data[\'conf\'][\'apps\'][\'3\']')
	exit()

data = loads(open(argv[1]).read())
levels = []
zoom = node(data, argv[2:], levels)
print('\n{0} >> {1}\n'.format(basename(argv[1]), ' > '.join(levels)))
show(zoom)
print('')


