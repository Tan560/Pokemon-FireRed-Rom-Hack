EventScript_PortablePC_HealParty::
	lockall
	special HealPlayerParty
	msgbox Text_PartyHealed, MSGBOX_AUTOCLOSE
	releaseall
	end

Text_PartyHealed:
	.string "Your Pokémon were restored to full\nhealth.$"
