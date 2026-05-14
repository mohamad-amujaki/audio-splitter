from __future__ import annotations

import streamlit as st

PAGE_TITLE = "Pemotong Audio Online | Potong MP3, M4A, WAV, FLAC"
PAGE_LEAD = (
    "Hasil disimpan ke folder lokal di komputer Anda. Pilih folder output sebelum memotong audio."
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
PAGE_KEYWORDS = (
    "pemotong audio, potong audio, split audio, mp3, m4a, wav, flac, ogg, aac, podcast, "
    "audiobook, ffmpeg, folder lokal"
)
RESPONSIVE_STYLE_KEY = "responsive_styles_injected"
SEO_META_KEY = "seo_meta_injected"

_SEO_META_JS = """
export default function (component) {
  const { data } = component;
  if (!data) {
    return;
  }

  const upsertMeta = (attribute, key, content) => {
    if (!content) {
      return;
    }

    let element = document.head.querySelector(`meta[${attribute}="${key}"]`);
    if (!element) {
      element = document.createElement("meta");
      element.setAttribute(attribute, key);
      document.head.appendChild(element);
    }
    element.setAttribute("content", content);
  };

  upsertMeta("name", "description", data.description);
  upsertMeta("name", "keywords", data.keywords);
  upsertMeta("name", "robots", data.robots);
  upsertMeta("property", "og:title", data.og_title);
  upsertMeta("property", "og:description", data.og_description);
  upsertMeta("property", "og:type", data.og_type);
  upsertMeta("name", "twitter:card", data.twitter_card);
  upsertMeta("name", "twitter:title", data.twitter_title);
  upsertMeta("name", "twitter:description", data.twitter_description);
}
"""

_SEO_META_COMPONENT = st.components.v2.component(
    "audio_splitter_seo_meta",
    html='<div aria-hidden="true" hidden></div>',
    js=_SEO_META_JS,
    isolate_styles=True,
)


def build_seo_meta_data() -> dict[str, str]:
    """Kembalikan payload meta HTML yang tidak ditampilkan di UI."""
    return {
        "description": PAGE_DESCRIPTION,
        "keywords": PAGE_KEYWORDS,
        "robots": "index, follow",
        "og_title": PAGE_TITLE,
        "og_description": PAGE_DESCRIPTION,
        "og_type": "website",
        "twitter_card": "summary",
        "twitter_title": PAGE_TITLE,
        "twitter_description": PAGE_DESCRIPTION,
    }


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


def inject_meta_tags() -> None:
    """Sisipkan meta tag SEO ke head dokumen tanpa menampilkan teks tambahan di halaman."""
    if st.session_state.get(SEO_META_KEY):
        return

    _SEO_META_COMPONENT(
        key="audio_splitter_seo_meta",
        data=build_seo_meta_data(),
        height=0,
    )
    st.session_state[SEO_META_KEY] = True


def render_page_header() -> None:
    """Tampilkan judul dan ringkasan singkat yang relevan bagi pengguna."""
    st.title("Pemotong Audio")
    st.caption(PAGE_LEAD)


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
