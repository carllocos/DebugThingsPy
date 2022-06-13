(module
  (type $t0 (func (param i32 i32)))
  (type $t1 (func (param i32 i32 i32)))
  (type $void->i32 (func (result i32)))
  (type $void->void (func))

  (; (import "env" "chip_pin_mode" (func $env.chipPinMode (type $t0))) ;)
  (import "env" "chip_ledc_analog_write" (func $env.analogWrite (type $t1)))
  (import "env" "chip_ledc_setup" (func $env.ledcSetup (type $t1)))
  (import "env" "chip_ledc_attach_pin" (func $env.ledcAttachPin (type $t0)))
  (import "env" "subscribe_interrupt" (func $env.subscribeInterrupt (type $t1)))

  (global $led i32 (i32.const 10)) ;; analog led pin
  (global $brigthness (mut i32) (i32.const 0))
  (global $delta (mut i32) (i32.const 0))
  (global $upButton i32 (i32.const 37)) ;; home button on m5stickc
  (global $channel i32 (i32.const 0))


  (func $incrDelta  (type $void->void)
      (i32.add (global.get $delta) (i32.const 10))
      global.set $delta)
      
  (func $initLed (type $void->void)
      (local $freq i32)
      (local $ledcTimer i32)
      (local.set $freq (i32.const 5000))
      (local.set $ledcTimer (i32.const 12))

    ;; Set pin mode
    (; (i32.const 2) ;)
    
    global.get $channel
    local.get $freq
    local.get $ledcTimer
    call $env.ledcSetup

    global.get $led
    global.get $channel
    call $env.ledcAttachPin)

  (func $isDeltaNotZero (type $void->i32)
    (i32.ne (i32.const 0)
            (global.get $delta)))

  (func $updateBrightness (type $void->void)
      (local $maxValue i32)
      (local.set $maxValue (i32.const 255))

      ;; change global $brigthness
      (i32.add (global.get $brigthness)
               (global.get $delta))
      global.set $brigthness
      ;; TODO add if for >= 255

      ;; write to pin
      global.get $channel
      global.get $brigthness
      local.get $maxValue
      call $env.analogWrite
      (; global.get $brigthness ;)
      (; global.get $led ;)
      (; call $env.analogWrite ;)

      ;; reset delta
      i32.const 0
      global.set $delta
)
  

  (func $main (type $void->void)

    call $initLed

    ;; register up Button
    global.get $upButton
    i32.const 0 ;; $incrDelta function ID
    i32.const 2 ;; onChange
    call $env.subscribeInterrupt

    (loop $infinite
      (if (call $isDeltaNotZero)
          (then
              (call $updateBrightness))
          (else nop))
      (br $infinite)))

  (export "main" (func $main)))
