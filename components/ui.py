import streamlit as st

def dashboard_card(container, title, value, hint):
    container.markdown(f"""
                      <div class="dashboard-card">
                      <h3>{title}</h3>
                      <div class="value">{value}</div>
                      <div class="hint">{hint}</div>
                      </div>
                      """,
                      unsafe_allow_html=True)