unsigned char fac_wasm[] = {
  0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00, 0x01, 0x0d, 0x03, 0x60,
  0x01, 0x7f, 0x00, 0x60, 0x00, 0x00, 0x60, 0x01, 0x7f, 0x01, 0x7f, 0x03,
  0x04, 0x03, 0x00, 0x02, 0x01, 0x07, 0x08, 0x01, 0x04, 0x6d, 0x61, 0x69,
  0x6e, 0x00, 0x02, 0x0a, 0x2a, 0x03, 0x02, 0x00, 0x0b, 0x17, 0x00, 0x20,
  0x00, 0x41, 0x01, 0x48, 0x04, 0x7f, 0x41, 0x01, 0x05, 0x20, 0x00, 0x41,
  0x01, 0x6b, 0x10, 0x01, 0x20, 0x00, 0x6c, 0x0b, 0x0b, 0x0d, 0x00, 0x03,
  0x40, 0x41, 0x05, 0x10, 0x01, 0x10, 0x00, 0x0c, 0x00, 0x0b, 0x0b
};
unsigned int fac_wasm_len = 83;
/*
0000000: 0061 736d                                 ; WASM_BINARY_MAGIC
0000004: 0100 0000                                 ; WASM_BINARY_VERSION
; section "Type" (1)
0000008: 01                                        ; section code
0000009: 00                                        ; section size (guess)
000000a: 03                                        ; num types
; type 0
000000b: 60                                        ; func
000000c: 01                                        ; num params
000000d: 7f                                        ; i32
000000e: 00                                        ; num results
; type 1
000000f: 60                                        ; func
0000010: 00                                        ; num params
0000011: 00                                        ; num results
; type 2
0000012: 60                                        ; func
0000013: 01                                        ; num params
0000014: 7f                                        ; i32
0000015: 01                                        ; num results
0000016: 7f                                        ; i32
0000009: 0d                                        ; FIXUP section size
; section "Function" (3)
0000017: 03                                        ; section code
0000018: 00                                        ; section size (guess)
0000019: 03                                        ; num functions
000001a: 00                                        ; function 0 signature index
000001b: 02                                        ; function 1 signature index
000001c: 01                                        ; function 2 signature index
0000018: 04                                        ; FIXUP section size
; section "Export" (7)
000001d: 07                                        ; section code
000001e: 00                                        ; section size (guess)
000001f: 01                                        ; num exports
0000020: 04                                        ; string length
0000021: 6d61 696e                                main  ; export name
0000025: 00                                        ; export kind
0000026: 02                                        ; export func index
000001e: 08                                        ; FIXUP section size
; section "Code" (10)
0000027: 0a                                        ; section code
0000028: 00                                        ; section size (guess)
0000029: 03                                        ; num functions
; function body 0
000002a: 00                                        ; func body size (guess)
000002b: 00                                        ; local decl count
000002c: 0b                                        ; end
000002a: 02                                        ; FIXUP func body size
; function body 1
000002d: 00                                        ; func body size (guess)
000002e: 00                                        ; local decl count
000002f: 20                                        ; local.get
0000030: 00                                        ; local index
0000031: 41                                        ; i32.const
0000032: 01                                        ; i32 literal
0000033: 48                                        ; i32.lt_s
0000034: 04                                        ; if
0000035: 7f                                        ; i32
0000036: 41                                        ; i32.const
0000037: 01                                        ; i32 literal
0000038: 05                                        ; else
0000039: 20                                        ; local.get
000003a: 00                                        ; local index
000003b: 41                                        ; i32.const
000003c: 01                                        ; i32 literal
000003d: 6b                                        ; i32.sub
000003e: 10                                        ; call
000003f: 01                                        ; function index
0000040: 20                                        ; local.get
0000041: 00                                        ; local index
0000042: 6c                                        ; i32.mul
0000043: 0b                                        ; end
0000044: 0b                                        ; end
000002d: 17                                        ; FIXUP func body size
; function body 2
0000045: 00                                        ; func body size (guess)
0000046: 00                                        ; local decl count
0000047: 03                                        ; loop
0000048: 40                                        ; void
0000049: 41                                        ; i32.const
000004a: 05                                        ; i32 literal
000004b: 10                                        ; call
000004c: 01                                        ; function index
000004d: 10                                        ; call
000004e: 00                                        ; function index
000004f: 0c                                        ; br
0000050: 00                                        ; break depth
0000051: 0b                                        ; end
0000052: 0b                                        ; end
0000045: 0d                                        ; FIXUP func body size
0000028: 2a                                        ; FIXUP section size
*/
