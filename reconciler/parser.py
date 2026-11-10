"""Bank statement parser converting raw CSV/PDF records into standardized transaction models."""

import csv
import io
import re
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class BankTransaction(BaseModel):
    transaction_date: str  # YYYY-MM-DD
    description: str
    reference_number: Optional[str] = None
    withdrawal: float = 0.0
    deposit: float = 0.0
    balance: float = 0.0
    extracted_party: Optional[str] = None


class BankStatementParser:
    """Parses diverse Indian & global bank statement formats (HDFC, ICICI, SBI, Standard)."""

    DATE_PATTERNS = [
        r"\d{2}/\d{2}/\d{4}",
        r"\d{4}-\d{2}-\d{2}",
        r"\d{2}-\d{2}-\d{4}",
    ]

    @classmethod
    def parse_csv(cls, file_content: str) -> List[BankTransaction]:
        reader = csv.DictReader(io.StringIO(file_content.strip()))
        transactions: List[BankTransaction] = []

        for row in reader:
            # Normalize column names
            normalized = {k.strip().lower().replace(" ", "_"): v for k, v in row.items() if k}

            date_str = (
                normalized.get("date")
                or normalized.get("transaction_date")
                or normalized.get("value_date")
                or ""
            )
            parsed_date = cls._normalize_date(date_str)
            if not parsed_date:
                continue

            desc = (
                normalized.get("description")
                or normalized.get("narration")
                or normalized.get("particulars")
                or ""
            )

            ref_no = (
                normalized.get("chq/ref_no")
                or normalized.get("reference")
                or normalized.get("ref_no")
                or cls._extract_utr_or_ref(desc)
            )

            withdrawal = cls._clean_float(
                normalized.get("withdrawal")
                or normalized.get("debit")
                or normalized.get("withdrawal_amt")
                or 0.0
            )

            deposit = cls._clean_float(
                normalized.get("deposit")
                or normalized.get("credit")
                or normalized.get("deposit_amt")
                or 0.0
            )

            balance = cls._clean_float(
                normalized.get("balance") or normalized.get("closing_balance") or 0.0
            )

            party = cls._extract_party_name(desc)

            tx = BankTransaction(
                transaction_date=parsed_date,
                description=desc,
                reference_number=ref_no,
                withdrawal=withdrawal,
                deposit=deposit,
                balance=balance,
                extracted_party=party,
            )
            transactions.append(tx)

        return transactions

    @staticmethod
    def _clean_float(val: Any) -> float:
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).replace(",", "").replace("₹", "").strip()
        try:
            return float(val_str)
        except ValueError:
            return 0.0

    @staticmethod
    def _normalize_date(raw_date: str) -> Optional[str]:
        raw_date = raw_date.strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
            try:
                dt = datetime.strptime(raw_date, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
        return None

    @staticmethod
    def _extract_utr_or_ref(desc: str) -> Optional[str]:
        # Extract UTR / IMPS / NEFT / UPI ref
        match = re.search(r"(?:UPI|IMPS|NEFT|RTGS|REF)[/-]?([A-Za-z0-9]{8,18})", desc, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _extract_party_name(desc: str) -> Optional[str]:
        # Common Indian bank transaction narrations: UPI/12345/Payment to VendorName/bank
        upi_match = re.search(r"UPI/(?:CR|DR)?/\d+/([^/]+)", desc)
        if upi_match:
            return upi_match.group(1).replace("-", " ").strip()
        neft_match = re.search(r"NEFT(?:-|\s+)[A-Z0-9]+(?:-|\s+)([^/-]+)", desc)
        if neft_match:
            return neft_match.group(1).strip()
        return None
