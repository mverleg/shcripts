
"""
Git is not great with storing large files, and often you don't need history in those cases.

So why not use some wrapping code for rsync instead? That's what this does.
"""

from argparse import ArgumentParser
from copy import copy
from os import getcwd
from re import match
from sys import stderr, argv, stdout
from os.path import isdir, join, dirname, isfile
from subprocess import Popen, PIPE


remote_file_name = '.filesync_remote'
ignore_file_name = '.filesync_ignore'
sync_cmd = ['rsync', '--archive', '--recursive', '--hard-links', '--itemize-changes',
	'--group', '--compress', '--rsh=ssh', '--exclude={0:s}'.format(remote_file_name),]


def parse_args(args):
	"""
	Parse the command line arguments and return the results.
	"""
	parser = ArgumentParser()
	parser.add_argument('-v', '--verbose', dest='verbose', action='count', default=0, help='add this flag to get more output')
	parser.add_argument('--notest', dest='do_test', action='store_false', default=True, help='skip some tests')
	subparsers = parser.add_subparsers(dest='action')
	pull_parser = subparsers.add_parser('pull')
	# foo_parser.add_argument('-c', '--count')
	push_parser = subparsers.add_parser('push')
	init_parser = subparsers.add_parser('init')
	init_parser.add_argument(dest='remote', help='The remote, format `ssh_host:/path/to/dir`')
	if not args:
		args = ['-h']
	opts = parser.parse_args(args)
	return opts


def parse_remote(remote_txt, allow_local=True):
	"""
	Split `remote_host:/path/to/dir` into `remote_host` and `/path/to/dir`
	"""
	if ':' not in remote_txt:
		if not allow_local:
			stderr.write('remote "{0:s}" does not seem to contain a host\n'.format(remote_txt))
			return None, None
		return None, remote_txt
	remote_match = match(r'^([^:]*[^:/])/?:([^:]*[^:/])/?$', remote_txt)
	if not remote_match:
		stderr.write('Contents of `.filesy_remote` should be only a string of the format ' \
		'`remote_host:/path/to/dir` (got "{0:s}")\n'.format(remote_txt))
		return None, None
	return remote_match.groups()


def read_remote(dirpth, verbose=0):
	"""
	Search for the file that contains information about the remote, parse it and return the result.
	"""
	assert isdir(dirpth), '{0:s} is not an existing directory'.format(dirpth)
	for depth in range(256):
		pth = join(dirpth, remote_file_name)
		if isfile(pth):
			with open(pth, 'r') as fh:
				remote_str = fh.read().strip()
			remote_host, remote_path = parse_remote(remote_str)
			if not remote_path:
				return None
			if verbose:
				stdout.write('root directory: {0:s}\n'.format(dirpth))
				stdout.write('remote: {0:s}:{1:s}\n'.format(remote_host, remote_path))
			return dirpth, remote_host, remote_path
		elif dirpth == dirname(dirpth):
			stderr.write('Don\'t know which remote host to use\n')
			stderr.write('Create a `.filesy_remote` in the root directory\n')
			stderr.write('Format: `remote_host:/path/to/dir`\n')
			return
		else:
			dirpth = dirname(dirpth)
	return StopIteration


def test_remote(remote_host, remote_path, verbose=0):
	"""
	Test that logging in to the remote works and that the directory exists.
	"""
	cmd = ['ssh', remote_host] + "if [ -d \'{0:s}\' ]; then echo \'yes\'; else echo \'no\'; fi".format(remote_path).split()
	if verbose:
		stdout.write(' '.join(cmd) + '\n')
	proc = Popen(cmd, stdin=None, stdout=PIPE, stderr=PIPE)
	out, err = proc.communicate()
	if out.strip() == 'yes':
		return True
	elif out.strip() == 'no':
		return False
	else:
		err = '(no output received)'
	if err:
		stderr.write('there was a problem while connecting to the remote {0:s}:\n'.format(remote_host))
		stderr.write(str(err) + '\n')
		return


