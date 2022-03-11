(module
  (import "env" "chip_delay"  (func $delay      (type $i32tovoid)))
  (import "env" "bmp_ctemp"   (func $ctemp      (type $voidtof32)))
  (import "env" "write_f32"   (func $sendtemp   (type $f32tovoid)))

  (type $i32tovoid  (func (param i32) (result)))
  (type $void2void  (func (param) (result)))
  (type $voidtof32  (func (param) (result f32)))
  (type $f32tovoid  (func (param f32) (result)))

  (export "main"    (func $main))

  (func $main (type $void2void)
    (loop 
      (call $ctemp)
      (call $sendtemp)

      (i32.const 1000)
      (call $delay)
      (br 0))))
