(module
  (type (;0;) (func))
  (type (;1;) (func (param i32 i32)))
  (type (;2;) (func (result i32)))
  (type (;3;) (func (param i32 i32) (result i32)))
  (import "env" "memory" (memory (;0;) 0))
  (func (;0;) (type 0)
    nop)
  (func (;1;) (type 1) (param i32 i32)
    local.get 1
    local.get 0
    i32.load offset=8
    local.get 0
    i32.load offset=4
    local.get 1
    i32.load
    local.get 0
    i32.load
    i32.add
    i32.add
    i32.add
    i32.const 20
    i32.add
    i32.store)
  (func (;2;) (type 2) (result i32)
    i32.const 244)
  (func (;3;) (type 3) (param i32 i32) (result i32)
    i32.const 244)
  (global (;0;) i32 (i32.const 0))
  (export "__wasm_apply_relocs" (func 0))
  (export "bar" (func 1))
  (export "__original_main" (func 2))
  (export "main" (func 3))
  (export "__dso_handle" (global 0))
  (export "__post_instantiate" (func 0)))
