"""
Integrated Intraday Stock Analysis Suite

"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta, date
import csv
import os
from threading import Thread
import re

DEFAULT_CSV = "stock_universe.csv"
MAX_DAYS_1M = 8  # Yahoo Finance limit for 1-minute data


def is_trading_day(dt):
    """Check if a date is a trading day (Monday-Friday)"""
    return dt.weekday() < 5  # 0-4 are Monday-Friday


def get_previous_trading_day(dt):
    """Get the previous trading day"""
    prev_day = dt - timedelta(days=1)
    while not is_trading_day(prev_day):
        prev_day -= timedelta(days=1)
    return prev_day


def get_trading_days_back(days):
    """Get start and end dates for N trading days back from today"""
    end_date = date.today()
    # If today is weekend, go back to Friday
    while not is_trading_day(end_date):
        end_date -= timedelta(days=1)
    
    start_date = end_date
    trading_days_counted = 0
    
    while trading_days_counted < days - 1:
        start_date = get_previous_trading_day(start_date)
        trading_days_counted += 1
    
    return start_date, end_date


def parse_date(date_str):
    """Parse date string in YYYY-MM-DD format"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def format_date(dt):
    """Format date to YYYY-MM-DD string"""
    if isinstance(dt, date):
        return dt.strftime("%Y-%m-%d")
    return str(dt)


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
    
    def clear_symbols(self):
        """Clear all symbols from memory (does not delete CSV file)"""
        self.save_symbols([])
    
    def load_default_csv(self):
        """Load the default CSV file"""
        if os.path.exists(self.csv_path):
            return self.load_symbols()
        else:
            # Create default symbols
            default_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
            self.save_symbols(default_symbols)
            return default_symbols


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
        # Initialize active_symbols with loaded symbols
        self.active_symbols = self.universe.load_symbols()
        self.symbol_selection_mode = tk.StringVar(value="csv")  # "csv" or "manual"
 
        self.interval_var = tk.StringVar(value="1m")
        self.duration_var = tk.IntVar(value=1)
        
        # Date range variables
        today = date.today()
        self.start_date_var = tk.StringVar(value=format_date(get_previous_trading_day(today)))
        self.end_date_var = tk.StringVar(value=format_date(today))
        
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
        """Create toolbar with CSV management and controls"""
        toolbar = tk.Frame(self.root, bg="#e2e8f0", pady=10)
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        # Left side: CSV management buttons
        btn_frame = tk.Frame(toolbar, bg="#e2e8f0")
        btn_frame.pack(side=tk.LEFT)
        
        buttons = [
            ("📁 Upload CSV", self.upload_csv, "#3b82f6"),
            ("📂 Load Default CSV", self.load_default_csv, "#3b82f6"),
            ("➕ Add Symbol", self.add_symbol, "#10b981"),
            ("✏️ Edit Symbols", self.edit_symbols, "#f59e0b"),
            ("🎯 Select Stocks", self.select_stocks, "#8b5cf6"),
            ("🗑️ Clear Symbols", self.clear_symbols, "#ef4444"),
            ("💾 Save CSV", lambda: messagebox.showinfo("Info", f"Symbols saved to {self.universe.csv_path}"), "#6366f1")
        ]
        
        for text, command, color in buttons:
            tk.Button(btn_frame_left,
                     text=text,
                     command=command,
                     bg=color,
                     fg="white",
                     font=("Helvetica", 9, "bold"),
                     relief="flat",
                     padx=12,
                     pady=8,
                     cursor="hand2").pack(side=tk.LEFT, padx=3)
        
        # Right side: Controls
        control_frame = tk.Frame(toolbar, bg="#e2e8f0")
        control_frame.pack(side=tk.RIGHT, padx=10)

        # Interval input
        tk.Label(control_frame, text="Interval:", bg="#e2e8f0", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=(5,2))
        tk.Entry(control_frame, textvariable=self.interval_var, width=8, font=("Helvetica", 9)).pack(side=tk.LEFT, padx=5)

        # Date range controls
        tk.Label(control_frame, text="Start:", bg="#e2e8f0", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=(10,2))
        start_entry = tk.Entry(control_frame, textvariable=self.start_date_var, width=12, font=("Helvetica", 9))
        start_entry.pack(side=tk.LEFT, padx=2)
        start_entry.bind('<FocusOut>', lambda e: self.validate_date_range())
        
        tk.Label(control_frame, text="End:", bg="#e2e8f0", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=(5,2))
        end_entry = tk.Entry(control_frame, textvariable=self.end_date_var, width=12, font=("Helvetica", 9))
        end_entry.pack(side=tk.LEFT, padx=2)
        end_entry.bind('<FocusOut>', lambda e: self.validate_date_range())
        
        # Predefined date range buttons
        date_btn_frame = tk.Frame(control_frame, bg="#e2e8f0")
        date_btn_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        for label, days in [("1D", 1), ("3D", 3), ("5D", 5), ("1W", 5)]:
            tk.Button(date_btn_frame, text=label, command=lambda d=days: self.set_date_range(d),
                     bg="#94a3b8", fg="white", font=("Helvetica", 8, "bold"),
                     relief="flat", padx=6, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=2)

        # Help button
        tk.Button(control_frame, text="❓ Help", command=self.show_help, bg="#64748b", fg="white",
                  font=("Helvetica", 9), relief="flat", padx=8, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=(12,0))
    
    def set_date_range(self, trading_days):
        """Set date range based on number of trading days"""
        start_date, end_date = get_trading_days_back(trading_days)
        self.start_date_var.set(format_date(start_date))
        self.end_date_var.set(format_date(end_date))
    
    def validate_date_range(self):
        """Validate that start date is before end date"""
        start_str = self.start_date_var.get()
        end_str = self.end_date_var.get()
        
        start_date = parse_date(start_str)
        end_date = parse_date(end_str)
        
        if start_date and end_date:
            if start_date > end_date:
                messagebox.showerror("Invalid Date Range", "Start date must be before end date")
                # Auto-correct
                self.start_date_var.set(format_date(get_previous_trading_day(end_date)))
            elif not is_trading_day(start_date):
                messagebox.showwarning("Non-Trading Day", f"{start_str} is not a trading day. Adjusting...")
                self.start_date_var.set(format_date(get_previous_trading_day(start_date)))
            elif not is_trading_day(end_date):
                messagebox.showwarning("Non-Trading Day", f"{end_str} is not a trading day. Adjusting...")
                self.end_date_var.set(format_date(get_previous_trading_day(end_date)))
    
    def load_default_csv(self):
        """Load default CSV file"""
        symbols = self.universe.load_default_csv()
        self.active_symbols = symbols  # Update active symbols
        messagebox.showinfo("Success", f"Loaded {len(symbols)} symbols from default CSV")
    
    def clear_symbols(self):
        """Clear all symbols from active analysis"""
        if messagebox.askyesno("Confirm", "Clear all symbols from analysis? (CSV file will not be deleted)"):
            self.universe.clear_symbols()
            self.active_symbols = []
            messagebox.showinfo("Success", "Symbols cleared from analysis")
    
    def select_stocks(self):
        """Open stock selection dialog with manual entry and checkbox list"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Stocks for Analysis")
        dialog.geometry("500x600")
        dialog.configure(bg="#f8fafc")
        
        # Store references locally for this dialog
        manual_frame = None
        checkbox_frame = None
        manual_entry = None
        checkbox_vars = {}
        checkbox_inner = None
        
        # Mode selection
        mode_frame = tk.LabelFrame(dialog, text="Selection Mode", bg="#ffffff", font=("Helvetica", 10, "bold"))
        mode_frame.pack(fill=tk.X, padx=15, pady=10)
        
        def switch_mode(mode):
            nonlocal manual_frame, checkbox_frame
            if mode == "manual":
                if checkbox_frame:
                    checkbox_frame.pack_forget()
                if manual_frame:
                    manual_frame.pack(fill=tk.BOTH, expand=True)
            else:
                if manual_frame:
                    manual_frame.pack_forget()
                if checkbox_frame:
                    checkbox_frame.pack(fill=tk.BOTH, expand=True)
        
        manual_radio = tk.Radiobutton(mode_frame, text="Manual Entry", variable=self.symbol_selection_mode,
                                      value="manual", bg="#ffffff", font=("Helvetica", 9),
                                      command=lambda: switch_mode("manual"))
        manual_radio.pack(side=tk.LEFT, padx=10, pady=5)
        
        csv_radio = tk.Radiobutton(mode_frame, text="Checkbox List (from CSV)", variable=self.symbol_selection_mode,
                                  value="csv", bg="#ffffff", font=("Helvetica", 9),
                                  command=lambda: switch_mode("csv"))
        csv_radio.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Content frame
        content_frame = tk.Frame(dialog, bg="#f8fafc")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Manual entry frame
        manual_frame = tk.Frame(content_frame, bg="#f8fafc")
        tk.Label(manual_frame, text="Enter symbols (comma or space separated):", 
                bg="#f8fafc", font=("Helvetica", 9)).pack(anchor=tk.W, pady=5)
        manual_entry = tk.Text(manual_frame, font=("Courier", 10), height=15, width=50)
        manual_entry.pack(fill=tk.BOTH, expand=True, pady=5)
        if self.active_symbols:
            manual_entry.insert("1.0", ", ".join(self.active_symbols))
        
        # Checkbox list frame
        checkbox_frame = tk.Frame(content_frame, bg="#f8fafc")
        scroll_frame = tk.Frame(checkbox_frame, bg="#f8fafc")
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(scroll_frame, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        checkbox_inner = tk.Frame(canvas, bg="#ffffff")
        
        checkbox_inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=checkbox_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate checkboxes
        symbols = self.universe.load_symbols()
        for sym in sorted(symbols):
            var = tk.BooleanVar(value=sym in self.active_symbols if self.active_symbols else True)
            checkbox_vars[sym] = var
            
            checkbox = tk.Checkbutton(checkbox_inner, text=sym, variable=var,
                                     bg="#ffffff", font=("Helvetica", 9),
                                     anchor=tk.W)
            checkbox.pack(fill=tk.X, padx=5, pady=2)
        
        # Show initial mode
        if self.symbol_selection_mode.get() == "manual":
            manual_frame.pack(fill=tk.BOTH, expand=True)
        else:
            checkbox_frame.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg="#f8fafc")
        btn_frame.pack(fill=tk.X, padx=15, pady=10)
        
        def apply_selection():
            if self.symbol_selection_mode.get() == "manual":
                text = manual_entry.get("1.0", tk.END).strip()
                symbols = [s.strip().upper() for s in re.split(r'[,\s]+', text) if s.strip()]
            else:
                symbols = [sym for sym, var in checkbox_vars.items() if var.get()]
            
            if not symbols:
                messagebox.showwarning("No Selection", "Please select at least one symbol")
                return
            
            # Update active symbols and save to CSV
            self.active_symbols = symbols
            self.universe.save_symbols(symbols)
            messagebox.showinfo("Success", f"Selected {len(symbols)} symbols: {', '.join(symbols[:5])}{'...' if len(symbols) > 5 else ''}")
            dialog.destroy()
        
        tk.Button(btn_frame, text="Apply Selection", command=apply_selection,
                 bg="#3b82f6", fg="white", font=("Helvetica", 10, "bold"),
                 padx=20, pady=8, relief="flat", cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg="#94a3b8", fg="white", font=("Helvetica", 10),
                 padx=20, pady=8, relief="flat", cursor="hand2").pack(side=tk.LEFT, padx=5)


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
                self.active_symbols = symbols  # Update active symbols
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
                self.active_symbols = symbols  # Update active symbols
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
            self.active_symbols = new_symbols  # Update active symbols
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
* **Start/End Date:** Set custom date range for analysis. Use predefined buttons (1D, 3D, 5D, 1W) for quick selection.
* **Expand/Collapse:** Click the **+** or **−** icon next to symbol names to expand/collapse detailed daily data.
* **View Mode:** Toggle between **Detailed** (full data) and **Average** (summary statistics) views.
* **Stock Selection:** Use **Select Stocks** button to choose symbols via manual entry or checkbox list.

---

## 📑 Analysis Tabs

### 🔄 Swing Counter

Tracks intraday price swings based on your custom **Swing %**. It identifies moves that deviate from the last reference point by your specified threshold using the selected interval.

* Results show parent rows with summary statistics and expandable child rows for daily breakdowns.

### 📉 n% Down From High

A real-time "dip" scanner. Filters for symbols currently trading at least **n% below** their daily high. Perfect for spotting intraday pullbacks.

* Results show parent rows with average metrics and expandable child rows for daily occurrences.

### ⏰ Early-Session Performance

Analyzes the **Opening Cross (09:30-09:40)** price action and tracks performance from the **Start Value (09:40)** to close. Shows detailed daily breakdown with high/low timestamps when expanded.

* **Expanded View:** Shows Opening Cross range, Start Value, Close Value, % Gain, and Remarks with timestamps.
* **Collapsed View:** Shows summary with average values and simplified remarks.

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
        self.view_mode = tk.StringVar(value="detailed")  # "detailed" or "average"
        self.expanded_items = set()  # Track which items are expanded
        # Map Treeview item -> original symbol text (for icon updates)
        self._item_symbol = {}

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
        style = ttk.Style()
        style.configure("TProgressbar", background="#3b82f6")
        style.map("TProgressbar", background=[("active", "#3b82f6")])
        
        self.progress_bar = ttk.Progressbar(progress_frame,
                                            variable=self.progress_var,
                                            maximum=100,
                                            length=300,
                                            mode='determinate',
                                            style="TProgressbar")
        self.progress_bar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        return progress_frame

    def update_progress(self, current, total):
        """Update progress bar and label"""
        if total > 0:
            progress_value = (current / total) * 100
            self.progress_var.set(progress_value)
            self.progress_label.config(text=f"Processing: {current}/{total}")
            self.frame.update_idletasks()

    def reset_progress(self, success=False):
        """Reset progress bar, optionally show success state"""
        if success:
            # Show green highlight on completion
            style = ttk.Style()
            style.configure("Success.TProgressbar", background="#10b981")
            self.progress_bar.config(style="Success.TProgressbar")
            self.progress_label.config(text="✓ Complete", fg="#10b981")
            self.frame.after(2000, self._reset_progress_normal)  # Reset after 2 seconds
        else:
            self.progress_var.set(0)
            self.progress_label.config(text="Ready", fg="#1e293b")
            self.progress_bar.config(style="TProgressbar")
    
    def _reset_progress_normal(self):
        """Reset progress bar to normal state"""
        self.progress_var.set(0)
        self.progress_label.config(text="Ready", fg="#1e293b")
        self.progress_bar.config(style="TProgressbar")
    
    def get_date_range(self):
        """Get start and end dates from app controls"""
        start_str = self.app.start_date_var.get()
        end_str = self.app.end_date_var.get()
        
        start_date = parse_date(start_str)
        end_date = parse_date(end_str)
        
        if not start_date or not end_date:
            # Fallback to days if date parsing fails
            days = max(1, int(self.app.duration_var.get()))
            start_date, end_date = get_trading_days_back(days)
        
        return start_date, end_date

    def create_treeview(self, columns, collapsible=True):
        """Create results treeview with expand/collapse support"""
        tree_frame = tk.Frame(self.frame, bg="#f8fafc")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Add view mode toggle
        view_frame = tk.Frame(tree_frame, bg="#f8fafc")
        view_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(view_frame, text="View Mode:", bg="#f8fafc", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=5)
        
        detailed_btn = tk.Radiobutton(view_frame, text="Detailed", variable=self.view_mode, 
                                      value="detailed", bg="#f8fafc", font=("Helvetica", 9),
                                      command=self.toggle_view_mode)
        detailed_btn.pack(side=tk.LEFT, padx=5)
        
        average_btn = tk.Radiobutton(view_frame, text="Average", variable=self.view_mode,
                                     value="average", bg="#f8fafc", font=("Helvetica", 9),
                                     command=self.toggle_view_mode)
        average_btn.pack(side=tk.LEFT, padx=5)
        
        # IMPORTANT:
        # - We use the special tree column (#0) as the ONLY "Symbol" column.
        # - The caller still passes a "Symbol" column name in `columns[0]` for clarity.
        # - All other columns are normal data columns.
        if not columns:
            raise ValueError("Treeview requires at least one column (e.g. 'Symbol').")

        symbol_col_name = columns[0]
        data_columns = columns[1:]

        tree = ttk.Treeview(tree_frame, columns=data_columns, show="tree headings", height=18)

        # Tree column (#0) becomes the symbol column
        tree.column("#0", width=220, anchor=tk.W, stretch=True)
        tree.heading("#0", text=symbol_col_name)

        for col in data_columns:
            tree.heading(col, text=col)
            tree.column(col, anchor=tk.CENTER, width=150)
        
        # Bind click events for expand/collapse
        tree.bind("<Button-1>", self.on_tree_click)
        # Also update icons when items are expanded/collapsed via double-click or other methods
        tree.bind("<<TreeviewOpen>>", self._on_item_expand)
        tree.bind("<<TreeviewClose>>", self._on_item_collapse)
        
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
    
    def on_tree_click(self, event):
        """Handle click on treeview to toggle expand/collapse"""
        tree = event.widget
        region = tree.identify_region(event.x, event.y)
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        
        # Only toggle when clicking the tree (symbol) column (#0).
        # This gives an explicit, predictable click-target for "+ / −".
        if (
            item
            and tree.get_children(item)
            and region == "tree"
            and column == "#0"
        ):
            is_open = bool(tree.item(item, "open"))
            tree.item(item, open=not is_open)
            if is_open:
                self.expanded_items.discard(item)
                self.update_expand_icon(tree, item, False)
            else:
                self.expanded_items.add(item)
                self.update_expand_icon(tree, item, True)
    
    def update_expand_icon(self, tree, item, is_expanded):
        """Update the expand/collapse icon for an item"""
        icon = "−" if is_expanded else "+"
        sym = self._item_symbol.get(item)
        if not sym:
            # Fallback: extract from current text
            sym = tree.item(item, "text").lstrip("+− ").strip()
            self._item_symbol[item] = sym
        tree.item(item, text=f"{icon} {sym}")
    
    def _on_item_expand(self, event):
        """Handle item expansion event"""
        tree = event.widget
        # Find which item was expanded by checking all items
        for item in tree.get_children():
            if tree.get_children(item) and tree.item(item, "open"):
                self.expanded_items.add(item)
                self.update_expand_icon(tree, item, True)
    
    def _on_item_collapse(self, event):
        """Handle item collapse event"""
        tree = event.widget
        # Find which item was collapsed by checking all items
        for item in tree.get_children():
            if tree.get_children(item) and not tree.item(item, "open"):
                self.expanded_items.discard(item)
                self.update_expand_icon(tree, item, False)
    
    def toggle_view_mode(self):
        """Toggle between detailed and average view modes"""
        # This will be overridden by specific tabs if needed
        pass

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
        """Add a parent row for collapsible tree with +/- icon"""
        if not values:
            return tree.insert("", tk.END, text="+", values=(), open=False)

        symbol = str(values[0])
        item = tree.insert("", tk.END, text=f"+ {symbol}", values=values[1:], open=False)
        self._item_symbol[item] = symbol
        
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
        # For children, the first element of `values` is displayed under the Symbol column (#0),
        # and the remaining values fill the data columns.
        if not values:
            item = tree.insert(parent, tk.END, text="", values=())
        else:
            item = tree.insert(parent, tk.END, text=str(values[0]), values=values[1:])
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
        self.expanded_items.clear()
        # Use active_symbols if available, otherwise load from CSV
        symbols = self.app.active_symbols if self.app.active_symbols else self.universe.load_symbols()
        total_symbols = len(symbols)
        
        if not symbols:
            messagebox.showwarning("No Symbols", "Please load or select symbols first")
            return
        
        start_date, end_date = self.get_date_range()
        
        for idx, sym in enumerate(symbols):
            self.update_progress(idx, total_symbols)
            try:
                interval = self.app.interval_var.get().strip()
                # Use date range instead of period
                data = yf.Ticker(sym).history(start=start_date, end=end_date + timedelta(days=1), interval=interval)

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
        
        self.update_progress(total_symbols, total_symbols)
        self.reset_progress(success=True)


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
        self.expanded_items.clear()
        # Use active_symbols if available, otherwise load from CSV
        symbols = self.app.active_symbols if self.app.active_symbols else self.universe.load_symbols()
        threshold = self.n_pct.get()
        total_symbols = len(symbols)
        
        if not symbols:
            messagebox.showwarning("No Symbols", "Please load or select symbols first")
            return
        
        start_date, end_date = self.get_date_range()
        
        for idx, sym in enumerate(symbols):
            self.update_progress(idx, total_symbols)
            try:
                interval = self.app.interval_var.get().strip()
                # Use date range instead of period
                df = yf.Ticker(sym).history(start=start_date, end=end_date + timedelta(days=1), interval=interval)
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
        
        self.update_progress(total_symbols, total_symbols)
        self.reset_progress(success=True)


class EarlySessionTab(BaseTab):
    """Tab 3: Early Session Performance Analyzer with Opening Cross Analysis"""
    
    def __init__(self, notebook, universe, app):
        super().__init__(notebook, universe, app)
        self.build_ui()
        self.stored_data = {}  # Store data for view mode switching

    def build_ui(self):
        controls = self.create_control_frame("Opening Cross Analysis (09:30-09:40)")
        
        tk.Label(controls, text="Analyzes price action from 09:30 to 09:40 and tracks performance", 
                bg="#ffffff", font=("Helvetica", 9), fg="#64748b").grid(row=0, column=0, columnspan=3, padx=5, pady=5)
        
        tk.Button(controls, text="📊 Analyze", bg="#3b82f6", fg="white",
                 font=("Helvetica", 10, "bold"), command=self.run, padx=20, pady=8,
                 relief="flat", cursor="hand2").grid(row=1, column=0, padx=15, pady=10)
        
        self.create_progress_bar()
        
        # Columns for detailed view
        self.detailed_columns = ("Symbol", "Date", "Opening Cross (09:30–09:40)", 
                                 "Start Value (09:40)", "Close Value", "% Gain from Start", "Remarks")
        # Columns for collapsed view
        self.collapsed_columns = ("Symbol", "Date", "Opening Cross (09:30–09:40)",
                                  "Start Value", "Close Value", "% Gain", "Remarks")
        
        self.tree = self.create_treeview(self.detailed_columns)

    def run(self):
        """Run Opening Cross analysis"""
        self.tree.delete(*self.tree.get_children())
        self.expanded_items.clear()
        # Use active_symbols if available, otherwise load from CSV
        symbols = self.app.active_symbols if self.app.active_symbols else self.universe.load_symbols()
        total_symbols = len(symbols)
        
        if not symbols:
            messagebox.showwarning("No Symbols", "Please load symbols first")
            return
        
        start_date, end_date = self.get_date_range()
        self.stored_data = {}
        
        for idx, sym in enumerate(symbols):
            self.update_progress(idx, total_symbols)
            try:
                interval = self.app.interval_var.get().strip()
                
                # Fetch data using date range
                ticker = yf.Ticker(sym)
                df = ticker.history(start=start_date, end=end_date + timedelta(days=1), interval=interval)
                
                if df.empty:
                    continue
                
                df["date"] = df.index.date
                daily_records = []
                
                for d, day_df in df.groupby("date"):
                    # Filter for market hours (09:30 - 16:00)
                    day_df = day_df.between_time("09:30", "16:00")
                    
                    if len(day_df) < 11:  # Need at least 11 minutes (09:30-09:40)
                        continue
                    
                    # Opening Cross: 09:30-09:40 (first 10 minutes, indices 0-9)
                    opening_cross = day_df.iloc[:10]
                    if len(opening_cross) < 10:
                        continue
                    
                    open_price = opening_cross.iloc[0]["Open"]
                    opening_high = opening_cross["High"].max()
                    opening_low = opening_cross["Low"].min()
                    opening_range = opening_high - opening_low
                    opening_range_pct = (opening_range / open_price * 100) if open_price > 0 else 0
                    
                    # Start Value: Price at exactly 09:40 (index 10)
                    start_value = day_df.iloc[10]["Close"] if len(day_df) > 10 else day_df.iloc[-1]["Close"]
                    
                    # Close Value: Last price of the day
                    close_value = day_df.iloc[-1]["Close"]
                    
                    # % Gain from Start Value
                    pct_gain = ((close_value - start_value) / start_value * 100) if start_value > 0 else 0
                    
                    # Find high and low with timestamps
                    day_high = day_df["High"].max()
                    day_low = day_df["Low"].min()
                    high_time = day_df[day_df["High"] == day_high].index[0].strftime("%H:%M")
                    low_time = day_df[day_df["Low"] == day_low].index[0].strftime("%H:%M")
                    
                    daily_records.append({
                        'date': d,
                        'opening_cross': f"${opening_low:.2f}-${opening_high:.2f} ({opening_range_pct:.2f}%)",
                        'opening_low': float(opening_low),
                        'opening_high': float(opening_high),
                        'opening_range_pct': float(opening_range_pct),
                        'start_value': start_value,
                        'close_value': close_value,
                        'pct_gain': pct_gain,
                        'day_high': day_high,
                        'day_low': day_low,
                        'high_time': high_time,
                        'low_time': low_time
                    })
                
                if not daily_records:
                    continue
                
                # Store data for view mode switching
                self.stored_data[sym] = daily_records
                
                # Calculate summary/averages
                avg_pct_gain = sum(r['pct_gain'] for r in daily_records) / len(daily_records)
                avg_start = sum(r['start_value'] for r in daily_records) / len(daily_records)
                avg_close = sum(r['close_value'] for r in daily_records) / len(daily_records)
                avg_opening_pct = sum(r['opening_range_pct'] for r in daily_records) / len(daily_records)
                avg_day_high = sum(r['day_high'] for r in daily_records) / len(daily_records)
                avg_day_low = sum(r['day_low'] for r in daily_records) / len(daily_records)
                
                # Determine if mostly HIGH or LOW in collapsed view
                positive_days = sum(1 for r in daily_records if r['pct_gain'] > 0)
                negative_days = sum(1 for r in daily_records if r['pct_gain'] < 0)
                # Collapsed summary remark: show only LOW or HIGH (NO timestamps)
                if avg_pct_gain >= 0:
                    summary_remark = f"HIGH: ${avg_day_high:.2f}"
                else:
                    summary_remark = f"LOW: ${avg_day_low:.2f}"
                
                # Add parent row (collapsed view)
                parent_values = (
                    sym,
                    "SUMMARY",
                    f"Avg cross: {avg_opening_pct:.2f}%",
                    f"${avg_start:.2f}",
                    f"${avg_close:.2f}",
                    f"{avg_pct_gain:.2f}%",
                    summary_remark
                )
                
                parent = self.add_parent_row(self.tree, parent_values, 5, 0)
                
                # Add child rows (expanded view) - hidden by default
                for record in daily_records:
                    # Detailed remarks with timestamps
                    remarks = f"LOW: ${record['day_low']:.2f} @ {record['low_time']} | HIGH: ${record['day_high']:.2f} @ {record['high_time']}"
                    
                    child_values = (
                        str(record['date']),
                        record['opening_cross'],
                        f"${record['start_value']:.2f}",
                        f"${record['close_value']:.2f}",
                        f"{record['pct_gain']:.2f}%",
                        remarks
                    )
                    
                    # Child rows live under the parent symbol; keep Symbol column empty.
                    child = self.add_child_row(self.tree, parent, ("",) + child_values)
                    
                    # Color code based on % gain
                    if record['pct_gain'] > 0:
                        self.tree.item(child, tags=('positive',))
                    elif record['pct_gain'] < 0:
                        self.tree.item(child, tags=('negative',))
                
                # Configure color tags
                self.tree.tag_configure('positive', background='#dcfce7')
                self.tree.tag_configure('negative', background='#fee2e2')
                
            except Exception as e:
                print(f"Error processing {sym}: {str(e)}")
        
        self.update_progress(total_symbols, total_symbols)
        self.reset_progress(success=True)
    
    def toggle_view_mode(self):
        """Switch between detailed and average view modes"""
        # Rebuild from stored data (no refetch) for deterministic results.
        self.tree.delete(*self.tree.get_children())
        self.expanded_items.clear()

        for sym, daily_records in self.stored_data.items():
            if not daily_records:
                continue

            avg_pct_gain = sum(r['pct_gain'] for r in daily_records) / len(daily_records)
            avg_start = sum(r['start_value'] for r in daily_records) / len(daily_records)
            avg_close = sum(r['close_value'] for r in daily_records) / len(daily_records)
            avg_opening_pct = sum(r['opening_range_pct'] for r in daily_records) / len(daily_records)
            avg_day_high = sum(r['day_high'] for r in daily_records) / len(daily_records)
            avg_day_low = sum(r['day_low'] for r in daily_records) / len(daily_records)

            if avg_pct_gain >= 0:
                summary_remark = f"HIGH: ${avg_day_high:.2f}"
            else:
                summary_remark = f"LOW: ${avg_day_low:.2f}"

            parent_values = (
                sym,
                "SUMMARY",
                f"Avg cross: {avg_opening_pct:.2f}%",
                f"${avg_start:.2f}",
                f"${avg_close:.2f}",
                f"{avg_pct_gain:.2f}%",
                summary_remark
            )
            parent = self.add_parent_row(self.tree, parent_values, 5, 0)

            if self.view_mode.get() == "average":
                # Average mode: keep collapsed-only rows (no children)
                continue

            for record in daily_records:
                remarks = f"LOW: ${record['day_low']:.2f} @ {record['low_time']} | HIGH: ${record['day_high']:.2f} @ {record['high_time']}"
                child_values = (
                    "",  # keep Symbol column empty for children
                    str(record['date']),
                    record['opening_cross'],
                    f"${record['start_value']:.2f}",
                    f"${record['close_value']:.2f}",
                    f"{record['pct_gain']:.2f}%",
                    remarks
                )
                child = self.add_child_row(self.tree, parent, child_values)
                if record['pct_gain'] > 0:
                    self.tree.item(child, tags=('positive',))
                elif record['pct_gain'] < 0:
                    self.tree.item(child, tags=('negative',))

        self.tree.tag_configure('positive', background='#dcfce7')
        self.tree.tag_configure('negative', background='#fee2e2')


class ReversalCycleTab(BaseTab):
    """Tab 4: n% Price Reversal Cycle Counter"""
    
    def __init__(self, notebook, universe , app):
        super().__init__(notebook, universe, app)
        self.n_pct = tk.DoubleVar(value=2.0)
        self.build_ui()

    def build_ui(self):
        controls = self.create_control_frame("Reversal Cycle Settings")
        
        tk.Label(controls, text="Reversal %:", bg="#ffffff", font=("Helvetica", 10)).grid(row=0, column=0, padx=5)
        tk.Entry(controls, textvariable=self.n_pct, width=8, font=("Helvetica", 10)).grid(row=0, column=1, padx=5)
        
        tk.Label(controls, text="(Date range set in toolbar)", bg="#ffffff", font=("Helvetica", 9), 
                fg="#64748b").grid(row=0, column=2, padx=(15, 5))
        
        tk.Button(controls, text="🔄 Count Cycles", bg="#ef4444", fg="white",
                 font=("Helvetica", 10, "bold"), command=self.run, padx=20, pady=8,
                 relief="flat", cursor="hand2").grid(row=0, column=3, padx=15)
        
        self.create_progress_bar()
        
        self.tree = self.create_treeview(("Symbol", "Total Cycles", "Avg Cycles/Day", "Daily Breakdown"), collapsible=True)

    def run(self):
        self.tree.delete(*self.tree.get_children())
        self.expanded_items.clear()
        # Use active_symbols if available, otherwise load from CSV
        symbols = self.app.active_symbols if self.app.active_symbols else self.universe.load_symbols()
        total_symbols = len(symbols)
        
        if not symbols:
            messagebox.showwarning("No Symbols", "Please load or select symbols first")
            return
        
        start_date, end_date = self.get_date_range()
        
        for idx, sym in enumerate(symbols):
            self.update_progress(idx, total_symbols)
            try:
                interval = self.app.interval_var.get().strip()
                # Use date range instead of period
                df = yf.Ticker(sym).history(start=start_date, end=end_date + timedelta(days=1), interval=interval)

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
        
        self.update_progress(total_symbols, total_symbols)
        self.reset_progress(success=True)




if __name__ == "__main__":
    root = tk.Tk()
    app = StockAnalysisApp(root)
    root.mainloop()