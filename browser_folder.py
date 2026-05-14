from __future__ import annotations

import base64
import json
from pathlib import Path

import streamlit.components.v1 as components

FOLDER_PICKER_HTML = """
<div>
  <button id="pick-folder" type="button">Pilih folder lokal…</button>
  <p id="folder-status">Belum ada folder dipilih.</p>
</div>
<script>
const DB_NAME = "audio-splitter";
const STORE_NAME = "folder-handle";

async function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      request.result.createObjectStore(STORE_NAME);
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function storeDirectoryHandle(handle) {
  const database = await openDatabase();
  await new Promise((resolve, reject) => {
    const transaction = database.transaction(STORE_NAME, "readwrite");
    transaction.objectStore(STORE_NAME).put(handle, "selected");
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
  });
}

async function loadDirectoryHandle() {
  const database = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = database.transaction(STORE_NAME, "readonly");
    const request = transaction.objectStore(STORE_NAME).get("selected");
    request.onsuccess = () => resolve(request.result || null);
    request.onerror = () => reject(request.error);
  });
}

async function refreshStatus() {
  const status = document.getElementById("folder-status");
  if (!window.showDirectoryPicker) {
    status.textContent = "Browser ini tidak mendukung pemilihan folder lokal.";
    return;
  }

  const handle = await loadDirectoryHandle();
  if (!handle) {
    status.textContent = "Belum ada folder dipilih.";
    return;
  }

  const permission = await handle.queryPermission({ mode: "readwrite" });
  if (permission !== "granted") {
    const requested = await handle.requestPermission({ mode: "readwrite" });
    if (requested !== "granted") {
      status.textContent = "Izin menulis ke folder belum diberikan.";
      return;
    }
  }

  status.textContent = `Folder terpilih: ${handle.name}`;
}

document.getElementById("pick-folder").addEventListener("click", async () => {
  const status = document.getElementById("folder-status");
  if (!window.showDirectoryPicker) {
    status.textContent = "Browser ini tidak mendukung pemilihan folder lokal.";
    return;
  }

  try {
    const handle = await window.showDirectoryPicker();
    await storeDirectoryHandle(handle);
    status.textContent = `Folder terpilih: ${handle.name}`;
  } catch (error) {
    status.textContent = "Folder tidak dipilih.";
  }
});

refreshStatus();
</script>
"""


def render_browser_folder_picker() -> None:
    components.html(FOLDER_PICKER_HTML, height=110)


def render_browser_folder_save(output_paths: list[Path], output_root: Path) -> None:
    if not output_paths:
        return

    files_payload = []
    for output_path in output_paths:
        files_payload.append(
            {
                "relative_path": output_path.relative_to(output_root).as_posix(),
                "data": base64.b64encode(output_path.read_bytes()).decode("ascii"),
            }
        )

    save_html = f"""
<script>
const files = {json.dumps(files_payload)};

async function openDatabase() {{
  return new Promise((resolve, reject) => {{
    const request = indexedDB.open("audio-splitter", 1);
    request.onupgradeneeded = () => {{
      request.result.createObjectStore("folder-handle");
    }};
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  }});
}}

async function loadDirectoryHandle() {{
  const database = await openDatabase();
  return new Promise((resolve, reject) => {{
    const transaction = database.transaction("folder-handle", "readonly");
    const request = transaction.objectStore("folder-handle").get("selected");
    request.onsuccess = () => resolve(request.result || null);
    request.onerror = () => reject(request.error);
  }});
}}

async function saveFiles() {{
  const handle = await loadDirectoryHandle();
  if (!handle) {{
    return;
  }}

  const permission = await handle.queryPermission({{ mode: "readwrite" }});
  if (permission !== "granted") {{
    const requested = await handle.requestPermission({{ mode: "readwrite" }});
    if (requested !== "granted") {{
      return;
    }}
  }}

  for (const file of files) {{
    const parts = file.relative_path.split("/");
    const fileName = parts.pop();
    let directoryHandle = handle;
    for (const part of parts) {{
      directoryHandle = await directoryHandle.getDirectoryHandle(part, {{ create: true }});
    }}
    const fileHandle = await directoryHandle.getFileHandle(fileName, {{ create: true }});
    const writable = await fileHandle.createWritable();
    const binary = Uint8Array.from(atob(file.data), (char) => char.charCodeAt(0));
    await writable.write(binary);
    await writable.close();
  }}
}}

saveFiles();
</script>
"""
    components.html(save_html, height=0)
