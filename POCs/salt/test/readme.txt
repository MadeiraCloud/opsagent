[description]
.
|-- etc/	#config dir
|   |-- module.lst #module list to test
|   `-- json/	   #test json for each module
|-- step.sh	#test single module
|-- rlt/	#output for run.sh
`-- run.sh	#test all module

[prepare]
copy test/ to /opt/madeira/env/lib/python2.7/site-packages/opsagent/state/
cd /opt/madeira/env/lib/python2.7/site-packages/opsagent/state/test
chmod 755 *.sh

[usage]
1.test all module
./run.sh

2.test single module (copy etc\json\xxx.json to ..\api.json eachtime)
./step.sh

3.test by manual
cd /opt/madeira/env/lib/python2.7/site-packages/opsagent/state
vim api.json 
/opt/madeira/env/bin/python adaptor.py
