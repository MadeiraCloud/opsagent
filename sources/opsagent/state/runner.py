'''
Madeira OpsAgent state runner

@author: Michael (michael@mc2.io)
'''

import os
import json

from salt.state import State

from opsagent import utils
from opsagent.exception import ExecutionException

class StateRunner(object):

	def __init__(self, config):

		self.state = None

		# init salt opts
		self._init_opts(config)

		# init state
		self._init_state()

		# init os type
		self._init_ostype()

		# pkg cache dir
		self._pkg_cache = (config['pkg_cache'] if 'pkg_cache' in config and config['pkg_cache'] and isinstance(config['pkg_cache'], basestring) else '/tmp/')

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
		for path in config['srv_root'].split(':'):
			# check and make path
			if not self.__mkdir(path):
				continue

			self._salt_opts['file_roots']['base'].append(path)

		if len(self._salt_opts['file_roots']['base']) == 0:		raise ExecutionException("Missing file roots argument")
		if not self.__mkdir(config['extension_modules']):		raise ExecutionException("Missing extension modules argument")

		self._salt_opts['extension_modules'] = config['extension_modules']

		if not self.__mkdir(config['cachedir']):	raise ExecutionException("Missing cachedir argument")

		self._salt_opts['cachedir'] = config['cachedir']

	def _init_state(self):
		"""
			Init salt state object.
		"""

		self.state = State(self._salt_opts)

	def _init_ostype(self):

		try:
			self.os_type = self.state.opts['grains']['os'].lower() if self.state.opts and \
				'grains' in self.state.opts and 'os' in self.state.opts['grains'] else 'unknown'

			if self.os_type == 'unknown':
				import subprocess

				config_file = self.__is_existed(['/etc/issue', '/etc/redhat-release'])
				if not config_file:
					raise ExecutionException("Cannot find the system config file")

				cmd = 'grep -io -E  "ubuntu|debian|centos|redhat|amazon" ' + config_file
				process = subprocess.Popen(
					cmd,
					shell=True,
					stdout=subprocess.PIPE,
					stderr=subprocess.PIPE)

				if process.returncode != 0:
					utils.log("ERROR", "Excute cmd %s failed..."%cmd, ("_init_ostype", self))
					raise ExecutionException("Excute cmd %s failed"%cmd)

				out, err = process.communicate()
				self.os_type = out
		except Exception, e:
			utils.log("ERROR", "Fetch agent's os type failed...", ("_init_ostype", self))
			raise ExecutionException("Fetch agent's os type failed")

	def exec_salt(self, states):
		"""
			Transfer and exec salt state.
			return result format: (result,comment,out_log), result:True/False
		"""

		result = False
		comment = ''
		out_log = ''

		# check
		if not states:
			out_log = "Null states"
			return (result, comment, out_log)
		if not states or not isinstance(states, list):
			out_log = "Invalid state format %s" % str(states)
			return (result, comment, out_log)

		# check whether contain specail module
		try:
			if self._is_special(states):
				self._enable_epel()
		except:
			utils.log("WARNING", "Enable epel repo failed...",("exec_salt", self))
			pass

		utils.log("INFO", "Begin to execute salt state...", ("exec_salt", self))
		for idx, state in enumerate(states):
			utils.log("INFO", "Begin to execute the %dth salt state..." % (idx+1), ("exec_salt", self))
			try:
				ret = self.state.call_high(state)
			except Exception, e:
				utils.log("ERROR", "Execute salt state %s failed: %s"% (json.dumps(state), str(e)), ("exec_salt", self))
				return (False, "Execute salt state exception", "")

			if ret:
				# parse the ret and return
				utils.log("INFO", json.dumps(ret), ("exec_salt", self))

				# set comment and output log
				require_in_comment = ''
				require_in_log = ''
				for r_tag, r_value in ret.items():
					if 'result' not in r_value:	continue 	# filter no result

					# parse require in result
 					if 'require_in' in r_tag:
						require_in_comment = '{0}{1}{2}'.format(
								require_in_comment,
								'\n\n' if require_in_comment else '',
								r_value['comment'] if 'comment' in r_value and r_value['comment'] else ''
							)
						require_in_log = '{0}{1}{2}'.format(
								require_in_log,
								'\n\n' if require_in_log else '',
								r_value['state_stdout'] if 'state_stdout' in r_value and r_value['state_stdout'] else ''
							)

					# parse require result
					elif 'require' in r_tag:
						comment = '{0}{1}{2}'.format(
							r_value['comment'] if 'comment' in r_value and r_value['comment'] else '',
							'\n\n' if comment else '',
							comment
							)
						out_log = '{0}{1}{2}'.format(
							r_value['state_stdout'] if 'state_stdout' in r_value and r_value['state_stdout'] else '',
							'\n\n' if out_log else '',
							out_log
							)

					# parse common result
					else:
						comment = '{0}{1}{2}'.format(
							comment,
							'\n\n' if comment else '',
							r_value['comment'] if 'comment' in r_value and r_value['comment'] else ''
							)
						out_log = '{0}{1}{2}'.format(
							out_log,
							'\n\n' if out_log else '',
							r_value['state_stdout'] if 'state_stdout' in r_value and r_value['state_stdout'] else ''
							)

					result = r_value['result']
					# break when one state runs failed
					if not result:
						break

				# add require in comment and log
				if require_in_comment:
					comment += '\n\n' + require_in_comment

				if require_in_log:
					out_log += '\n\n' + require_in_log

			else:
				out_log = "wait failed"

		return (result, comment, out_log)

	def _is_special(self, states):
		"""
			Check whether contain gem/npm/pip state.
		"""
		is_special = False
		for state in states:
			for tag, module in state.iteritems():
				if len([ m for m in module.keys() if m in['gem', 'npm', 'pip'] ]) > 0:
					is_special = True
					break

		return is_special

	def _enable_epel(self):
		"""
			Install and enbale epel in yum package manager system.
		"""
		if self.os_type not in ['centos', 'redhat', 'amazon']:	return

		try:
			if not self._pkg_cache.endswith('/'):	self._pkg_cache += '/'
			if not self.__is_existed(self._pkg_cache+'epel-release-6-8.noarch.rpm'):
				utils.log("WARNING", "Cannot find the epel rpm package in %s" % self._pkg_cache, ("_enable_epel", self))
				return

			import subprocess
			if self.os_type in ['centos', 'redhat']:	# install with rpm on centos|redhat
				cmd = 'rpm -ivh ' + self._pkg_cache + 'epel-release-6-8.noarch.rpm'
			else:	# install with yum on amazon ami
				cmd = 'yum -y install epel-release'

			cmd += '; yum-config-manager --enable epel'

			devnull = open('/dev/null', 'w')
			subprocess.Popen(
				cmd,
				shell=True,
				stdout=devnull,
				stderr=devnull,
				)
		except Exception, e:
			utils.log("ERROR", str(e), ("_enable_epel", self))
			return

	def __mkdir(self, path):
		"""
			Check and make directory.
		"""
		if not os.path.isdir(path):
			try:
				os.makedirs(path)
			except OSError, e:
				utils.log("ERROR", "Create directory %s failed" % path, ("__mkdir", self))
				return False

		return True

	def __is_existed(self, files):
		"""
			Check files whether existed.
		"""
		file_list = []

		if isinstance(files, basestring):
			file_list.append(files)
		elif isinstance(files, list):
			file_list = files
		else:
			utils.log("WARNING", "No input files to check...", ("__is_existed", self))
			return

		the_file = None
		for f in file_list:
			if os.path.isfile(f):
				the_file = f
				break

		if not the_file:
			utils.log("WARNING", "No files in %s existed..." % str(files), ("__is_existed", self))
			return

		return the_file

# For unit tests only
def main():
        salt_opts = {
                'file_client':       'local',
                'renderer':          'yaml_jinja',
                'failhard':          False,
                'state_top':         'salt://top.sls',
                'nodegroups':        {},
                'file_roots':        '/srv/salt',
                'state_auto_order':  False,
                'extension_modules': '/var/cache/salt/minion/extmods',
                'id':                '',
                'pillar_roots':      '',
                'cachedir':          '/var/cache/madeira/',
                'test':              False,
                }

        states = {
                '_scribe_1_scm_git_git://github.com/facebook/scribe.git_latest' : {
                        "git": [
                                "latest",
                                {
                                        "name": "git://github.com/facebook/scribe.gits",
                                        "rev": "master",
                                        "target": "/madeira/deps/scribe",
                                        "user": "root"
                                }
                        ]
                }
        }

        runner = StateRunner(salt_opts)

        ret = runner.exec_salt(states)

        if ret:
                print json.dumps(ret, sort_keys=True,
                          indent=4, separators=(',', ': '))
        else:
                print "wait failed"

if __name__ == '__main__':
		main()
