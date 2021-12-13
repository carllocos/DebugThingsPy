# DebugThingsPy

A client-side out-of-things debugging tool for IoT devices that runs WebAssemby using [WOOD](https://github.com/carllocos/WOOD).
Similar to out-of-place, it supports local debugging of a remote application by bringing a debugsession (application and execution state) of a remote application to the developer side.


## Setup

To use the debugger we need to:
- Compile and execute WOOD locally. The application that runs locally is preferabely the one that also runs remotely and thus needs debugging. If the application is not the one that needs debugging, you can always use the upload functionality of the debugger to change it to the one that needs debugging. Once started local WOOD will start a in pause mode and start listening for incoming socket connections at port 8080.
- Flash WOOD alongside the application to debug on the remote ESP32. Similarly we can start from a Wasm application that does not need debugging and update app dynamically by means of the upload functionality. Once started WOOD will execute the provided application and start listening for incoming socket connection at port nr 80. 
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
     -   *single-stop*: the Debugger retrieves a debug session from the target application only for the first breakpoint that is reached. Once the debug session is retrieved, the debugger removes all the breakpoints (including the one that got reached) and resumes the execution of the application.
     -   *remove-and-proceed*: the debugger retrieves a debug session at each breakpoint. Once retrieved it also 1) removes the reached breakpoint and 2) resumes the application execution.
     -   *default*: the debugger retrieves the execution at each breakpoint, does not remove any breakpoint and leaves the application paused. Note that there is no need to write this value in the debug configuration file since it is the default behaviour.

<br>

To start the debugger run *dbg.py* in interactive mode ``python3.8 -i dbg.py``.


## Example:

```c

# Debugging examples/fac.wast 

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
> [else_instr] = rmt.module.linenr(30)
> rmt.addbreakpoint(else_instr) # adding bp at line 30
[INFO] added breakpoint
[INFO] reached breakpoint <line 30 (0x64): i32.const>
> loc.receive_session(rmt.session) # bringing session to local device
[INFO] `local` received debug session
> loc.step() # each debug action generates a new debug session version
[INFO] stepped
<things.debug_session.DebugSession object at 0x7f506d8be940>
> loc.restore_session(0)  # retore a particular debug session version
[INFO] `local` received debug session


# Uploading examples/blinkled.wast & performing Remote Function Calls for on and off functions
# blinkled app turns on and off a led connected on pin 26

> from web_assembly import WAModule
> blinkled_app = WAModule.from_file('examples/blinkled.wast')
> rmt.upload_module(blink_app) # upload dynamically a new Wasm to the remote device
[INFO] Module Updated
> rmt.pause() # pauses the execution on the remote VM. This leaves the led on or off.
[INFO] `remote` is paused
> loc.upload_module(blinkled_app, proxy=['$on', '$off']) # upload to local device and proxy 'on' and 'off' functions
[INFO] Module Updated
> loc.run() # Led will blink on remote device :)
```

## Documentation
### Debugger API

The API available to the *loc* and *rmt* Debugger objects.

 - `connect() -> None`: connects the debugger to VM using the *port* number and *host* from the config file.
 - `run() -> None`: runs the VM.

- `pause() -> None`: pauses the execution on the VM.

 - `step(amount: int = 1) -> DebugSession`: step to the next instruction. You can also step more than once by changing *amount*.

 - `step_over() -> DebugSession`: steps over and returns the new debug session which we also use to update the *session* property.

 - `add_breapkpoint(expr: Union[Expr, int]) -> None`: if *expr* is a Wasm instruction, it places a breakpoint at that particular instruction. If *expr* is an integer, then the debugger places a breakpoint at the first instruction available at that line number in the *module*.

 - `remove_breakpoint(inst: Union[Expr, int]) -> None`: If *instr* is an *Expr*, it removes the breakpoint set at that Wasm instruction. If *inst* is an integer, it removes a breakpoint set at line number *inst*. If more that one instruction is available at the line number, it removes the breakpoint set on the outerst instruction.


 - `session -> Union[None, DebugSession]`: a property that gives access to the current debug session. The session is avalaible only after reaching a breakpoint or after a call to *debug_session()*. Otherwise the property is set to *None*.
 
 - `module -> WAModule`: a property that gives access to Wasm module pointed by *program* value in the JSON config. This module is the Wasm application that is currently available on the device.

 - `upload_proxies(proxy: Union[None, List[str]) = None) -> None:` only for local VM. It provides the local VM a list of function names that needs proxying i.e. when local VM encounters a function call to any of those function names it performs a remote function invocation instead of executing the call locally. An exception is raised if any of the function names do not correspond with functions defined in the *module* property.

 - `upload_module(mod: WAModule, proxy: Union[List[str], None]= None) -> None`: upload the WAModule to the device and remote call the functions provided by the *proxy* list. This method allows to dynamically change the Wasm application that executes on the VM.

- `receive_session(debugsess: Debugsession) -> None`: send a debug session to the VM.

- `debug_session() -> DebugSession:` forces the retrieval of a debug session on the device. After completion of the method call, the device is left in a paused state and the debug session is made available on the *session* property.

