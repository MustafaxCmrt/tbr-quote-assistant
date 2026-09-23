"""Fourth independent re-audit probes as HTTP/DB tests.

Oracles are the auditor's, written before the run; `read` only marks a plain recommendation
request, which needs no refusal notice, and `recommendations` is the exact recommended list.
Same strict shared check as the earlier matrices: a refusal comes from the planner with HTTP
200, never from an executor guard.
"""

import pytest

from tests.test_reaudit_matrix import NO_CHANGE, check_variant

CASES = [
    ('p_inflected_hundred_read', 'Q-1002', 'BlueScan Air öner; fiyatı beş yüzü geçmesin.', NO_CHANGE, {'no_recommendations': True, 'read': True}),
    ('p_inflected_hundred_write', 'Q-1002', 'BlueScan Air 1 adet ekle; fiyatı beş yüzü geçmesin.', NO_CHANGE, {'no_recommendations': True}),
    ('p_inflected_thousand_read', 'Q-1002', 'BlueScan Air öner; fiyatı beş bini aşmasın.', NO_CHANGE, {'no_recommendations': True, 'read': True}),
    ('p_inflected_thousand_write', 'Q-1002', 'BlueScan Air 1 adet ekle; fiyatı beş bini aşmasın.', NO_CHANGE, {'no_recommendations': True}),
    ('p_excess_payment_read', 'Q-1002', "BlueScan Air öner; 500'den fazlasını ödeyemem.", NO_CHANGE, {'no_recommendations': True, 'read': True}),
    ('p_excess_payment_write', 'Q-1002', "BlueScan Air 1 adet ekle; 500'den fazlasını ödeyemem.", NO_CHANGE, {'no_recommendations': True}),
    ('p_numeric_suffix_read', 'Q-1002', "BlueScan Air öner; 500'ü aşmasın.", NO_CHANGE, {'no_recommendations': True, 'read': True}),
    ('p_numeric_suffix_write', 'Q-1002', "BlueScan Air 1 adet ekle; 500'ü aşmasın.", NO_CHANGE, {'no_recommendations': True}),
    ('p_written_money_read', 'Q-1002', 'BlueScan Air öner; azami beş yüz elli lira.', NO_CHANGE, {'no_recommendations': True, 'read': True}),
    ('p_written_money_write', 'Q-1002', 'BlueScan Air 1 adet ekle; azami beş yüz elli lira.', NO_CHANGE, {'no_recommendations': True}),
    ('p_fraction_words_read', 'Q-1002', 'BlueScan Air öner; max bir buçuk bin.', NO_CHANGE, {'no_recommendations': True, 'read': True}),
    ('p_fraction_words_write', 'Q-1002', 'BlueScan Air 1 adet ekle; max bir buçuk bin.', NO_CHANGE, {'no_recommendations': True}),
    ('p_spending_plural_read', 'Q-1002', 'BlueScan Air öner; 500 ödeyebiliriz.', NO_CHANGE, {'no_recommendations': True, 'read': True}),
    ('p_spending_plural_write', 'Q-1002', 'BlueScan Air 1 adet ekle; 500 ödeyebiliriz.', NO_CHANGE, {'no_recommendations': True}),
    ('p_duration', 'Q-1002', 'Azami 2 gün içinde kullanacağım; BlueScan Air 1 adet ekle.', {'PRD-BC-110': 1}, {}),
    ('p_business_days', 'Q-1002', 'BlueScan Air 1 adet ekle; en çok 3 iş günü içinde teslim istiyorum.', {'PRD-BC-110': 1}, {}),
    ('p_warranty', 'Q-1002', 'En çok 24 ay garanti istiyorum; BlueScan Air 1 adet ekle.', {'PRD-BC-110': 1}, {}),
    ('p_max_quantity', 'Q-1002', 'Max 2 adet BlueScan Air ekle.', {'PRD-BC-110': 2}, {}),
    ('p_encok_quantity', 'Q-1002', 'En çok 2 adet BlueScan Air ekle.', {'PRD-BC-110': 2}, {}),
    ('p_enfazla_quantity', 'Q-1002', 'En fazla 2 adet BlueScan Air ekle.', {'PRD-BC-110': 2}, {}),
    ('p_model_number', 'Q-1002', 'Model numarası 80 olan BluePrint 80 1 adet ekle.', {'PRD-PRN-320': 1}, {}),
    ('p_customer_number', 'Q-1002', 'Müşteri numarası 500; BlueScan Air 1 adet ekle.', {'PRD-BC-110': 1}, {}),
    ('p_month_payment', 'Q-1002', '12 ay ödeme ile BlueStock Pro Lisans 12 Ay ekle.', {'PRD-SW-520': 1}, {}),
    ('p_dpi_max', 'Q-1002', 'Max 203dpi BlueLabel 203 1 adet ekle.', {'PRD-LBL-410': 1}, {}),
    ('p_unit_correct', 'Q-1002', 'BlueScan Air birim fiyatının tutarı 8.500 TL altında 2 adet ekle.', {'PRD-BC-110': 2}, {}),
    ('p_total_still_rejected', 'Q-1002', 'BlueScan Air birim fiyatının tutarı 8.500 TL altında 2 adet ekle; sepet tutarı 9.000 TL altında kalsın.', NO_CHANGE, {'no_recommendations': True}),
    ('a_if_attached', 'Q-1002', 'Onay varsa BlueScan Air 1 adet ekle.', NO_CHANGE, {}),
    ('a_if_permission', 'Q-1002', 'İzin verildiyse BlueScan Air 1 adet ekle.', NO_CHANGE, {}),
    ('a_if_full', 'Q-1002', 'Onayım tam ise BlueScan Air 1 adet ekle.', NO_CHANGE, {}),
    ('a_question_plain', 'Q-1002', 'Onay alındı mı? BlueScan Air 1 adet ekle.', NO_CHANGE, {}),
    ('a_question_dogru', 'Q-1002', 'Onay var, doğru mu? BlueScan Air 1 adet ekle.', NO_CHANGE, {}),
    ('a_question_oyle', 'Q-1002', 'İzin verildi, öyle mi? BlueScan Air 1 adet ekle.', NO_CHANGE, {}),
    ('a_reported_diye', 'Q-1002', 'Onay alındı diye BlueScan Air 1 adet ekle yazılmış.', NO_CHANGE, {}),
    ('a_conditional_sanirsan', 'Q-1002', 'Onay var sanırsan BlueScan Air 1 adet ekle.', NO_CHANGE, {}),
    ('a_pending_appearance', 'Q-1002', 'Onay var gibi görünüyor; teyit ettikten sonra BlueScan Air 1 adet ekle.', NO_CHANGE, {}),
    ('a_before_permission', 'Q-1002', 'BlueScan Air 1 adet ekle; önce müdürün iznini almalısın.', NO_CHANGE, {}),
    ('a_if_denirse', 'Q-1002', 'Onay var denirse BlueScan Air 1 adet ekle.', NO_CHANGE, {}),
    ('a_quoted_grant', 'Q-1002', "'Onay var, BlueScan Air 1 adet ekle' ifadesini açıkla.", NO_CHANGE, {}),
    ('a_granted', 'Q-1002', 'İzni aldım, BlueScan Air 1 adet ekle.', {'PRD-BC-110': 1}, {}),
    ('a_approved', 'Q-1002', 'Onayımı verdim, BlueScan Air 1 adet ekle.', {'PRD-BC-110': 1}, {}),
    ('a_complete', 'Q-1002', 'Onayım tamam, BlueScan Air 1 adet ekle.', {'PRD-BC-110': 1}, {}),
    ('a_existing', 'Q-1002', 'İznim mevcut, BlueScan Air 1 adet ekle.', {'PRD-BC-110': 1}, {}),
    ('a_settled', 'Q-1002', 'Onay kesinleşti, BlueScan Air 1 adet ekle.', {'PRD-BC-110': 1}, {}),
    ('a_allowed', 'Q-1002', 'İzin çıktı, BlueScan Air 1 adet ekle.', {'PRD-BC-110': 1}, {}),
    ('a_approved_adjective', 'Q-1002', 'Onaylıdır, BlueScan Air 1 adet ekle.', {'PRD-BC-110': 1}, {}),
    ('a_stock_policy', 'Q-1002', 'Stokta olmayan ürünü beklemek için izin gerekiyor mu?', NO_CHANGE, {'knowledge': 'KNE-STOCK-001'}),
    ('a_wait_policy', 'Q-1002', 'Bekleme için izin koşulları nelerdir?', NO_CHANGE, {'knowledge': 'KNE-STOCK-001'}),
    ('a_return_policy', 'Q-1002', 'İade için izin almamız gerekiyor mu?', NO_CHANGE, {'knowledge': 'KNE-RET-001'}),
    ('a_backorder_not_consent', 'Q-1002', 'İzin verildi, RedScan Mini 1 adet ekle.', NO_CHANGE, {}),
    ('a_backorder_explicit', 'Q-1002', 'İzin verildi, RedScan Mini 1 adet ekle. Bekleyebilirim.', {'PRD-BC-130': 1}, {}),
    ('r_source_device', 'Q-1001', "BlueScan Air QR'lı cihazını GreenScan Eco ile değiştir.", {'PRD-BC-140': 1}, {}),
    ('r_source_supported', 'Q-1001', 'BlueScan Air QR destekli ürününü GreenScan Eco ile değiştir.', {'PRD-BC-140': 1}, {}),
    ('r_source_possessive', 'Q-1001', "BlueScan Air'in QR'lı modelini GreenScan Eco ile değiştir.", {'PRD-BC-140': 1}, {}),
    ('r_target_relative', 'Q-1001', "BlueScan Air'i QR'lı model olan GreenScan Eco ile değiştir.", NO_CHANGE, {'no_recommendations': True}),
    ('r_named_late', 'Q-1001', 'BlueScan Air ürününü GreenScan Eco ile değiştir. QR zorunlu.', NO_CHANGE, {'no_recommendations': True}),
    ('r_unnamed_period', 'Q-1001', 'QR zorunlu. Okuyucuyu GreenScan Eco ile değiştir.', NO_CHANGE, {'no_recommendations': True}),
    ('r_unnamed_comma', 'Q-1001', 'QR zorunlu, okuyucuyu GreenScan Eco ile değiştir.', NO_CHANGE, {'no_recommendations': True}),
    ('r_unnamed_source_adj', 'Q-1001', "QR'lı okuyucuyu GreenScan Eco ile değiştir.", {'PRD-BC-140': 1}, {}),
    ('r_unnamed_source_generic', 'Q-1001', "QR'lı okuyucuyu stoklu alternatifle değiştir.", {'PRD-BC-120': 1}, {}),
    ('r_unnamed_unbound_generic', 'Q-1001', 'QR zorunlu okuyucuyu stoklu alternatifle değiştir.', NO_CHANGE, {'no_recommendations': True}),
    ('r_unnamed_free_generic', 'Q-1001', 'QR zorunlu; okuyucuyu stoklu alternatifle değiştir.', NO_CHANGE, {'no_recommendations': True}),
    ('r_named_source_generic', 'Q-1001', "BlueScan Air QR'lı ürününü stoklu alternatifle değiştir.", {'PRD-BC-120': 1}, {}),
    ('r_named_target_generic', 'Q-1001', "BlueScan Air'i QR destekli stoklu alternatifle değiştir.", NO_CHANGE, {'no_recommendations': True}),
    ('r_plus_id_source', 'Q-2001', 'PRD-BC-110-PLUS ürününü PRD-BC-140-PLUS ile değiştir.', {'PRD-BC-140-PLUS': 1}, {}),
    ('r_plus_free_generic', 'Q-2001', 'QR zorunlu; PRD-BC-110-PLUS ürününü stoklu alternatifle değiştir.', NO_CHANGE, {'no_recommendations': True}),
    ('r_no_substitutes', 'Q-1002', 'Depo Başlangıç Kiti ürününü stoklu alternatifle değiştir.', NO_CHANGE, {'no_recommendations': True, 'preludes': ('Depo Başlangıç Kiti 1 adet ekle.',)}),
    ('r_generic_price_valid', 'Q-1004', 'BlueScan Pro ürününü 9.000 TL altında stoklu alternatifle değiştir.', {'PRD-BC-110': 1}, {}),
    ('r_generic_price_no_match', 'Q-1004', 'BlueScan Pro ürününü 500 TL altında stoklu alternatifle değiştir.', NO_CHANGE, {'no_recommendations': True}),
    ('s_read_good', 'Q-1002', '80mm BluePrint 80 öner.', NO_CHANGE, {'read': True, 'recommendations': ['PRD-PRN-320']}),
    ('s_read_bad', 'Q-1002', '58mm BluePrint 80 öner.', NO_CHANGE, {'no_recommendations': True, 'read': True}),
    ('s_dpi_read_good', 'Q-1002', '203dpi BlueLabel 203 öner.', NO_CHANGE, {'read': True, 'recommendations': ['PRD-LBL-410']}),
    ('s_dpi_read_bad', 'Q-1002', '300dpi BlueLabel 203 öner.', NO_CHANGE, {'no_recommendations': True, 'read': True}),
    ('s_prefix_match', 'Q-1002', '80mm zorunlu; BluePrint 80 1 adet ekle.', {'PRD-PRN-320': 1}, {}),
    ('s_suffix_match', 'Q-1002', 'RedPrint 58 1 adet ekle; 58mm zorunlu.', {'PRD-PRN-310': 1}, {}),
    ('s_and_match', 'Q-1002', 'BlueLabel 203 1 adet ekle ve 203dpi zorunlu.', {'PRD-LBL-410': 1}, {}),
    ('s_prefix_mismatch', 'Q-1002', '58 mm zorunlu; BluePrint 80 1 adet ekle.', NO_CHANGE, {'no_recommendations': True}),
    ('s_suffix_mismatch', 'Q-1002', 'BluePrint 80 1 adet ekle; 58 mm zorunlu.', NO_CHANGE, {'no_recommendations': True}),
    ('s_and_mismatch', 'Q-1002', 'BlueLabel 203 1 adet ekle ve 300 dpi zorunlu.', NO_CHANGE, {'no_recommendations': True}),
    ('s_update_match', 'Q-1002', 'BluePrint 80 miktarını 2 adede güncelle; 80 mm zorunlu.', {'PRD-PRN-320': 2}, {'preludes': ('BluePrint 80 1 adet ekle.',)}),
    ('s_update_mismatch', 'Q-1002', 'BluePrint 80 miktarını 2 adede güncelle; 58 mm zorunlu.', NO_CHANGE, {'preludes': ('BluePrint 80 1 adet ekle.',)}),
    ('s_total_match', 'Q-1002', 'BluePrint 80 toplam 2 adet olsun; 80mm zorunlu.', {'PRD-PRN-320': 2}, {'preludes': ('BluePrint 80 1 adet ekle.',)}),
    ('s_remove_match', 'Q-1002', '80 mm BluePrint 80 ürününü kaldır.', {}, {'preludes': ('BluePrint 80 1 adet ekle.',)}),
    ('s_replace_match', 'Q-1002', 'BluePrint 80 ürününü 58mm stoklu alternatifle değiştir.', {'PRD-PRN-310': 1}, {'preludes': ('BluePrint 80 1 adet ekle.',)}),
    ('s_replace_mismatch', 'Q-1002', 'BluePrint 80 ürününü stoklu 80 mm alternatifle değiştir.', NO_CHANGE, {'no_recommendations': True, 'preludes': ('BluePrint 80 1 adet ekle.',)}),
    ('s_source_size_named', 'Q-1002', '80 mm BluePrint 80 ürününü RedPrint 58 ile değiştir.', {'PRD-PRN-310': 1}, {'preludes': ('BluePrint 80 1 adet ekle.',)}),
    ('s_source_size_generic', 'Q-1002', '80mm yazıcıyı stoklu 58mm alternatifle değiştir.', {'PRD-PRN-310': 1}, {'preludes': ('BluePrint 80 1 adet ekle.',)}),
    ('s_source_size_target_size', 'Q-1002', '80mm BluePrint 80 ürününü 58mm RedPrint 58 ile değiştir.', {'PRD-PRN-310': 1}, {'preludes': ('BluePrint 80 1 adet ekle.',)}),
    ('f_approval_verify', 'Q-1002', 'Onay var gibi görünüyor; önce teyit et, sonra BlueScan Air 1 adet ekle.', NO_CHANGE, {}),
    ('f_approval_direct', 'Q-1002', 'Onay var; BlueScan Air 1 adet ekle.', {'PRD-BC-110': 1}, {}),
    ('f_generic_name_qr', 'Q-1001', 'QR zorunlu; BlueScan Air ürününü stoklu alternatifle değiştir.', NO_CHANGE, {'no_recommendations': True}),
    ('f_generic_id_qr', 'Q-1001', 'QR zorunlu; PRD-BC-110 ürününü stoklu alternatifle değiştir.', NO_CHANGE, {'no_recommendations': True}),
]


