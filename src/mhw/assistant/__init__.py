"""Data-assistant service — the chatbot's brains, frontend-agnostic.

All intelligence lives here (agent loop, tools, chart specs, deck builder, access guard) so the
Streamlit page is a thin HTTP client and a future React frontend rebuilds only the chat shell.
Nothing in this package imports Streamlit.
"""
