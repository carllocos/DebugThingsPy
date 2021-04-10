(module
 (; Type declarations ;)
 (type $i32tov (func (param i32) (result)))
 (type $i32toi32 (func (param i32) (result i32)))
 (type $f32tov (func (param f32) (result )))
 (type $f64tov (func (param f64) (result )))
 (type $i64tov (func (param i64) (result )))
 (type $v2v (func (param) (result)))

 (; Define one function ;)
 (export "main" (func $main))
 (memory 2)
 (table funcref (elem  $main $ff64tov $fi64tov $ff32tov $fi32tov))

 (func $fi32tov (type $i32tov))
 (func $ff32tov (type $f32tov))
 (func $fi64tov (type $i64tov))
 (func $ff64tov (type $f64tov))
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

    (loop 
       (local.get $f32 )
       (local.get $f64 )
       (local.get $i32 )
       (local.get $i64 )


			 (i32.const 5)
			 (call $fac)
			 (call $fi32tov)
			 (call $fi64tov)
			 (call $fi32tov)
			 (call $ff64tov)
			 (call $ff32tov)

       (br 0)))

 (; (start $fac5) ;)
)

