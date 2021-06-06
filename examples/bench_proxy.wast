(module
 (import "env" "chip_delay"   (func $delay     (type $i32tovoid)))
 (import "env" "sht3x_ctemp"  (func $ctemp  (type $voidtof32)))
 (import "env" "write_f32"    (func $sendTemp  (type $f32tovoid)))

 (type $i32tovoid  (func (param i32) (result)))
 (type $voidtovoid (func (param) (result)))
 (type $voidtof32  (func (param) (result f32)))
 (type $f32tovoid  (func (param f32) (result)))

 (export "main"    (func $main))

 (func $getCTemp (type $voidtof32)
    (call $ctemp))

 (func $main (type $voidtovoid)
    (loop 
       (call $getCTemp)
       (call $sendTemp)

       ;;sleep 1sec
       (i32.const 1000)  
       (call $delay)
       (br 0)))
)