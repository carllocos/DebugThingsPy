# DebugThingsPy
An out-of-place debugging tool for IoT devices.




## Setup


Create a configuration file  of the form:
````
 {
	"program": "examples/fac.wast"
	"out":"out/",
	"proxy": ["fac"],
	"devices": [
		{
			"name": "M5stickC",
			"host": "ip addr",
			"port": 80,
			"serial": "/dev/ttyUSB0",
			"policy": "single-stop",
			"enable": true

		},
		{
			"name": "local",
			"port": 8080,
			"enable": true
		}
	]

}
````


<br>

To start the debugger execute

```c
> loc # access to the local VM
> rmt # access to the remote VM
> rmt.module # instance of WAModule access to Wasm running on the remote VM

> module.linenr(38) # list of instr at line 38
> loc.addbreakpoint(module.linenr(38)[0])
> loc.session.caal


```
> python3.8 -i dbg.py


## Debugger API

 - connect(): connects debugger to VM
 - run() : runs VM
 - step(): step to next instruction
 - step_ove(): steps over
 - add_breapkpoint(linenr) :  places a breakpoint at given line number
 - remove_breakpoint(linenr) :  remove a breakpoint at given line number
 - session: gives the debug session (generated only after reaching a breakpoint)
 - module : access to Wasm module being debugged

 - upload_proxies(list of strings) : takes a list of functions names that need proxying.

 - upload_module(WAModule):  upload the WAModule to the device. This allows to dynamically change Wasm to execute on the VM

- receive_session(a Debugsession): send a debug session (instance of DebugSession) to the VM

Example

```c
> rmt.connect()
> instructions = rmt.module.linenr(38)
> post_fac_call = instructions[0]
> rmt.add_breakpoint(post_fac_call)
> rmt.session.callstack.print()
> rmt.session.stack.print()

> rmt.run() # resumes 

```