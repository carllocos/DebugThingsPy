(module
  (type (;0;) (func))
  (type (;1;) (func (param i32 i32) (result i32)))
  (type (;2;) (func (result i32)))
  (import "env" "memory" (memory (;0;) 0))
  (func $__wasm_call_ctors (type 0)
    call $__wasm_apply_relocs)
  (func $__wasm_apply_relocs (type 0)
    nop)
  (func $fact (type 1) (param i32 i32) (result i32)
    (local i32 i32)
    local.get 1
    i32.load offset=4
    local.set 2
    loop  ;; label = @1
      local.get 2
      local.set 3
      block  ;; label = @2
        local.get 0
        local.get 2
        i32.eq
        br_if 0 (;@2;)
        local.get 0
        i32.const 2
        i32.ge_s
        if  ;; label = @3
          local.get 1
          i32.load
          local.get 0
          i32.mul
          local.set 3
          br 1 (;@2;)
        end
        i32.const 1
        return
      end
      local.get 1
      local.get 3
      i32.store
      local.get 0
      i32.const -1
      i32.add
      local.set 0
      br 0 (;@1;)
    end
    unreachable)
  (func $__original_main (type 2) (result i32)
    loop  ;; label = @1
      br 0 (;@1;)
    end
    unreachable)
  (func $main (type 1) (param i32 i32) (result i32)
    call $__original_main)
  (func $__post_instantiate (type 0)
    call $__wasm_call_ctors)
  (global (;0;) i32 (i32.const 0))
  (export "__wasm_apply_relocs" (func $__wasm_apply_relocs))
  (export "fact" (func $fact))
  (export "__original_main" (func $__original_main))
  (export "main" (func $main))
  (export "__dso_handle" (global 0))
  (export "__post_instantiate" (func $__post_instantiate)))
