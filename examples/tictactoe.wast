(module

 (type $i2v (func (param i32) (result)))
 (type $v2v (func (param) (result)))
 (type $v2i (func (result i32)))
 (type $i2i (func (param i32) (param i32) (result i32)))

 (export "main" (func $main ))

 (memory 3);; WARDUINO BUG?
 (table funcref (elem  $emptyboard $isFull $play))

 ;;Memory GameState stored as
 ;;   Index Board Start, size board, Char _, Char O, Char X, freePos
 (global $gameStateAddr  i32   (i32.const 0)) ;; memory ix where gamestate starts
 (global $nextAction (mut i32) (i32.const 0)) ;; emptyboardFuncIxd
 (global $currentPlayer (mut i32) (i32.const 79)) ;;Player O starts

 ;;Function Indexes Getters
 (func $isFull (type $v2v)
			 (local $playFuncIdx i32)
			 (local $emptyBoardFuncIdx i32)
			 (local $boardSize i32)

			 (local.set $playFuncIdx (i32.const 2))
			 (local.set $emptyBoardFuncIdx (i32.const 0))
			 (local.set $boardSize (i32.const 9))

			 (if (result i32)
				 (i32.eq (call $getFreePos)
								 (local.get $boardSize))
				 (then (local.get $emptyBoardFuncIdx))
				 (else (local.get $playFuncIdx)))
			 
			 (global.set $nextAction)
			 )

 (func $setNextPlayer (type $v2v) ;;TODO Remove
			 (local $Xchar i32)
			 (local $Ochar i32)
			 (local.set $Xchar (i32.const 88)) ;; ascii X
			 (local.set $Ochar (i32.const 79)) ;; ascii O

			 (if (result i32)
						(i32.eq (global.get $currentPlayer)
										(local.get $Xchar))
			    (then (local.get $Ochar))
			    (else (local.get $Xchar)))

			 (global.set $currentPlayer)
			 )



 ;; GAME STATE Getters & Setters
 (func $getFreePos (type $v2i)
			 (i32.load
				 (i32.add (global.get $gameStateAddr)
									(i32.const 4))))

 (func $setFreePos (type $i2v)
			 (i32.store
				 (i32.add (global.get $gameStateAddr)
									(i32.const 4))
				 (local.get 0))
			 )


 ;;API
 (func $emptyboard (type $v2v)
			 (local $playFuncIdx i32)
			 (local $underScore i32)
			 (local $boardAddr i32)
			 (local $boardIdx i32)
			 (local $boardSize i32) ;; TODO missing playsFuncIdx from wARDuino

			 (local.set $playFuncIdx (i32.const 2))
			 (local.set $underScore (i32.const 95)) ;; Ascii underscore
			 (local.set $boardIdx (i32.const 0))
			 (local.set $boardSize (i32.const 9))
			 (local.set $boardAddr 
									(i32.load (global.get $gameStateAddr)))

			 (block
		 (loop (result)
				(i32.store
					(i32.add
							(local.get $boardAddr)
							(i32.mul (local.get $boardIdx)
											 (i32.const 4)))
					(local.get $underScore))

				(local.set $boardIdx
									 (i32.add (local.get $boardIdx)
														(i32.const 1)))

			 (i32.eq (local.get $boardIdx)
							 (local.get $boardSize));;todo correct

				(br_if 1)
				(br 0)))

		(local.get $playFuncIdx)
		(i32.const 0)
		(call $setFreePos)

		(global.set $nextAction)
 )


 (func $play (type $v2v)
			 (local $isFullFuncIdx i32)
			 (local.set $isFullFuncIdx (i32.const 1))

			 (i32.store
				 (i32.add (i32.load
										(global.get $gameStateAddr))
									(i32.mul (call $getFreePos)
													 (i32.const 4)))
					(global.get $currentPlayer))

			 (call $setNextPlayer)

			 ;;advance the grid free pos index
			 (i32.add (i32.const 1)
								(call $getFreePos))
			 (call $setFreePos)

			 (global.set $nextAction
									 (local.get $isFullFuncIdx))
			 )


(func $initGameState (type $v2v)
		;;Index Board, size board, Char _, Char O, Char X, freePos

		;;store board index 
		(i32.store (global.get $gameStateAddr) 
							 (i32.mul (i32.const 2) ;; 2 elements form the GameState
												(i32.const 4))) ;;each element is 4 bytes

		;; current free position on board
		(i32.store (i32.add (i32.const 4)
												(global.get $gameStateAddr))
							 (i32.const 0)) ;; freePos

		(call $emptyboard)
)
 
 (func $main (type $v2v)
			(call $initGameState)

			(loop (result)
						(call_indirect
							(type $v2v)
							(global.get $nextAction))
						(br 0))
							)
	
 (; (start $main) ;)
 )

