EventScript_PortablePC_HealParty::
	lockall
	special HealPlayerParty
	playfanfare MUS_HEAL
	waitfanfare
	msgbox Text_PartyHealed, MSGBOX_AUTOCLOSE
	releaseall
	end

Text_PartyHealed:
	.string "Your Pokémon were restored to full\nhealth.$"
