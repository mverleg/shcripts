
#todo: test if it works locally
#todo: refactor delete option into separate commands?
#todo: add two-way sync (possibly just sequence of pull & push)
#todo: add clone

"""
Git is not great with storing large files, and often you don't need history in those cases.

So why not use some wrapping code for rsync instead? That's what this does.
"""

from argparse import ArgumentParser
from copy import copy
from fcntl import flock, LOCK_EX, LOCK_SH, LOCK_UN
from os import getcwd, remove
from re import match
from sys import stderr, argv, stdout
from os.path import isdir, join, dirname, isfile, exists
from subprocess import Popen, PIPE


remote_file_name = '.filesync_remote'
ignore_file_name = '.filesync_ignore'
lock_file_name = '.rsync.lock~'
sync_cmd = ['rsync', '--archive', '--recursive', '--hard-links', '--itemize-changes',
	'--group', '--compress', '--rsh=ssh', '--exclude={0:s}'.format(remote_file_name),
	'--exclude={0:s}'.format(lock_file_name),]


def parse_args(args):
	"""
	Parse the command line arguments and return the results.
	"""
	parser = ArgumentParser()
	parser.add_argument('-v', '--verbose', dest='verbose', action='count', default=0, help='Add this flag to get more output.')
	parser.add_argument('--notest', dest='do_test', action='store_false', default=True, help='Skip some tests (faster but fewer warnings).')
	subparsers = parser.add_subparsers(dest='action')
	pull_parser = subparsers.add_parser('pull', help='Download changes from the remote server to the local directory (deleting files is optional).')
	pull_parser.add_argument('-d', '--delete', dest='delete', action='store_true', default=False,
		help='Delete local files that do not exist on the remote.')
	# foo_parser.add_argument('-c', '--count')
	push_parser = subparsers.add_parser('push', help='Send local changes to the remote server (deleting files is optional).')
	push_parser.add_argument('-d', '--delete', dest='delete', action='store_true', default=False,
		help='Delete files on the remote that do not exist locally.')
	init_parser = subparsers.add_parser('init', help='Turn the current directory into a repository (provide `host:directory`).')
	init_parser.add_argument(dest='remote', help='The remote, format `ssh_host:/path/to/dir`')
	unlock_parser = subparsers.add_parser('unlock', help='After you make sure no other sync processes are running locally '
		'or remotely, you can use this to force releasing locks.')
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


def test_remote(remote_host, remote_path, verbose=0):
	"""
	Test that logging in to the remote works and that the directory exists.
	"""
	cmd = ['ssh', remote_host, ('"if [ -d \"{0:s}\" ]; then flock --nonblock \"{1:s}\" --command \"\"; '
		'if [ \"$?\" == \"0\" ]; then echo \"ok\"; else echo \"locked\"; fi; '
		'else echo \"nonexistent\"; fi;"').format(remote_path, join(remote_path, lock_file_name))]
	if verbose:
		stdout.write(' '.join(cmd) + '\n')
	proc = Popen(' '.join(cmd), stdin=None, stdout=PIPE, stderr=PIPE, shell=True)
	out, err = [(val or b'').decode('utf8').strip() for val in proc.communicate()]
	if out == 'locked':
		stderr.write(('directory `{1:s}` is already locked on host `{0:s}`; another synchronization '
			'may be running; if not, use `unlock`.\n').format(remote_host, remote_path))
		return False
	elif out == 'nonexistent':
		stderr.write('directory `{1:s}` not found or could not log in to host `{0:s}`\n'.format(remote_host, remote_path))
		return False
	elif out == 'ok':
		return True
	else:
		err += ' no or incorrect output received: "{0:s}"'.format(out.replace(b'\n', b''))
	stderr.write('there was a problem while connecting to the remote {0:s}:\n'.format(remote_host))
	stderr.write(str(err) + '\n')
	return False


def init(remote, local_dir=None, do_test=True, verbose=0):
	"""
	Initialize the current directory as a 'repository', by making a `.filesync_remote` file.
	"""
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
	pth = join(local_dir, ignore_file_name)
	if not exists(pth):
		with open(pth, 'w+') as fh:
			fh.write('.git/\n')
	stdout.write('sync directory initialized with remote directory {1:s} on host {0:s}\n'.format(remote_host, remote_path))


def unlock(local_path, remote_host, remote_path, verbose=0):
	"""
	Release the locks locally and remotely by removing the lock files.
	Should only be used after making sure that no rsync process is running.
	"""
	unlock_local(local_path, verbose=verbose)
	unlock_remote(remote_host, remote_path, verbose=verbose)


