"""AirPilot web app (Gradio). Reads PORT, binds 0.0.0.0 for Render.

Core is stdlib; Gradio is the only third-party dep and only used by the web UI.
The same Incident Commander runs offline (fixtures) so the demo needs no key.
"""
from __future__ import annotations

import os

import gradio as gr

from airpilot.client import AirwallexClient
from airpilot.agent import command
from airpilot import fixtures as _fx
from airpilot import receipts as _rc


def run():
    client = AirwallexClient()
    client.offline = True  # demo uses fixtures; flip to live with real creds
    rc = command(client, now=_fx.scenario_now())
    html = _rc.to_html(rc)
    summary = ("source=%s · incidents=%d · acted=%d · blocked=%d"
               % (rc["source"], rc["incidents_found"],
                  rc["acted_count"], rc["blocked_count"]))
    return html, summary


with gr.Blocks(title="AirPilot — Incident Commander") as demo:
    gr.Markdown("# 🛡️ AirPilot — Airwallex Payment Ops Incident Commander\n"
                "Proposes remedies; a deterministic verifier decides what moves money. "
                "**Never double-pays.**")
    btn = gr.Button("Run Incident Commander (offline demo)")
    summary = gr.Textbox(label="Result", interactive=False)
    html_out = gr.HTML()
    btn.click(run, None, [html_out, summary])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=port)
