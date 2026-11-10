"""ERPNext API sync client for posting bank clearance vouchers."""

import httpx
from typing import List, Dict, Any, Optional
from reconciler.matcher import ReconciliationMatch


class ERPNextReconcileSync:
    def __init__(self, base_url: str, api_key: str, api_secret: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"token {api_key}:{api_secret}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def update_clearance_date(self, payment_entry_name: str, clearance_date: str) -> bool:
        """Update clearance_date on ERPNext Payment Entry."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.put(
                    f"{self.base_url}/api/resource/Payment Entry/{payment_entry_name}",
                    headers=self.headers,
                    json={"clearance_date": clearance_date},
                )
                return res.status_code == 200
            except Exception:
                return False

    async def create_bank_transaction(self, match: ReconciliationMatch, bank_account: str) -> Optional[str]:
        """Create Frappe 'Bank Transaction' DocType record."""
        tx = match.bank_transaction
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                payload = {
                    "doctype": "Bank Transaction",
                    "date": tx.transaction_date,
                    "bank_account": bank_account,
                    "deposit": tx.deposit,
                    "withdrawal": tx.withdrawal,
                    "description": tx.description,
                    "reference_number": tx.reference_number,
                    "party_type": match.erpnext_payment.party_type,
                    "party": match.erpnext_payment.party_name,
                    "allocated_amount": tx.deposit if tx.deposit > 0 else tx.withdrawal,
                    "payment_document": "Payment Entry",
                    "payment_entry": match.erpnext_payment.name,
                }
                res = await client.post(
                    f"{self.base_url}/api/resource/Bank Transaction",
                    headers=self.headers,
                    json=payload,
                )
                if res.status_code in (200, 201):
                    return res.json().get("data", {}).get("name")
            except Exception:
                pass
        return None
