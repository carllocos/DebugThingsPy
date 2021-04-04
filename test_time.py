from wasmtime import Store, Module, Instance, Config, Engine


#settings configution
config = Config()
config.debug_info = True
config.wasm_threads = False
config.wasm_module_linking = False

engine = Engine(config)
store: Store = Store(engine)

module = Module.from_file(store.engine, 'fac.wat')
instance = Instance(store, module, [])



if __name__ == "__main__":
    print(f'instance {instance}')



