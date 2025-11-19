"""Page configuration and shared styles."""
import streamlit as st

BASE_STYLES = """
<style>
.insights-box {
    background: #f1f6ff;
    border: 1px solid #c8d8f2;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
}
body,
.stApp,
.stApp div,
.stApp p,
.stApp li,
.stApp span,
.stApp label,
.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4,
.stApp h5,
.stApp h6 {
    color: #5f6368 !important;
}
.stApp {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}
.stApp > header {
    flex: 0 0 auto;
}
.stApp > main {
    flex: 1 0 auto;
    display: flex;
}
.stApp > main .block-container {
    flex: 1 0 auto;
    display: flex;
    flex-direction: column;
}
.app-footer {
    margin-top: auto;
    padding: 1.25rem 0 2rem;
    text-align: center;
    color: #6c6c6c;
}
.app-footer hr {
    margin: 0 0 1rem;
    border: none;
    border-top: 1px solid #e2e2e2;
}
.footer-disclaimer {
    font-size: 0.78rem;
    color: #7a7a7a;
    line-height: 1.45;
    margin-top: 0.75rem;
}
.hero-disclaimer {
    font-size: 0.84rem;
    color: #7a7a7a;
    margin-top: 0.35rem;
}
.insights-panel__brand {
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
    color: #6b7a99;
    margin-bottom: 0.3rem;
}
.insights-panel__title {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 0.35rem;
}
.insights-panel__disclaimer {
    font-size: 0.78rem;
    color: #7a7a7a;
    margin-bottom: 0.65rem;
}
.insights-panel__body {
    font-size: 0.92rem;
    color: #444;
}
.insights-panel__loading {
    font-style: italic;
    color: #4f5b78;
}
</style>
"""


def configure_page() -> None:
    """Apply Streamlit layout settings and shared CSS."""
    st.set_page_config(layout="wide")
    st.markdown(BASE_STYLES, unsafe_allow_html=True)


__all__ = ["configure_page"]
