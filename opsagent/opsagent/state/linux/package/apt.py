'''
apt repo and pkg

@author: Peng Zhao (peng@mc2.io)
'''

class APTrepo(File):

	def __init__(self, name, content):
		self.__name = name
		self.__content = content

	def present(self):
		try:
		except:
			pass

	def absent(self):
		try:
		except:
			pass

class APTpkg(Command):

	def __init__(self, pkgs, fromrepo=None, debconf=None, verify_gpg=False):
		self.__pkgs		= pkgs
		self.__fromrepo	= fromrepo
		self.__debconf	= debconf
		self.__verify_gpg = verify_gpg

	def present(self):
		try:
			result = _find_install_targets(name, version, pkgs, sources,
										   fromrepo=fromrepo, **kwargs)
			try:
				desired, targets = result
			except ValueError:
				# _find_install_targets() found no targets or encountered an error
				return result
		
			# Remove any targets that are already installed, to avoid upgrading them
			if pkgs:
				pkgs = [dict([(x, y)]) for x, y in targets.iteritems()]
			elif sources:
				sources = [x for x in sources if x.keys()[0] in targets]
		
			#if __opts__['test']:
			#	if targets:
			#		if sources:
			#			summary = ', '.join(targets)
			#		else:
			#			summary = ', '.join([_get_desired_pkg(x, targets)
			#								 for x in targets])
			#		comment = 'The following packages are set to be ' \
			#				  'installed/updated: {0}.'.format(summary)
			#	else:
			#		comment = ''
			#	return {'name': name,
			#			'changes': {},
			#			'result': None,
			#			'comment': comment}
		
			comment = []
			pkg_ret = self.__install(name,
											  refresh=refresh,
											  version=version,
											  fromrepo=fromrepo,
											  skip_verify=skip_verify,
											  pkgs=pkgs,
											  sources=sources,
											  **kwargs)
			if isinstance(pkg_ret, dict):
				changes = pkg_ret
			elif isinstance(pkg_ret, basestring):
				changes = {}
				comment.append(pkg_ret)
			else:
				changes = {}
		
			if sources:
				modified = [x for x in changes.keys() if x in targets]
				not_modified = [x for x in desired if x not in targets]
				failed = [x for x in targets if x not in modified]
			else:
				ok, failed = \
					_verify_install(
						desired, __salt__['pkg.list_pkgs'](
							versions_as_list=True, **kwargs
						)
					)
				modified = [x for x in ok if x in targets]
				not_modified = [x for x in ok if x not in targets]
		
			if modified:
				if sources:
					summary = ', '.join(modified)
				else:
					summary = ', '.join([_get_desired_pkg(x, desired)
										 for x in modified])
				if len(summary) < 20:
					comment.append('The following packages were installed/updated: '
								   '{0}.'.format(summary))
				else:
					comment.append(
						'{0} targeted package{1} {2} installed/updated.'.format(
							len(modified),
							's' if len(modified) > 1 else '',
							'were' if len(modified) > 1 else 'was'
						)
					)
		
			if not_modified:
				if sources:
					summary = ', '.join(not_modified)
				else:
					summary = ', '.join([_get_desired_pkg(x, desired)
										 for x in not_modified])
				if len(not_modified) <= 20:
					comment.append('The following packages were already installed: '
								   '{0}.'.format(summary))
				else:
					comment.append(
						'{0} targeted package{1} {2} already installed.'.format(
							len(not_modified),
							's' if len(not_modified) > 1 else '',
							'were' if len(not_modified) > 1 else 'was'
						)
					)
		
			if failed:
				if sources:
					summary = ', '.join(failed)
				else:
					summary = ', '.join([_get_desired_pkg(x, desired)
										 for x in failed])
				comment.insert(0, 'The following packages failed to '
								  'install/update: {0}.'.format(summary))
				return {'name': name,
						'changes': changes,
						'result': False,
						'comment': ' '.join(comment)}
			else:
				return {'name': name,
						'changes': changes,
						'result': True,
						'comment': ' '.join(comment)}

		except:
			pass

	def absent(self):
		try:
		except:
			pass

	def __update(self):
		try:
			ret = {}
			out = self.__run_stdout('apt-get -q update', output_loglevel='debug')
			for line in out.splitlines():
				cols = line.split()
				if not cols:
					continue
				ident = ' '.join(cols[1:])
				if 'Get' in cols[0]:
					# Strip filesize from end of line
					ident = re.sub(r' \[.+B\]$', '', ident)
					ret[ident] = True
				elif cols[0] == 'Ign':
					ret[ident] = False
				elif cols[0] == 'Hit':
					ret[ident] = None
			return ret
		except:
			pass

	def __install(self, update=False, debconf=None):
		try:
			if update:	self.__update()
			if debconf:	__salt__['debconf.set_file'](debconf)

			pkg_params, pkg_type = __salt__['pkg_resource.parse_targets'](name,
																		  pkgs,
																		  sources,
																		  **kwargs)
		
			# Support old "repo" argument
			repo = kwargs.get('repo', '')
			if not fromrepo and repo:
				fromrepo = repo
		
			old = list_pkgs()
		
			downgrade = False
			if pkg_params is None or len(pkg_params) == 0:
				return {}
			elif pkg_type == 'file':
				cmd = ['dpkg', '-i', '--force-confold']
				if skip_verify:
					cmd.append('--force-bad-verify')
				cmd.extend(pkg_params)
			elif pkg_type == 'repository':
				if pkgs is None and kwargs.get('version') and len(pkg_params) == 1:
					# Only use the 'version' param if 'name' was not specified as a
					# comma-separated list
					pkg_params = {name: kwargs.get('version')}
				targets = []
				for param, version_num in pkg_params.iteritems():
					if version_num is None:
						targets.append(param)
					else:
						cver = old.get(param)
						if cver is not None \
								and salt.utils.compare_versions(ver1=version_num,
																oper='<',
																ver2=cver,
																cmp_func=version_cmp):
							downgrade = True
						targets.append('{0}={1}'.format(param, version_num.lstrip('=')))
				if fromrepo:
					log.info('Targeting repo {0!r}'.format(fromrepo))
				cmd = ['apt-get', '-q', '-y']
				if downgrade or kwargs.get('force_yes', False):
					cmd.append('--force-yes')
				cmd = cmd + ['-o', 'DPkg::Options::=--force-confold']
				cmd = cmd + ['-o', 'DPkg::Options::=--force-confdef']
				if skip_verify:
					cmd.append('--allow-unauthenticated')
				if fromrepo:
					cmd.extend(['-t', fromrepo])
				cmd.append('install')
				cmd.extend(targets)
		
			self.__run(cmd, env=kwargs.get('env'), python_shell=False, output_loglevel='debug')
			__context__.pop('pkg.list_pkgs', None)
			new = list_pkgs()
			return salt.utils.compare_dicts(old, new)
		except:
			pass

