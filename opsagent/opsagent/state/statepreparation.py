'''
Madeira OpsAgent states preparator

@author: Michael
'''


# System imports
import os
import json
import hashlib

# Internal imports
from salt.state import State
from opsagent.exception import StatePrepareExcepton,OpsAgentException


class StatePreparation(object):

	ssh_key_type = ['ecdsa', 'ssh-rsa', 'ssh-dss']

	requisity_map = {
		# only for clear enviroment
		'package.gem.package' : {
			'package.pkg.package' : { 'name' : ['rubygems'] }
		},

		## only for clear enviroment(not check node version and so on, use nvm to control nodejs version)
		'package.npm.package' : {
			'package.pkg.package' : { 'name' : ['npm'] }
		},

		'package.pecl.package' : {
			'package.pkg.package' : { 'name' : ['php-pear'] }
		},

		'package.pip.package' : {
			'package.pkg.package' : { 'name' : ['python-pip'] }
		}
	}

	def __init__(self, config):

		self.pre_mapping = {
			'package.pkg.package'	:	self.__package,
			'package.apt.package'	:	self._package_apt_package,
			'package.yum.package'	:	self._package_yum_package,
			'package.gem.package'	:	self._package_gem_package,
			'package.npm.package'	:	self._package_npm_package,
			'package.pecl.package'	:	self._package_pecl_package,
			'package.pip.package'	:	self._package_pip_package,
			'package.zypper.package':	self._package_zypper_package,
			'package.yum.repo'		:	self._package_yum_repo,
			'package.apt.repo'		:	self._package_apt_repo,
			'package.gem.source'	:	self._package_gem_source,
			'path.file'				:	self._path_file,
			'path.dir'				:	self._path_dir,
			'path.symlink'			:	self._path_symlink,
			'scm.git'				:	self._scm_git,
			'scm.svn'				:	self._scm_svn,
			'scm.hg'				:	self._scm_hg,
			'service.supervisord'	:	self._service_supervisord,
			'service.sysvinit'		:	self._service_sysvinit,
			'service.upstart'		:	self._service_upstart,
			'sys.cmd'				:	self._sys_cmd,
			'sys.script'			:	self._sys_script,
			'sys.cron'				:	self._sys_cron,
			'sys.user'				:	self._sys_user,
			'sys.group'				:	self._sys_group,
			'sys.hostname'			:	self._sys_hostname,
			'sys.hosts'				:	self._sys_hosts,
			'sys.mount'				:	self._sys_mount,
			'sys.ntp'				:	self._sys_ntp,
			'sys.selinux'			:	self._sys_selinux,
			'system.ssh.auth'		:	self._system_ssh_auth,
			'system.ssh.known_host' :	self._system_ssh_known_host,
		}

		# init salt opts
		self._init_opts(config)

		# init state
		self._init_state()

		self.states = None

	def _init_opts(self, config):

		self._salt_opts = {
			'file_client':       'local',
			'renderer':          'yaml_jinja',
			'failhard':          False,
			'state_top':         'salt://top.sls',
			'nodegroups':        {},
			'file_roots':        {'base': [ ]},
			'state_auto_order':  False,
			'extension_modules': None,
			'id':                '',
			'pillar_roots':      '',
			'cachedir':          None,
			'test':              False,
		}

		# file roots
		for path in config['file_roots'].split(':'):
			# check and make path
			if not self.__mkdir(path):
				continue

			self._salt_opts['file_roots']['base'].append(path)

		if len(self._salt_opts['file_roots']['base']) == 0:
			print "ERROR: Missing file roots argument"
			## todo

		if not self.__mkdir(config['extension_modules']):
			print "ERROR: Missing extension modules argument"
			## todo

		self._salt_opts['extension_modules'] = config['extension_modules']

		if not self.__mkdir(config['cachedir']):
			print "ERROR: Missing cachedir argument"
			## todo
		self._salt_opts['cachedir'] = config['cachedir']

	def _init_state(self):
		"""
			Init salt state object.
		"""

		self.state = State(self._salt_opts)

	def transfer(self, step, module, parameter):
		"""
			Transfer the module json data to salt states.
		"""

		if not module:
			print "please input module"
			return

		if module not in self.pre_mapping:
			print "not supported module %s" % module
			return

		state = self.pre_mapping[module](module, parameter, None, step)
		if not state or not isinstance(state, dict):
			print "Transfer json to salt state failed"
			return

		self.states = state
		return state

	def exec_salt(self, step, module, parameter):
		"""
			Transfer and exec salt state.
			return result format: (result,err_log,out_log), result:True/False
		"""

		result = err_log = out_log = None

		# transfer
		state = self.transfer(step, module, parameter)
		if not state:
			err_log = "transfer salt state failed"
			print err_log
			return (False, err_log, out_log)

		ret = self.state.call_high(state)
		if ret:
			# parse the ret and return
			print json.dumps(ret, sort_keys=True,
				  indent=4, separators=(',', ': '))

			## set error and output log
			result = True
			for r_tag, r_value in ret.items():
				# error log and std out log
				if 'state_stderr' in r_value:
					err_log = r_value['state_stderr']
				if 'state_stdout' in r_value:
					out_log = r_value['state_stdout']

				if not r_value['result']:
					break

		else:
			out_log = "wait failed"

		return (result, err_log, out_log)

	## package
	def _package_yum_package(self, module, parameter, uid=None, step=None):
		"""
			Transfer yum package to salt state.
		"""
		return self.__package(module, parameter, uid, step)

	def _package_apt_package(self, module, parameter, uid=None, step=None):
		"""
			Transfer apt package to salt state.
		"""
		return self.__package(module, parameter, uid, step)

	def _package_gem_package(self, module, parameter, uid=None, step=None):
		"""
			Transfer gem package to salt state.
		"""
		return self.__package(module, parameter, uid, step)

	def _package_npm_package(self, module, parameter, uid=None, step=None):
		"""
			Transfer npm package to salt state.
		"""

		return self.__package(module, parameter, uid, step)

	def _package_pecl_package(self, module, parameter, uid=None, step=None):
		"""
			Transfer pecl package to salt state.
		"""
		return self.__package(module, parameter, uid, step)

	def _package_pip_package(self, module, parameter, uid=None, step=None):
		"""
			Transfer pip package to salt state.
		"""
		return self.__package(module, parameter, uid, step)

	def _package_zypper_package(self, module, parameter, uid=None, step=None):
		"""
			Transfer zypper package to salt state.
		"""
		return self.__package(module, parameter, uid, step)

	def __package(self, module, parameter, uid=None, step=None):
		"""
			Transfer package to salt state.
		"""
		pkg_state = {}

		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict) or 'name' not in parameter:
			print "invalid preparation states"
			return pkg_state

		if self.__check_module(module) != 0:
			print "invalid package type"
			return 2

		m_list = module.split('.')

		state_mapping = {}
		addin = {}

		# add requisity
		# requisities = []
		# if m_list[1] in ['gem', 'npm', 'pecl', 'pip']:
		# 	req_state = self.__get_requisity(module)
		# 	if req_state:
		# 		for req in req_state:
		# 			for req_tag, req_value in req.items():
		# 				pkg_state[req_tag] = req_value

		# 				requisities.append({ next(iter(req_value)) : req_tag })

		if m_list[1] in ['apt', 'yum']:
			m_list[1] = 'pkg'

		# get package name and verson
		for attr, value in parameter.items():
			if not value: continue

			if attr == 'name':
				if isinstance(value, dict):
					for name, version in value.items():
						state = 'installed'

						if version in ['latest', 'removed', 'purged']:
							state = version

						if state not in state_mapping:	state_mapping[state] = []

						if state == 'installed':
							if version:
								state_mapping[state].append({name:version})
							else:
								state_mapping[state].append(name)

						else:
							state_mapping[state].append(name)

				# support for requisity
				elif isinstance(value, list):
					state_mapping['installed'] = value

			else:

				addin[attr] = value

				if attr == 'verify_gpg':
					addin[attr] = True if value == 'True' else False

		for state, packages in state_mapping.items():
			if not packages: continue

			addin['names'] = packages

			pkg = [
				addin,
				state
			]

			# if requisities:
			# 	pkg.append({'require':requisities})

			tag = self.__get_tag(module, uid, step, 'pkgs', state)

			pkg_state[tag] = {
				m_list[1] : pkg
			}

		return pkg_state

	## repo, source
	def _package_yum_repo(self, module, parameter, uid=None, step=None):
		"""
			Transfer yum repository to salt state.
		"""
		return self.__repo(module, parameter, uid, step)

	def _package_apt_repo(self, module, parameter, uid=None, step=None):
		"""
			Transfer apt repository to salt state.
		"""
		return self.__repo(module, parameter, step)

	def _package_gem_source(self, module, parameter, uid=None, step=None):
		"""
			Transfer gem source to salt state.
		"""
		return self.__repo(module, parameter, step)

	def __repo(self, module, parameter, uid=None, step=None):
		"""
			Transfer repository to salt state.
		"""

		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			print "invalid preparation states"
			return 1

		if self.__check_module(module) != 0:
			print "invalid repository type"
			return 2

		m_list = module.split('.')
		type = m_list[1]

		repo_state = {}
		state = None

		# file
		if type in ['apt', 'yum']:
			filename = parameter['name']
			content  = parameter['content']
			if type == 'apt':
				if not filename.endswith('.list'):
					filename += '.list'
				path = '/etc/apt/sources.list.d/' + filename
			else:
				if not filename.endswith('repo'):
					filename += '.repo'
				path = '/etc/yum.repos.d/' + filename

			state = 'managed'

			tag = self.__get_tag('path.file', uid, step, path, state)

			repo_state = {
				tag	:	{
					'file'	:	[
						state,
						{
							'name'		:	path,
							'user'		:	'root',
							'group'		:	'root',
							'mode'		:	'644',
							'contents'	:	content,
						}
					]
				}
			}

		elif type == 'gem':

			# requisities = []

			# # add package requisity
			# req_state = self.__get_requisity('package.gem.package')
			# if req_state:
			# 	for req in req_state:
			# 		for req_tag, req_value in req.items():
			# 			repo_state[req_tag] = req_value

			# 			requisities.append({ next(iter(req_value)) : req_tag })

			# gem source
			if 'url' not in parameter or not parameter['url']:
				print "invalid parameters"
				return 3

			state = 'run'
			tag = self.__get_tag(module, uid, step, parameter['url'])

			cmd = [
				state,
				{
					'name'	: 'gem source --add ' + parameter['url'],
					'shell'	: '/bin/bash',
					'user'	: 'root',
					'group'	: 'root',
				}
			]

			# add requisity
			# if requisities:
			# 	cmd.append({ 'require' : requisities })

			repo_state[tag] = {
				'cmd' : cmd
			}

		##elif type == 'zypper'

		return repo_state

	## file, directory, symlink
	def _path_file(self, module, parameter, uid=None, step=None):
		"""
			Transfer file to salt state.
		"""
		return self.__file(module, parameter, uid, step)

	def _path_dir(self, module, parameter, uid=None, step=None):
		"""
			Transfer directory to salt state.
		"""
		return self.__file(module, parameter, uid, step)

	def _path_symlink(self, module, parameter, uid=None, step=None):
		"""
			Transfer symlink to salt state.
		"""
		return self.__file(module, parameter, uid, step)

	def __file(self, module, parameter, uid=None, step=None):
		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			print "invalid preparation states"
			return 1

		if self.__check_module(module) != 0:
			print "invalid file type"
			return 2

		m_list = module.split('.')
		type = m_list[1]

		addin = {}
		filename = None

		for attr, value in parameter.items():
			if not value: continue

			if attr == 'path':
				addin['name'] = filename = value

			else:
				if type == 'symlink' and attr == 'source':
					attr = 'name'

				addin[attr] = value

		if not addin or not filename:
			print "invalid parameters"
			return 3

		state = type
		if type == 'file':
			state = 'managed'
		elif type == 'dir':
			state = 'directory'

		tag = self.__get_tag(module, uid, step, filename, state)

		file_state = {
			tag : {
				'file' : [
					state,
					addin,
				]
			}
		}

		return file_state

	## scm
	def __scm(self, module, parameter, uid=None, step=None):
		"""
			Transfer scm to salt state.
		"""
		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			print "invalid preparation states"
			return 1

		if self.__check_module(module) != 0:
			print "invalid scm type"
			return 2

		m_list = module.split('.')
		type = m_list[1]

		state = 'latest'
		repo = None
		addin = {}
		scm_dir_addin = {}

		for attr, value in parameter.items():
			if not value:	continue

			if attr == 'repo':
				addin['name'] = repo = value.split('-')[1].strip()

			elif attr == 'branch':
				if type == 'git':
					addin['rev'] = value

			elif attr == 'revision':
				addin['rev'] = value

			elif attr == 'path':
				addin['target'] = value

			elif attr == 'user':
				addin['user'] = value
				scm_dir_addin['user'] = value

			elif attr == 'force':
				addin['force_checkout'] = True if value == 'True' else False

			elif attr == 'group':
				scm_dir_addin['group'] = value

			elif attr == 'mode':
				scm_dir_addin['mode'] = value

			else:
				if type == 'git':
					if attr == 'version':
						addin['rev'] = value
					elif attr == 'ssh-key':
						addin['identity'] = value
					#else:
						## invalid attributes

				elif type == 'svn':
					if attr in ['username', 'password']:
						addin[attr] = value
					#else:
						## invalid attributes

				#elif type == 'hg':
					## invalid attributes

		if not addin or not repo:
			print "invalid parameters"
			return 3

		scm_states = {}

		tag = self.__get_tag(module, uid, step, repo, state)
		scm_state =	{
			tag : {
				type : [
					state,
					addin,
				]
			}
		}

		scm_states[tag] = {
			type : [
				state,
				addin
			]
		}

		# add directory state
		# scm_dir_state = 'file'
		# dir_state = 'directory'
		# if addin['target'] and scm_dir_addin:
		# 	scm_dir_addin['recurse'] = scm_dir_addin.keys()
		# 	scm_dir_addin['name'] = addin['target']

		# 	scm_dir_tag = self.__get_tag('path.dir', uid, step, addin['target'], dir_state)

		# 	scm_states[scm_dir_tag] = {
		# 		scm_dir_state : [
		# 			dir_state,
		# 			scm_dir_addin,
		# 			{
		# 				'require' : [
		# 					{ type : tag }
		# 				]
		# 			},
		# 		]
		# 	}

		return scm_states

	def _scm_git(self, module, parameter, uid=None, step=None):
		"""
			Transfer git repo to salt state.
		"""
		return self.__scm(module, parameter, uid, step)

	def _scm_svn(self, module, parameter, uid=None, step=None):
		"""
			Transfer svn repo to salt state.
		"""
		return self.__scm(module, parameter, uid, step)

	def _scm_hg(self, module, parameter, uid=None, step=None):
		"""
			Transfer hg repo to salt state.
		"""
		return self.__scm(module, parameter, uid, step)

	## service
	def __service(self, module, parameter, uid=None, step=None):
		"""
			Transfer service to salt state.
		"""

		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			print "invalid preparation states"
			return 1

		if self.__check_module(module) != 0:
			print "invalid service state"
			return 2

		m_list = module.split('.')
		type = m_list[1]

		state = 'running'
		if type in ['sysvinit', 'upstart']:
			type = 'service'

		srv_state = {}
		addin = {}

		for attr, value in parameter.items():
			if not value: continue

			if attr == 'name':
				addin['name'] = value

			elif attr == 'username':
				if type == 'supervisord':
					addin['user'] = username

			else:
				if attr == 'config':
					addin['conf_file'] = value
				elif attr == 'watch':
					if isinstance(value, list):
						watch = value

		if not addin or 'name' not in addin:
			print "invalid parameters"
			return 3

		# add watch
		watch = []
		if parameter['watch'] and isinstance(parameter['watch'], list):
			for file in parameter['watch']:
				watch_module = 'path.dir' if os.path.isdir(file) else 'path.file'

				if watch_module == 'path.dir':
					watch_state = 'directory'
				else:
					watch_state = 'managed'

				watch_tag = self.__get_tag(watch_module, uid, step, file, watch_state)

				srv_state[watch_tag] = {
					'file' : [
						watch_state,
						{
							'name' : file
						},
					]
				}

				watch.append({'file' : watch_tag})

		# add service
		tag = self.__get_tag(module, uid, step, addin['name'], state)

		service = [
			state,
			addin,
		]
		if watch:
			service.append({'watch':watch})

		srv_state[tag] = {
			type : service
		}

		return srv_state

	def _service_supervisord(self, module, parameter, uid=None, step=None):
		"""
			Transfer supervisord service to salt state.
		"""
		return self.__service(module, parameter, uid, step)

	def _service_sysvinit(self, module, parameter, uid=None, step=None):
		"""
			Transfer sysvinit service to salt state.
		"""
		return self.__service(module, parameter, uid, step)

	def _service_upstart(self, module, parameter, uid=None, step=None):
		"""
			Transfer upstart service to salt state.
		"""
		return self.__service(module, parameter, uid, step)

	## sys
	def _sys_cmd(self, module, parameter, uid=None, step=None):
		"""
			Transfer system cmd to salt state.
		"""

		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			print "invalid preparation states"
			return 1

		if self.__check_module(module) != 0:
			print "invalid system command state"
			return 2

		type = module.split('.')[1]

		addin = {}
		cmd = None
		for attr, value in parameter.items():
			if not value: continue

			if attr == 'name' or attr == 'cmd':
				addin['name'] = cmd = value

			elif attr == 'bin':
				addin['shell'] = value

			elif attr in ['cwd', 'user', 'group', 'env', 'timeout']:
				addin[attr] = value

			#elif attr == 'with_path':
				##addin['onlyif'] = '' # only when path existed

			#elif attr == 'without_path':
				##addin['unless'] = '' # only when path not existed

		if not addin or not cmd:
			print "invalid parameters"
			return 3

		cmd_state = {}
		# deal content
		if 'content' in parameter and parameter['content']:
			cmd_file_addin = {'mode':'0755'}

			if 'user' in addin:
				cmd_file_addin['user'] = addin['user']

			if 'group' in addin:
				cmd_file_addin['group'] = addin['group']

			cmd_file_state = 'managed'
			cmd_file_tag = self.__get_tag('path.file', uid, step, addin['name'], cmd_file_state)

			cmd_state[cmd_file_tag] = {
				'file' : [
					cmd_file_state,
					cmd_file_addin,
				]
			}

		# deal args
		if 'args' in parameter and parameter['args']:
			addin['name'] += ' ' + parameter['args']

		state = 'run'
		cmd = [
			state,
			addin,
		]

		# add require
		requirity = {}
		if cmd_state:
			cmd.append({ 'require' : [ { 'file' : addin['name'] } ] })

		tag = self.__get_tag(module, uid, step, cmd, state)

		cmd_state[tag] ={
				type : cmd
		}

		return cmd_state

	def _sys_script(self, module, parameter, uid=None, step=None):
		"""
			Transfer system script to salt state.
		"""

		return self._sys_cmd(module, parameter, uid, step)

	def _sys_cron(self, module, parameter, uid=None, step=None):
		"""
			Transfer system cron to salt state.
		"""

		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			print "invalid preparation states"
			return 1

		if self.__check_module(module) != 0:
			print "invalid system cron state"
			return 2

		type = module.split('.')[1]
		addin = {}

		for attr, value in parameter.items():
			if not value: continue

			if attr == 'cmd':
				addin['name'] = value

			elif attr in ['minute', 'hour', 'month']:
				addin[attr] = value

			elif attr == 'day of month':
				addin['daymonth'] = value

			elif attr == 'day of week':
				addin['dayweek'] = value

			elif attr == 'username':
				addin['user'] = value

			#else:
				## invalid attributes

		if not addin or 'name' not in addin:
			print "invalid parameters"
			return 3

		state = 'present'
		tag = self.__get_tag(module, uid, step, addin['name'], state)

		return {
			tag : {
				type : [
					state,
					addin,
				]
			}
		}

	def _sys_user(self, module, parameter, uid=None, step=None):
		"""
			Transfer system username to salt state.
		"""

		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			print "invalid preparation states"
			return 1

		if self.__check_module(module) != 0:
			print "invalid system state"
			return 2

		type = module.split('.')[1]
		addin = {}

		for attr, value in parameter.items():
			if not value: continue

			if attr == 'username':
				addin['name'] = value

			elif attr == 'password':
				addin['password'] = value

			elif attr in ['fullname', 'uid', 'gid', 'shell', 'home', 'groups']:
				addin[attr] = value

			##elif attr == 'nologin':

		if not addin or 'name' not in addin:
			print "invalid parameters"
			return 3

		state = 'present'
		tag = self.__get_tag(module, uid, step, addin['name'], state)

		return {
			tag : {
				type : [
					state,
					addin
				]
			}
		}

	def _sys_group(self, module, parameter, uid=None, step=None):
		"""
			Transfer system group to salt state.
		"""

		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			print "invalid preparation states"
			return 1

		if self.__check_module(module) != 0:
			print "invalid system group state"
			return 2

		type = module.split('.')[1]
		addin = {}

		for attr, value in parameter.items():
			if not value: continue

			if attr == 'groupname':
				addin['name'] = value

			elif attr == 'gid':
				addin[attr] = value

			elif attr == 'system group':
				addin['system'] = True if value == 'True' else False

			#else:
				## invalid attributes

		if not addin or 'name' not in addin:
			print "invalid parameters"
			return 3

		state = 'present'
		tag = self.__get_tag(module, uid, step, addin['name'], state)

		return {
			tag : {
				type : [
					state,
					addin
				]
			}
		}

	def _sys_hostname(self, module, parameter, uid=None, step=None):
		"""
			Transfer system hostname to salt state.
		"""

		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			print "invalid preparation states"
			return 1

		if self.__check_module(module) != 0:
			print "invalid system hostname state"
			return 2

		addin = {}
		host = parameter['hostname']
		ip = None

		for attr, value in parameter.items():
			if not value: continue

			if attr == 'hostname':
				host = value

			elif attr == 'ip':
				addin['ip'] = value

			#else:
				## invalid attributes

		if not addin or not host:
			print "invalid parameters"
			return 3

		return {
			host : {
				'host' : [
					'present',
					addin
				]
			}
		}

	def _sys_hosts(self, module, parameter, uid=None, step=None):
		"""
			Transfer system hosts to salt state.
		"""

		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			print "invalid preparation states"
			return 1

		if self.__check_module(module) != 0:
			print "invalid system hostname state"
			return 2

		name = '/etc/hosts'
		state = 'managed'
		tag = self.__get_tag('path.file', uid, step, name, state)

		hosts_state = {
			tag	:	{
				'file'	: [
					state,
					{
						'name'		:	name,
						'user'		:	'root',
						'group'		:	'root',
						'mode'		:	'0644',
						'contents'	:	parameter['content'],
					}
				]
			}
		}

		return hosts_state

	def _sys_mount(self, module, parameter, uid=None, step=None):
		"""
			Transfer system mount to salt state.
		"""

		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			print "invalid preparation states"
			return 1

		if self.__check_module(module) != 0:
			print "invalid system state"
			return 2

		type = module.split('.')[1]

		addin = {}
		mount = None

		for attr, value in parameter.items():
			if not value: continue

			if attr == 'path':
				addin['name'] = mount = value

			elif attr == 'dev':
				addin['device'] = value

			elif attr == 'filesystem':
				addin['fstype'] = value

			elif attr == 'dump':
				addin['dump'] = atoi(value)

			elif attr == 'passno':
				addin['pass_num'] = atoi(value)

			elif attr == 'args':
				addin['opts'] = value

		if not addin or not mount:
			print "invalid parameters"
			return 3

		state = 'mounted'
		tag = self.__get_tag(module, uid, step, mount, state)

		return {
			tag : {
				type : [
					state,
					addin
				]
			}
		}

	def _sys_ntp(self, module, parameter, uid=None, step=None):
		"""
			Transfer system ntp to salt state.
		"""
		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			print "invalid preparation states"
			return 1

		if self.__check_module(module) != 0:
			print "invalid system state"
			return 2

		addin = {}
		ntp = None

	def _sys_selinux(self, module, parameter, uid=None, step=None):
		"""
			Transfer system selinux to salt state.
		"""

		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			print "invalid preparation states"
			return 1

		if self.__check_module(module) != 0:
			print "invalid system state"
			return 2

		type = module.split('.')[1]
		selinuxname = None

		if selinuxname:

			return {
				selinuxname : {
					type : [
						'boolean',
						{
							'value' : parameter['on']
						}
					]
				}
			}

	## ssh
	def _system_ssh_auth(self, module, parameter, uid=None, step=None):
		"""
			Transfer SSH authorized_key to salt state.
		"""

		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			print "invalid preparation states"
			return 1

		if self.__check_module(module) != 0:
			print "invalid system SSH authorized_key state"
			return 2

		auth = []
		addin = {}

		for attr, value in parameter.items():
			if not value: continue

			if attr == 'authname':
				addin['name'] = value

			elif attr == 'username':
				addin['user'] = value

			elif attr == 'filename':
				addin['config'] = value

			elif attr == 'encrypt_algorithm':
				if value in self.ssh_key_type:
					addin['enc'] = value

			elif attr == 'content':
				# parse the auth file
				for line in value.split('\n'):
					if not line: continue

					auth.append(line)

		if not addin:
			print "invalid parameters"
			return 3

		state = 'present'
		type = module.split('.', 1)[1].replace('.', '_')
		auth_state = {}

		# multi auth_ssh
		if auth:
			name = ''.join(str(i) for i in auth)
			tag = self.__get_tag(module, uid, step, name, state)

			auth_state[tag] = {
				type : [
					{
						'names' : auth
					},
					state,
					addin
				]
			}

		# one auth_ssh
		else:
			if 'name' not in addin:
				print "invalid parameters"
				return 3

			tag = self.__get_tag(module, uid, step, addin['name'], state)


			auth_state[tag] = {
				type : [
					state,
					addin,
				]
			}

		return auth_state

	def _system_ssh_known_host(self, module, parameter, uid=None, step=None):
		"""
			Transfer system SSH known_hosts to salt state.
		"""

		# check
		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			print "invalid preparation states"
			return 1

		if self.__check_module(module) != 0:
			print "invalid system SSH known_hosts state"
			return 2

		#type = module.split('.', 1)[1].replace('.', '_')
		type = 'ssh_known_hosts'
		addin = {}

		for attr, value in parameter.items():
			if not value: continue

			if attr == 'hostname':
				addin['name'] = value

			elif attr == 'username':
				addin['user'] = value

			elif attr == 'filename':
				addin['config'] = value

			elif attr == 'fingerprint':
				addin[attr] = value

			elif attr == 'encrypt_algorithm':
				if value in self.ssh_key_type:
					addin['enc'] = value

		if not addin or 'name' not in addin:
			print "invalid parameters"
			return 3

		state = 'present'
		tag = self.__get_tag(module, uid, step, addin['name'], state)

		return {
			tag : {
				type : [
					state,
					addin,
				]
			}
		}

	def __get_tag(self, module, uid=None, step=None, name=None, state=None):
		"""
			generate state identify tag.
		"""

		if not isinstance(module, basestring):
			module = str(module)

		tag = module.replace('.', '_')

		if step:
			if not isinstance(step, basestring):
				step = str(step)
			tag = step + '_' + tag

		if uid:
			if not isinstance(step, basestring):
				uid = str(uid)
			tag = uid + '_' + tag

		if name:
			if not isinstance(name, basestring):
				name = str(name)
			tag += '_' + name

		if state:
			if not isinstance(state, basestring):
				state = str(state)
			tag += '_' + state

		tag = '_' + tag

		#return hashlib.md5(tag).hexdigest()
		return tag

	def __get_requisity(self, module):
		"""
			Generate requisity state.
		"""

		req_state = []

		if module in self.requisity_map and module in self.pre_mapping:
			requisity = self.requisity_map[module]

			for req_module, req_parameter in requisity.items():
				if req_module not in self.pre_mapping: continue

				state = self.pre_mapping[req_module](req_module, req_parameter)

				if state:
					req_state.append(state)

		return req_state

	def __check_module(self, module):
		"""
			Check format of module.
		"""

		module_map = {
			'package'		: ['pkg', 'apt', 'yum', 'gem', 'npm', 'pecl', 'pip'],
			'repo'			: ['apt', 'yum', 'zypper'],
			'source'		: ['gem'],
			'path'			: ['file', 'dir', 'symlink'],
			'scm' 			: ['git', 'svn', 'hg'],
			'service'		: ['supervisord', 'sysvinit', 'upstart'],
			'sys'			: ['cmd', 'cron', 'group', 'host', 'mount', 'ntp', 'selinux', 'user'],
			'system'		: ['ssh_auth', 'ssh_known_host']
		}

		m_list = module.split('.')

		if len(m_list) <= 1:
			print "invalib module format"
			return 1

		p_module = m_list[0]
		s_module = m_list[1]

		if m_list[0] == 'package':
			p_module = m_list[2]

		elif m_list[0] == 'system':
			s_module = module.split('.', 1)[1].replace('.', '_')

		if p_module not in module_map.keys() or s_module not in module_map[p_module]:
			print "not supported module: %s, %s" % (p_module, s_module)
			return 2

		return 0

	def __mkdir(self, path):
		"""
			Check and make directory.
		"""
		if not os.path.isdir(path):
			try:
				os.makedirs(path)
			except OSError, e:
				print "Create directory %s failed" % path
				return False

		return True

