(module
 (import "env" "chip_delay"   (func $delay       (type $i32tovoid)))
 (import "env" "sht3x_ctemp"  (func $reqTemp     (type $i32tof32)))
 (import "env" "isConnected"  (func $isConnected (type $i32toi32)))

 (type $i32tovoid  (func (param i32) (result)))
 (type $i32toi32   (func (param i32) (result i32)))
 (type $i32tof32   (func (param i32) (result f32)))
 (type $voidtovoid (func (param) (result)))
 (type $voidtof32  (func (param) (result f32)))
 (type $f32tovoid  (func (param f32) (result)))

 (export "main"    (func $main))

 (global $sensorA i32 (i32.const 3030))
 (global $sensorB i32 (i32.const 3031))
 (global $connected (mut f32) (f32.const 0))

(func $regulate (type $f32tovoid) nop)
(func $inc_connected (type $voidtovoid)
    (f32.add
      (global.get $connected)
      (f32.const 1)
    )
    (global.set $connected))

(func $getTemp (type $i32tof32)
    (local.get 0)
    (call $isConnected)
    (if (result f32)
        (then 
         (call $inc_connected)
         (local.get 0)
         (call $reqTemp))
        (else
          (f32.const 0.0))))

(func $allTemps (type $voidtof32)
    (global.get $sensorA)
    (call $getTemp)
    (global.get $sensorB)
    (call $getTemp)
    f32.add
)


 (func $main (type $voidtovoid)
    (loop 
       (global.set $connected (f32.const 0))

       (call $allTemps)
       (global.get $connected)
       f32.div

       (call $regulate)

       ;;sleep 5sec
       (i32.const 5000)
       (call $delay)
       (br 0)))
)