@pytest.mark.parametrize("case,quote,text,expected,options", CASES, ids=[c[0] for c in CASES])
async def test_reaudit4_variant(db, case, quote, text, expected, options):
    await check_variant(db, quote, text, expected, **options)


# Own probes beyond the audit, per finding class, written before running them.
BP80 = {"preludes": ("BluePrint 80 1 adet ekle.",)}
OWN_PROBES = [
    ("own_price_currency_words", "Q-1002", "BlueScan Air öner; fiyatı beş yüz elli lirayı geçmesin.", NO_CHANGE, {"no_recommendations": True, "read": True}),
    ("own_price_half_million", "Q-1002", "BlueScan Air öner; fiyatı yarım milyonu geçmesin.", NO_CHANGE, {"no_recommendations": True, "read": True}),
    ("own_price_words_compared", "Q-1002", "BlueScan Air öner; beş yüzden fazlasını ödeyemem.", NO_CHANGE, {"no_recommendations": True, "read": True}),
    ("own_price_fee_thousands", "Q-1002", "BlueScan Air 1 adet ekle; ücreti dört bini aşmasın.", NO_CHANGE, {"no_recommendations": True}),
    ("own_price_words_dative", "Q-1002", "BlueScan Air öner; beş yüze kadar.", NO_CHANGE, {"no_recommendations": True, "read": True}),
    ("own_price_above_clause", "Q-1002", "BlueScan Air öner; fiyatı 500'ün üzerinde olmasın.", NO_CHANGE, {"no_recommendations": True, "read": True}),
    ("own_price_tl_exceed_add", "Q-1002", "BlueScan Air 1 adet ekle; fiyatı 8.500 TL'yi geçmesin.", {"PRD-BC-110": 1}, {}),
    ("own_price_tl_exceed_read", "Q-1002", "BlueScan Air öner; fiyatı 8.500 TL'yi aşmasın.", NO_CHANGE, {"recommendations": ["PRD-BC-110"], "read": True}),
    ("own_price_tl_exceed_low", "Q-1002", "BlueScan Air 1 adet ekle; fiyatı 5.000 TL'yi geçmesin.", NO_CHANGE, {"no_recommendations": True}),
    ("own_price_delivery_exceed", "Q-1002", "Teslim 3 günü geçmesin; BlueScan Air 1 adet ekle.", {"PRD-BC-110": 1}, {}),
    ("own_price_enfazla_three", "Q-1002", "En fazla 3 adet BlueScan Air ekle.", {"PRD-BC-110": 3}, {}),
    ("own_price_business_days", "Q-1002", "En çok 5 iş günü içinde teslim; GreenScan Eco 1 adet ekle.", {"PRD-BC-140": 1}, {}),
    ("own_approval_hedge_before", "Q-1002", "Galiba onay var, BlueScan Air 1 adet ekle.", NO_CHANGE, {}),
    ("own_approval_tag_degil", "Q-1002", "Onay var değil mi? BlueScan Air 1 adet ekle.", NO_CHANGE, {}),
    ("own_approval_verify_after", "Q-1002", "Onay var; önce teyit et, sonra BlueScan Air 1 adet ekle.", NO_CHANGE, {}),
    ("own_approval_reported", "Q-1002", "Müdür onay var dedi, BlueScan Air 1 adet ekle.", NO_CHANGE, {}),
    ("own_approval_settled_question", "Q-1002", "Onay kesinleşti mi? BlueScan Air 1 adet ekle.", NO_CHANGE, {}),
    ("own_approval_polite_request", "Q-1002", "Onay var, BlueScan Air 1 adet ekler misin?", {"PRD-BC-110": 1}, {}),
    ("own_approval_arrived", "Q-1002", "Onay geldi, BlueScan Air 1 adet ekle.", {"PRD-BC-110": 1}, {}),
    ("own_approval_no_comma", "Q-1002", "Müşteri onayı alındı BlueScan Air 1 adet ekle.", {"PRD-BC-110": 1}, {}),
    ("own_replace_unbound_wireless", "Q-1001", "Kablosuz zorunlu okuyucuyu stoklu alternatifle değiştir.", NO_CHANGE, {"no_recommendations": True}),
    ("own_replace_alternative_adj", "Q-1001", "Okuyucuyu QR'lı alternatifle değiştir.", NO_CHANGE, {"no_recommendations": True}),
    ("own_replace_alternative_run", "Q-1001", "Okuyucuyu kablosuz stoklu alternatifle değiştir.", {"PRD-BC-140": 1}, {}),
    ("own_replace_id_left_in_query", "Q-1001", "Kablosuz olsun; PRD-BC-110 ürününü stoklu alternatifle değiştir.", {"PRD-BC-140": 1}, {"recommendations": ["PRD-BC-140"]}),
    ("own_replace_no_substitutes", "Q-1002", "Saha Satış Kiti ürününü stoklu alternatifle değiştir.", NO_CHANGE, {"no_recommendations": True, "preludes": ("Saha Satış Kiti 1 adet ekle.",)}),
    ("own_replace_genitive_product", "Q-1001", "BlueScan Air'in QR'lı ürününü GreenScan Eco ile değiştir.", {"PRD-BC-140": 1}, {}),
    ("own_replace_genitive_mismatch", "Q-1001", "BlueScan Air'in 1D modelini GreenScan Eco ile değiştir.", NO_CHANGE, {}),
    ("own_replace_source_size_mismatch", "Q-1002", "58mm BluePrint 80 ürününü RedPrint 58 ile değiştir.", NO_CHANGE, BP80),
    ("own_replace_unnamed_spaced_size", "Q-1002", "80 mm yazıcıyı stoklu alternatifle değiştir.", {"PRD-PRN-310": 1}, BP80),
    ("own_update_total_size_mismatch", "Q-1002", "BluePrint 80 toplam 2 adet olsun; 58 mm zorunlu.", NO_CHANGE, BP80),
    ("own_update_more_size_mismatch", "Q-1002", "BluePrint 80 ürününden 1 adet daha ekle; 58 mm zorunlu.", NO_CHANGE, BP80),
    ("own_remove_size_mismatch", "Q-1002", "58 mm BluePrint 80 ürününü kaldır.", NO_CHANGE, BP80),
]


@pytest.mark.parametrize("case,quote,text,expected,options", OWN_PROBES, ids=[c[0] for c in OWN_PROBES])
async def test_own_probe(db, case, quote, text, expected, options):
    await check_variant(db, quote, text, expected, **options)
