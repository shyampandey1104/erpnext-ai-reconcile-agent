# Copyright (c) 2026, Shyamkumar Pandey and contributors
# For license information, please see license.txt

app_name = "samples"
app_title = "Erpnext Ai Reconcile Agent"
app_publisher = "Shyamkumar Pandey"
app_description = "Erpnext Ai Reconcile Agent for Frappe and ERPNext"
app_email = "shyampandey1104@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------
app_include_css = "/assets/samples/css/samples.bundle.css"
app_include_js = "/assets/samples/js/samples.bundle.js"

# Document Events
# ---------------
doc_events = {
    "DocType Event": {
        "on_submit": "samples.engine.on_document_submit",
        "on_cancel": "samples.engine.on_document_cancel"
    }
}

# Scheduled Tasks
# ---------------
scheduler_events = {
    "daily": [
        "samples.engine.daily_scheduled_sync"
    ]
}
