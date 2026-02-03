"""
Integrated Intraday Stock Analysis Suite

"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import csv
import os
from threading import Thread

DEFAULT_CSV = "stock_universe.csv"
MAX_DAYS_1M = 8  # Yahoo Finance limit for 1-minute data


class StockUniverse:
    """Manages stock symbols via CSV file"""
    
    def __init__(self, csv_path=DEFAULT_CSV):
        self.csv_path = csv_path
        if not os.path.exists(csv_path):
            self.save_symbols(["AAPL", "MSFT", "GOOGL", "TSLA"])

    def load_symbols(self):
        try:
            with open(self.csv_path, "r") as f:
                return [row[0].strip().upper() for row in csv.reader(f) if row and row[0].strip()]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load symbols: {str(e)}")
            return []

    def save_symbols(self, symbols):
        try:
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                for s in sorted(set(symbols)):
                    if s.strip():
                        writer.writerow([s.strip().upper()])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save symbols: {str(e)}")


class StockAnalysisApp:
    """Main application window"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Intraday Stock Analysis Suite")
        self.root.geometry("1400x800")
        self.root.configure(bg="#f8fafc")

        # Notebook / tab tracking for cross-tab toolbar actions
        self.notebook = None
        self.tabs = []

        self.universe = StockUniverse()
 
        self.interval_var = tk.StringVar(value="1m")
        self.duration_var = tk.IntVar(value=1)
        self.setup_styles()
        self.create_header()
        self.create_toolbar()
        self.create_tabs()

    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Progress bar styles
        style.configure(
            "Normal.Horizontal.TProgressbar",
            troughcolor="#e5e7eb",
            background="#3b82f6",
        )
        style.configure(
            "Success.Horizontal.TProgressbar",
            troughcolor="#e5e7eb",
            background="#22c55e",
        )
        
        # Treeview styling
        style.configure("Treeview",
                       background="#ffffff",
                       foreground="#1e293b",
                       rowheight=28,
                       fieldbackground="#ffffff",
                       borderwidth=0)
        style.map('Treeview', background=[('selected', '#3b82f6')])
        style.configure("Treeview.Heading",
                       background="#e2e8f0",
                       foreground="#1e293b",
                       relief="flat",
                       font=('Helvetica', 10, 'bold'))
        
        # Notebook styling
        style.configure('TNotebook', background='#f8fafc', borderwidth=0)
        style.configure('TNotebook.Tab', padding=[20, 10], font=('Helvetica', 10))

    def create_header(self):
        """Create application header"""
        header = tk.Frame(self.root, bg="#0f172a", pady=20)
        header.pack(fill=tk.X)
        
        tk.Label(header,
                text="📈 Intraday Stock Analysis Suite",
                font=("Helvetica", 22, "bold"),
                bg="#0f172a",
                fg="#f1f5f9").pack()
        
        tk.Label(header,
                text="Multi-strategy intraday scanners and analyzers",
                font=("Helvetica", 10),
                bg="#0f172a",
                fg="#94a3b8").pack()

    def create_toolbar(self):
        """Create toolbar with CSV management"""
        toolbar = tk.Frame(self.root, bg="#e2e8f0", pady=10)
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        btn_frame_left = tk.Frame(toolbar, bg="#e2e8f0")
        btn_frame_left.pack(side=tk.LEFT)
        
        buttons = [
            ("📁 Upload CSV", self.upload_csv, "#3b82f6"),
            ("➕ Add Symbol", self.add_symbol, "#10b981"),
            ("✏️ Edit Symbols", self.edit_symbols, "#f59e0b"),
            ("💾 Save CSV", lambda: messagebox.showinfo("Info", f"Symbols saved to {self.universe.csv_path}"), "#6366f1"),
        ]
        
        for text, command, color in buttons:
            tk.Button(btn_frame_left,
                     text=text,
                     command=command,
                     bg=color,
                     fg="white",
                     font=("Helvetica", 9, "bold"),
                     relief="flat",
                     padx=15,
                     pady=8,
                     cursor="hand2").pack(side=tk.LEFT, padx=5)

        # Symbol controls shared from toolbar (target Early Session tab when active)
        btn_frame_right = tk.Frame(toolbar, bg="#e2e8f0")
        btn_frame_right.pack(side=tk.LEFT, padx=(20, 0))

        tk.Button(
            btn_frame_right,
            text="Load Default Symbols",
            command=self.toolbar_load_default_symbols,
            bg="#6366f1",
            fg="white",
            font=("Helvetica", 9, "bold"),
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame_right,
            text="Clear Symbols",
            command=self.toolbar_clear_symbols,
            bg="#ef4444",
            fg="white",
            font=("Helvetica", 9, "bold"),
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame_right,
            text="Select Symbols from CSV",
            command=self.toolbar_open_symbol_selector,
            bg="#3b82f6",
            fg="white",
            font=("Helvetica", 9, "bold"),
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=5)
            
        # --- NEW: Global interval & duration controls ---
        control_frame = tk.Frame(toolbar, bg="#e2e8f0")
        control_frame.pack(side=tk.RIGHT, padx=10)

        # Interval input (user can type custom value)
        tk.Label(control_frame, text="Interval:", bg="#e2e8f0").pack(side=tk.LEFT, padx=(5,2))
        tk.Entry(control_frame, textvariable=self.interval_var, width=8).pack(side=tk.LEFT, padx=5)

        # Duration (days) spinbox — used as period like 'Nd' for intraday
        tk.Label(control_frame, text="Days:", bg="#e2e8f0").pack(side=tk.LEFT, padx=(10,2))
        tk.Spinbox(control_frame, from_=1, to=MAX_DAYS_1M, width=4, textvariable=self.duration_var).pack(side=tk.LEFT, padx=5)

        # Help button
        tk.Button(control_frame, text="❓ Help", command=self.show_help, bg="#64748b", fg="white",
                  font=("Helvetica", 9), relief="flat", padx=8, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=(12,0))


    def create_tabs(self):
        """Create analysis tabs"""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.notebook = notebook
        self.tabs = []
        
        tabs = [
            (SwingCounterTab, "🔄 Swing Counter"),
            (DownFromHighTab, "📉 n% Down From High"),
            (EarlySessionTab, "⏰ Early-Session Performance"),
            (ReversalCycleTab, "🔁 n% Reversal Cycles")
        ]
        
        for TabClass, label in tabs:
            tab = TabClass(notebook, self.universe, self)
            self.tabs.append(tab)
            notebook.add(tab.frame, text=label)

    def get_current_tab(self):
        """Return the currently selected tab instance, if any."""
        if self.notebook is None:
            return None
        current_id = self.notebook.select()
        for tab in self.tabs:
            if str(tab.frame) == current_id:
                return tab
        return None

    # Toolbar symbol control delegates (primarily for EarlySessionTab)
    def toolbar_load_default_symbols(self):
        tab = self.get_current_tab()
        try:
            from_types = (EarlySessionTab,)
        except NameError:
            from_types = ()
        if tab is not None and isinstance(tab, from_types):
            tab._load_default_symbols()

    def toolbar_clear_symbols(self):
        tab = self.get_current_tab()
        try:
            from_types = (EarlySessionTab,)
        except NameError:
            from_types = ()
        if tab is not None and isinstance(tab, from_types):
            tab._clear_active_symbols()

    def toolbar_open_symbol_selector(self):
        tab = self.get_current_tab()
        try:
            from_types = (EarlySessionTab,)
        except NameError:
            from_types = ()
        if tab is not None and isinstance(tab, from_types):
            tab._open_symbol_selector()

    def upload_csv(self):
        """Upload CSV file with stock symbols"""
        file_path = filedialog.askopenfilename(
            title="Select Stock Universe CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    symbols = [row[0].strip().upper() for row in csv.reader(f) if row and row[0].strip()]
                self.universe.save_symbols(symbols)
                messagebox.showinfo("Success", f"Loaded {len(symbols)} symbols from {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV: {str(e)}")

    def add_symbol(self):
        """Add a new symbol"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Symbol")
        dialog.geometry("300x120")
        dialog.configure(bg="#f8fafc")
        
        tk.Label(dialog, text="Enter Symbol:", bg="#f8fafc", font=("Helvetica", 10)).pack(pady=10)
        entry = tk.Entry(dialog, font=("Helvetica", 11), width=20)
        entry.pack(pady=5)
        entry.focus()
        
        def save():
            symbol = entry.get().strip().upper()
            if symbol:
                symbols = self.universe.load_symbols()
                symbols.append(symbol)
                self.universe.save_symbols(symbols)
                messagebox.showinfo("Success", f"Added {symbol}")
                dialog.destroy()
        
        tk.Button(dialog, text="Add", command=save, bg="#10b981", fg="white", 
                 font=("Helvetica", 10, "bold"), padx=20, pady=5).pack(pady=10)

    def edit_symbols(self):
        """Edit symbol list"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Symbols")
        dialog.geometry("400x500")
        dialog.configure(bg="#f8fafc")
        
        tk.Label(dialog, text="Stock Symbols (one per line):", 
                bg="#f8fafc", font=("Helvetica", 11, "bold")).pack(pady=10)
        
        text = tk.Text(dialog, font=("Courier", 10), width=30, height=20)
        text.pack(padx=20, pady=5, fill=tk.BOTH, expand=True)
        
        symbols = self.universe.load_symbols()
        text.insert("1.0", "\n".join(symbols))
        
        def save():
            content = text.get("1.0", tk.END)
            new_symbols = [s.strip().upper() for s in content.split("\n") if s.strip()]
            self.universe.save_symbols(new_symbols)
            messagebox.showinfo("Success", f"Updated {len(new_symbols)} symbols")
            dialog.destroy()
        
        tk.Button(dialog, text="Save Changes", command=save, bg="#3b82f6", 
                 fg="white", font=("Helvetica", 10, "bold"), padx=20, pady=8).pack(pady=10)
        

    def show_help(self):
        """Show help dialog describing each tab and the controls"""
        help_win = tk.Toplevel(self.root)
        help_win.title("Help — Intraday Stock Analysis Suite")
        help_win.geometry("750x650")
        help_win.configure(bg="#f8fafc")

        text = tk.Text(help_win, wrap="word", font=("Helvetica", 10), bg="#ffffff", 
                      padx=15, pady=15, relief="flat", bd=0)
        text.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Configure text tags for markdown styling
        text.tag_configure("heading2", font=("Helvetica", 14, "bold"), foreground="#0f172a", 
                          spacing3=10, spacing1=8)
        text.tag_configure("heading3", font=("Helvetica", 12, "bold"), foreground="#1e293b", 
                          spacing3=8, spacing1=6)
        text.tag_configure("bold", font=("Helvetica", 10, "bold"), foreground="#1e293b")
        text.tag_configure("code", font=("Courier", 9), foreground="#dc2626", 
                          background="#fee2e2")
        text.tag_configure("note", foreground="#7c3aed", font=("Helvetica", 10, "italic"), 
                          lmargin1=20, lmargin2=20, rmargin=20)
        text.tag_configure("bullet", lmargin1=20, lmargin2=35)
        text.tag_configure("separator", foreground="#cbd5e1", font=("Helvetica", 8))

        help_content = """
---

## 🛠️ Global Controls

* **Interval:** Choose your data granularity (e.g., **1m, 5m, 15m**). Note that smaller intervals have stricter historical limits.
* **Days:** Set the lookback period (e.g., `5d`).
> **Note:** 1-minute data is restricted to a maximum of `MAX_DAYS_1M` by the provider.

### 📊 Toolbar Controls

* **Upload CSV / Add Symbol / Edit Symbols / Save CSV:** Manage your stock universe CSV file.
* **Load Default Symbols:** Loads all symbols from the default CSV into the active symbol list (Early Session tab only).
* **Clear Symbols:** Clears the active symbol list without modifying the CSV file (Early Session tab only).
* **Select Symbols from CSV:** Opens a checkbox dialog to select symbols from your CSV universe (Early Session tab only).

### 🔽 Expand/Collapse Results

* Click the **Symbol column** (first column) on any row showing `[+] SYMBOL` to expand and view detailed daily breakdowns.
* Click again on `[−] SYMBOL` to collapse and hide the details.
* **No data refetching:** Expanding/collapsing uses cached data only, making it instant.

---

## 📑 Analysis Tabs

### 🔄 Swing Counter

Tracks intraday price swings based on your custom **Swing %**. It identifies moves that deviate from the last reference point by your specified threshold using the selected interval.

* Results show parent rows with summary statistics and expandable child rows for daily breakdowns.

### 📉 n% Down From High

A real-time "dip" scanner. Filters for symbols currently trading at least **n% below** their daily high. Perfect for spotting intraday pullbacks.

* Results show parent rows with average metrics and expandable child rows for daily occurrences.

### ⏰ Early-Session Performance

Analyzes the opening cross period and tracks performance from the start value through the close.

**Key Features:**

* **Date Range Selection:** Choose Start Date and End Date (YYYY-MM-DD format). Dates automatically exclude weekends and market holidays.
* **Preset Buttons:** Use **1D, 3D, 5D, 1W** to quickly set date ranges backward from the current trading day. These buttons update the date fields automatically.
* **View Modes:**
  * **Detailed:** Shows parent summary rows with expandable child rows for each trading session. Click `[+]` to see daily breakdowns.
  * **Average:** Shows aggregated statistics per symbol (average % gain, average prices) without daily details.
* **Symbol Selection:** 
  * Enter symbols manually (comma-separated) in the Symbols field.
  * Use toolbar buttons to load from CSV, clear the list, or select via checkbox dialog.
  * If no symbols are entered, the analysis uses all symbols from the default CSV.

**Analysis Logic:**

* **Opening Cross:** Calculates the percentage change between the price at **09:30** and **09:40** (first available candles).
* **Start Value:** Price at exactly **09:40** (or nearest forward candle).
* **Close Value:** Last closing price of the trading session.
* **% Gain:** Percentage change from Start Value to Close Value.
* **Remarks:** Shows LOW/HIGH prices with timestamps in detailed mode, or summary LOW/HIGH in collapsed view.

### 🔁 n% Reversal Cycles

Identifies "ping-pong" price action. Detects completed cycles where the price moves up by **n%** and then fully reverses by **n%** (or vice versa).

* Results show parent rows with total cycles and expandable child rows for daily cycle counts.

---

## 💡 Pro Tips

* **Avoid Data Gaps:** If you need a longer history, switch to **5m** or **15m** intervals to bypass 1-minute limitations.
* **Blank Results?** Not all tickers support sub-minute data. If a chart is empty, the ticker likely doesn't provide data for that specific interval.
* **Stay Within Limits:** Keep the **Days** setting low when using the **1m** interval to prevent fetch errors.
* **View Mode Switching:** In Early Session tab, switching between Detailed and Average modes is instant—no data refetching required.
* **Progress Bar:** The progress bar turns green when analysis completes successfully, then resets automatically.

---
"""
        
        # Parse and insert content with markdown formatting
        lines = help_content.split('\n')
        for line in lines:
            if line.startswith('---'):
                text.insert(tk.END, '─' * 50 + '\n', 'separator')
            elif line.startswith('## '):
                text.insert(tk.END, line[3:] + '\n', 'heading2')
            elif line.startswith('### '):
                text.insert(tk.END, line[4:] + '\n', 'heading3')
            elif line.startswith('> '):
                # Process note with bold and code formatting
                note_text = line[2:]
                self._insert_formatted_line(text, note_text, 'note')
                text.insert(tk.END, '\n')
            elif line.startswith('* '):
                # Process bullet points with bold and code formatting
                bullet_text = line[2:]
                text.insert(tk.END, '• ', 'bullet')
                self._insert_formatted_line(text, bullet_text, 'bullet')
                text.insert(tk.END, '\n')
            else:
                # Regular text with possible formatting
                self._insert_formatted_line(text, line, None)
                text.insert(tk.END, '\n')
        
        text.config(state=tk.DISABLED)

        tk.Button(help_win, text="Close", command=help_win.destroy, bg="#3b82f6", fg="white",
                  font=("Helvetica", 10, "bold"), padx=12, pady=8).pack(pady=8)
    
    def _insert_formatted_line(self, text_widget, line, base_tag):
        """Insert a line of text with markdown formatting (bold, italic, code)"""
        import re
        
        # Pattern for **bold**
        bold_pattern = r'\*\*([^*]+)\*\*'
        # Pattern for `code`
        code_pattern = r'`([^`]+)`'
        
        # Find all matches with their positions
        matches = []
        for match in re.finditer(bold_pattern, line):
            matches.append((match.start(), match.end(), 'bold', match.group(1)))
        for match in re.finditer(code_pattern, line):
            matches.append((match.start(), match.end(), 'code', match.group(1)))
        

        matches.sort(key=lambda x: x[0])
        
        last_pos = 0
        for start, end, tag_type, content in matches:
            if start > last_pos:
                text_widget.insert(tk.END, line[last_pos:start], base_tag)

            text_widget.insert(tk.END, content, tag_type)
            last_pos = end
        

        if last_pos < len(line):
            text_widget.insert(tk.END, line[last_pos:], base_tag)
        
