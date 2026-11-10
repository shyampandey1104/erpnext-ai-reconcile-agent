"""Multi-factor fuzzy reconciliation engine for ERPNext."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from rapidfuzz import fuzz
from pydantic import BaseModel
from reconciler.parser import BankTransaction


class ERPNextPaymentEntry(BaseModel):
    name: str  # ACC-PAY-2026-0001
    posting_date: str
    party_type: str  # Customer / Supplier
    party_name: str
    paid_amount: float
    reference_no: Optional[str] = None
    clearance_date: Optional[str] = None


class ReconciliationMatch(BaseModel):
    bank_transaction: BankTransaction
    erpnext_payment: ERPNextPaymentEntry
    confidence_score: float  # 0 to 100
    match_reasons: List[str]
    is_auto_reconcilable: bool


class ReconciliationMatcher:
    """Matches bank transactions with ERPNext unallocated Payment Entries."""

    def __init__(self, confidence_threshold: float = 85.0, date_window_days: int = 5):
        self.confidence_threshold = confidence_threshold
        self.date_window_days = date_window_days

    def match_records(
        self,
        bank_txs: List[BankTransaction],
        erp_payments: List[ERPNextPaymentEntry],
    ) -> List[ReconciliationMatch]:
        matches: List[ReconciliationMatch] = []
        unmatched_erp = list(erp_payments)

        for tx in bank_txs:
            tx_amount = tx.deposit if tx.deposit > 0 else tx.withdrawal
            best_match: Optional[ERPNextPaymentEntry] = None
            best_score = 0.0
            best_reasons: List[str] = []

            for payment in unmatched_erp:
                score = 0.0
                reasons: List[str] = []

                # 1. Exact amount match (Weight: 45 points)
                if abs(payment.paid_amount - tx_amount) < 0.01:
                    score += 45.0
                    reasons.append("Exact amount matched")
                elif abs(payment.paid_amount - tx_amount) <= 1.0:
                    score += 35.0
                    reasons.append("Amount match within ₹1 rounding")
                else:
                    # Amount mismatch usually invalidates candidate
                    continue

                # 2. Reference / Cheque number exact match (Weight: 35 points)
                if payment.reference_no and tx.reference_number:
                    if payment.reference_no.lower() in tx.reference_number.lower() or tx.reference_number.lower() in payment.reference_no.lower():
                        score += 35.0
                        reasons.append("Reference/UTR exact match")

                # 3. Fuzzy Party Name Match (Weight: 25 points)
                party_query = tx.extracted_party or tx.description
                similarity = fuzz.partial_ratio(party_query.lower(), payment.party_name.lower())
                if similarity >= 80:
                    party_pts = (similarity / 100.0) * 25.0
                    score += party_pts
                    reasons.append(f"Party name similarity: {similarity:.0f}%")

                # 4. Date Proximity Check (Weight: 15 points)
                date_diff = self._calc_date_diff(tx.transaction_date, payment.posting_date)
                if date_diff <= self.date_window_days:
                    score += max(0, 15 - (date_diff * 2))
                    reasons.append(f"Date difference: {date_diff} day(s)")

                # Normalize score capped at 100
                final_score = min(score, 100.0)
                if final_score > best_score:
                    best_score = final_score
                    best_match = payment
                    best_reasons = reasons

            if best_match and best_score >= self.confidence_threshold:
                matches.append(
                    ReconciliationMatch(
                        bank_transaction=tx,
                        erpnext_payment=best_match,
                        confidence_score=round(best_score, 1),
                        match_reasons=best_reasons,
                        is_auto_reconcilable=best_score >= 90.0,
                    )
                )
                unmatched_erp.remove(best_match)

        return matches

    @staticmethod
    def _calc_date_diff(d1_str: str, d2_str: str) -> int:
        try:
            d1 = datetime.strptime(d1_str, "%Y-%m-%d")
            d2 = datetime.strptime(d2_str, "%Y-%m-%d")
            return abs((d1 - d2).days)
        except Exception:
            return 999