- `restore_session(version_nr:int) -> Union[DebugSession, None]:` a method that allows to go back in time. It restores the current debug session on the VM to the given *version_nr*. If such version number does not exist it returns *None* otherwise it returns the restored *Debugsession*.

<br>

### WAModule API

The API availalbe for WAModule objects (web_assembly/wamodule.py).

-  `types() -> Types`: property that gives access to a *Types object* (web_assembly/types.py). A Types object corresponds with the types component of a module. 
  ```c
     > fac_mod = WAModule.from_file('examples/fac.wast')
     > types = fac_mod.types
     > types.start # start address of the types component
     > types.end # end address of the types component
     > types[0]  # first type definition in types component
     ['i32'] -> None
     > types['$i32toi32']  # type definition with name '$i32toi32'
     ['i32'] -> i32
  ```
- `functions() -> Functions`: proprety that gives access to a *Functions* object (web_assembly/func.py). Corresponds with the functions component defined in the module.
  ```c
     > fac_mod = WAModule.from_file('examples/fac.wast')
     > funcs = fac_mod.functions
     > funcs.start # start address of the types component
     > funcs.end # end address of the types component
     > funcs[0]  # first function definition in functions component.
     > fac = funcs['$fac']  # function object with name '$fac'
     > fac.idx # id of function in module
     > fac.name # name of function in module
     > fac.code # a *Code object* that corresponds with the code section of the function in the module.
     > fac.locals # List of *Local objects* that corresponds with the variables defined in the function.
     > funcs.exports # list of functions in the module marked as export
     > funcs.imports # list of functions in the module marked as import
     ['i32'] -> i32
  ```

-  `exports() -> List[Function]`: retuns a list of the Funtion objects (web_assembly/func.py) that are defined in the module and marked as export.

-  `imports() -> List[Function]`: retuns a list of the Funtion objects (web_assembly/func.py) that are defined in the module and marked as import.

- `filepath(self) -> Union[str, None]`: path to the source file used to generate the WAModule object.
    def linenr(self, nr: int):

-  `addr(addr: Union[str, int]) -> Union[Expr, None]`:

- `compile() -> bytes`: compile the current wast source file into bytes using *wabt*.


- `codes(self) -> Codes`: a *Codes* objects that provides access to code section of the module. For each function we also forsee a *Code* object.
 ```c
     > fac_mod = WAModule.from_file('examples/fac.wast')
     > codes = fac_mod.codes
     > codes['0x52']  # instruction at hexa address '0x52'
      <line 26 (0x5e): call>
     > codes[94] # same as before but with integer
     > fac_body = codes[1]  # code section of function with ID 1
     > assert fac_body['0x52'] == codes['0x52']
     > codes.linenr(34) # instructions at linenr 34
     > fac_body.linenr(27)
     > fac_body.expressions # list of all expressions in the body of the function
     > fac_body.exp_type('i32.const') # list of all the expressions of type 'i32.const' in the function.
     > fac_body.next_instruction(fac_body['0x52']) # the instruction that follow the argument instruction in the code section.
  ```

- `from_file(path: str, out: Union[str, None] = None) -> WAModule`: static method that generates a WAModule from a wast source file pointed by *path*. The *out* argument specifies a location where files generated for the source can be temporary stored. If not provided, the *out* of the JSON config is used instead.


<br>

### DebugSession API

The API avaible for *DebugSession* objects (things/debug_session.py).


- `breakpoints() -> List[str]`: list of hexa addresses where a breakpoint has been set on the VM.

-  `version() -> Union[int, None]`: the version number of the session. Initialy set to zero when the first debug session is retrieved. Each operation that affects a debug session i.e. the execution and application state (e.g. step) will increase the number.

- `pc_error() -> Union[Expr, None]`: the instruction address that caused the an exception on the VM or caused the VM to restart. Is updated at each newly exception or restart.

- `exception() -> Union[str, None]`: the exception messages raised by the VM when an exception got raised. This value is only set if the debugger was connected to the VM at the moment the exception occured.
    
- `module() -> WAModule`: the module to which the debug session belongs to.

- `callstack() -> CallStack`: a property that gives access to a CallStack object that represents the callstack of the VM.

- 'stack() -> Stack': a property that gives access to a Stack object that represents the stack of values in the VM.

- `memory() -> Memory`: access to the memory pages used in the Wasm app.

- `table() -> Table`: access to the table used in the Wasm app.

- `br_table()) -> List[int]:` the table of values used by branching instructions (e.g. br).

- `globals() -> Globals`: access to the global variables/values used in the Wasm app.

- `pc() -> Union[Expr, None]`: the position of the program counter

-  `modified(self) -> bool`: checks if this debug session version got modified since the retrieval.

-  `to_json(self) -> dict`: shoul be changed. Returns a dictionary of the current debug session and thus not a JSON.

- `from_json(_json: dict, module: WAModule, device: Device) -> DebugSession`: should be called *from_dict* generates a DebugSession object from a dictionary.


## TODO's
- Start local WOOD alongside the debugger using the configuration file.
- Logger
- Add tests
- Make the debugger a command line tool.
- Discover mode
- Allow manual changes on the debug session