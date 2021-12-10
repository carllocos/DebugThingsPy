# DebugThingsPy

A client-side out-of-things debugging tool for IoT devices that runs WebAssemby using [WOOD](https://github.com/carllocos/WOOD).
Similar to out-of-place, it supports local debugging of a remote application by bringing a debugsession (application and execution state) of a remote application to the developer side.


## Setup

To use the debugger we need to:
- Compile and execute WOOD locally. The program that runs locally could be anything given that we can change it dynamically later on.
- Flash WOOD alongside the application to debug on the remote ESP32. Similarly we can flash any Wasm application since we can update the Wasm app dynamically.
- Create a JSON configuration file named *.dbgconfig.json* with the following content:
````
 {
	"program": "examples/fac.wast"
	"out":"out/",
	"proxy": ["fac"],
	"devices": [
		{
			"name": "remote",
			"host": "IP Address",
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
- *program*: path to the Wast source file that needs debugging.
- *out*: path to where to dump all the files generated throughout debugging.
- *devices*: list of devices that needs debugging. Currently only support for two devices. A device has the following content:
  -  *name*: gives a name to the device. This value is for convenience.
  -  *host*: the IP address of the remote device. Only meant for the remote device.
  -  *port*: port number of the socket. Currently fixed to 80 and 8080 for respectively the remote and local device.
  -  *enable*: enables or disables the debugging of the device. will be removed in the future.
  -  *serial*: the serial address of the device. Currently not supported.
  -  *policy*: configures the debugger on how to behave once a breakpoint is reached on the corresponding device. Possible values:
     -   *single-stop*: the Debugger Manager retrieves a debug session from the target application only for the first breakpoint that is reached. Once the debug session is retrieved, the debugger removes all the breakpoints (including the one that got reached) and resumes the execution of the application.
     -   *remove-and-proceed*: the debugger retrieves a debug session at each breakpoint. Once retrieved it also 1) removes the reached breakpoint and 2) resumes the application execution.
     -   *default*: the debugger retrieves the execution at each breakpoint, does not remove any breakpoint and leaves the application paused. Note that there is no need to write this value in the debug configuration file since it is the default behaviour.

<br>

To start the debugger run *dbg.py* in interactive mode ``python3.8 -i dbg.py``.


## Example:

```c

# Debugging Factorial 

python3.8 -i dbg.py
> loc # local VM
<things.debug.Debugger object at 0x7f2b2ad42640>
> rmt # remote VM
<things.debug.Debugger object at 0x7f2b2ad42550>
> rmt.connect()
[INFO] connected to `remote`
> loc.connect()
[INFO] connected to `local`
> rmt.module # Wasm (instance of WAModule) running on the remote VM
<web_assembly.wamodule.WAModule object at 0x7f2b2ad42460>
> rmt.module.linenr(30) # list of instr at line 30
[<line 30 (0x7b): i32.const>]
> [else_line] = rmt.module.linenr(30)
> rmt.addbreakpoint(else_line) # adding bp at line 30
[INFO] added breakpoint
[INFO] reached breakpoint <line 30 (0x64): i32.const>
> loc.receive_session(rmt.session) # bringing session to local device
[INFO] `local` received debug session
> loc.step() # each debug action generates a new debug session version
[INFO] stepped
<things.debug_session.DebugSession object at 0x7f506d8be940>
> loc.restore_session(0)  # retore a particular debug session version
[INFO] `local` received debug session


# Uploading Wasm & performing Remote Function Calls

> from web_assembly import WAModule
> blinkled_app = WAModule.from_file('examples/blinkled.wast')
> rmt.upload_module(blink_app) # upload dynamically a new Wasm to the remote device
[INFO] Module Updated
> loc.upload_module(blinkled_app, proxy=['$on', '$off']) # upload to local device and proxy 'on' and 'off' functions
[INFO] Module Updated
> loc.run() # Led will blink on remote device :)
```

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



## TODO's
- Start local WOOD alongside the debugger using the configuration file.
- Logger
- Add tests
- Make the debugger a command line tool.
