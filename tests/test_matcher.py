"""Unit tests for ReconciliationMatcher."""

from reconciler.parser import BankTransaction
from reconciler.matcher import ReconciliationMatcher, ERPNextPaymentEntry


def test_matcher_exact_amount_and_reference():
    tx = BankTransaction(
        transaction_date="2026-11-02",
        description="UPI/CR/630811928312/SHARMA TEXTILES/HDFC",
        reference_number="630811928312",
        deposit=45000.0,
        withdrawal=0.0,
        balance=450000.0,
        extracted_party="SHARMA TEXTILES",
    )

    erp_entry = ERPNextPaymentEntry(
        name="ACC-PAY-2026-00089",
        posting_date="2026-11-02",
        party_type="Customer",
        party_name="Sharma Textiles and Garments",
        paid_amount=45000.0,
        reference_no="630811928312",
    )

    matcher = ReconciliationMatcher(confidence_threshold=80.0)
    matches = matcher.match_records([tx], [erp_entry])

    assert len(matches) == 1
    m = matches[0]
    assert m.confidence_score >= 90.0
    assert m.is_auto_reconcilable is True
    assert m.erpnext_payment.name == "ACC-PAY-2026-00089"
