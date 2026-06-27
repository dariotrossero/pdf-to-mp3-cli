"""Interfaz gráfica: arrastrar PDF/DOCX y convertir a MP3."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from tkinterdnd2 import DND_FILES, TkinterDnD

from .converter import SUPPORTED_EXTENSIONS, ConvertOptions, convert_batch


class PdfToMp3App:
    def __init__(self, root: TkinterDnD.Tk) -> None:
        self.root = root
        self.root.title("PDF a MP3")
        self.root.minsize(480, 420)
        self.root.geometry("560x480")

        self._files: list[Path] = []
        self._busy = False

        self._build_ui()

    def _build_ui(self) -> None:
        padding = {"padx": 12, "pady": 6}

        self.drop_frame = tk.Frame(
            self.root,
            relief=tk.GROOVE,
            bd=2,
            bg="#f0f4f8",
            highlightbackground="#94a3b8",
            highlightthickness=1,
        )
        self.drop_frame.pack(fill=tk.X, **padding, ipady=28)

        self.drop_label = tk.Label(
            self.drop_frame,
            text="Arrastra PDF o DOCX aquí\n(o haz clic para seleccionar)",
            bg="#f0f4f8",
            fg="#475569",
            font=("Segoe UI", 11),
            cursor="hand2",
        )
        self.drop_label.pack(expand=True)
        self.drop_label.bind("<Button-1>", lambda _e: self._browse_files())

        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind("<<Drop>>", self._on_drop)
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self._on_drop)

        list_header = tk.Frame(self.root)
        list_header.pack(fill=tk.X, **padding)
        tk.Label(
            list_header,
            text="Archivos a convertir",
            font=("Segoe UI", 10, "bold"),
        ).pack(side=tk.LEFT)

        btn_frame = tk.Frame(list_header)
        btn_frame.pack(side=tk.RIGHT)
        self.add_btn = ttk.Button(btn_frame, text="Agregar…", command=self._browse_files)
        self.add_btn.pack(side=tk.LEFT, padx=(0, 6))
        self.remove_btn = ttk.Button(
            btn_frame, text="Quitar", command=self._remove_selected
        )
        self.remove_btn.pack(side=tk.LEFT)
        self.clear_btn = ttk.Button(
            btn_frame, text="Limpiar", command=self._clear_files
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(6, 0))

        list_frame = tk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 6))

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_list = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set,
            font=("Segoe UI", 10),
            activestyle="none",
        )
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_list.yview)

        progress_frame = tk.Frame(self.root)
        progress_frame.pack(fill=tk.X, **padding)

        self.status_var = tk.StringVar(value="Listo")
        self.status_label = tk.Label(
            progress_frame,
            textvariable=self.status_var,
            anchor=tk.W,
            font=("Segoe UI", 9),
            fg="#64748b",
        )
        self.status_label.pack(fill=tk.X, pady=(0, 4))

        self.progress = ttk.Progressbar(progress_frame, mode="determinate", maximum=100)
        self.progress.pack(fill=tk.X)

        action_frame = tk.Frame(self.root)
        action_frame.pack(fill=tk.X, padx=12, pady=(6, 12))

        self.transcribe_btn = ttk.Button(
            action_frame,
            text="Convertir a MP3",
            command=self._start_conversion,
        )
        self.transcribe_btn.pack(side=tk.RIGHT)

        tk.Label(
            action_frame,
            text="El MP3 se guarda junto al archivo original (edge-tts)",
            font=("Segoe UI", 9),
            fg="#64748b",
        ).pack(side=tk.LEFT)

    def _parse_dropped_paths(self, data: str) -> list[Path]:
        paths: list[Path] = []
        for raw in self.root.tk.splitlist(data):
            path = Path(raw.strip("{}").strip())
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                paths.append(path.resolve())
        return paths

    def _on_drop(self, event) -> None:
        if self._busy:
            return
        self._add_files(self._parse_dropped_paths(event.data))

    def _browse_files(self) -> None:
        if self._busy:
            return
        selected = filedialog.askopenfilenames(
            title="Seleccionar PDF o DOCX",
            filetypes=[
                ("Documentos", "*.pdf *.docx"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx"),
                ("Todos", "*.*"),
            ],
        )
        if selected:
            self._add_files([Path(f).resolve() for f in selected])

    def _add_files(self, paths: list[Path]) -> None:
        added = 0
        for path in paths:
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            if path not in self._files:
                self._files.append(path)
                self.file_list.insert(tk.END, str(path))
                added += 1
        if added:
            self.status_var.set(f"{len(self._files)} archivo(s) en la lista")

    def _remove_selected(self) -> None:
        if self._busy:
            return
        indices = list(self.file_list.curselection())
        if not indices:
            return
        for index in reversed(indices):
            self.file_list.delete(index)
            del self._files[index]
        self.status_var.set(
            f"{len(self._files)} archivo(s) en la lista" if self._files else "Listo"
        )

    def _clear_files(self) -> None:
        if self._busy:
            return
        self._files.clear()
        self.file_list.delete(0, tk.END)
        self.status_var.set("Listo")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.transcribe_btn.config(state=state)
        self.add_btn.config(state=state)
        self.remove_btn.config(state=state)
        self.clear_btn.config(state=state)
        self.drop_label.config(cursor="" if busy else "hand2")

    def _update_progress(self, message: str, fraction: float) -> None:
        def apply() -> None:
            self.status_var.set(message)
            self.progress["value"] = fraction * 100

        self.root.after(0, apply)

    def _start_conversion(self) -> None:
        if self._busy:
            return
        if not self._files:
            messagebox.showinfo("Sin archivos", "Agrega al menos un PDF o DOCX.")
            return

        self._set_busy(True)
        self.progress["value"] = 0
        self.status_var.set("Iniciando…")

        files = list(self._files)
        thread = threading.Thread(
            target=self._run_conversion,
            args=(files,),
            daemon=True,
        )
        thread.start()

    def _run_conversion(self, files: list[Path]) -> None:
        try:
            results = convert_batch(
                files,
                options=ConvertOptions(),
                on_progress=self._update_progress,
            )
        except Exception as exc:
            self.root.after(
                0,
                lambda: self._on_conversion_done([], error=str(exc)),
            )
            return

        self.root.after(0, lambda: self._on_conversion_done(results))

    def _on_conversion_done(
        self,
        results: list[tuple[Path, Path | Exception]],
        *,
        error: str | None = None,
    ) -> None:
        self._set_busy(False)
        self.progress["value"] = 100 if results or error else 0

        if error:
            self.status_var.set("Error")
            messagebox.showerror("Error", error)
            return

        ok = [mp3 for _, mp3 in results if isinstance(mp3, Path)]
        failed = [(src, err) for src, err in results if isinstance(err, Exception)]

        if failed and not ok:
            self.status_var.set("Falló la conversión")
            details = "\n".join(f"• {src.name}: {err}" for src, err in failed)
            messagebox.showerror("Error", details)
            return

        if failed:
            self.status_var.set(f"Completado con errores ({len(ok)}/{len(results)})")
            details = "\n".join(f"• {src.name}: {err}" for src, err in failed)
            messagebox.showwarning(
                "Completado con errores",
                f"Convertidos: {len(ok)}\nFallidos: {len(failed)}\n\n{details}",
            )
        else:
            self.status_var.set(f"Listo — {len(ok)} archivo(s) convertido(s)")
            messagebox.showinfo(
                "Completado",
                f"Se generaron {len(ok)} MP3 junto a los archivos originales.",
            )


def main() -> None:
    root = TkinterDnD.Tk()
    PdfToMp3App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