class BaseTab:
    """Base class for analysis tabs with common UI elements"""
    
    def __init__(self, notebook, universe, app):
        self.app = app
        self.universe = universe
        self.frame = tk.Frame(notebook, bg="#f8fafc")
        self.is_running = False
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_label = None
        self.progress_bar = None
        # Collapsible tree support (per-tab)
        self.collapsible_tree = None
        self.tree_parent_children = {}
        self.tree_parent_symbol = {}
        self.tree_expanded = set()

    def create_control_frame(self, title):
        """Create control panel"""
        frame = tk.LabelFrame(self.frame,
                             text=title,
                             bg="#ffffff",
                             fg="#1e293b",
                             font=("Helvetica", 11, "bold"),
                             padx=20,
                             pady=15)
        frame.pack(fill=tk.X, padx=15, pady=15)
        return frame

    def create_progress_bar(self):
        """Create progress bar frame and return it"""
        progress_frame = tk.Frame(self.frame, bg="#f8fafc")
        progress_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Progress label
        self.progress_label = tk.Label(progress_frame, 
                                       text="Ready",
                                       bg="#f8fafc",
                                       fg="#1e293b",
                                       font=("Helvetica", 9))
        self.progress_label.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame,
                                            variable=self.progress_var,
                                            maximum=100,
                                            length=300,
                                            mode='determinate',
                                            style="Normal.Horizontal.TProgressbar")
        self.progress_bar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        return progress_frame

    def update_progress(self, current, total):
        """Update progress bar and label"""
        if total > 0:
            progress_value = (current / total) * 100
            self.progress_var.set(progress_value)
            self.progress_label.config(text=f"Processing: {current}/{total}")
            self.frame.update_idletasks()

    def reset_progress(self):
        """Reset progress bar"""
        self.progress_var.set(0)
        self.progress_label.config(text="Ready")
        if self.progress_bar is not None:
            self.progress_bar.config(style="Normal.Horizontal.TProgressbar")

    def mark_completed(self, total):
        """Mark progress as completed and briefly show success state"""
        if total > 0:
            self.update_progress(total, total)
        if self.progress_bar is not None:
            self.progress_bar.config(style="Success.Horizontal.TProgressbar")
        if self.progress_label is not None and total > 0:
            self.progress_label.config(text=f"Completed: {total}/{total}")
        self.frame.update_idletasks()
        # Reset after short delay to keep UI responsive but clean
        self.frame.after(700, self.reset_progress)

    def create_treeview(self, columns, collapsible=False):
        """Create results treeview with optional collapsible support"""
        tree_frame = tk.Frame(self.frame, bg="#f8fafc")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor=tk.CENTER, width=150)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        if collapsible:
            # Initialize mapping for this tab/tree
            self.collapsible_tree = tree
            self.tree_parent_children = {}
            self.tree_parent_symbol = {}
            self.tree_expanded = set()
            tree.bind("<Button-1>", self._on_tree_click)

        return tree

    def add_colored_row(self, tree, values, threshold_col=None, threshold_val=0, reverse=False):
        """Add row with color coding"""
        item = tree.insert("", tk.END, values=values)
        
        if threshold_col is not None and len(values) > threshold_col:
            try:
                val = float(str(values[threshold_col]).rstrip('%'))
                if reverse:
                    color = '#fee2e2' if val > threshold_val else '#dcfce7' if val < -threshold_val else '#fef3c7'
                else:
                    color = '#dcfce7' if val > threshold_val else '#fee2e2' if val < -threshold_val else '#fef3c7'
                tree.item(item, tags=(color,))
                tree.tag_configure(color, background=color)
            except ValueError:
                pass
        
        return item

    def add_parent_row(self, tree, values, threshold_col=None, threshold_val=0, reverse=False):
        """Add a parent row for collapsible tree"""
        # Prefix first column with [+] indicator for collapsed rows when using collapsible tree
        display_values = list(values)
        if tree is self.collapsible_tree and display_values:
            raw_symbol = str(display_values[0])
            display_values[0] = f"[+] {raw_symbol}"
        item = tree.insert("", tk.END, values=tuple(display_values), open=False)
        if tree is self.collapsible_tree:
            # Track parent symbol text and initialize children list
            self.tree_parent_symbol[item] = str(values[0])
            self.tree_parent_children.setdefault(item, [])
        
        if threshold_col is not None and len(values) > threshold_col:
            try:
                val = float(str(values[threshold_col]).rstrip('%'))
                if reverse:
                    color = '#fee2e2' if val > threshold_val else '#dcfce7' if val < -threshold_val else '#fef3c7'
                else:
                    color = '#dcfce7' if val > threshold_val else '#fee2e2' if val < -threshold_val else '#fef3c7'
                tree.item(item, tags=(color,))
                tree.tag_configure(color, background=color)
            except ValueError:
                pass
        
        return item

    def add_child_row(self, tree, parent, values):
        """Add a child row to a parent"""
        item = tree.insert(parent, tk.END, values=values)
        if tree is self.collapsible_tree:
            self.tree_parent_children.setdefault(parent, []).append(item)
        return item

    def _on_tree_click(self, event):
        """Handle click on treeview to toggle expand/collapse via [+]/[-]."""
        if self.collapsible_tree is None:
            return
        tree = self.collapsible_tree
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        # Only toggle when clicking the first (symbol) column on a parent row
        if not item or column != "#1" or item not in self.tree_parent_children:
            return
        self._toggle_parent_row(tree, item)

    def _toggle_parent_row(self, tree, parent):
        """Toggle a single parent row's expanded/collapsed state without refetching data."""
        children = self.tree_parent_children.get(parent, [])
        if not children:
            return

        values = list(tree.item(parent, "values"))
        # Recover raw symbol from stored mapping
        raw_symbol = self.tree_parent_symbol.get(parent, str(values[0]))

        if parent in self.tree_expanded:
            # Collapse: detach children and show [+]
            for child in children:
                tree.detach(child)
            self.tree_expanded.remove(parent)
            if values:
                values[0] = f"[+] {raw_symbol}"
            tree.item(parent, values=tuple(values))
        else:
            # Expand: reattach children directly below parent and show [−]
            index = list(tree.get_children("")).index(parent)
            for offset, child in enumerate(children, start=1):
                tree.reattach(child, "", index + offset)
            self.tree_expanded.add(parent)
            if values:
                values[0] = f"[−] {raw_symbol}"
            tree.item(parent, values=tuple(values))


