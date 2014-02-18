'''
Madeira OpsAgent state runner

@author: Michael (michael@mc2.io)
'''

import os
import json

from salt.state import State

from opsagent import utils
from opsagent.exception import ExcutionException, OpsAgentException

class StateRunner(object):

	def __init__(self, config):

		self.state = None

		# init salt opts
		self._init_opts(config)

		# init state
		self._init_state()

		# get os type
		self.os_type = self.state.opts['grains']['os'].lower() if self.state.opts and \
			'grains' in self.state.opts and 'os' in self.state.opts['grains'] else 'unknown'

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

		if len(self._salt_opts['file_roots']['base']) == 0:		raise ExcutionException("Missing file roots argument")
		if not self.__mkdir(config['extension_modules']):		raise ExcutionException("Missing extension modules argument")

		self._salt_opts['extension_modules'] = config['extension_modules']

		if not self.__mkdir(config['cachedir']):	raise ExcutionException("Missing cachedir argument")

		self._salt_opts['cachedir'] = config['cachedir']

	def _init_state(self):
		"""
			Init salt state object.
		"""

		self.state = State(self._salt_opts)

	def exec_salt(self, states):
		"""
			Transfer and exec salt state.
			return result format: (result,comment,out_log), result:True/False
		"""

		result = False
		comment = ''
		out_log = ''

		# check
		if not states or not isinstance(states, list):
			out_log = "invalid state"
			return (result, comment, out_log)

		utils.log("INFO", "Begin to execute salt state...", ("exec_salt", self))
		for idx, state in enumerate(states):
			utils.log("INFO", "Begin to execute the %dth salt state..." % (idx+1), ("exec_salt", self))
			ret = self.state.call_high(state)
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

def main():

        import json

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
