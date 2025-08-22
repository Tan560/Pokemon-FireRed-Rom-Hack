EventScript_PermanentRepelUsed::
	lockall
	checkflag FLAG_SYS_PERMANENT_REPEL_ACTIVE
	compare VAR_RESULT, TRUE
	goto_if_eq EventScript_RepelOnMessage
	msgbox Text_EternalRepelOff, MSGBOX_DEFAULT
	goto EventScript_RepelEnd

EventScript_RepelOnMessage::
	msgbox Text_EternalRepelOn, MSGBOX_DEFAULT

EventScript_RepelEnd::
	releaseall
	end

Text_EternalRepelOn::
	.string "The Permanent Repel was turned on.$"

Text_EternalRepelOff::
	.string "The Permanent Repel was turned off.$"