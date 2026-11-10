"""Unit tests for BankStatementParser."""

from reconciler.parser import BankStatementParser


def test_parse_csv_statement():
    sample_csv = """Date,Description,Chq/Ref_No,Withdrawal,Deposit,Balance
02/11/2026,UPI/CR/630811928312/SHARMA TEXTILES/HDFC,630811928312,0.00,45000.00,450000.00
04/11/2026,NEFT-N1042026-VIRAR PACKAGING LTD,N1042026,18250.00,0.00,431750.00
"""
    txs = BankStatementParser.parse_csv(sample_csv)
    assert len(txs) == 2

    assert txs[0].transaction_date == "2026-11-02"
    assert txs[0].deposit == 45000.0
    assert txs[0].reference_number == "630811928312"
    assert "SHARMA TEXTILES" in (txs[0].extracted_party or "")

    assert txs[1].transaction_date == "2026-11-04"
    assert txs[1].withdrawal == 18250.0
