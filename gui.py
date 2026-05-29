#!/usr/bin/env python3
"""Desktop GUI for File Organizer using Tkinter."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import scrolledtext
import threading
import os
from pathlib import Path

# Import organizer functions
import sys
sys.path.insert(0, str(Path(__file__).parent))
from context_aware_organizer import (
    organize_directory,
    load_config,
    get_category_for_file,
)


class FileOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("File Organizer")
        self.root.geometry("700x500")
        self.root.configure(bg='#0891B2')
        
        self.config = load_config()
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='white', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title = tk.Label(main_frame, text="📁 File Organizer", 
                        font=('Helvetica', 24, 'bold'), 
                        bg='white', fg='#0891B2')
        title.pack(pady=(0, 10))
        
        subtitle = tk.Label(main_frame, text="Automatic file organization with smart protection",
                           font=('Helvetica', 11), bg='white', fg='#666')
        subtitle.pack(pady=(0, 20))
        
        # Target directories section
        dir_frame = tk.LabelFrame(main_frame, text=" Target Folders ", 
                                 font=('Helvetica', 10, 'bold'),
                                 bg='white', fg='#0891B2')
        dir_frame.pack(fill='x', pady=(0, 15), padx=5)
        
        self.dir_var = tk.StringVar()
        dir_entry = tk.Entry(dir_frame, textvariable=self.dir_var, 
                            font=('Courier', 10), width=40, relief='flat', 
                            highlightthickness=1, highlightbackground='#ccc')
        dir_entry.pack(side='left', padx=10, pady=10, fill='x', expand=True)
        
        browse_btn = tk.Button(dir_frame, text="Browse", 
                              command=self.browse_folder,
                              font=('Helvetica', 9),
                              bg='#0891B2', fg='white',
                              relief='flat', padx=15,
                              cursor='hand2')
        browse_btn.pack(side='right', padx=10, pady=10)
        
        # Options
        opt_frame = tk.Frame(main_frame, bg='white')
        opt_frame.pack(fill='x', pady=(0, 15))
        
        self.dry_run_var = tk.BooleanVar(value=True)
        self.recursive_var = tk.BooleanVar(value=False)
        
        dry_check = tk.Checkbutton(opt_frame, text="Dry Run (Preview only)",
                                 variable=self.dry_run_var,
                                 font=('Helvetica', 10), bg='white')
        dry_check.grid(row=0, column=0, padx=5, sticky='w')
        
        rec_check = tk.Checkbutton(opt_frame, text="Include subfolders",
                                 variable=self.recursive_var,
                                 font=('Helvetica', 10), bg='white')
        rec_check.grid(row=0, column=1, padx=20, sticky='w')
        
        # Action buttons
        btn_frame = tk.Frame(main_frame, bg='white')
        btn_frame.pack(fill='x', pady=(0, 15))
        
        self.organize_btn = tk.Button(btn_frame, text="Organize Now", 
                                      command=self.organize_files,
                                      font=('Helvetica', 11, 'bold'),
                                      bg='#22C55E', fg='white',
                                      relief='flat', padx=30, pady=8,
                                      cursor='hand2')
        self.organize_btn.pack(side='left', padx=5)
        
        self.clear_btn = tk.Button(btn_frame, text="Clear Log", 
                                    command=self.clear_log,
                                    font=('Helvetica', 10),
                                    bg='#f0f0f0', fg='#333',
                                    relief='flat', padx=20, pady=8,
                                    cursor='hand2')
        self.clear_btn.pack(side='right', padx=5)
        
        # Status/Log area
        log_frame = tk.LabelFrame(main_frame, text=" Status Log ",
                                  font=('Helvetica', 10, 'bold'),
                                  bg='white', fg='#0891B2')
        log_frame.pack(fill='both', expand=True, padx=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                 font=('Courier', 9),
                                                 relief='flat',
                                                 height=10,
                                                 wrap='word',
                                                 bg='#f8f9fa',
                                                 fg='#333')
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Protected files info
        info_text = tk.Label(main_frame, 
                            text="Protected: .ssh • .git • node_modules • README • LICENSE • System folders",
                            font=('Helvetica', 8), bg='white', fg='#888')
        info_text.pack(pady=(10, 0))
    
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dir_var.set(folder)
    
    def log(self, message):
        self.log_text.insert('end', message + '\n')
        self.log_text.see('end')
    
    def clear_log(self):
        self.log_text.delete('1.0', 'end')
    
    def organize_files(self):
        target_dir = self.dir_var.get() or os.path.expanduser('~/Downloads')
        
        if not Path(target_dir).exists():
            messagebox.showerror("Error", f"Directory not found: {target_dir}")
            return
        
        self.organize_btn.config(state='disabled', bg='#ccc')
        self.log(f"Starting organization of: {target_dir}")
        
        def run_org():
            org_config = {
                'dry_run': self.dry_run_var.get(),
                'recursive': self.recursive_var.get(),
                'categories': self.config['categories'],
                'important_patterns': self.config['important_patterns'],
                'hidden_exceptions': self.config['hidden_exceptions'],
            }
            try:
                organize_directory(target_dir, org_config)
                self.log("Organization complete!")
            except Exception as e:
                self.log(f"Error: {e}")
            self.organize_btn.config(state='normal', bg='#22C55E')
        
        threading.Thread(target=run_org, daemon=True).start()


if __name__ == '__main__':
    root = tk.Tk()
    app = FileOrganizerGUI(root)
    root.mainloop()