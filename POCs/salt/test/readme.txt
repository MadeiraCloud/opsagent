.
|-- etc\	#config dir
|   |-- module.lst #module list to test
|   `-- json\	   #test json for each module
|-- one.sh	#test single module
|-- rlt\	#output for all.sh
`-- all.sh	#test all module

usage:
1.test all module
./all.sh

2.test one module (copy etc\json\xxx.json to ..\api.json eachtime)
./one.sh

3.test by manual
vim /opt/madeira/env/lib/python2.7/site-packages/opsagent/state/api.json 
cd /opt/madeira/env/lib/python2.7/site-packages/opsagent/state
/opt/madeira/env/bin/python adaptor.py