class SwingCounterTab(BaseTab):
    """Tab 1: Daily Stock Swing Counter"""
    
    def __init__(self, notebook, universe, app):
        super().__init__(notebook, universe, app)
        self.swing_pct = tk.DoubleVar(value=5.0)
        self.build_ui()

    def build_ui(self):
        controls = self.create_control_frame("Swing Analysis Settings")
        
        tk.Label(controls, text="Swing %:", bg="#ffffff", font=("Helvetica", 10)).grid(row=0, column=0, padx=5)
        tk.Entry(controls, textvariable=self.swing_pct, width=10, font=("Helvetica", 10)).grid(row=0, column=1, padx=5)
        
        tk.Button(controls, text="▶ Run Analysis", bg="#3b82f6", fg="white",
                 font=("Helvetica", 10, "bold"), command=self.run, padx=20, pady=8,
                 relief="flat", cursor="hand2").grid(row=0, column=2, padx=15)
        
        self.create_progress_bar()
        
        self.tree = self.create_treeview(("Symbol", "Up Swings", "Down Swings", "Total Swings", "Avg Daily"), collapsible=True)

    def run(self):
        self.tree.delete(*self.tree.get_children())
        symbols = self.universe.load_symbols()
        total_symbols = len(symbols)
        
        for idx, sym in enumerate(symbols):
            self.update_progress(idx, total_symbols)
            try:
                interval = self.app.interval_var.get().strip()
                days = max(1, int(self.app.duration_var.get()))
                period = f"{days}d"
                data = yf.Ticker(sym).history(period=period, interval=interval)

                if data.empty:
                    continue

                # Group by date to track daily swings
                data["date"] = data.index.date
                daily_swings = []
                
                for date, day_data in data.groupby("date"):
                    prices = day_data["Close"].values
                    if len(prices) < 2:
                        continue
                    
                    up = down = 0
                    ref = prices[0]
                    
                    for p in prices[1:]:
                        pct_change = (p - ref) / ref * 100
                        if pct_change >= self.swing_pct.get():
                            up += 1
                            ref = p
                        elif pct_change <= -self.swing_pct.get():
                            down += 1
                            ref = p
                    
                    daily_swings.append((date, up, down, up + down))
                
                if not daily_swings:
                    continue
                
                # Calculate summary
                total_up = sum(x[1] for x in daily_swings)
                total_down = sum(x[2] for x in daily_swings)
                total_all = sum(x[3] for x in daily_swings)
                avg_daily = total_all / len(daily_swings) if daily_swings else 0
                
                # Add parent row with summary
                parent = self.add_parent_row(self.tree, 
                                            (sym, total_up, total_down, total_all, f"{avg_daily:.2f}"),
                                            3, 5)
                
                # Add child rows with daily data
                for date, up, down, total in daily_swings:
                    self.add_child_row(self.tree, parent, (f"  {date}", up, down, total, ""))
                
            except Exception as e:
                print(f"Error processing {sym}: {str(e)}")
        
        self.mark_completed(total_symbols)


