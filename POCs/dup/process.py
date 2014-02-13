import subprocess, select, sys, os

call = ["bash","dup.sh"]
process = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
logs = {process.stdout: open("out.log", "w"), process.stderr: open("err.log", "w")}
done = {process.stdout: False, process.stderr: False}
while (process.poll() is None) or (not all(done.values())):
    ready = select.select([process.stdout, process.stderr], [], [])[0]
    for stream in ready:
        data = os.read(stream.fileno(), 1)
        if data:
            sys.stdout.write(data)
            logs[stream].write(data)
        else:
            done[stream] = True
logs[process.stdout].close()
logs[process.stderr].close()
