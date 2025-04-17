import os
import shutil
import re
import threading
import numpy as np
import pydicom
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

# DICOM Series Copy Tool - GUI Application
class DICOMSeriesCopierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DICOM Series Copier")
        self.root.geometry("1100x700")

        # Initialize parameters and state
        self.series_info = {}
        self.filtered_uids = []
        self.input_folder = None
        self.last_output_folder = None
        self.last_naming_mode = "original"
        self.last_custom_name = ""
        self.last_prefix = ""
        self.current_image = None
        self.current_series_uid = None
        self.current_index = 0
        # Top button section
        btn_frame = tk.Frame(root)
        btn_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        tk.Button(btn_frame, text="Load DICOM Folder", command=self.load_dicom_root).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Copy Selected Series", command=self.copy_selected_series).pack(side=tk.LEFT, padx=10)

        # Search bar
        search_frame = tk.Frame(root)
        search_frame.pack(fill=tk.X, padx=10)
        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.update_filtered_series())
        tk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Main layout: folder tree + series list + preview
        main_frame = tk.Frame(root)
        main_frame.pack(expand=True, fill=tk.BOTH)
        # Left: Folder tree
        tree_frame = tk.Frame(main_frame)
        tree_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 5), pady=5)

        self.tree = ttk.Treeview(tree_frame)
        tree_scroll = tk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.Y)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<<TreeviewOpen>>", self.on_tree_expand)

        # Right: Series list and preview canvas
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(5, 10), pady=5)

        listbox_frame = tk.Frame(right_frame)
        listbox_frame.pack(fill=tk.X)

        self.series_listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE, width=120, height=15)
        listbox_scroll = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.series_listbox.yview)
        self.series_listbox.config(yscrollcommand=listbox_scroll.set)
        self.series_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        listbox_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.series_listbox.bind("<<ListboxSelect>>", self.on_series_select)

        self.preview_canvas = tk.Canvas(right_frame, width=256, height=256, bg="black")
        self.preview_canvas.pack(pady=10)
        self.preview_canvas.bind("<MouseWheel>", self.on_mouse_scroll)

        self.loading_label = tk.Label(root, text="", fg="blue")
        self.loading_label.pack(pady=(0, 2))

        self.progress_bar = ttk.Progressbar(root, mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=10, pady=(0, 5))
        self.progress_bar.pack_forget()
    def load_dicom_root(self):
        folder = filedialog.askdirectory(title="Select DICOM Root Folder")
        if not folder:
            return
        self.input_folder = folder
        self.tree.delete(*self.tree.get_children())
        self.insert_node("", folder)

    def insert_node(self, parent, abspath):
        node = self.tree.insert(parent, "end", text=os.path.basename(abspath), values=[abspath])
        if self.has_subdirs(abspath):
            self.tree.insert(node, "end")  # Placeholder for expandable indicator

    def has_subdirs(self, path):
        try:
            return any(os.path.isdir(os.path.join(path, f)) for f in os.listdir(path))
        except:
            return False

    def on_tree_expand(self, event):
        node = self.tree.focus()
        children = self.tree.get_children(node)
        if len(children) == 1 and self.tree.item(children[0], "text") == "":
            self.tree.delete(children[0])
            path = self.tree.item(node)["values"][0]
            for name in sorted(os.listdir(path)):
                full = os.path.join(path, name)
                if os.path.isdir(full):
                    self.insert_node(node, full)

    def on_tree_select(self, event):
        self.series_listbox.delete(0, tk.END)
        self.preview_canvas.delete("all")
        selected = self.tree.focus()
        folder_path = self.tree.item(selected)["values"][0]
        if self.tree.get_children(selected):  # Has children? not a leaf
            return
        self.loading_label.config(text="Loading, please wait...")
        threading.Thread(target=self.load_series_in_background, args=(folder_path,)).start()

    def load_series_in_background(self, folder_path):
        all_files = [os.path.join(root, f) for root, _, files in os.walk(folder_path) for f in files]
        total = len(all_files)
        self.root.after(0, lambda: self.show_progress_bar(total))

        series_info = {}
        for i, filepath in enumerate(all_files):
            self.root.after(0, lambda val=i: self.progress_bar.step(1))
            try:
                ds = pydicom.dcmread(filepath, stop_before_pixels=True)
                uid = ds.SeriesInstanceUID
                desc = getattr(ds, "SeriesDescription", "No Description")
                rel_path = os.path.relpath(os.path.dirname(filepath), self.input_folder)
                raw_date = getattr(ds, "SeriesDate", getattr(ds, "StudyDate", ""))
                date_str = self.format_dicom_date(raw_date)
                if uid not in series_info:
                    series_info[uid] = {
                        "description": desc,
                        "files": [filepath],
                        "folder": rel_path,
                        "date": date_str
                    }
                else:
                    series_info[uid]["files"].append(filepath)
            except:
                continue

        self.root.after(0, lambda: self.update_series_list(series_info))

    def show_progress_bar(self, total):
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = total
        self.progress_bar.pack(fill=tk.X, padx=10, pady=(0, 5))

    def update_series_list(self, series_info):
        self.series_info = series_info
        self.loading_label.config(text="")
        self.progress_bar.pack_forget()
        self.update_filtered_series()

    def update_filtered_series(self):
        keyword = self.search_var.get().lower()
        self.series_listbox.delete(0, tk.END)
        self.filtered_uids = []
        for uid, info in self.series_info.items():
            desc = info["description"]
            count = len(info["files"])
            rel_path = info.get("folder", "")
            date = info.get("date", "")
            label = f"[{desc}] {count} images {date} ({rel_path})"
            if keyword in label.lower():
                self.series_listbox.insert(tk.END, label)
                self.filtered_uids.append(uid)
    def on_series_select(self, event):
        selection = self.series_listbox.curselection()
        if not selection or selection[0] >= len(self.filtered_uids):
            self.preview_canvas.delete("all")
            return
        uid = self.filtered_uids[selection[0]]
        self.current_series_uid = uid
        self.current_index = len(self.series_info[uid]["files"]) // 2
        self.show_image_by_index(uid, self.current_index)

    def on_mouse_scroll(self, event):
        if not self.current_series_uid:
            return
        files = self.series_info[self.current_series_uid]["files"]
        if event.delta < 0:
            self.current_index = min(self.current_index + 1, len(files) - 1)
        else:
            self.current_index = max(self.current_index - 1, 0)
        self.show_image_by_index(self.current_series_uid, self.current_index)

    def show_image_by_index(self, uid, index):
        files = self.series_info[uid]["files"]
        if not files or index >= len(files):
            return
        try:
            ds = pydicom.dcmread(files[index])
            if hasattr(ds, "pixel_array"):
                img = ds.pixel_array.astype(np.float32)
                img -= img.min()
                img /= img.max()
                img *= 255
                img = img.astype(np.uint8)
                im = Image.fromarray(img).resize((256, 256)).convert("L")
                self.current_image = ImageTk.PhotoImage(im)
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image)
            else:
                self.preview_canvas.delete("all")
                self.preview_canvas.create_text(128, 128, text="No image data", fill="white")
        except Exception as e:
            print("Image preview failed:", e)
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(128, 128, text="Preview failed", fill="white")

    def format_dicom_date(self, date_str):
        if not date_str or len(date_str) != 8:
            return "Unknown date"
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    def copy_selected_series(self):
        selected_indices = self.series_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select at least one series to copy.")
            return

        selected_uids = [self.filtered_uids[i] for i in selected_indices]

        name_win = tk.Toplevel(self.root)
        name_win.title("Select Folder Naming Mode")
        name_win.geometry("400x200")
        name_win.grab_set()

        naming_mode = tk.StringVar(value=self.last_naming_mode)
        prefix_var = tk.StringVar(value=self.last_prefix)
        custom_name_var = tk.StringVar(value=self.last_custom_name)

        tk.Label(name_win, text="Select folder naming mode:", anchor="w").pack(fill=tk.X, pady=5, padx=10)
        tk.Radiobutton(name_win, text="Original Description", variable=naming_mode, value="original").pack(anchor="w", padx=20)
        tk.Radiobutton(name_win, text="Custom Name (shared by all)", variable=naming_mode, value="custom").pack(anchor="w", padx=20)
        tk.Entry(name_win, textvariable=custom_name_var).pack(fill=tk.X, padx=40)
        tk.Radiobutton(name_win, text="Prefix + Original Description", variable=naming_mode, value="prefix").pack(anchor="w", padx=20)
        tk.Entry(name_win, textvariable=prefix_var).pack(fill=tk.X, padx=40)

        def start_copy():
            name_win.destroy()
            self._do_copy_series(selected_uids, naming_mode.get(), prefix_var.get(), custom_name_var.get())

        tk.Button(name_win, text="Start Copy", command=start_copy).pack(pady=10)
    def _do_copy_series(self, selected_uids, naming_mode, prefix, custom_name):
        out_folder = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=self.last_output_folder if self.last_output_folder else self.input_folder
        )
        if not out_folder:
            return
        self.last_output_folder = out_folder
        self.last_naming_mode = naming_mode
        self.last_custom_name = custom_name
        self.last_prefix = prefix

        for uid in selected_uids:
            info = self.series_info[uid]
            desc = info["description"]

            if naming_mode == "original":
                folder_name = desc
            elif naming_mode == "custom":
                folder_name = custom_name
            elif naming_mode == "prefix":
                folder_name = f"{prefix}{desc}"
            else:
                folder_name = desc

            safe_folder_name = self.sanitize_filename(folder_name)

            for file_path in info["files"]:
                rel_path = os.path.relpath(file_path, start=self.input_folder)
                rel_dir = os.path.dirname(rel_path)
                filename = os.path.basename(file_path)

                target_dir = os.path.join(out_folder, rel_dir, safe_folder_name)
                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, filename)
                shutil.copy2(file_path, target_path)

        messagebox.showinfo("Done", "Selected series successfully copied.")

    def sanitize_filename(self, name):
        name = name.strip()
        name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name)
        return name if name else "Unnamed"

# Entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = DICOMSeriesCopierApp(root)
    root.mainloop()