class DownFromHighTab(BaseTab):
    """Tab 2: n% Down From Day's High Scanner"""
    
    def __init__(self, notebook, universe, app):
        super().__init__(notebook, universe, app)
        self.n_pct = tk.DoubleVar(value=3.0)
        self.build_ui()

    def build_ui(self):
        controls = self.create_control_frame("Scanner Settings")
        
        tk.Label(controls, text="% Down From High:", bg="#ffffff", font=("Helvetica", 10)).grid(row=0, column=0, padx=5)
        tk.Entry(controls, textvariable=self.n_pct, width=10, font=("Helvetica", 10)).grid(row=0, column=1, padx=5)
        
        tk.Button(controls, text="🔍 Scan Now", bg="#10b981", fg="white",
                 font=("Helvetica", 10, "bold"), command=self.run, padx=20, pady=8,
                 relief="flat", cursor="hand2").grid(row=0, column=2, padx=15)
        
        self.create_progress_bar()
        
        self.tree = self.create_treeview(("Symbol", "Current Price", "Day High", "% Down", "Avg %"), collapsible=True)

    def run(self):
        self.tree.delete(*self.tree.get_children())
        symbols = self.universe.load_symbols()
        threshold = self.n_pct.get()
        total_symbols = len(symbols)
        
        for idx, sym in enumerate(symbols):
            self.update_progress(idx, total_symbols)
            try:
                interval = self.app.interval_var.get().strip()
                days = max(1, int(self.app.duration_var.get()))
                period = f"{days}d"
                df = yf.Ticker(sym).history(period=period, interval=interval)
                if df.empty:
                    continue

                # Group by date to track daily data
                df["date"] = df.index.date
                daily_data = []
                
                for date, day_data in df.groupby("date"):
                    
                    if len(day_data) <= 10:
                        continue
                    day_after_10 = day_data.iloc[11:]
                    high = day_after_10["High"].max()
                    current = day_data["Close"].iloc[-1]
                    drop = (high - current) / high * 100
                    daily_data.append((date, current, high, drop))
                
                if not daily_data:
                    continue
                
                # Filter by threshold and calculate averages
                filtered_data = [d for d in daily_data if d[3] >= threshold]
                if not filtered_data:
                    continue
                
                avg_drop = sum(d[3] for d in filtered_data) / len(filtered_data)
                avg_high = sum(d[2] for d in filtered_data) / len(filtered_data)
                avg_current = sum(d[1] for d in filtered_data) / len(filtered_data)
                
                # Add parent row with summary
                parent = self.add_parent_row(self.tree, 
                                            (sym, f"${avg_current:.2f}", f"${avg_high:.2f}", f"{avg_drop:.2f}%", f"{avg_drop:.2f}%"),
                                            3, threshold, reverse=True)
                
                # Add child rows with daily data
                for date, current, high, drop in filtered_data:
                    self.add_child_row(self.tree, parent, (f"  {date}", f"${current:.2f}", f"${high:.2f}", f"{drop:.2f}%", ""))
                
            except Exception as e:
                print(f"Error processing {sym}: {str(e)}")
        
        self.mark_completed(total_symbols)


