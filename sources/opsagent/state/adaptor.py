'''
Madeira OpsAgent states adaptor

@author: Michael (michael@mc2.io)
'''


# System imports
import os
import hashlib
import collections

# Internal imports
from opsagent import utils
from opsagent.exception import StateException, OpsAgentException

class StateAdaptor(object):

	ssh_key_type = ['ssh-rsa', 'ecdsa', 'ssh-dss']

	mod_map = {
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
			'type'	: 'gem',
			'require'	: {
				'linux.apt.package' : { 'name' : ['rubygems'] },
			},
		},
		'common.npm.package'	: {
			'attributes' : {
				'name'		: 'names',
				#'path'		: '',
				#'index_url' : '',
			},
			'states' : [
				'installed', 'removed', 'bootstrap'
			],
			'type'	: 'npm',
			'require'	: {
				'linux.apt.package' : { 'name' : ['npm'] },
			}
		},
		'common.pecl.package'	: {
			'attributes' : {
				'name' : 'names'
			},
			'states' : [
				'installed', 'removed'
			],
			'type'	: 'pecl',
			'require'	: {
				'linux.apt.package' : { 'name' : ['php-pear'] },
			}
		},
		'common.pip.package'	: {
			'attributes' : {
				'name' : 'names'
			},
			'states' : [
				'installed', 'removed'
			],
			'type'	: 'pip',
			'require' : {
				'linux.apt.package' : { 'name' : ['python-pip'] },
			}
		},

		## repo
		'linux.apt.repo'	: {
			'attributes' : {
				'name' 		: 'name',
				'contents' 	: 'content'
			},
			'states' : [
				'managed'
			],
			'type' : 'file',
		},
		'linux.yum.repo' : {
			'attributes' : {
				'name' 		: 'name',
				'contents' 	: 'content'
			},
			'states' : [
				'managed'
			],
			'type' : 'file'
		},
		'common.gem.source' : {
			'attributes' : {
				'url' : 'name'
			},
			'state' : [
				'run'
			],
			'type' : 'cmd'
		},

		## scm
		'common.git' : {
			'attributes' : {
				'repo'		: 'name',
				'branch'	: 'branch',
				'version'	: 'rev',
				'ssh_key'	: 'identify',
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
				'branch'	: 'branch',
				'revision'	: 'rev',
				'username'	: 'username',
				'password'	: 'password',
				'path'		: 'target',
				'user'		: 'user',
				'force'		: 'force',
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
				'branch'	: 'branch',
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

		## path
		'linux.dir' : {
			'attributes' : {
				'path' : 'name',
				'user' : 'user',
				'group' : 'group',
				'mode' : 'mode',
				'recursive' : 'recurse',
				'absent' : 'absent',
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
				'absent' : 'absent',
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
				'user'	 : 'user',
				'group'	 : 'group',
				'mode'	 : 'mode',
				'absent' : 'absent'
			},
			'states' : [
				'symlink', 'absent'
			],
			'type' : 'file'
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
		'linux.upstart' : {
			'attributes' : {
				'name' : 'name',
				# 'watch' : 'watch',
			},
			'states' : ['running'],
			'type' : 'service',
		},

		## cmd
		'linux.cmd' : {
			'attributes' : {
				'bin'			: 'shell',
				'cmd'			: 'name',
				'cwd'			: 'cwd',
				'user'			: 'user',
				'group'			: 'group',
				'timeout'		: 'timeout',
				'env'			: 'env',
				'with_path'		: 'onlyif',
				'without_path'	: 'unless',
			},
			'states' : [
				'run', 'call', 'wait', 'script'
			],
			'type' : 'cmd',
		},

		## cron
		'linux.cron' : {
			'attributes' : {
				'minute'		:	'minute',
				'hour'			:	'hour',
				'day of month'	:	'daymonth',
				'month'			:	'month',
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
				'nologin'	: 'nologin',
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
		'linux.hosts' : {
			'attributes' : {
				'content' : 'contents'
			},
			'states' : ['managed'],
			'type' : 'file',
		},

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
				'path'				: 'pv',
				'name'				: 'name',
				# 'available'			: '',
				# 'chunk size'		: '',
				# 'contiguous'		: '',
				# 'discards'			: '',
				# 'stripe number'		: '',
				# 'stripe size'		: '',
				'LE number'			: 'extents',
				'LV size'			: 'size',
				# 'minor number'		: '',
				# 'persistent'		: '',
				# 'mirror number'		: '',
				# 'no udev sync'		: '',
				# 'monitor'			: '',
				# 'ignore monitoring' : '',
				# 'permission' 		: '',
				# 'pool metadata size': '',
				# 'region size'		: '',
				# 'readahead'			: '',
				# 'snapshot'			: '',
				# 'thinpool'			: '',
				# 'type'				: '',
				# 'virtual size'		: '',
				# 'zero'				: '',
				# 'autobackup'		: '',
				# 'tag'				: '',
				# 'allocation policy'	: '',
			},
			'states' : ['lv_present', 'lv_absent'],
			'type' : 'lvm',
		},

		## virtual env
		'common.virtualenv' : {
			'attributes' : {
				'path'					: 'name',
				'python'				: 'python',
				'system-site-packages'	: 'system_site_packages',
				# 'always-copy'			: '',
				# 'unzip-setuptools'		: '',
				# 'no-setuptools'			: '',
				# 'no-pip'				: '',
				'extra-search-dir'		: 'extra-search-dir',
			},
			'states' : ['managed'],
			'type' : 'virtualenv',
		},

		## ssh
		'common.ssh.auth' : {
			'attributes' : {
				'authname'	:	'name',
				'username'	:	'user',
				'filename'	:	'config',
				'content'	:	'content',
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

		self.states = None

	def convert(self, step, module, parameter):
		"""
			convert the module json data to salt states.
		"""

		utils.log("DEBUG", "Begin to convert module json data ...", ("convert", self))

		if not isinstance(module, basestring):	raise StateException("Invalid input parameter: %s, %s" % (module, parameter))
		if not isinstance(parameter, dict):		raise StateException("Invalid input parameter: %s, %s" % (module, parameter))
		if module not in self.mod_map:			raise StateException("Unsupported module %s" % module)

		# convert from unicode to string
		utils.log("DEBUG", "Begin to convert unicode parameter to string ...", ("convert", self))
		parameter = utils.uni2str(parameter)

		self.states = self.__salt(step, module, parameter)
		return self.states

	def __salt(self, step, module, parameter):
		salt_state = {}

		addin = self.__init_addin(module, parameter)
		module_states = self.__build_up(module, addin)

		for state, addin in module_states.items():
			# add require
			utils.log("DEBUG", "Begin to generate requirity ...", ("_convert", self))
			require = []
			if 'require' in self.mod_map[module]:
				req_state = self.__get_require(self.mod_map[module]['require'])
				if req_state:
					for req_tag, req_value in req_state.items():
						salt_state[req_tag] = req_value
						require.append({ next(iter(req_value)) : req_tag })

			# add require in
			utils.log("DEBUG", "Begin to generate require-in ...", ("_convert", self))
			require_in = []
			if 'require_in' in self.mod_map[module]:
				req_in_state = self.__get_require_in(self.mod_map[module]['require_in'], parameter)
				if req_in_state:
					for req_in_tag, req_in_value in req_in_state.items():
						salt_state[req_in_tag] = req_in_value
						require_in.append({ next(iter(req_in_value)) : req_in_tag })

			## add watch, todo
			utils.log("DEBUG", "Begin to generate watch ...",("_convert", self))
			watch = []
			# if 'watch' in parameter and isinstance(parameter['watch'], list):
			# 	watch_state = self.__add_watch(parameter['watch'], step)
			# 	if watch_state:
			# 		for watch_tag, watch_value in watch_state.items():
			# 			salt_state[watch_tag] = watch_value
			# 			watch.append({file:watch_tag})

			# build up module state
			module_state = [
				state,
				addin
			]

			if require:		module_state.append({ 'require' : require })
			if require_in:	module_state.append({ 'require_in' : require_in })
			if watch:		module_state.append({ 'watch' : watch })

			# tag
			#name = addin['names'] if 'names' in addin else addin['name']
			tag = self.__get_tag(module, None, step, None, state)
			utils.log("DEBUG", "Generated tag is %s" % tag, ("_convert", self))
			salt_state[tag] = {
				self.mod_map[module]['type'] : module_state
			}

			# add env and sls
			if 'require_in' in self.mod_map[module]:
				salt_state[tag]['__env__'] = 'base'
				salt_state[tag]['__sls__'] = 'madeira'
		if not salt_state:	raise StateException("conver state failed: %s %s" % (module, parameter))
		return salt_state

	def __init_addin(self, module, parameter):
		addin = {}

		for attr, value in parameter.items():
			if value is None:	continue

			if attr in self.mod_map[module]['attributes'].keys():
				key = self.mod_map[module]['attributes'][attr]
				if isinstance(value, dict):
					addin[key] = [k if not v else {k:v} for k, v in value.items()]
				else:
					addin[key] = value
		if not addin:	raise StateExcepttion("No addin founded: %s, %s" % (module, parameter))
		return addin

	def __build_up(self, module, addin):
		default_state = self.mod_map[module]['states'][0]
		module_state = {
			default_state : addin
		}

		if module in ['linux.apt.package', 'linux.yum.package', 'common.gem.package', 'common.npm.package', 'common.pecl.package', 'common.pip.package']:
			module_state = {}

			for item in addin['names']:
				pkg_name = None
				pkg_state = None
				if isinstance(item, dict):
					for k, v in item.items():
						pkg_name 	= k
						pkg_state 	= default_state

						if v in self.salt_map[module]['states']:
							pkg_state = v

						if pkg_state not in module_state:			module_state[pkg_state] = {}
						if 'names' not in module_state[pkg_state]:	module_state[pkg_state]['names'] = []

						if pkg_state == default_state:
							module_state[pkg_state]['names'].append(item)
						else:
							module_state[pkg_state]['names'].append(pkg_name)

				else:	# insert into default state
					pkg_state	= default_state

					if pkg_state not in module_state:			module_state[pkg_state] = {}
					if 'names' not in module_state[pkg_state]:	module_state[pkg_state]['names'] = []

					module_state[pkg_state]['names'].append(item)

		elif module in ['common.git', 'common.svn', 'common.hg']:
			if 'name' in addin:
				module_state[default_state]['name'] = addin['name'].split('-')[1].strip()

			# set revision
			if 'branch' in addin:
				module_state[default_state]['rev'] = addin['branch']
				module_state[default_state].pop('branch')

		elif module in ['linux.apt.repo', 'linux.yum.repo']:
			if 'name' in addin:
				filename = addin['name']
				obj_dir =  None

				if module == 'linux.apt.repo':
					obj_dir = '/etc/apt/sources.list.d/'
					if not filename.endswith('.list'):
						filename += '.list'
				elif module == 'linux.yum.repo':
					obj_dir = '/etc/yum.repos.d/'
					if not filename.endswith('repo'):
						filename += '.repo'

				if filename and obj_dir:
					module_state[default_state]['name'] = obj_dir + filename

		elif module in ['common.gem.source']:
			module_state[default_state].update(
				{
					'name'	: 'gem source --add ' + addin['name'],
					'shell'	: '/bin/bash',
					'user'	: 'root',
					'group'	: 'root',
				}
			)

		elif module in ['common.ssh.auth', 'common.ssh.known_host']:
			auth = []

			if 'enc' in addin and addin['enc'] not in self.ssh_key_type:
				module_state[default_state]['enc'] = self.ssh_key_type[0]

			if module == 'common.ssh.auth' and 'content' in addin:
				for line in value.split('\n'):
					if not line: continue

					auth.append(line)

				module_state[default_state]['names'] = auth

				# remove name attribute
				module_state[default_state].pop('name')

		elif module in ['linux.dir', 'linux.file', 'linux.symlink']:
			# set absent
			if 'absent' in addin and addin['absent']:
				module_state.pop(default_state)
				module_state['absent'] = {
					'name' : addin['name']
				}

			# set recurse
			elif 'recurse' in addin and addin['recurse']:
				module_state[default_state]['recurse'] = []
				if 'user' in addin and addin['user']:
					module_state[default_state]['recurse'].append('user')
				if 'group' in addin and addin['group']:
					module_state[default_state]['recurse'].append('group')
				if 'mode' in addin and addin['mode']:
					module_state[default_state]['recurse'].append('mode')

			if module == 'linux.dir':
				module_state[default_state]['makedirs'] = True

		elif module in ['linux.cmd']:
			if 'onlyif' in addin:
				module_state[default_state]['onlyif'] = "[ -d " + addin['onlyif'] + " ]"

			if 'unless' in addin:
				module_state[default_state]['unless'] = "[ -d " + addin['unless'] + " ]"

			if 'timeout' in addin:
				module_state[default_state]['timeout'] = int(addin['timeout'])

		elif module in ['linux.user']:
			# set nologin shell
			if 'nologin' in addin:
				module_state[default_state].pop('nologin')

				if addin['nologin']:
					module_state[default_state]['shell'] = '/sbin/nologin'

		elif module in ['linux.mount']:
			for attr in ['dump', 'pass_num']:
				if attr in addin:
					try:
						module_state[default_state][attr] = int(addin['dump'])
					except:
						module_state[default_state][attr] = 0

		elif module in ['linux.hosts']:

			module_state[default_state] = {
				'name' 		: '/etc/hosts',
				'user' 		: 'root',
				'group' 	: 'root',
				'mode' 		: '0644',
				'contents' 	: addin['contents']
			}
		if not module_state:	raise StateException("Build up module state failed: %s" % module)
		return module_state

	def __get_tag(self, module, uid=None, step=None, name=None, state=None):
		"""
			generate state identify tag.
		"""
		tag = module.replace('.', '_')
		if step:	tag = step + '_' + tag
		if uid:		tag = uid + '_' + tag
		if name:	tag += '_' + name
		if state:	tag += '_' + state
		return '_' + tag

	def __get_require(self, require):
		"""
			Generate require state.
		"""

		requre_state = {}

		for module, parameter in require.items():
			if module not in self.mod_map.keys():	continue

			# addin = self.__init_addin(module, parameter)

			# state 	= self.salt_map[module]['states'][0]
			# tag 	= self.__get_tag(module, None, None, 'require', state)
			# type 	= self.salt_map[module]['type']

			the_requre_state = self._transfer('require', module, parameter)

			if the_requre_state:
				requre_state.update(the_requre_state)

			# requre_state[tag] = {
			# 	type : [
			# 		state,
			# 		addin
			# 	]
			# }

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
			state = self.mod_map[module]['states'][0]
			type = self.mod_map[module]['type']

			tag = self.__get_tag(module, None, None, 'require_in', state)

			require_in_state[tag] = {
				type : [
					state,
					req_addin
				]
			}

		return require_in_state

	def __add_watch(self, watch):
		"""
			Generate watch state.
		"""

		watch_state = {}

		for file in watch:
			watch_module = 'path.dir' if os.path.isdir(file) else 'path.file'
			state = 'directory' if watch_module == 'path.dir' else 'managed'

			watch_tag = self.__get_tag(watch_module, None, step, file, state)

			watch_state[watch_tag] = {
				'file' : [
					state,
					{
						'name' : file
					},
				]
			}

		return watch_state

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

		if state not in self.mod_map[module]['states']:
			print "not supported state %s in module %s" % (state, module)
			return 1

		return 0

# ===================== UT =====================
def ut():
	import json
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

	from opsagent.state.runner import StateRunner
	adaptor = StateAdaptor()
	runner = StateRunner(config)

	# print json.dumps(adaptor._salt_opts, sort_keys=True,
	# 	indent=4, separators=(',', ': '))

	err_log = None
	out_log = None
	for uid, com in pre_states['component'].items():
		states = {}

		for p_state in com['state']:
			step = p_state['id']
			state = adaptor.convert(step, p_state['module'], p_state['parameter'])
			print json.dumps(state)

			if not state or not isinstance(state, dict):
				err_log = "convert salt state failed"
				print err_log
				result = (False, err_log, out_log)
			else:
				result = runner.exec_salt(state)
			print result

	# out_states = [salt_opts] + states
	# with open('states.json', 'w') as f:
	# 	json.dump(out_states, f)

if __name__ == '__main__':
	ut()
