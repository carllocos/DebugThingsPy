(module
 (import "env" "chip_delay"   (func $delay       (type $i32tovoid)))
 (import "env" "print"        (func $print       (type $f32tovoid)))
 (import "env" "req_temp"  (func $reqTemp     (type $i32tof32)))
 (import "env" "is_connected" (func $isConnected (type $i32toi32)))

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

(func $inc_connected (type $voidtovoid)
    (f32.add
      (global.get $connected)
      (f32.const 1))
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

(func $avgTemp (type $voidtof32)
    (local $sum f32)
    (global.get $sensorA)
    (call $getTemp)
    (global.get $sensorB)
    (call $getTemp)
    f32.add
    (local.set $sum)

    (f32.eq 
        (global.get $connected)
        (f32.const 0))
    (if (result f32)
        (then
            (f32.const 0.0))
        (else 
            (local.get $sum)
            (global.get $connected)
            f32.div)))


 (func $main (type $voidtovoid)
    (loop 
       (global.set $connected (f32.const 0))
       (call $avgTemp)
       (call $print)
       ;;sleep 3sec
       (i32.const 3000)
       (call $delay)
       (br 0)))
)