class EarlySessionTab(BaseTab):
    """Tab 3: Early Session Performance Analyzer"""
    
    def __init__(self, notebook, universe, app):
        super().__init__(notebook, universe, app)
        # Date range selection state
        self.start_date_var = tk.StringVar()
        self.end_date_var = tk.StringVar()
        # View mode state: Detailed vs Average
        self.view_mode_var = tk.StringVar(value="Detailed")
        # Manual symbol selection (comma-separated)
        self.manual_symbols_var = tk.StringVar()
        # Cached analysis results {symbol: [record dicts]}
        self.analysis_cache = {}
        self._init_default_dates()
        self.build_ui()

    def build_ui(self):
        controls = self.create_control_frame("Early Session Performance (Opening Cross vs Close)")

        # View mode toggle
        mode_frame = tk.Frame(controls, bg="#ffffff")
        mode_frame.grid(row=0, column=0, columnspan=5, padx=5, pady=(0, 4), sticky="w")
        tk.Label(mode_frame, text="View:", bg="#ffffff", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=(0, 4))
        tk.Radiobutton(
            mode_frame,
            text="Detailed",
            variable=self.view_mode_var,
            value="Detailed",
            bg="#ffffff",
            font=("Helvetica", 9),
            command=self._on_view_mode_change,
        ).pack(side=tk.LEFT, padx=(0, 4))
        tk.Radiobutton(
            mode_frame,
            text="Average",
            variable=self.view_mode_var,
            value="Average",
            bg="#ffffff",
            font=("Helvetica", 9),
            command=self._on_view_mode_change,
        ).pack(side=tk.LEFT, padx=(0, 4))

        # Date range inputs (replace numeric Days to Analyze)
        tk.Label(controls, text="Start Date (YYYY-MM-DD):", bg="#ffffff", font=("Helvetica", 10)).grid(row=1, column=0, padx=5, pady=2, sticky="w")
        tk.Entry(controls, textvariable=self.start_date_var, width=12, font=("Helvetica", 10)).grid(row=1, column=1, padx=5, pady=2, sticky="w")

        tk.Label(controls, text="End Date (YYYY-MM-DD):", bg="#ffffff", font=("Helvetica", 10)).grid(row=1, column=2, padx=5, pady=2, sticky="w")
        tk.Entry(controls, textvariable=self.end_date_var, width=12, font=("Helvetica", 10)).grid(row=1, column=3, padx=5, pady=2, sticky="w")

        # Predefined date buttons (1D / 3D / 5D / 1W) — update dates based on current trading day
        preset_frame = tk.Frame(controls, bg="#ffffff")
        preset_frame.grid(row=2, column=0, columnspan=4, pady=(4, 2), sticky="w")
        for label, days in [("1D", 1), ("3D", 3), ("5D", 5), ("1W", 7)]:
            tk.Button(
                preset_frame,
                text=label,
                bg="#e5e7eb",
                fg="#111827",
                font=("Helvetica", 9),
                relief="flat",
                padx=8,
                pady=3,
                cursor="hand2",
                command=lambda d=days: self.apply_preset_days(d),
            ).pack(side=tk.LEFT, padx=3)

        tk.Button(controls, text="📊 Analyze", bg="#3b82f6", fg="white",
                 font=("Helvetica", 10, "bold"), command=self.run, padx=20, pady=8,
                 relief="flat", cursor="hand2").grid(row=1, column=4, padx=15, pady=2, sticky="w")

        # Symbol selection controls
        symbol_frame = tk.Frame(controls, bg="#ffffff")
        symbol_frame.grid(row=3, column=0, columnspan=5, pady=(6, 2), sticky="we")
        symbol_frame.columnconfigure(1, weight=1)

        tk.Label(symbol_frame, text="Symbols (comma separated):", bg="#ffffff", font=("Helvetica", 10)).grid(row=0, column=0, padx=5, sticky="w")
        tk.Entry(symbol_frame, textvariable=self.manual_symbols_var, width=50, font=("Helvetica", 10)).grid(
            row=0, column=1, padx=5, pady=2, sticky="we"
        )
        
        self.create_progress_bar()
        
        self.tree = self.create_treeview(("Symbol", "Date", "Opening Cross", "Start Value", "Close Value", "% Gain", "Remarks"), collapsible=True)

    def run(self):
        """Analyze early-session performance over a date range with business-day handling."""
        symbols = self._get_active_symbols()
        if not symbols:
            # Preserve existing behavior if the user hasn't defined an active list
            symbols = self.universe.load_symbols()

        # Parse and validate dates
        try:
            start_date = datetime.strptime(self.start_date_var.get().strip(), "%Y-%m-%d").date()
            end_date = datetime.strptime(self.end_date_var.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Invalid Dates", "Please enter valid Start and End dates in YYYY-MM-DD format.")
            return

        if start_date >= end_date:
            messagebox.showerror("Invalid Range", "Start Date must be earlier than End Date.")
            return

        # Build trading calendar: business days only (skip weekends & common holidays)
        trading_range = pd.bdate_range(start=start_date, end=end_date)
        if trading_range.empty:
            messagebox.showerror("No Trading Days", "The selected date range contains no valid trading days.")
            return

        # Respect Yahoo 1-minute history limits if using 1m interval
        interval = self.app.interval_var.get().strip()
        trading_days = [d.date() for d in trading_range]
        if interval == "1m" and len(trading_days) > MAX_DAYS_1M:
            trading_days = trading_days[-MAX_DAYS_1M:]
            messagebox.showwarning(
                "Limit Applied",
                f"Yahoo Finance allows max {MAX_DAYS_1M} trading days for 1-minute data. "
                f"Using the most recent {MAX_DAYS_1M} days in the selected range.",
            )

        if not trading_days:
            messagebox.showerror("No Trading Days", "No valid trading days after applying provider limits.")
            return

        total_symbols = len(symbols)
        self.analysis_cache = {}
        self.tree.delete(*self.tree.get_children())

        for idx, sym in enumerate(symbols):
            self.update_progress(idx, total_symbols)
            try:
                df = yf.Ticker(sym).history(
                    start=trading_days[0],
                    end=trading_days[-1] + timedelta(days=1),
                    interval=interval,
                )

                if df.empty:
                    continue

                df["date"] = df.index.date
                daily_records = []

                for d, day in df.groupby("date"):
                    if len(day) < 2:
                        continue

                    # Opening cross window and start value at/after 09:40
                    times = day.index.time
                    t_0930 = datetime.strptime("09:30", "%H:%M").time()
                    t_0940 = datetime.strptime("09:40", "%H:%M").time()

                    # Price at/after 09:30 for opening cross baseline
                    oc_candidates = [i for i, t in enumerate(times) if t >= t_0930]
                    if not oc_candidates:
                        continue
                    oc_idx = oc_candidates[0]
                    oc_price = float(day.iloc[oc_idx]["Close"])

                    # Start value at/after 09:40
                    start_candidates = [i for i, t in enumerate(times) if t >= t_0940]
                    if not start_candidates:
                        continue
                    start_idx = start_candidates[0]
                    start_row = day.iloc[start_idx]
                    start_price = float(start_row["Close"])

                    # Opening cross % change between 09:30 and 09:40
                    open_pct = (start_price - oc_price) / oc_price * 100 if oc_price != 0 else 0.0

                    # Close vs start % gain
                    close_price = float(day["Close"].iloc[-1])
                    pct = (close_price - start_price) / start_price * 100 if start_price != 0 else 0.0

                    # Session low/high with timestamps
                    low_idx = day["Low"].idxmin()
                    high_idx = day["High"].idxmax()
                    low_price = float(day.loc[low_idx]["Low"])
                    high_price = float(day.loc[high_idx]["High"])
                    low_ts = low_idx.strftime("%H:%M")
                    high_ts = high_idx.strftime("%H:%M")

                    daily_records.append(
                        {
                            "date": d,
                            "start": start_price,
                            "close": close_price,
                            "pct": pct,
                            "open_pct": open_pct,
                            "low": low_price,
                            "low_ts": low_ts,
                            "high": high_price,
                            "high_ts": high_ts,
                        }
                    )

                if not daily_records:
                    continue

                self.analysis_cache[sym] = daily_records

            except Exception as e:
                print(f"Error processing {sym}: {str(e)}")

        # Render results from cache according to the current view mode
        self._render_results()
        self.mark_completed(total_symbols)

    def _init_default_dates(self):
        """Initialize start/end date fields based on the current trading day."""
        today = datetime.now().date()
        # Current trading day = last business day on or before today
        current_trading = pd.bdate_range(end=today, periods=1)[0].date()
        # Default: last 5 business days ending at current trading day
        bdays = pd.bdate_range(end=current_trading, periods=5)
        self.start_date_var.set(bdays[0].date().strftime("%Y-%m-%d"))
        self.end_date_var.set(bdays[-1].date().strftime("%Y-%m-%d"))

    def apply_preset_days(self, num_days):
        """Apply a backward-looking preset (1D/3D/5D/1W) from the current trading day.

        This updates only the Start/End date fields; it does NOT trigger analysis automatically.
        """
        today = datetime.now().date()
        # Anchor on current trading day (last business day up to today)
        current_trading = pd.bdate_range(end=today, periods=1)[0].date()
        bdays = pd.bdate_range(end=current_trading, periods=num_days)
        if bdays.empty:
            return
        self.start_date_var.set(bdays[0].date().strftime("%Y-%m-%d"))
        self.end_date_var.set(bdays[-1].date().strftime("%Y-%m-%d"))

    def _get_active_symbols(self):
        """Return the current active symbol list, deduplicated and uppercased."""
        raw = self.manual_symbols_var.get().strip()
        if not raw:
            return []
        parts = [p.strip().upper() for p in raw.split(",") if p.strip()]
        seen = set()
        ordered = []
        for p in parts:
            if p not in seen:
                seen.add(p)
                ordered.append(p)
        return ordered

    def _load_default_symbols(self):
        """Load symbols from the default CSV into the manual input (does not modify CSV)."""
        symbols = self.universe.load_symbols()
        if not symbols:
            return
        self.manual_symbols_var.set(", ".join(sorted(set(symbols))))

    def _clear_active_symbols(self):
        """Clear active symbol list without changing the CSV on disk."""
        self.manual_symbols_var.set("")

    def _open_symbol_selector(self):
        """Checkbox-based symbol selector backed by CSV, kept in sync with manual input."""
        csv_symbols = self.universe.load_symbols()
        if not csv_symbols:
            return

        current = set(self._get_active_symbols())

        win = tk.Toplevel(self.frame)
        win.title("Select Symbols from CSV")
        win.geometry("320x420")
        win.configure(bg="#f8fafc")

        container = tk.Frame(win, bg="#f8fafc")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container, bg="#f8fafc", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas, bg="#f8fafc")

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        vars_map = {}
        for sym in sorted(csv_symbols):
            var = tk.BooleanVar(value=(sym in current))
            chk = tk.Checkbutton(
                inner,
                text=sym,
                variable=var,
                bg="#f8fafc",
                anchor="w",
            )
            chk.pack(fill=tk.X, anchor="w")
            vars_map[sym] = var

        def apply_selection():
            selected = [s for s, v in vars_map.items() if v.get()]
            manual = self._get_active_symbols()
            merged = manual + selected
            seen = set()
            final = []
            for s in merged:
                if s not in seen:
                    seen.add(s)
                    final.append(s)
            self.manual_symbols_var.set(", ".join(final))
            win.destroy()

        tk.Button(
            win,
            text="Apply",
            command=apply_selection,
            bg="#3b82f6",
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=12,
            pady=6,
        ).pack(pady=(4, 10))

    def _on_view_mode_change(self):
        """Re-render from cache when switching Detailed/Average modes without refetching data."""
        self._render_results()

    def _render_results(self):
        """Render TreeView from cached analysis for Detailed/Average modes."""
        # Clear rows and reset collapse tracking
        self.tree.delete(*self.tree.get_children())
        self.tree_parent_children = {}
        self.tree_parent_symbol = {}
        self.tree_expanded = set()

        if not self.analysis_cache:
            return

        detailed = self.view_mode_var.get() == "Detailed"

        for sym, records in self.analysis_cache.items():
            if not records:
                continue

            avg_pct = sum(r["pct"] for r in records) / len(records)
            avg_open_pct = sum(r["open_pct"] for r in records) / len(records)
            avg_start = sum(r["start"] for r in records) / len(records)
            avg_close = sum(r["close"] for r in records) / len(records)

            # Collapsed remarks: show only LOW or only HIGH (no timestamps)
            min_low = min(records, key=lambda r: r["low"])
            max_high = max(records, key=lambda r: r["high"])
            if abs(min_low["low"] - avg_start) > abs(max_high["high"] - avg_start):
                collapsed_remark = f"LOW: {min_low['low']:.2f}"
            else:
                collapsed_remark = f"HIGH: {max_high['high']:.2f}"

            if detailed:
                date_label = (
                    f"{records[0]['date']} → {records[-1]['date']}"
                    if len(records) > 1
                    else str(records[0]["date"])
                )
            else:
                date_label = f"{len(records)} sessions"

            parent = self.add_parent_row(
                self.tree,
                (
                    sym,
                    date_label,
                    f"{avg_open_pct:.2f}%",
                    f"{avg_start:.2f}",
                    f"{avg_close:.2f}",
                    f"{avg_pct:.2f}%",
                    collapsed_remark,
                ),
                threshold_col=5,
                threshold_val=0,
                reverse=False,
            )

            if not detailed:
                # Average mode shows only one row per symbol
                continue

            for r in records:
                remarks = f"LOW: {r['low']:.2f} @ {r['low_ts']} | HIGH: {r['high']:.2f} @ {r['high_ts']}"
                self.add_child_row(
                    self.tree,
                    parent,
                    (
                        f"  {r['date']}",
                        str(r["date"]),
                        f"{r['open_pct']:.2f}%",
                        f"{r['start']:.2f}",
                        f"{r['close']:.2f}",
                        f"{r['pct']:.2f}%",
                        remarks,
                    ),
                )


