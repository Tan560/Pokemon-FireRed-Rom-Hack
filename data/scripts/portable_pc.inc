EventScript_PortablePC_HealParty::
    lockall
    playse MUS_HEAL
    special HealPlayerParty
    waitse
    msgbox Text_PartyHealed, MSGBOX_AUTOCLOSE
    releaseall
    end

Text_PartyHealed:
    .string "Your Pokémon were restored to full\nhealth.$"
