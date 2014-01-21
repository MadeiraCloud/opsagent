'''
Madeira OpsAgent states adaptor

@author: Michael (michael@mc2.io)
'''


# System imports
import os
import json
import hashlib
import collections

# Internal imports
from opsagent import utils
from opsagent.exception import StatePrepareExcepton,OpsAgentException

class StateAdaptor(object):

	ssh_key_type = ['ecdsa', 'ssh-rsa', 'ssh-dss']

	salt_map = {
		## package
		'linux.apt.package'	: {
			'attributes' : {
				'name'			: 'names',
				'fromrepo'		: 'fromrepo',
				'debconf'		: 'debconf',
				'verify_gpg'	: 'verify_gpg',
			},
			'states' : [
				'installed', 'latest', 'removed', 'purged'
			],
			'type'	: 'pkg',
		},
		'linux.yum.package'	: {
			'attributes' : {
				'name'			: 'names',
				'fromrepo'		: 'fromrepo',
				'enablerepo'	: 'enablerepo',
				'disablerepo'	: 'disablerepo',
				'verify_gpg'	: 'verify_gpg',
			},
			'states' : [
				'installed', 'latest', 'removed', 'purged'
			],
			'type'	: 'pkg',
		},
		'common.gem.package'	: {
			'attributes' : {
				'name'	: 'names',
			},
			'states' : [
				'installed', 'removed'
			],
			'type'	: 'pkg',
			'require'	: {
				'linux.yum.package' : { 'name' : ['rubygems'] },
			},
		},
		'common.npm.package'	: {
			'attributes' : {
				'name'		: 'names',
				'path'		: '',
				'index_url' : '',
			},
			'states' : [
				'installed', 'removed', 'bootstrap'
			],
			'type'	: 'pkg',
			'require'	: {
				'linux.yum.package' : { 'name' : ['npm'] },
			}
		},
		'common.pecl.package'	: {
			'attributes' : {
				'name' : 'names'
			},
			'states' : [
				'installed', 'removed'
			],
			'type'	: 'pkg',
			'require'	: {
				'linux.yum.package' : { 'name' : ['php-pear'] }
			}
		},
		'common.pip.package'	: {
			'attributes' : {
				'name' : 'names'
			},
			'states' : [
				'installed', 'removed'
			],
			'type'	: 'pkg',
			'require' : {
				'linux.yum.package' : { 'name' : ['python-pip'] }
			}
		},

		## repo
		'package.apt.repo'	: {
			'attributes' : {
				'name' : 'path',
				'contents' : 'content'
			},
			'states' : [
				'managed'
			],
			'type' : 'file',
		},
		'package.yum.repo' : {
			'attributes' : {
				'name' : 'path',
				'contents' : 'content'
			},
			'states' : [
				'managed'
			],
			'type' : 'file'
		},
		'package.gem.source' : {
			'attributes' : {
				'url' : 'name'
			},
			'state' : [
				'run'
			],
			'type' : 'cmd'
		},

		## path
		'linux.dir' : {
			'attributes' : {
				'path' : 'name',
				'user' : 'user',
				'group' : 'group',
				'mode' : 'mode',
				##'recursive' : { 'recurse' : ['user', 'group', 'mode'] },
				##'absent' : 'absent',
			},
			'states' : [
				'directory', 'absent'
			],
			'type' : 'file'
		},
		'linux.file' : {
			'attributes' : {
				'path' : 'name',
				'user' : 'user',
				'group' : 'group',
				'mode' : 'mode',
				'content' : 'contents',
				## 'absent' : 'absent',
			},
			'states' : [
				'managed', 'absent'
			],
			'type' : 'file'
		},
		'linux.symlink' : {
			'attributes' : {
				'source' : 'name',
				'target' : 'target',
				## 'absent' : 'absent'
			},
			'states' : [
				'symlink', 'absent'
			],
			'type' : 'symlink'
		},

		## scm
		'common.git' : {
			'attributes' : {
				'repo'		: 'name',
				'branch'	: 'rev',
				# 'version'	:,
				# 'ssh_key'	: 'identify',
				'path'		: 'target',
				'user'		: 'user',
				'force'		: 'force_checkout',
			},
			'states' : [
				'latest', 'present',
			],
			'type' : 'git',
			'require' : {
				'linux.yum.package' : { 'name' : ['git'] }
			},
			'require_in' : {
				'linux.dir' : {
					'path' : 'name',
					'user' : 'user',
					'group' : 'group',
					'mode' : 'mode',
				}
			}
		},
		'common.svn' : {
			'attributes' : {
				'repo'		: 'name',
				'branch'	: '',
				'revision'	: 'rev',
				'username'	: 'username',
				'password'	: 'password',
				'path'		: 'target',
				'user'		: 'user',
				'force'		: 'forge',
			},
			'states' : [
				'latest', 'export'
			],
			'type' : 'svn',
			'require' : {
				'linux.yum.package' : { 'name' : ['subversion'] }
			},
			'require_in' : {
				'linux.dir' : {
					'path' : 'name',
					'user' : 'user',
					'group' : 'group',
					'mode' : 'mode'
				}
			},
		},
		'common.hg' : {
			'attributes' : {
				'repo'		: 'name',
				'branch'	: '',
				'revision'	: 'rev',
				#'ssh_key'	: '',
				'path'		: 'target',
				'user'		: 'user',
				'force'		: 'force',
			},
			'states' : [
				'latest'
			],
			'type' : 'hg',
			'require' : {
				'linux.yum.package' : { 'name' : ['mercurial'] }
			},
			'require_in' : {
				'linux.dir' : {
					'path' : 'name',
					'user' : 'user',
					'group' : 'group',
					'mode' : 'mode'
				}
			},
		},

		## service
		'linux.supervisord' : {
			'attributes' : {
				'name'	:	'name',
				'config':	'conf_file',
				#'watch'	:	'',
			},
			'states' : ['running'],
			'type' : 'supervisord',
		},
		'linux.systemd' : {
			'attributes' : {
				'name' : 'name',
				# 'watch' : ''
			},
			'states' : ['running'],
			'type' : 'service',
		},
		'linux.sysvinit' : {
			'attributes' : {
				'name' : 'name',
				# 'watch' : ''
			},
			'states' : ['running'],
			'type' : 'service',
		},

		## cmd
		'sys.cmd' : {
			'attributes' : {
				'bin'			: 'shell',
				'cmd'			: 'name',
				'cwd'			: 'cwd',
				'user'			: 'user',
				'group'			: 'group',
				'timeout'		: 'timeout',
				'env'			: 'env',
				#'with_path'		: '',
				#'without_path'	: '',
			},
			'states' : [
				'run', 'call', 'wait', 'script'
			],
			'type' : 'cmd',
		},

		## cron
		'linux.cron' : {
			'attributes' : {
				'minute'	:	'minute',
				'hour'		:	'hour',
				'day of month'	:	'daymonth',
				'month'		:	'month',
				'day of week'	:	'dayweek',
				'username'		:	'user',
				'cmd'			:	'name'
			},
			'states' : [
				'present', 'absent'
			],
			'type' : 'cron',
		},

		## user
		'linux.user' : {
			'attributes' : {
				'username'	: 'name',
				'password'	: 'password',
				'fullname'	: 'fullname',
				'uid'		: 'uid',
				'gid'		: 'gid',
				'shell'		: 'shell',
				'home'		: 'home',
				#'nologin'	: '',
				'groups'	: 'groups',
			},
			'states' : [ 'present', 'absent' ],
			'type' : 'user'
		},

		## group
		'linux.group' : {
			'attributes' : {
				'groupname' : 'name',
				'gid' : 'gid',
				'system group' : 'system'
			},
			'states' : ['present', 'absent'],
			'type' : 'group'
		},

		## hostname

		## hosts

		## mount
		'linux.mount' : {
			'attributes' : {
				'path'		:	'name',
				'dev'		:	'device',
				'filesystem':	'fstype',
				'dump'		:	'dump',
				'passno'	:	'pass_num',
				'args'		:	'opts'
			},
			'states' : ['mounted', 'unmounted'],
			'type' : 'mount'
		},

		## selinux
		'linux.selinux' : {
			'attributes' : {
			},
			'states' : ['boolean', 'mode'],
			'type' : 'selinux',
			'linux.yum.package' : {
				'name' : ['libsemanage', 'setools-console', 'policycoreutils-python']
			}
		},

		## timezone
		'linux.timezone' : {
			'attributes' : {
				'name' : 'name',
				'use_utc' : 'utc'
			},
			'states' : ['system'],
			'type' : 'timezone'
		},

		## lvm
		'linux.lvm.pv'	: {
			'attributes' : {
				'path'					: 'names',
				# 'force'					: '',
				# 'uuid'					: '',
				# 'zero'					: '',
				'data alignment'		: 'dataalignment',
				'data alignment offset'	: 'dataalignmentoffset',
				'metadata size'			: 'metadatasize',
				# 'metadata type'			: '',
				'metadata copies'		: 'metadatacopies',
				'metadata ignore'		: 'metadataignore',
				'restore file'			: 'restorefile',
				'no restore file'		: 'norestorefile',
				'label sector'			: 'labelsector',
				'PV size'				: 'setphysicalvolumesize',
			},
			'states' : ['pv_present'],
			'type' : 'lvm'
		},
		'linux.lvm.vg'	: {
			'attributes' : {
				'name'	: 'name',
				'path' 	: 'devices',
				'clustered'	: 'clustered',
				'max LV number'	: 'maxlogicalvolumes',
				'max PV number'	: 'maxphysicalvolumes',
				# 'metadata type'	: '',
				'metadata copies'	: 'metadatacopies',
				'PE size'	: 'physicalextentsize',
				# 'autobackup'	: '',
				# 'tag'	: '',
				# 'allocation policy'	:	'',
			},
			'states' : ['vg_present', 'vg_absent'],
			'type' : 'lvm'
		},
		'linux.lvm.lv'	: {
			'attributes'	: {
				'path'				: '',
				'name'				: '',
				'available'			: '',
				'chunk size'		: '',
				'contiguous'		: '',
				'discards'			: '',
				'stripe number'		: '',
				'stripe size'		: '',
				'LE number'			: '',
				'LV size'			: '',
				'minor number'		: '',
				'persistent'		: '',
				'mirror number'		: '',
				'no udev sync'		: '',
				'monitor'			: '',
				'ignore monitoring' : '',
				'permission' 		: '',
				'pool metadata size': '',
				'region size'		: '',
				'readahead'			: '',
				'snapshot'			: '',
				'thinpool'			: '',
				'type'				: '',
				'virtual size'		: '',
				'zero'				: '',
				'autobackup'		: '',
				'tag'				: '',
				'allocation policy'	: '',
			},
			'states' : ['lv_present', 'lv_absent'],
			'type' : 'lvm',
		},

		## ssh
		'common.ssh.auth' : {
			'attributes' : {
				'authname'	:	'name',
				'username'	:	'user',
				'filename'	:	'config',
				#'content'	:	'',
				'encrypt_algorithm' : 'enc',
			},
			'states' : ['present', 'absent'],
			'type' : 'ssh_auth'
		},
		'common.ssh.known_host' : {
			'attributes' : {
				'hostname'	:	'name',
				'username'	:	'user',
				'filename'	:	'config',
				'fingerprint'		: 'fingerprint',
				'encrypt_algorithm'	: 'enc',
			},
			'states' : ['present', 'absent'],
			'type' : 'ssh_known_hosts'
		},
	}

	def __init__(self):

		self.pre_mapping = {
			'package.pkg.package'	:	self._package,
			'package.apt.package'	:	self._package,
			'package.yum.package'	:	self._package,
			'package.gem.package'	:	self._package,
			'package.npm.package'	:	self._package,
			'package.pecl.package'	:	self._package,
			'package.pip.package'	:	self._package,
			'package.zypper.package':	self._repo,
			'package.yum.repo'		:	self._repo,
			'package.apt.repo'		:	self._repo,
			'package.gem.source'	:	self._repo,
			'path.file'				:	self._file,
			'path.dir'				:	self._file,
			'path.symlink'			:	self._file,
			'scm.git'				:	self._scm,
			'scm.svn'				:	self._scm,
			'scm.hg'				:	self._scm,
			'service.supervisord'	:	self._service,
			'service.sysvinit'		:	self._service,
			'service.upstart'		:	self._service,
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
			'sys.timezone'			:	self._sys_timezone,
			'system.ssh.auth'		:	self._system_ssh_auth,
			'system.ssh.known_host' :	self._system_ssh_known_host,
		}

		self.states = None

	def transfer(self, step, module, parameter):
		"""
			Transfer the module json data to salt states.
		"""

		utils.log("DEBUG", "Begin to transfer module json data ...", ("transfer", self))

		if not isinstance(module, basestring) or not isinstance(parameter, dict):
			utils.log("ERROR", "Invalid input parameter: %s, %s" % (module, parameter), ("transfer", self))
			return

		# check module
		if module not in self.salt_map:
			utils.log("WARNING", "Not supported module %s" % module, ("transfer", self))
			return

		## state(update later)
		state = self.salt_map[module]['states'][0]
		# check state
		if self.__check_state(module, state) != 0:
			utils.log("WARNING", "Not supported state %s" % state, ("transfer", self))
			return

		# convert from unicode to string
		utils.log("DEBUG", "Begin to convert unicode parameter to string ...", ("transfer", self))
		parameter = self.__convert(parameter)

		# transfer
		if module in ['linux.apt.package', 'linux.yum.package', 'common.gem.package', 'common.npm.package', 'common.pecl.package', 'common.pip.package']:
			salt_state = self._package(step, module, parameter)
		else:
			salt_state = self._transfer(step, module, parameter, state)
		if not salt_state or not isinstance(salt_state, dict):
			utils.log("ERROR", "Transfer json to salt state failed", ("transfer", self))
			return

		self.states = salt_state
		return salt_state

	def _transfer(self, step, module, parameter, state):

		salt_state = {}

		# generate addin
		addin = self.__init_addin(module, parameter)
		if not addin:
			utils.log("ERROR", "Transfer module parameters failed: %s, %s" % (module, parameter), ("_transfer", self))
			return salt_state

		# add require
		utils.log("DEBUG", "Begin to generate requirity ...", ("_transfer", self))
		require = []
		if 'require' in self.salt_map[module]:
			req_state = self.__get_require(self.salt_map[module]['require'])
			if req_state:
				for req_tag, req_value in req_state.items():
					salt_state[req_tag] = req_value

					require.append({ next(iter(req_value)) : req_tag })

		# add require in
		utils.log("DEBUG", "Begin to generate require-in ...", ("_transfer", self))
		require_in = []
		if 'require_in' in self.salt_map[module]:
			req_in_state = self.__get_require_in(self.salt_map[module]['require_in'], parameter)
			if req_in_state:
				for req_in_tag, req_in_value in req_in_state.items():
					salt_state[req_in_tag] = req_in_value

					require_in.append({ next(iter(req_in_value)) : req_in_tag })

		# build up
		module_state = [
			state,
			addin
		]

		if require:
			module_state.append({ 'require' : require })
		if require_in:
			module_state.append({ 'require_in' : require_in })

		# tag
		#name = addin['names'] if 'names' in addin else addin['name']
		tag = self.__get_tag(module, None, step, None, state)
		utils.log("DEBUG", "Generated tag is %s" % tag, ("_transfer", self))

		type = self.salt_map[module]['type']

		salt_state[tag] = {
			type : module_state
		}

		# add env and sls
		if 'require_in' in self.salt_map[module]:
			salt_state[tag]['__env__'] = 'base'
			salt_state[tag]['__sls__'] = 'madeira'

		return salt_state

	def __init_addin(self, module, parameter):

		addin = {}

		for attr, value in parameter.items():
			if value is None:	continue

			if attr in self.salt_map[module]['attributes'].keys():
				key = self.salt_map[module]['attributes'][attr]

				if isinstance(value, dict):
					addin[key] = []
					for k, v in value.items():
						if v:
							addin[key].append({k:v})
						else:
							addin[key].append(k)

				else:
					addin[key] = value

					## todo
					if module in ['common.git', 'common.svn', 'common.hg'] and key == 'name':
						addin[key] = value.split('-')[1].strip()

		return addin

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

	def __get_require(self, require):
		"""
			Generate require state.
		"""

		requre_state = {}

		for module, parameter in require.items():
			if module not in self.salt_map.keys():	continue

			addin = self.__init_addin(module, parameter)

			state 	= self.salt_map[module]['states'][0]
			tag 	= self.__get_tag(module, None, None, 'require', state)
			type 	= self.salt_map[module]['type']

			requre_state[tag] = {
				type : [
					state,
					addin
				]
			}

		return requre_state

	def __get_require_in(self, require_in, parameter):
		"""
			Generate require in state.
		"""

		require_in_state = {}

		for module, attrs in require_in.items():
			req_addin = {}
			for k, v in attrs.items():
				if not v or k not in parameter:	continue

				req_addin[v] = parameter[k]

			#addin = self.__init_addin(module, req_p)
			state = self.salt_map[module]['states'][0]
			type = self.salt_map[module]['type']

			tag = self.__get_tag(module, None, None, 'require_in', state)

			require_in_state[tag] = {
				type : [
					state,
					req_addin
				]
			}

		return require_in_state

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
			'sys'			: ['cmd', 'cron', 'group', 'host', 'mount', 'ntp', 'selinux', 'user', 'timezone'],
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

	def __check_state(self, module, state):
		"""
			Check supported state.
		"""

		if state not in self.salt_map[module]['states']:
			print "not supported state %s in module %s" % (state, module)
			return 1

		return 0

	def __convert(self, data):
		"""
			Convert data from unicode to string.
		"""

		if isinstance(data, basestring):
			return str(data)
		elif isinstance(data, collections.Mapping):
			return dict(map(self.__convert, data.iteritems()))
		elif isinstance(data, collections.Iterable):
			return type(data)(map(self.__convert, data))
		else:
			return data

	##################################################################################
	## package
	def _package(self, step, module, parameter):
		"""
			Transfer package to salt state.
		"""
		pkg_state = {}

		m_list = module.split('.')

		state_mapping = {}
		addin = {}

		# add require
		require = []
		if 'require' in self.salt_map[module]:
			req_state = self.__get_require(self.salt_map[module]['require'])
			if req_state:
				for req in req_state:
					for req_tag, req_value in req.items():
						pkg_state[req_tag] = req_value

						require.append({ next(iter(req_value)) : req_tag })

		if m_list[1] in ['apt', 'yum']:
			m_list[1] = 'pkg'

		# get package name and verson
		for attr, value in parameter.items():
			if value is None: continue

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

				# support for require
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

			if require:
				pkg.append({ 'require' : require })

			tag = self.__get_tag(module, None, step, 'pkgs', state)

			pkg_state[tag] = {
				m_list[1] : pkg
			}

		return pkg_state

	## repo, source
	def _repo(self, module, parameter, uid=None, step=None):
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

			requisities = []

			# # add package require
			req_state = self.__get_require('package.gem.package')
			if req_state:
				for req in req_state:
					for req_tag, req_value in req.items():
						repo_state[req_tag] = req_value

						requisities.append({ next(iter(req_value)) : req_tag })

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

			# add require
			if requisities:
				cmd.append({ 'require' : requisities })

			repo_state[tag] = {
				'cmd' : cmd
			}

		##elif type == 'zypper'

		return repo_state

	## file, directory, symlink
	def _file(self, module, parameter, uid=None, step=None):
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
			if value is None: continue

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
	def _scm(self, module, parameter, uid=None, step=None):
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
			if value is None:	continue

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
		scm_dir_state = 'file'
		dir_state = 'directory'
		if addin['target'] and scm_dir_addin:
			scm_dir_addin['recurse'] = scm_dir_addin.keys()
			scm_dir_addin['name'] = addin['target']

			scm_dir_tag = self.__get_tag('path.dir', uid, step, addin['target'], dir_state)

			scm_states[scm_dir_tag] = {
				scm_dir_state : [
					dir_state,
					scm_dir_addin,
					{
						'require' : [
							{ type : tag }
						]
					},
				]
			}

		return scm_states

	## service
	def _service(self, module, parameter, uid=None, step=None):
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
			if value is None: continue

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
			if value is None: continue

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
			if value is None: continue

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
			if value is None: continue

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
			if value is None: continue

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
			if value is None: continue

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
			if value is None: continue

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
			Transfer system ntp to salt state. (Salt currently only supports Windows platform.)
		"""
		# check
		# if not isinstance(module, basestring) or not isinstance(parameter, dict):
		# 	print "invalid preparation states"
		# 	return 1

		# if self.__check_module(module) != 0:
		# 	print "invalid system state"
		# 	return 2

		# addin = {}
		# ntp = None

		return None

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
		addin = {}
		selinux_state = {}

		# add require
		require = []
		req_state = self.__get_require(module)
		if req_state:
			for req in req_state:
				for req_tag, req_value in req.items():
					selinux_state[req_tag] = req_value

					require.append({ next(iter(req_value)) : req_tag })

		for attr, value in parameter.items():
			if value is None:	continue

			if attr == 'on':
				if value == True:
					addin['name'] = 'enforcing'
				else:
					addin['name'] = 'permissive'

			else:
				addin[attr] = value

		if not addin:
			print "invalid parameters"
			return 3

		state = 'mode'
		tag = self.__get_tag(module, uid, step, addin['name'], state)

		selinux = [
			state,
			addin
		]
		if require:
			selinux.append(
				{ 'require' : require }
			)
		selinux_state[tag] = {
			type : selinux
		}

		return selinux_state

	def _sys_timezone(self, module, parameter, uid=None, step=None):
		"""
			Transfer system timezon to salt state.
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
			if value is None:	continue

			if attr == 'name':
				addin['name'] = value

			elif attr == 'use_utc':
				addin['utc'] = value

			else:
				addin[attr] = value

		if not addin or 'name' not in addin:
			print "invalid parameters"
			return 3

		state = 'system'
		tag = self.__get_tag(module, uid, step, addin['name'], state)

		return {
			tag : {
				type : [
					state,
					addin,
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
			if value is None: continue

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
			if value is None: continue

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

        from staterunner import StateRunner
	adaptor = StateAdaptor()
	runner = StateRunner(config)

	# print json.dumps(adaptor._salt_opts, sort_keys=True,
	# 	indent=4, separators=(',', ': '))

	err_log = None
	out_log = None
	for uid, com in pre_states['component'].items():
		states = {}

		for p_state in com['state']:

			step = p_state['stateid']

			state = adaptor.transfer(step, p_state['module'], p_state['parameter'])

			print json.dumps(state)

			if not state or not isinstance(state, dict):
				err_log = "transfer salt state failed"
				print err_log
				result = (False, err_log, out_log)

			else:
				result = runner.exec_salt(state)

			print result

	# out_states = [salt_opts] + states
	# with open('states.json', 'w') as f:
	# 	json.dump(out_states, f)

if __name__ == '__main__':
	main()