def init(remote, local_dir=None, do_test=True, verbose=0):
	remote_host, remote_path = parse_remote(remote)
	local_dir = local_dir or getcwd()
	pth = join(local_dir, remote_file_name)
	if isfile(pth):
		stderr.write('{0:s} already exists; not making any changes\n'.format(remote_file_name))
		return
	if do_test:
		if not test_remote(remote_host, remote_path, verbose=verbose):
			stderr.write('directory `{1:s}` not found or could not log in to host `{0:s}`\n'.format(remote_host, remote_path))
	with open(pth, 'w+') as fh:
		fh.write('{0:s}:{1:s}'.format(remote_host, remote_path))
	stdout.write('sync directory initialized with remote directory {1:s} on host {0:s}\n'.format(remote_host, remote_path))


def push(local_dir, remote_host, remote_dir, verbose=0):
	"""
	Send the local files to the remote.
	"""
	ignore_file_pth = join(local_dir, ignore_file_name)
	transmit_dir(source_dir=local_dir, target_dir='{0:s}:{1:s}'.format(remote_host, remote_dir),
		ignore_file_pth=ignore_file_pth, verbose=verbose)


#todo: show an error when locked
#todo: also use flock locally


def pull(local_dir, remote_host, remote_dir, verbose=0):
	"""
	Get the remote files to the local directory.
	"""
	ignore_file_pth = join(local_dir, ignore_file_name)
	transmit_dir(source_dir='{0:s}:{1:s}'.format(remote_host, remote_dir), target_dir=local_dir,
		ignore_file_pth=ignore_file_pth, lock_file='{0:s}'.format(join(remote_dir, '.lock~')), verbose=verbose)


def transmit_dir(source_dir, target_dir, ignore_file_pth='', remote_lock='exclusive', lock_file='/tmp/rsync_lock~', verbose=0):
	"""
	Send everything from `source_dir` to `target_dir`.
	"""
	assert not source_dir.endswith('/') and not target_dir.endswith('/')
	assert remote_lock in ['exclusive', 'shared', None]
	cmd = copy(sync_cmd)
	if isfile(ignore_file_pth):
		cmd += ['--exclude-from', ignore_file_pth]
	if remote_lock:
		cmd += ('--rsync-path=\'function lock_rsync () { flock --{0:s} --timeout=5 "{1:s}" '
			'--command "rsync $*"; }; lock_rsync\''.format(remote_lock, lock_file))
	cmd += ['{0:s}/'.format(source_dir), '{0:s}'.format(target_dir)]
	if verbose:
		stdout.write(' '.join(cmd) + '\n')
	proc = Popen(cmd, stdin=None, stdout=PIPE, stderr=PIPE)
	for line in iter(proc.stdout.readline, b''):
		stdout.write(line.split(' ', 1)[-1])
	out, err = proc.communicate()
	if err:
		stderr.write('there was a problem while transmitting from {0:s} to {1:s}:\n'.format(source_dir, target_dir))
		stderr.write(str(err) + '\n')
		return


def main(args):
	opts = parse_args(args)
	if opts.action == 'init':
		print('init!')
		init(opts.remote, do_test=opts.do_test, verbose=opts.verbose)
		return
	remote = read_remote(getcwd(), verbose=opts.verbose)
	if not remote:
		exit(1)
	local_path, remote_host, remote_path = remote
	if opts.do_test:
		if not test_remote(remote_host, remote_path, verbose=opts.verbose):
			stderr.write('directory `{1:s}` not found or could not log in to host `{0:s}`\n'.format(remote_host, remote_path))
			exit(2)
	if opts.action == 'push':
		push(local_path, remote_host, remote_path, verbose=opts.verbose)
	if opts.action == 'pull':
		pull(local_path, remote_host, remote_path, verbose=opts.verbose)


if __name__ == '__main__':
	main(argv[1:])