# codes for test
def main():

	pre_states = json.loads(open('api.json').read())

	# salt_opts = {
	# 	'file_client':       'local',
	# 	'renderer':          'yaml_jinja',
	# 	'failhard':          False,
	# 	'state_top':         'salt://top.sls',
	# 	'nodegroups':        {},
	# 	'file_roots':        {'base': ['/srv/salt']},
	# 	'state_auto_order':  False,
	# 	'extension_modules': '/var/cache/salt/minion/extmods',
	# 	'id':                '',
	# 	'pillar_roots':      '',
	# 	'cachedir':          '/code/OpsAgent/cache',
	# 	'test':              False,
	# }

	config = {
		'file_roots' : '/srv/salt',
		'extension_modules' : '/var/cache/salt/minion/extmods',
		'cachedir' : '/code/OpsAgent/cache'
	}

	import pdb
	pdb.set_trace()

	sp = StatePreparation(config)

	print json.dumps(sp._salt_opts, sort_keys=True,
		indent=4, separators=(',', ': '))

	for uid, com in pre_states['component'].items():
		states = {}

		for p_state in com['state']:

			step = p_state['stateid']

			if p_state['module'] in sp.pre_mapping:

				ret = sp.exec_salt(step, p_state['module'], p_state['parameter'])

	# out_states = [salt_opts] + states
	# with open('states.json', 'w') as f:
	# 	json.dump(out_states, f)

if __name__ == '__main__':
	main()