class Command(ojbect):

	def __run_stdout(self):
		ret = _run(cmd,
				   runas=runas,
				   cwd=cwd,
				   stdin=stdin,
				   shell=shell,
				   python_shell=python_shell,
				   env=env,
				   clean_env=clean_env,
				   template=template,
				   rstrip=rstrip,
				   umask=umask,
				   output_loglevel=output_loglevel,
				   quiet=quiet,
				   timeout=timeout,
				   reset_system_locale=reset_system_locale,
				   saltenv=saltenv)
	
		lvl = _check_loglevel(output_loglevel, quiet)
		if lvl is not None:
			if ret['retcode'] != 0:
				if lvl < LOG_LEVELS['error']:
					lvl = LOG_LEVELS['error']
				log.error(
					'Command {0!r} failed with return code: {1}'
					.format(cmd, ret['retcode'])
				)
			if ret['stdout']:
				log.log(lvl, 'stdout: {0}'.format(ret['stdout']))
			if ret['stderr']:
				log.log(lvl, 'stderr: {0}'.format(ret['stderr']))
		return ret['stdout']

	def __run(self):
		#if salt.utils.is_true(quiet):
		#	salt.utils.warn_until(
		#		'Lithium',
		#		'The \'quiet\' option is deprecated and will be removed in the '
		#		'\'Lithium\' Salt release. Please use output_loglevel=quiet '
		#		'instead.'
		#	)
	
		# Set the default working directory to the home directory of the user
		# salt-minion is running as. Defaults to home directory of user under which
		# the minion is running.
		if not cwd:
			cwd = os.path.expanduser('~{0}'.format('' if not runas else runas))
	
			# make sure we can access the cwd
			# when run from sudo or another environment where the euid is
			# changed ~ will expand to the home of the original uid and
			# the euid might not have access to it. See issue #1844
			if not os.access(cwd, os.R_OK):
				cwd = '/'
				#if salt.utils.is_windows():
				#	cwd = os.tempnam()[:3]
		else:
			# Handle edge cases where numeric/other input is entered, and would be
			# yaml-ified into non-string types
			cwd = str(cwd)
	
		#if not salt.utils.is_windows():
		#	if not os.path.isfile(shell) or not os.access(shell, os.X_OK):
		#		msg = 'The shell {0} is not available'.format(shell)
		#		raise CommandExecutionError(msg)
	
		#if shell.lower().strip() == 'powershell':
		#	# If we were called by script(), then fakeout the Windows
		#	# shell to run a Powershell script.
		#	# Else just run a Powershell command.
		#	stack = traceback.extract_stack(limit=2)
	
		#	# extract_stack() returns a list of tuples.
		#	# The last item in the list [-1] is the current method.
		#	# The third item[2] in each tuple is the name of that method.
		#	if stack[-2][2] == 'script':
		#		cmd = 'Powershell -File ' + cmd
		#	else:
		#		cmd = 'Powershell ' + cmd
		# munge the cmd and cwd through the template
		(cmd, cwd) = _render_cmd(cmd, cwd, template, saltenv)
	
		ret = {}
	
		if not env:
			env = {}
		elif isinstance(env, basestring):
			try:
				env = yaml.safe_load(env)
			except yaml.parser.ParserError as err:
				log.error(err)
				env = {}
		if not isinstance(env, dict):
			log.error('Invalid input: {0}, must be a dict or '
					  'string - yaml represented dict'.format(env))
			env = {}
	
		#if runas and salt.utils.is_windows():
		#	# TODO: Figure out the proper way to do this in windows
		#	msg = 'Sorry, {0} does not support runas functionality'
		#	raise CommandExecutionError(msg.format(__grains__['os']))
	
		if runas:
			# Save the original command before munging it
			try:
				pwd.getpwnam(runas)
			except KeyError:
				raise CommandExecutionError(
					'User {0!r} is not available'.format(runas)
				)
			try:
				# Getting the environment for the runas user
				# There must be a better way to do this.
				py_code = 'import os, json;' \
						  'print(json.dumps(os.environ.__dict__))'
				if __grains__['os'] in ['MacOS', 'Darwin']:
					env_cmd = ('sudo -i -u {1} -- "{2}"'
							   ).format(shell, runas, sys.executable)
				elif __grains__['os'] in ['FreeBSD']:
					env_cmd = ('su - {1} -c "{0} -c \'{2}\'"'
							   ).format(shell, runas, sys.executable)
				else:
					env_cmd = ('su -s {0} - {1} -c "{2}"'
							   ).format(shell, runas, sys.executable)
				env_json = subprocess.Popen(
					env_cmd,
					shell=python_shell,
					stdin=subprocess.PIPE,
					stdout=subprocess.PIPE
				).communicate(py_code)[0]
				env_json = (filter(lambda x: x.startswith('{') and x.endswith('}'),
								   env_json.splitlines()) or ['{}']).pop()
				env_runas = json.loads(env_json).get('data', {})
				env_runas.update(env)
				env = env_runas
			except ValueError:
				raise CommandExecutionError(
					'Environment could not be retrieved for User {0!r}'.format(
						runas
					)
				)
	
		if _check_loglevel(output_loglevel, quiet) is not None:
			# Always log the shell commands at INFO unless quiet logging is
			# requested. The command output is what will be controlled by the
			# 'loglevel' parameter.
			log.info(
				'Executing command {0!r} {1}in directory {2!r}'.format(
					cmd, 'as user {0!r} '.format(runas) if runas else '', cwd
				)
			)
	
		if reset_system_locale is True:
			#if not salt.utils.is_windows():
			#	# Default to C!
			#	# Salt only knows how to parse English words
			#	# Don't override if the user has passed LC_ALL
			env.setdefault('LC_ALL', 'C')
			#else:
			#	# On Windows set the codepage to US English.
			#	cmd = 'chcp 437 > nul & ' + cmd
	
		if clean_env:
			run_env = env
	
		else:
			run_env = os.environ.copy()
			run_env.update(env)
	
		kwargs = {'cwd': cwd,
				  'shell': python_shell,
				  'env': run_env,
				  'stdin': str(stdin) if stdin is not None else stdin,
				  'stdout': stdout,
				  'stderr': stderr,
				  'with_communicate': with_communicate}
	
		if umask:
			try:
				_umask = int(str(umask).lstrip('0'), 8)
				if not _umask:
					raise ValueError('Zero umask not allowed.')
			except ValueError:
				msg = 'Invalid umask: \'{0}\''.format(umask)
				raise CommandExecutionError(msg)
		else:
			_umask = None
	
		if runas or umask:
			kwargs['preexec_fn'] = functools.partial(
					_chugid_and_umask,
					runas,
					_umask)
	
		#if not salt.utils.is_windows():
		#	# close_fds is not supported on Windows platforms if you redirect
		#	# stdin/stdout/stderr
		#	if kwargs['shell'] is True:
		#		kwargs['executable'] = shell
		#	kwargs['close_fds'] = True
	
		if not os.path.isabs(cwd) or not os.path.isdir(cwd):
			raise CommandExecutionError(
				'Specified cwd {0!r} either not absolute or does not exist'
				.format(cwd)
			)
	
		# This is where the magic happens
		try:
			proc = salt.utils.timed_subprocess.TimedProc(cmd, **kwargs)
		except (OSError, IOError) as exc:
			raise CommandExecutionError('Unable to run command "{0}" with the context "{1}", reason: {2}'.format(cmd, kwargs, exc))
	
		try:
			proc.wait(timeout)
		except TimedProcTimeoutError as exc:
			ret['stdout'] = str(exc)
			ret['stderr'] = ''
			ret['pid'] = proc.process.pid
			# ok return code for timeouts?
			ret['retcode'] = 1
			return ret
	
		out, err = proc.stdout, proc.stderr
	
		if rstrip:
			if out is not None:
				out = out.rstrip()
			if err is not None:
				err = err.rstrip()
	
		ret['stdout'] = out
		ret['stderr'] = err
		ret['pid'] = proc.process.pid
		ret['retcode'] = proc.process.returncode
		try:
			__context__['retcode'] = ret['retcode']
		except NameError:
			# Ignore the context error during grain generation
			pass
		return ret
