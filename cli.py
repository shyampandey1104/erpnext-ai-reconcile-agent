#!/usr/bin/env python3
"""CLI utility for running automated bank reconciliation."""

import typer
from rich.console import Console
from rich.table import Table
from typing import Optional
import os

from reconciler.parser import BankStatementParser
from reconciler.matcher import ReconciliationMatcher, ERPNextPaymentEntry

app = typer.Typer(help="ERPNext AI Automated Financial Reconciliation Agent")
console = Console()

# Mock ERPNext ledger payment records
MOCK_ERP_ENTRIES = [
    ERPNextPaymentEntry(
        name="ACC-PAY-2026-00089",
        posting_date="2026-11-02",
        party_type="Customer",
        party_name="Sharma Textiles and Garments",
        paid_amount=45000.0,
        reference_no="630811928312",
    ),
    ERPNextPaymentEntry(
        name="ACC-PAY-2026-00092",
        posting_date="2026-11-03",
        party_type="Supplier",
        party_name="Virar Packaging Pvt Ltd",
        paid_amount=18250.0,
        reference_no="N1042026",
    ),
    ERPNextPaymentEntry(
        name="ACC-PAY-2026-00098",
        posting_date="2026-11-06",
        party_type="Customer",
        party_name="Ananya Traders Mumbai",
        paid_amount=125000.0,
        reference_no="HDFCR520261107",
    ),
]


@app.command()
def reconcile(
    file_path: str = typer.Argument(..., help="Path to bank statement CSV file"),
    threshold: float = typer.Option(80.0, "--threshold", "-t", help="Confidence threshold (0-100)"),
):
    """Reconcile bank statement with ERPNext Payment Entries."""
    if not os.path.exists(file_path):
        console.print(f"[bold red]File not found:[/] {file_path}")
        raise typer.Exit(code=1)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    transactions = BankStatementParser.parse_csv(content)
    console.print(f"[bold cyan]🔍 Parsed {len(transactions)} bank transactions from {file_path}[/]\n")

    matcher = ReconciliationMatcher(confidence_threshold=threshold)
    matches = matcher.match_records(transactions, MOCK_ERP_ENTRIES)

    table = Table(title=f"Reconciliation Results ({len(matches)} matched)")
    table.add_column("Date", style="dim")
    table.add_column("Bank Narration", style="cyan")
    table.add_column("ERP Payment ID", style="magenta")
    table.add_column("ERP Party Name", style="white")
    table.add_column("Amount (₹)", style="green")
    table.add_column("Confidence", style="bold yellow")
    table.add_column("Auto-Clear", style="bold green")

    for m in matches:
        amt = m.bank_transaction.deposit or m.bank_transaction.withdrawal
        auto_flag = "✓ YES" if m.is_auto_reconcilable else "⚠️ REVIEW"
        table.add_row(
            m.bank_transaction.transaction_date,
            m.bank_transaction.description[:35] + "...",
            m.erpnext_payment.name,
            m.erpnext_payment.party_name,
            f"₹{amt:,.2f}",
            f"{m.confidence_score}%",
            auto_flag,
        )

    console.print(table)
    console.print(f"\n[bold green]✓ Reconciled successfully! {len(matches)} vouchers ready to push to ERPNext Bank Reconciliation Tool.[/]")


if __name__ == "__main__":
    app()