class ReversalCycleTab(BaseTab):
    """Tab 4: n% Price Reversal Cycle Counter"""
    
    def __init__(self, notebook, universe , app):
        super().__init__(notebook, universe, app)
        self.n_pct = tk.DoubleVar(value=2.0)
        self.days = tk.IntVar(value=5)
        self.build_ui()

    def build_ui(self):
        controls = self.create_control_frame("Reversal Cycle Settings (Max 7 days)")
        
        tk.Label(controls, text="Reversal %:", bg="#ffffff", font=("Helvetica", 10)).grid(row=0, column=0, padx=5)
        tk.Entry(controls, textvariable=self.n_pct, width=8, font=("Helvetica", 10)).grid(row=0, column=1, padx=5)
        
        tk.Label(controls, text="Days:", bg="#ffffff", font=("Helvetica", 10)).grid(row=0, column=2, padx=(15, 5))
        spinbox = tk.Spinbox(controls, from_=1, to=MAX_DAYS_1M, textvariable=self.days,
                            width=8, font=("Helvetica", 10))
        spinbox.grid(row=0, column=3, padx=5)
        
        tk.Button(controls, text="🔄 Count Cycles", bg="#ef4444", fg="white",
                 font=("Helvetica", 10, "bold"), command=self.run, padx=20, pady=8,
                 relief="flat", cursor="hand2").grid(row=0, column=4, padx=15)
        
        self.create_progress_bar()
        
        self.tree = self.create_treeview(("Symbol", "Total Cycles", "Avg Cycles/Day", "Daily Breakdown"), collapsible=True)

    def run(self):
        self.tree.delete(*self.tree.get_children())
        symbols = self.universe.load_symbols()
        days = min(self.days.get(), MAX_DAYS_1M)
        total_symbols = len(symbols)
        
        if self.days.get() > MAX_DAYS_1M:
            messagebox.showwarning("Limit Exceeded",
                                  f"Yahoo Finance allows max {MAX_DAYS_1M} days for 1-minute data. Using {MAX_DAYS_1M} days.")
        
        for idx, sym in enumerate(symbols):
            self.update_progress(idx, total_symbols)
            try:
                interval = self.app.interval_var.get().strip()
                df = yf.Ticker(sym).history(period=f"{days}d", interval=interval)

                if df.empty:
                    continue

                df["date"] = df.index.date
                daily_cycles = []
                
                for date, day_df in df.groupby("date"):
                    if len(day_df) < 2:
                        continue
                    
                    cycles = 0
                    ref = day_df["Open"].iloc[0]
                    direction = None

                    for p in day_df["Close"]:
                        pct_change = (p - ref) / ref * 100
                        
                        if direction is None:
                            if pct_change >= self.n_pct.get():
                                direction = "up"
                                ref = p
                            elif pct_change <= -self.n_pct.get():
                                direction = "down"
                                ref = p
                        else:
                            if direction == "up" and pct_change <= -self.n_pct.get():
                                cycles += 1
                                direction = None
                                ref = p
                            elif direction == "down" and pct_change >= self.n_pct.get():
                                cycles += 1
                                direction = None
                                ref = p
                    
                    daily_cycles.append((date, cycles))
                
                if not daily_cycles:
                    continue
                
                # Calculate summary
                total_cycles = sum(c[1] for c in daily_cycles)
                avg_cycles = total_cycles / len(daily_cycles) if daily_cycles else 0
                
                # Add parent row with summary
                parent = self.add_parent_row(self.tree, (sym, total_cycles, f"{avg_cycles:.2f}", f"{len(daily_cycles)} days"), 1, 5)
                
                # Add child rows with daily data
                for date, cycles in daily_cycles:
                    self.add_child_row(self.tree, parent, (f"  {date}", cycles, "", ""))
                
            except Exception as e:
                print(f"Error processing {sym}: {str(e)}")
        
        self.mark_completed(total_symbols)




if __name__ == "__main__":
    root = tk.Tk()
    app = StockAnalysisApp(root)
    root.mainloop()