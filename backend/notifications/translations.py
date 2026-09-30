"""
Source of the lg (Luganda) and sw (Kiswahili) translations for every
notification template and label, keyed by event_type / label code so the
English msgids never have to be retyped. `manage.py build_locale` turns this
into locale/<lang>/LC_MESSAGES/django.po + .mo.

Kiswahili: reviewed for standard East African usage. Luganda: best-effort,
FLAGGED FOR NATIVE-SPEAKER REVIEW before production (see DECISIONS.md).
Placeholders (%(name)s) must be kept exactly.
"""

TEMPLATES = {
    "sw": {
        "deposit_confirmed": ("Malipo yamepokelewa", "%(amount)s UGX zimeongezwa kwenye pochi ya %(student_name)s."),
        "deposit_failed": ("Malipo hayakufanikiwa", "Malipo yako ya %(amount)s UGX kwa %(student_name)s hayakufanikiwa: %(reason_label)s"),
        "contributor_topup_received": ("Malipo kutoka kwa %(contributor_name)s", "%(contributor_name)s ameongeza %(amount)s UGX kwenye pochi ya %(student_name)s."),
        "gift_received": ("Zawadi kwa %(student_name)s", '%(sender_name)s amemtumia %(student_name)s zawadi ya %(amount)s UGX: "%(message)s"'),
        "recurring_topup_executed": ("Malipo yaliyopangwa yamekamilika", "Malipo yako yaliyopangwa ya %(amount)s UGX kwa %(student_name)s yamekamilika."),
        "recurring_topup_failed": ("Malipo yaliyopangwa yameshindikana", "Malipo yako yaliyopangwa ya %(amount)s UGX kwa %(student_name)s yameshindikana: %(reason_label)s"),
        "recurring_topup_paused": ("Malipo yaliyopangwa yamesimamishwa", "Malipo yako yaliyopangwa kwa %(student_name)s yamesimamishwa baada ya majaribio %(failures)s kushindikana. Yasasishe kwenye programu ili kuendelea."),
        "low_balance": ("Salio ni dogo", "Salio la %(student_name)s ni %(balance)s UGX, chini ya kiwango chako cha tahadhari cha %(threshold)s UGX. Gusa ili kuongeza."),
        "savings_goal_reached": ("Lengo la akiba limefikiwa!", '%(student_name)s amefikia lengo la akiba "%(goal_name)s" (%(target_amount)s UGX).'),
        "savings_withdrawal_completed": ("Akiba imetolewa", "%(amount)s UGX kutoka akiba ya %(student_name)s zimetumwa kwa %(phone_number)s."),
        "savings_withdrawal_failed": ("Kutoa akiba kumeshindikana", "Kutoa %(amount)s UGX kutoka akiba ya %(student_name)s kumeshindikana na pesa zimerudishwa kwenye akiba: %(reason_label)s"),
        "card_frozen": ("Kadi imezuiwa", "Kadi ya %(student_name)s imezuiwa na %(actor_name)s. Hakuna malipo yanayoweza kufanywa nayo."),
        "card_unfrozen": ("Kadi imefunguliwa", "Kadi ya %(student_name)s imefunguliwa na %(actor_name)s."),
        "card_reported_lost": ("Kadi imeripotiwa kupotea", "Kadi ya %(student_name)s imeripotiwa kupotea na %(actor_name)s. Omba shule ikupe kadi mpya."),
        "card_locked_pin_failures": ("Kadi imefungwa", "Kadi ya %(student_name)s imezuiwa baada ya majaribio %(failures)s ya PIN isiyo sahihi."),
        "p2p_transfer_received": ("Pesa zimepokelewa", "%(student_name)s amepokea %(amount)s UGX kutoka kwa %(sender_name)s."),
        "p2p_alert_raised": ("Tahadhari ya mtindo wa uhamisho", "Inahitaji ukaguzi: %(student_name)s — %(rule_label)s."),
        "shortfall_flagged": ("Upungufu wa POS", "Mauzo ya nje ya mtandao kwenye kadi ya %(student_name)s yalipungua kwa %(shortfall_amount)s UGX (kifaa %(device_name)s). Tafadhali kagua."),
        "pos_transaction_flagged": ("Mauzo ya POS yamewekewa alama", "Mauzo ya nje ya mtandao kwenye kadi ya %(student_name)s yamevunja sheria (%(flags_label)s). Tafadhali kagua."),
        "dispute_status_changed": ("Taarifa ya malalamiko", "Malalamiko yako #%(dispute_id)s sasa ni: %(status_label)s. %(notes)s"),
        "attendance_tap_in": ("Amefika shuleni", "%(student_name)s ameingia saa %(time)s."),
        "data_request_updated": ("Taarifa ya ombi la data", "Ombi lako la %(request_type_label)s #%(request_id)s sasa ni %(status_label)s."),
        "pooled_fund_contribution_confirmed": ("Mchango umepokelewa", 'Mchango wako wa %(amount)s UGX kwa "%(fund_title)s" umepokelewa.'),
    },
    "lg": {
        "deposit_confirmed": ("Ssente zituuse", "%(amount)s UGX ziyongeddwa ku wallet ya %(student_name)s."),
        "deposit_failed": ("Okusasula tekugenze bulungi", "Ssente zo %(amount)s UGX eza %(student_name)s tezituuse: %(reason_label)s"),
        "contributor_topup_received": ("Ssente okuva eri %(contributor_name)s", "%(contributor_name)s ayongeddeko %(amount)s UGX ku wallet ya %(student_name)s."),
        "gift_received": ("Ekirabo kya %(student_name)s", '%(sender_name)s aweerezza %(student_name)s ekirabo kya %(amount)s UGX: "%(message)s"'),
        "recurring_topup_executed": ("Okusasula okwateekebwawo kuwedde", "Ssente zo ezaateekebwawo %(amount)s UGX eza %(student_name)s zisasuddwa."),
        "recurring_topup_failed": ("Okusasula okwateekebwawo kulemye", "Ssente zo ezaateekebwawo %(amount)s UGX eza %(student_name)s ziremye: %(reason_label)s"),
        "recurring_topup_paused": ("Okusasula okwateekebwawo kuyimiriziddwa", "Okusasula kwo okwateekebwawo okwa %(student_name)s kuyimiriziddwa oluvannyuma lw'okulemererwa emirundi %(failures)s. Kukyuse mu app okuddamu."),
        "low_balance": ("Ssente ntono", "Ssente za %(student_name)s zisigadde %(balance)s UGX, wansi w'ekipimo kyo ekya %(threshold)s UGX. Nyiga okwongerako."),
        "savings_goal_reached": ("Ekiruubirirwa ky'okutereka kituukiddwako!", "%(student_name)s atuuse ku kiruubirirwa ky'okutereka \"%(goal_name)s\" (%(target_amount)s UGX)."),
        "savings_withdrawal_completed": ("Ssente z'okutereka ziweerezeddwa", "%(amount)s UGX okuva mu nterekero ya %(student_name)s ziweerezeddwa ku %(phone_number)s."),
        "savings_withdrawal_failed": ("Okuggya ssente mu nterekero kulemye", "Okuggya %(amount)s UGX mu nterekero ya %(student_name)s kulemye era ssente zizziddwa mu nterekero: %(reason_label)s"),
        "card_frozen": ("Kaadi eyimiriziddwa", "Kaadi ya %(student_name)s eyimiriziddwa %(actor_name)s. Tekyasobola kusasula."),
        "card_unfrozen": ("Kaadi ezziddwawo", "Kaadi ya %(student_name)s ezziddwawo %(actor_name)s."),
        "card_reported_lost": ("Kaadi ebuze", "%(actor_name)s ayogedde nti kaadi ya %(student_name)s ebuze. Saba essomero kaadi empya."),
        "card_locked_pin_failures": ("Kaadi esibiddwa", "Kaadi ya %(student_name)s eyimiriziddwa oluvannyuma lwa PIN enkyamu emirundi %(failures)s."),
        "p2p_transfer_received": ("Ssente zifuniddwa", "%(student_name)s afunye %(amount)s UGX okuva eri %(sender_name)s."),
        "p2p_alert_raised": ("Okulabula ku ntambula ya ssente", "Kyetaaga okwekebejjebwa: %(student_name)s — %(rule_label)s."),
        "shortfall_flagged": ("Ebbula ku POS", "Okutunda okutaali ku mutimbagano ku kaadi ya %(student_name)s kwabulako %(shortfall_amount)s UGX (ekyuma %(device_name)s). Kebera."),
        "pos_transaction_flagged": ("Okutunda ku POS kulabiddwa", "Okutunda okutaali ku mutimbagano ku kaadi ya %(student_name)s kwamenye etteeka (%(flags_label)s). Kebera."),
        "dispute_status_changed": ("Ebifa ku kwemulugunya", "Okwemulugunya kwo #%(dispute_id)s kati: %(status_label)s. %(notes)s"),
        "attendance_tap_in": ("Atuuse ku ssomero", "%(student_name)s ayingidde ku ssaawa %(time)s."),
        "data_request_updated": ("Ebifa ku kusaba data", "Okusaba kwo okwa %(request_type_label)s #%(request_id)s kati %(status_label)s."),
        "pooled_fund_contribution_confirmed": ("Obuyambi bufuniddwa", "Obuyambi bwo obwa %(amount)s UGX eri \"%(fund_title)s\" bufuniddwa."),
    },
}

