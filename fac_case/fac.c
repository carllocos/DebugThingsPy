unsigned char fac_wasm[] = {
  0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00, 0x01, 0x0e, 0x03, 0x60,
  0x01, 0x7f, 0x00, 0x60, 0x00, 0x00, 0x60, 0x02, 0x7e, 0x7f, 0x01, 0x7f,
  0x03, 0x04, 0x03, 0x00, 0x02, 0x01, 0x07, 0x08, 0x01, 0x04, 0x6d, 0x61,
  0x69, 0x6e, 0x00, 0x02, 0x0a, 0x37, 0x03, 0x02, 0x00, 0x0b, 0x1c, 0x00,
  0x20, 0x01, 0x41, 0x01, 0x4a, 0x04, 0x7f, 0x20, 0x00, 0x42, 0x01, 0x7c,
  0x20, 0x01, 0x41, 0x01, 0x6b, 0x10, 0x01, 0x20, 0x01, 0x6c, 0x05, 0x41,
  0x01, 0x0b, 0x0b, 0x15, 0x01, 0x01, 0x7f, 0x41, 0x05, 0x21, 0x00, 0x03,
  0x40, 0x42, 0x0d, 0x20, 0x00, 0x10, 0x01, 0x10, 0x00, 0x0c, 0x00, 0x0b,
  0x0b
};
unsigned int fac_wasm_len = 97;
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
0000013: 02                                        ; num params
0000014: 7e                                        ; i64
0000015: 7f                                        ; i32
0000016: 01                                        ; num results
0000017: 7f                                        ; i32
0000009: 0e                                        ; FIXUP section size
; section "Function" (3)
0000018: 03                                        ; section code
0000019: 00                                        ; section size (guess)
000001a: 03                                        ; num functions
000001b: 00                                        ; function 0 signature index
000001c: 02                                        ; function 1 signature index
000001d: 01                                        ; function 2 signature index
0000019: 04                                        ; FIXUP section size
; section "Export" (7)
000001e: 07                                        ; section code
000001f: 00                                        ; section size (guess)
0000020: 01                                        ; num exports
0000021: 04                                        ; string length
0000022: 6d61 696e                                main  ; export name
0000026: 00                                        ; export kind
0000027: 02                                        ; export func index
000001f: 08                                        ; FIXUP section size
; section "Code" (10)
0000028: 0a                                        ; section code
0000029: 00                                        ; section size (guess)
000002a: 03                                        ; num functions
; function body 0
000002b: 00                                        ; func body size (guess)
000002c: 00                                        ; local decl count
000002d: 0b                                        ; end
000002b: 02                                        ; FIXUP func body size
; function body 1
000002e: 00                                        ; func body size (guess)
000002f: 00                                        ; local decl count
0000030: 20                                        ; local.get
0000031: 01                                        ; local index
0000032: 41                                        ; i32.const
0000033: 01                                        ; i32 literal
0000034: 4a                                        ; i32.gt_s
0000035: 04                                        ; if
0000036: 7f                                        ; i32
0000037: 20                                        ; local.get
0000038: 00                                        ; local index
0000039: 42                                        ; i64.const
000003a: 01                                        ; i64 literal
000003b: 7c                                        ; i64.add
000003c: 20                                        ; local.get
000003d: 01                                        ; local index
000003e: 41                                        ; i32.const
000003f: 01                                        ; i32 literal
0000040: 6b                                        ; i32.sub
0000041: 10                                        ; call
0000042: 01                                        ; function index
0000043: 20                                        ; local.get
0000044: 01                                        ; local index
0000045: 6c                                        ; i32.mul
0000046: 05                                        ; else
0000047: 41                                        ; i32.const
0000048: 01                                        ; i32 literal
0000049: 0b                                        ; end
000004a: 0b                                        ; end
000002e: 1c                                        ; FIXUP func body size
; function body 2
000004b: 00                                        ; func body size (guess)
000004c: 01                                        ; local decl count
000004d: 01                                        ; local type count
000004e: 7f                                        ; i32
000004f: 41                                        ; i32.const
0000050: 05                                        ; i32 literal
0000051: 21                                        ; local.set
0000052: 00                                        ; local index
0000053: 03                                        ; loop
0000054: 40                                        ; void
0000055: 42                                        ; i64.const
0000056: 0d                                        ; i64 literal
0000057: 20                                        ; local.get
0000058: 00                                        ; local index
0000059: 10                                        ; call
000005a: 01                                        ; function index
000005b: 10                                        ; call
000005c: 00                                        ; function index
000005d: 0c                                        ; br
000005e: 00                                        ; break depth
000005f: 0b                                        ; end
0000060: 0b                                        ; end
000004b: 15                                        ; FIXUP func body size
0000029: 37                                        ; FIXUP section size
*/
