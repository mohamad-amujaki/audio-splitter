from __future__ import annotations

import streamlit as st

PAGE_TITLE = "Pemotong Audio Online | Potong MP3, M4A, WAV, FLAC"
PAGE_LEAD = (
    "Potong file audio panjang menjadi beberapa bagian berdurasi 10, 20, atau 30 menit. "
    "Hasil disimpan ke folder lokal di komputer Anda tanpa re-encode saat format asal dipilih."
)
PAGE_INTRO_MARKDOWN = (
    "Aplikasi pemotong audio ini mendukung format populer seperti MP3, M4A, WAV, FLAC, OGG, "
    "dan AAC. Cocok untuk podcast, rekaman kuliah, audiobook, serta file musik yang perlu "
    "dibagi menjadi beberapa bagian."
)
PAGE_DESCRIPTION = (
    "Pemotong audio online untuk memecah file MP3, M4A, WAV, FLAC, dan format audio lain "
    "menjadi beberapa segmen berdurasi tetap. Pemrosesan lokal, pilih folder output lokal, "
    "dan simpan hasil langsung ke komputer Anda."
)
RESPONSIVE_STYLE_KEY = "responsive_styles_injected"


def configure_streamlit_page() -> None:
    """Atur judul halaman dan layout awal agar mudah dibaca di desktop maupun ponsel."""
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon="🎧",
        layout="centered",
        initial_sidebar_state="collapsed",
        menu_items={
            "Get help": None,
            "Report a bug": None,
        },
    )


def render_page_intro() -> None:
    """Tampilkan judul dan narasi pembuka yang jelas untuk pengguna dan mesin pencari."""
    st.title("Pemotong Audio Online")
    st.caption(PAGE_LEAD)
    st.markdown(f"{PAGE_INTRO_MARKDOWN}\n\n{PAGE_DESCRIPTION}")


def inject_responsive_styles() -> None:
    """Suntikkan CSS ringan sekali per sesi untuk tata letak responsif dan target sentuh."""
    if st.session_state.get(RESPONSIVE_STYLE_KEY):
        return

    st.markdown(
        """
        <style>
          main .block-container {
            max-width: 760px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
          }

          @media (max-width: 768px) {
            main .block-container {
              padding-left: 1rem;
              padding-right: 1rem;
            }

            div[data-testid="stRadio"] [role="radiogroup"] {
              flex-wrap: wrap;
              row-gap: 0.5rem;
            }
          }

          @media (prefers-reduced-motion: reduce) {
            * {
              scroll-behavior: auto !important;
              transition: none !important;
              animation: none !important;
            }
          }

          .audio-folder-picker button {
            min-height: 44px;
            width: 100%;
          }

          .audio-folder-picker [id="folder-status"] {
            margin-top: 0.75rem;
            line-height: 1.5;
            word-break: break-word;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state[RESPONSIVE_STYLE_KEY] = True