def unlock_local(local_path, verbose=0):
	pth = join(local_path, lock_file_name)
	if exists(pth):
		stdout.write('removing lock file {0:s}\n'.format(pth))
		remove(pth)
	elif verbose:
		stdout.write('local directory not locked\n')


def unlock_remote(remote_host, remote_path, verbose=0):
	pth = join(remote_path, lock_file_name)
	cmd = ['ssh', remote_host, '"if [ -e "{0:s}" ]; then echo "removing lock file {0:s} on {1:s}"; rm -f "{0:s}"; {2:s} fi;"'
		.format(pth, remote_host, 'else echo "remote on {0:s} not locked";'.format(remote_host) if verbose else '')]
	if verbose:
		stdout.write(' '.join(cmd) + '\n')
	proc = Popen(' '.join(cmd), shell=True)
	proc.communicate()


def push(local_dir, remote_host, remote_dir, delete=False, verbose=0):
	"""
	Send the local files to the remote.
	"""
	ignore_file_pth = join(local_dir, ignore_file_name)
	transmit_dir(source_host=None, source_dir=local_dir, target_host=remote_host, target_dir=remote_dir,
		delete=delete, ignore_file_pth=ignore_file_pth, verbose=verbose)


def pull(local_dir, remote_host, remote_dir, delete=False, verbose=0):
	"""
	Get the remote files to the local directory.
	"""
	ignore_file_pth = join(local_dir, ignore_file_name)
	transmit_dir(source_host=remote_host, source_dir=remote_dir, target_host=None, target_dir=local_dir,
		delete=delete, ignore_file_pth=ignore_file_pth, verbose=verbose)


def transmit_dir(source_host, source_dir, target_host, target_dir, delete, ignore_file_pth='', verbose=0):
	"""
	Send everything from `source_dir` to `target_dir`.
	"""
	assert not source_dir.endswith('/') and not target_dir.endswith('/')
	cmd = copy(sync_cmd)
	if isfile(ignore_file_pth):
		cmd += ['--exclude-from={0:s}'.format(ignore_file_pth)]
	local_lock_type, remote_lock_type = (LOCK_EX, 'shared') if source_host else (LOCK_SH, 'exclusive')
	if source_host and not target_host:
		local_host, local_dir, remote_host, remote_dir  = target_host, target_dir, source_host, source_dir
	elif target_host and not source_host:
		local_host, local_dir, remote_host, remote_dir  = source_host, source_dir, target_host, target_dir
	else:
		raise NotImplementedError('The situation where neither or both source and target are remote, is not implemented.')
		#todo
	if delete:
		cmd += ['--delete']
	cmd += [('--rsync-path=\'function lock_rsync () {{ for target; do true; done; mkdir -p "$target"; '
		'flock --{0:s} --timeout=1 "{1:s}" --command "\\rsync $*"; }}; lock_rsync\'')
			.format(remote_lock_type, join(remote_dir, lock_file_name))]
	cmd += ['{0:s}:{1:s}/'.format(source_host or '', source_dir).lstrip(':'), '{0:s}:{1:s}'.format(target_host or '', target_dir).lstrip(':')]
	if verbose:
		stdout.write(' '.join(cmd) + '\n')
	with open(join(local_dir, lock_file_name), 'w+') as fh:
		flock(fh, local_lock_type)
		try:
			proc = Popen(' '.join(cmd), stdin=None, stdout=PIPE, stderr=PIPE, shell=True)
			for line in iter(proc.stdout.readline, b''):
				stdout.write(line.decode('utf8').split(' ', 1)[-1])
			out, err = proc.communicate()
		except KeyboardInterrupt:
			unlock_remote(remote_host, remote_dir, verbose=verbose)
			out, err = '', ''
		flock(fh, LOCK_UN)
	if err:
		stderr.write('there was a problem while transmitting from {0:s} to {1:s} :\n'.format(source_dir, target_dir))
		stderr.write(str(err) + '\n')
		return


def main(args):
	opts = parse_args(args)
	if opts.action == 'init':
		init(opts.remote, do_test=opts.do_test, verbose=opts.verbose)
		return
	remote = read_remote(getcwd(), verbose=opts.verbose)
	if not remote:
		exit(1)
	local_path, remote_host, remote_path = remote
	if opts.action == 'unlock':
		unlock(local_path, remote_host, remote_path, verbose=opts.verbose)
		return
	if opts.do_test:
		if not test_remote(remote_host, remote_path, verbose=opts.verbose):
			exit(2)
	if opts.action == 'push':
		push(local_path, remote_host, remote_path, delete=opts.delete, verbose=opts.verbose)
	if opts.action == 'pull':
		pull(local_path, remote_host, remote_path, delete=opts.delete, verbose=opts.verbose)


if __name__ == '__main__':
	main(argv[1:])


