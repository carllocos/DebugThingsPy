(module
 (import "env" "chip_pin_mode"      (func $pin_mode         (type $ii2v)))
 (import "env" "chip_digital_write" (func $digital_write    (type $ii2v)))
 (import "env" "chip_delay"         (func $delay            (type $i2v)))

 (; Type declarations ;)
 (type $ii2v (func (param i32) (param i32) (result)))
 (type $i2v (func (param i32)             (result)))
 (type $v2v (func (param)                 (result)))

 (; Define one function ;)
 (export "main" (func $blink_loop))

 (func $wait (type $v2v)
    (i32.const 500)
    (call $delay))

 (func $on (type $v2v)
    (i32.const 26)
    (i32.const 1)
    (call $digital_write))

 (func $off (type $v2v)
    (i32.const 26)
    (i32.const 0)
    (call $digital_write))

 (func $blink_loop (type $v2v)
   (i32.const 26)
   (i32.const 2)
   (call $pin_mode)
  (loop

    (call $on)
    (call $wait)

    (call $off)
    (call $wait)
    (br 0)))
)
