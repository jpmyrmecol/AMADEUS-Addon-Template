# Copyright (C) 2026 Yusuke Notomi
# SPDX-License-Identifier: 0BSD

"""Standalone example GUI. Only file paths cross the AMADEUS boundary."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import queue
import threading

from reader import read_config, read_results


def inspect_inputs(config: Path | None, results: Path | None) -> dict:
    output = {}
    if config is not None:
        output["configuration"] = read_config(config)
    if results is not None:
        output["csv"] = read_results(results)
    return output


def run_gui(args) -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox

    root = tk.Tk()
    root.title("AMADEUS Result Viewer (independent add-on)")
    root.geometry("900x640")
    root.minsize(600, 400)
    root.configure(bg="#111111")
    data_dir = args.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    settings_path = data_dir / "settings.json"
    settings = {}
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            if not isinstance(settings, dict):
                raise ValueError("Settings must be an object.")
        except (OSError, ValueError) as exc:
            settings = {}
            messagebox.showwarning("Settings", f"Could not read saved selections: {exc}", parent=root)
    selections = {
        "config": tk.StringVar(value=str(args.config or settings.get("config", ""))),
        "results": tk.StringVar(value=str(args.results or settings.get("results", ""))),
    }
    tk.Label(root, text="Read AMADEUS results and configuration", bg="#111111", fg="white", font=("Arial", 17, "bold")).pack(pady=15)
    for key, label, patterns in (("config", "Configuration", "*.yaml *.yml"), ("results", "Results CSV", "*.csv")):
        row = tk.Frame(root, bg="#111111")
        row.pack(fill="x", padx=16, pady=5)
        tk.Label(row, text=label, width=14, anchor="w", bg="#111111", fg="white").pack(side="left")
        tk.Entry(row, textvariable=selections[key]).pack(side="left", fill="x", expand=True, padx=5)
        def browse(field=key, pattern=patterns):
            value = filedialog.askopenfilename(parent=root, filetypes=[("Input file", pattern), ("All files", "*")])
            if value:
                selections[field].set(value)
        tk.Button(row, text="Browse...", command=browse).pack(side="left")
    status = tk.StringVar(value="Input files are read only. No coordinates, units or frame numbers are converted.")
    tk.Label(root, textvariable=status, bg="#111111", fg="#aaaaaa", wraplength=850).pack(padx=16, pady=8)
    output = tk.Text(root, wrap="none", bg="#181818", fg="white", insertbackground="white")
    output.pack(fill="both", expand=True, padx=16, pady=8)
    results_queue = queue.Queue()
    busy = False

    def load():
        nonlocal busy
        if busy:
            return
        values = {key: var.get().strip() for key, var in selections.items()}
        if not any(values.values()):
            messagebox.showinfo("Select input", "Choose a configuration, a results CSV, or both.", parent=root)
            return
        busy = True
        button.configure(state="disabled")
        status.set("Reading files...")
        def worker():
            try:
                result = inspect_inputs(Path(values["config"]) if values["config"] else None,
                                        Path(values["results"]) if values["results"] else None)
                results_queue.put((result, None))
            except Exception as exc:
                results_queue.put((None, str(exc)))
        threading.Thread(target=worker, daemon=True).start()
        def poll():
            nonlocal busy
            try:
                result, error = results_queue.get_nowait()
            except queue.Empty:
                root.after(50, poll)
                return
            busy = False
            button.configure(state="normal")
            if error:
                status.set(error)
                messagebox.showerror("Unable to read input", error, parent=root)
                return
            output.delete("1.0", "end")
            output.insert("end", json.dumps(result, indent=2, ensure_ascii=False, default=str))
            try:
                temporary = settings_path.with_suffix(".tmp")
                temporary.write_text(json.dumps(values, indent=2), encoding="utf-8")
                os.replace(temporary, settings_path)
            except OSError as exc:
                status.set(f"Files read, but selections could not be saved: {exc}")
                return
            status.set("Files read without modification. CSV record counts are not interpreted as frame or animal counts.")
        root.after(50, poll)

    button = tk.Button(root, text="Read files", command=load)
    button.pack(pady=(0, 12))
    if args.config or args.results:
        root.after(100, load)
    root.mainloop()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="AMADEUS config.yaml (read only)")
    parser.add_argument("--results", type=Path, help="AMADEUS results CSV (read only)")
    parser.add_argument("--dropped-file", type=Path,
                        help="A file dropped onto this add-on's Home panel (CSV, YAML)")
    parser.add_argument("--data-dir", type=Path,
                        default=Path(os.environ.get("AMADEUS_ADDON_DATA_DIR", Path.home() / ".amadeus-result-viewer")))
    parser.add_argument("--check", action="store_true", help="Read inputs and print JSON without opening a GUI")
    args = parser.parse_args()
    if args.dropped_file is not None:
        suffix = args.dropped_file.suffix.lower()
        if suffix == ".csv":
            args.results = args.dropped_file
        elif suffix in {".yaml", ".yml"}:
            args.config = args.dropped_file
        else:
            parser.error("The example accepts dropped CSV, YAML and YML files only.")
    if args.check:
        print(json.dumps(inspect_inputs(args.config, args.results), indent=2, ensure_ascii=False, default=str))
    else:
        run_gui(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
