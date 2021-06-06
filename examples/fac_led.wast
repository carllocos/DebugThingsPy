(module
 (import "env" "chip_pin_mode"      (func $pin_mode         (type $ii2v)))
 (import "env" "chip_digital_write" (func $digital_write    (type $ii2v)))
 (import "env" "chip_delay"         (func $delay            (type $i2v)))

 (; Type declarations ;)
 (type $ii2v (func (param i32) (param i32) (result)))
 (type $i2v (func (param i32)             (result)))
 (type $i32tov (func (param i32) (result)))
 (type $i32toi32 (func (param i32) (result i32)))
 (type $v2v (func (param) (result)))

 (; Define one function ;)
 (export "main" (func $main))
 (memory 2)
 (table funcref (elem  $main))

 (global $g1  i32   (i32.const 0)) ;; memory ix where gamestate starts
 (global $g2 (mut i32) (i32.const 0)) ;; emptyboardFuncIxd

 (func $wait (type $v2v)
    (i32.const 500)
    (call $delay))

 (func $toggle (type $i32tov)
  (if (i32.gt_s
        (local.get 0)
        (i32.const 0))
      (then
        (i32.const 26)
        (i32.const 0)
        (call $digital_write))
      (else
        (i32.const 26)
        (i32.const 1)
        (call $digital_write)))
    (call $wait))

 (func $fac (type $i32toi32)
     (i32.gt_s
       (local.get 0)
       (i32.const 1))
     (if (result i32)
       (then 
         (i32.sub 
           (local.get 0)
           (i32.const 1))
         (call $fac)
         (local.get 0)
         i32.mul)
       (else
				 (i32.const 1))))

 (func $main (type $v2v)
       (local $f32 f32)
       (local $f64 f64)
       (local $i32 i32)
       (local $i64 i64)
			 (local.set $f32 (f32.const 32.3232))
			 (local.set $f64 (f64.const 64.646464))
			 (local.set $i32 (i32.const 32))
			 (local.set $i64 (i64.const 64))

       (i32.const 26)
       (i32.const 2)
       (call $pin_mode)

    (loop 

			 (i32.const 5)
			 (call $fac)
			 (call $toggle)

       (br 0)))

)

