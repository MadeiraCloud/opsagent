# -*- coding: utf-8 -*-
'''
Execution Module Directory
'''

def state_std(kwargs, res):
	if kwargs and kwargs.has_key('state_ret'):
		kwargs['state_ret']['state_stdout'] += res['stdout'] + '\n'
