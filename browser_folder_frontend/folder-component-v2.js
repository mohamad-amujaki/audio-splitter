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
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
    transaction.objectStore(STORE_NAME).put(handle, "output");
  });
}

async function loadDirectoryHandle() {
  const database = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = database.transaction(STORE_NAME, "readonly");
    transaction.onerror = () => reject(transaction.error);
    const request = transaction.objectStore(STORE_NAME).get("output");
    request.onsuccess = () => resolve(request.result || null);
    request.onerror = () => reject(request.error);
  });
}

async function ensureWritePermission(handle) {
  const permission = await handle.queryPermission({ mode: "readwrite" });
  if (permission === "granted") {
    return true;
  }

  const requested = await handle.requestPermission({ mode: "readwrite" });
  return requested === "granted";
}

function decodeBase64(base64) {
  const raw = atob(base64);
  const bytes = new Uint8Array(raw.length);
  for (let index = 0; index < raw.length; index += 1) {
    bytes[index] = raw.charCodeAt(index);
  }
  return bytes;
}

export default function (component) {
  const { parentElement, data, setStateValue } = component;
  const pickButton = parentElement.querySelector("#pick-folder");
  const folderStatus = parentElement.querySelector("#folder-status");

  if (!pickButton || !folderStatus) {
    return;
  }

  let directoryHandle = parentElement.__audioSplitterDirectoryHandle || null;
  let lastReportedName = parentElement.dataset.lastReportedName || "";

  function setStatus(message) {
    folderStatus.textContent = message;
  }

  function publishState(payload) {
    setStateValue("name", payload.name ?? "");
    setStateValue("selected", Boolean(payload.selected));
    setStateValue("saved", Number(payload.saved ?? 0));
    setStateValue("error", payload.error ?? null);
  }

  async function restoreDirectoryHandle() {
    if (directoryHandle) {
      return directoryHandle;
    }

    try {
      const storedHandle = await loadDirectoryHandle();
      if (!storedHandle) {
        return null;
      }

      if (!(await ensureWritePermission(storedHandle))) {
        return null;
      }

      directoryHandle = storedHandle;
      parentElement.__audioSplitterDirectoryHandle = directoryHandle;
      setStatus(`Folder terpilih: ${directoryHandle.name}`);
      return directoryHandle;
    } catch (error) {
      return null;
    }
  }

  function reportSelection(force) {
    if (!directoryHandle) {
      return;
    }

    const payload = {
      name: directoryHandle.name,
      selected: true,
      saved: 0,
      error: null,
    };
    if (force || directoryHandle.name !== lastReportedName) {
      lastReportedName = directoryHandle.name;
      parentElement.dataset.lastReportedName = lastReportedName;
      publishState(payload);
    }
  }

  async function saveFiles(files) {
    if (!(await restoreDirectoryHandle())) {
      publishState({
        name: "",
        selected: false,
        saved: 0,
        error: "Pilih folder output lokal terlebih dahulu.",
      });
      return;
    }

    if (!(await ensureWritePermission(directoryHandle))) {
      publishState({
        name: directoryHandle.name,
        selected: true,
        saved: 0,
        error: "Izin menulis ke folder belum diberikan.",
      });
      return;
    }

    try {
      for (const file of files) {
        const parts = file.relative_path.split("/");
        const fileName = parts.pop();
        let targetDirectory = directoryHandle;
        for (const part of parts) {
          targetDirectory = await targetDirectory.getDirectoryHandle(part, { create: true });
        }
        const fileHandle = await targetDirectory.getFileHandle(fileName, { create: true });
        const writable = await fileHandle.createWritable();
        await writable.write(decodeBase64(file.data));
        await writable.close();
      }

      publishState({
        name: directoryHandle.name,
        selected: true,
        saved: files.length,
        error: null,
      });
    } catch (error) {
      publishState({
        name: directoryHandle.name,
        selected: true,
        saved: 0,
        error: "Gagal menyimpan file ke folder lokal.",
      });
    }
  }

  async function syncFromData() {
    const files = JSON.parse((data && data.files_json) || "[]");
    if (files.length > 0) {
      await saveFiles(files);
      return;
    }

    await restoreDirectoryHandle();
    if (directoryHandle) {
      reportSelection(true);
    }
  }

  if (!pickButton.dataset.bound) {
    pickButton.dataset.bound = "true";
    pickButton.addEventListener("click", async () => {
      if (!window.showDirectoryPicker) {
        setStatus("Browser ini tidak mendukung pemilihan folder lokal.");
        return;
      }

      try {
        directoryHandle = await window.showDirectoryPicker();
        parentElement.__audioSplitterDirectoryHandle = directoryHandle;
        await storeDirectoryHandle(directoryHandle);
        setStatus(`Folder terpilih: ${directoryHandle.name}`);
        reportSelection(true);
      } catch (error) {
        setStatus("Folder tidak dipilih.");
      }
    });
  }

  void syncFromData();
}