LABELS = {
    "sw": {
        "expired": "ombi la malipo limeisha muda", "declined": "malipo yamekataliwa",
        "aggregator_error": "mtoa huduma ya malipo amerudisha hitilafu", "insufficient_funds": "salio halitoshi",
        "payout_failed": "uhamisho wa pesa kwa simu umeshindikana", "card_frozen": "kadi imezuiwa",
        "card_lost": "kadi imeripotiwa kupotea", "daily_cap_exceeded": "kikomo cha matumizi ya siku kimepitwa",
        "weekly_cap_exceeded": "kikomo cha matumizi ya wiki kimepitwa",
        "per_transaction_cap_exceeded": "kikomo cha ununuzi mmoja kimepitwa", "category_blocked": "aina iliyozuiwa",
        "category_not_allowed": "aina isiyoruhusiwa", "item_blocked": "bidhaa iliyozuiwa",
        "merchant_blocked": "mfanyabiashara aliyezuiwa", "exceeds_offline_ceiling": "imepita kikomo cha nje ya mtandao",
        "shortfall": "salio halitoshi", "open": "wazi", "under_review": "inakaguliwa",
        "resolved_refunded": "imetatuliwa — pesa zimerudishwa", "resolved_denied": "imetatuliwa — hakuna marejesho",
        "pending": "inasubiri", "in_progress": "inashughulikiwa", "completed": "imekamilika", "rejected": "imekataliwa",
        "many_distinct_senders": "amepokea pesa kutoka kwa wanafunzi wengi tofauti",
        "repeated_near_cap": "ametuma mara kwa mara kiasi kinachokaribia kikomo cha siku",
        "export": "nakala ya data", "correction": "marekebisho", "deletion": "kufuta",
    },
    "lg": {
        "expired": "okusaba okusasula kuweddeko obudde", "declined": "okusasula kugaaniddwa",
        "aggregator_error": "kkampuni esasula ezzeeyo ensobi", "insufficient_funds": "ssente tezimala",
        "payout_failed": "okuweereza ssente ku ssimu kulemye", "card_frozen": "kaadi eyimiriziddwa",
        "card_lost": "kaadi ebuze", "daily_cap_exceeded": "ekkomo ly'olunaku lisukkiddwa",
        "weekly_cap_exceeded": "ekkomo ly'wiiki lisukkiddwa", "per_transaction_cap_exceeded": "ekkomo ly'okugula omulundi gumu lisukkiddwa",
        "category_blocked": "ekika ekiziyiziddwa", "category_not_allowed": "ekika ekitakkirizibwa",
        "item_blocked": "ekintu ekiziyiziddwa", "merchant_blocked": "omusuubuzi aziyiziddwa",
        "exceeds_offline_ceiling": "kisusse ekkomo ery'obutaba ku mutimbagano", "shortfall": "ssente tezimala",
        "open": "kiggule", "under_review": "kyekebejjebwa", "resolved_refunded": "kigonjoddwa — ssente zizziddwayo",
        "resolved_denied": "kigonjoddwa — tewali kuzzaayo", "pending": "kirindiridde", "in_progress": "kikolebwako",
        "completed": "kiwedde", "rejected": "kigaaniddwa",
        "many_distinct_senders": "afunye ssente okuva eri abayizi bangi ab'enjawulo",
        "repeated_near_cap": "aweerezza emirundi mingi ssente eziri kumpi n'ekkomo ly'olunaku",
        "export": "kopi ya data", "correction": "okutereeza", "deletion": "okusangulawo",
    },
}
