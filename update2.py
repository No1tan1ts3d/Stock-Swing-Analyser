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
            tk.Button(btn_frame,
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

        # # Interval input with help
        # tk.Label(control_frame, text="Interval:", bg="#e2e8f0", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=(5,2))
        # interval_entry = tk.Entry(control_frame, textvariable=self.interval_var, width=8, font=("Helvetica", 9))
        # interval_entry.pack(side=tk.LEFT, padx=5)
        # tk.Button(control_frame, text="?", width=2, relief="flat", bg="#94a3b8", fg="white",
        #          font=("Helvetica", 8, "bold"), cursor="hand2", 
        #          command=lambda: show_help("interval")).pack(side=tk.LEFT, padx=(2, 5))

        # # Date range controls with help
        # tk.Label(control_frame, text="Start:", bg="#e2e8f0", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=(10,2))
        # start_entry = tk.Entry(control_frame, textvariable=self.start_date_var, width=12, font=("Helvetica", 9))
        # start_entry.pack(side=tk.LEFT, padx=2)
        # start_entry.bind('<FocusOut>', lambda e: self.validate_date_range())
        
        # tk.Label(control_frame, text="End:", bg="#e2e8f0", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=(5,2))
        # end_entry = tk.Entry(control_frame, textvariable=self.end_date_var, width=12, font=("Helvetica", 9))
        # end_entry.pack(side=tk.LEFT, padx=2)
        # end_entry.bind('<FocusOut>', lambda e: self.validate_date_range())
        # tk.Button(control_frame, text="?", width=2, relief="flat", bg="#94a3b8", fg="white",
        #          font=("Helvetica", 8, "bold"), cursor="hand2", 
        #          command=lambda: show_help("date_range")).pack(side=tk.LEFT, padx=(2, 5))
        
        # # Predefined date range buttons
        # date_btn_frame = tk.Frame(control_frame, bg="#e2e8f0")
        # date_btn_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        # for label, days in [("1D", 1), ("3D", 3), ("5D", 5), ("1W", 5)]:
        #     tk.Button(date_btn_frame, text=label, command=lambda d=days: self.set_date_range(d),
        #              bg="#94a3b8", fg="white", font=("Helvetica", 8, "bold"),
        #              relief="flat", padx=6, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=2)

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
        label_frame = tk.Frame(manual_frame, bg="#f8fafc")
        label_frame.pack(fill=tk.X, anchor=tk.W, pady=5)
        tk.Label(label_frame, text="Enter symbols (comma or space separated):", 
                bg="#f8fafc", font=("Helvetica", 9)).pack(side=tk.LEFT)
        tk.Button(label_frame, text="?", width=2, relief="flat", bg="#94a3b8", fg="white",
                 font=("Helvetica", 8, "bold"), cursor="hand2", 
                 command=lambda: show_help("ticker_input")).pack(side=tk.LEFT, padx=(5, 0))
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
        
        tabs = [
            (SwingCounterTab, "🔄 Swing Counter"),
            (DownFromHighTab, "📉 n% Down From High"),
            (EarlySessionTab, "⏰ Early-Session Performance"),
            (ReversalCycleTab, "🔁 n% Reversal Cycles")
        ]
        
        for TabClass, label in tabs:
            tab = TabClass(notebook, self.universe, self)
            notebook.add(tab.frame, text=label)

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

### 📉 n% Down From High

A real-time "dip" scanner. Filters for symbols currently trading at least **n% below** their daily high. Perfect for spotting intraday pullbacks.

### ⏰ Early-Session Performance

Analyzes the **Opening Cross (09:30-09:40)** price action and tracks performance from the **Start Value (09:40)** to close. Shows detailed daily breakdown with high/low timestamps when expanded.

* **Expanded View:** Shows Opening Cross range, Start Value, Close Value, % Gain, and Remarks with timestamps.
* **Collapsed View:** Shows summary with average values and simplified remarks.

### 🔁 n% Reversal Cycles

Identifies "ping-pong" price action. Detects completed cycles where the price moves up by **n%** and then fully reverses by **n%** (or vice versa).

---

## 💡 Pro Tips

* **Avoid Data Gaps:** If you need a longer history, switch to **5m** or **15m** intervals to bypass 1-minute limitations.
* **Blank Results?** Not all tickers support sub-minute data. If a chart is empty, the ticker likely doesn't provide data for that specific interval.
* **Stay Within Limits:** Keep the **Days** setting low when using the **1m** interval to prevent fetch errors.

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
        
def show_help(feature_name):
    """Show contextual help for a feature"""
    help_messages = {
        "ticker_input": "Enter stock symbols separated by commas.",
        "start_time": "The baseline time to capture the reference price.",
        "run_calculate": "Fetches data and applies High/Low gain logic.",
        "swing_pct": "Percentage threshold for detecting price swings.",
        "n_pct_down": "Percentage threshold for filtering stocks down from daily high.",
        "reversal_pct": "Percentage threshold for detecting reversal cycles.",
        "interval": "Data granularity (1m, 5m, 15m, etc.). Smaller intervals have stricter historical limits.",
        "date_range": "Start and end dates for analysis. Use predefined buttons for quick selection.",
    }
    
    message = help_messages.get(feature_name, f"Help for {feature_name}")
    messagebox.showinfo(f"Help: {feature_name}", message)


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
    
    def create_help_button(self, parent, feature_name, row=None, column=None):
        """Create a small '?' help button"""
        help_btn = tk.Button(parent, text="?", width=2, relief="flat",
                            bg="#94a3b8", fg="white", font=("Helvetica", 8, "bold"),
                            cursor="hand2", command=lambda: show_help(feature_name))
        if row is not None and column is not None:
            help_btn.grid(row=row, column=column, padx=(2, 0))
        else:
            help_btn.pack(side=tk.LEFT, padx=(2, 0))
        return help_btn

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
    
        
    def create_date_interval_controls(self, parent_frame):
        """Create date range and interval controls for individual tab"""
        control_frame = tk.Frame(parent_frame, bg="#ffffff")
        control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Interval input with help
        tk.Label(control_frame, text="Interval:", bg="#ffffff", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=(5,2))
        interval_entry = tk.Entry(control_frame, textvariable=self.app.interval_var, width=8, font=("Helvetica", 9))
        interval_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="?", width=2, relief="flat", bg="#94a3b8", fg="white",
                font=("Helvetica", 8, "bold"), cursor="hand2", 
                command=lambda: show_help("interval")).pack(side=tk.LEFT, padx=(2, 5))

        # Date range controls with help
        tk.Label(control_frame, text="Start:", bg="#ffffff", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=(10,2))
        start_entry = tk.Entry(control_frame, textvariable=self.app.start_date_var, width=12, font=("Helvetica", 9))
        start_entry.pack(side=tk.LEFT, padx=2)
        start_entry.bind('<FocusOut>', lambda e: self.app.validate_date_range())
        
        tk.Label(control_frame, text="End:", bg="#ffffff", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=(5,2))
        end_entry = tk.Entry(control_frame, textvariable=self.app.end_date_var, width=12, font=("Helvetica", 9))
        end_entry.pack(side=tk.LEFT, padx=2)
        end_entry.bind('<FocusOut>', lambda e: self.app.validate_date_range())
        tk.Button(control_frame, text="?", width=2, relief="flat", bg="#94a3b8", fg="white",
                font=("Helvetica", 8, "bold"), cursor="hand2", 
                command=lambda: show_help("date_range")).pack(side=tk.LEFT, padx=(2, 5))
        
        # Predefined date range buttons
        date_btn_frame = tk.Frame(control_frame, bg="#ffffff")
        date_btn_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        for label, days in [("1D", 1), ("3D", 3), ("5D", 5), ("1W", 5)]:
            tk.Button(date_btn_frame, text=label, command=lambda d=days: self.app.set_date_range(d),
                     bg="#94a3b8", fg="white", font=("Helvetica", 8, "bold"),
                     relief="flat", padx=6, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=2)

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
        
        # Note: Success style will be created dynamically in reset_progress if needed
        # to avoid layout issues with ttk styles
        
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
            # Use label color change to indicate success (more reliable than style changes)
            # Optionally try to change progress bar color, but don't fail if it doesn't work
            try:
                style = ttk.Style()
                # Try to temporarily change the base TProgressbar color to green
                # Store original color first
                try:
                    original_bg = style.lookup("TProgressbar", "background") or "#3b82f6"
                    style.configure("TProgressbar", background="#10b981")
                    # Schedule reset of color after showing success
                    self.frame.after(2100, lambda: style.configure("TProgressbar", background=original_bg))
                except Exception:
                    # If style modification fails, that's okay - label color will indicate success
                    pass
            except Exception:
                # If any style operation fails, just continue with label color change
                pass
            
            self.progress_label.config(text="✓ Complete", fg="#10b981")
            self.frame.after(2000, self._reset_progress_normal)  # Reset after 2 seconds
        else:
            self.progress_var.set(0)
            self.progress_label.config(text="Ready", fg="#1e293b")
    
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
        self.create_help_button(controls, "swing_pct", row=0, column=2)
        
        run_btn_frame = tk.Frame(controls, bg="#ffffff")
        run_btn_frame.grid(row=0, column=3, padx=15)
        tk.Button(run_btn_frame, text="▶ Run Analysis", bg="#3b82f6", fg="white",
                 font=("Helvetica", 10, "bold"), command=self.run, padx=20, pady=8,
                 relief="flat", cursor="hand2").pack(side=tk.LEFT)
        self.create_help_button(run_btn_frame, "run_calculate")
        
        # Add date and interval controls
        self.create_date_interval_controls(self.frame)
        
        self.create_progress_bar()
        
        self.tree = self.create_treeview(("Symbol", "Up Swings", "Down Swings", "Total Swings", "Avg Daily"))

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
        self.create_help_button(controls, "n_pct_down", row=0, column=2)
        
        scan_btn_frame = tk.Frame(controls, bg="#ffffff")
        scan_btn_frame.grid(row=0, column=3, padx=15)
        tk.Button(scan_btn_frame, text="🔍 Scan Now", bg="#10b981", fg="white",
                 font=("Helvetica", 10, "bold"), command=self.run, padx=20, pady=8,
                 relief="flat", cursor="hand2").pack(side=tk.LEFT)
        self.create_help_button(scan_btn_frame, "run_calculate")
        
        self.create_progress_bar()
        
        self.tree = self.create_treeview(("Symbol", "Current Price", "Day High", "% Down"))

    def run(self):
        self.tree.delete(*self.tree.get_children())
        self.expanded_items.clear()
        symbols = self.app.active_symbols if self.app.active_symbols else self.universe.load_symbols()
        threshold = self.n_pct.get()
        total_symbols = len(symbols)
        
        if not symbols:
            messagebox.showwarning("No Symbols", "Please load or select symbols first")
            return
        
        # Determine if market is currently open (Monday-Friday, 09:30-16:00)
        today = date.today()
        current_time = datetime.now().time()
        is_market_open = (
            is_trading_day(today) and
            datetime.strptime("09:30", "%H:%M").time() <= current_time <= datetime.strptime("16:00", "%H:%M").time()
        )
        
        if is_market_open:
            # During trading hours: check current price vs high so far today
            analysis_date = today
            check_type = "current"  # Check current price vs day high
        else:
            # Outside trading hours: check last trading day's LOW vs HIGH
            analysis_date = get_previous_trading_day(today)
            check_type = "low"  # Check previous day's low vs high
        
        for idx, sym in enumerate(symbols):
            self.update_progress(idx, total_symbols)
            try:
                interval = self.app.interval_var.get().strip()
                # Fetch data for the analysis date only
                df = yf.Ticker(sym).history(start=analysis_date, end=analysis_date + timedelta(days=1), interval=interval)
                
                if df.empty:
                    continue
                
                # Get high price for the day
                high = df["High"].max()
                
                if check_type == "current":
                    # During market hours: use current (latest) close price
                    current = df["Close"].iloc[-1]
                else:
                    # After hours: use the LOW price of the day
                    current = df["Low"].min()
                
                # Calculate how much down from high
                drop = (high - current) / high * 100
                
                # Only show if it meets the threshold
                if drop < threshold:
                    continue
                
                # Add single row
                self.add_parent_row(self.tree, 
                                (sym, f"${current:.2f}", f"${high:.2f}", f"{drop:.2f}%"),
                                3, threshold, reverse=True)
                
            except Exception as e:
                print(f"Error processing {sym}: {str(e)}")
        
        self.update_progress(total_symbols, total_symbols)
        self.reset_progress(success=True)

    # def run(self):
    #     self.tree.delete(*self.tree.get_children())
    #     self.expanded_items.clear()
    #     # Use active_symbols if available, otherwise load from CSV
    #     symbols = self.app.active_symbols if self.app.active_symbols else self.universe.load_symbols()
    #     threshold = self.n_pct.get()
    #     total_symbols = len(symbols)
        
    #     if not symbols:
    #         messagebox.showwarning("No Symbols", "Please load or select symbols first")
    #         return
        
    #     start_date, end_date = self.get_date_range()
        
    #     for idx, sym in enumerate(symbols):
    #         self.update_progress(idx, total_symbols)
    #         try:
    #             interval = self.app.interval_var.get().strip()
    #             # Use date range instead of period
    #             df = yf.Ticker(sym).history(start=start_date, end=end_date + timedelta(days=1), interval=interval)
    #             if df.empty:
    #                 continue

    #             # Group by date to track daily data
    #             df["date"] = df.index.date
    #             daily_data = []
                
    #             for date, day_data in df.groupby("date"):
                    
    #                 if len(day_data) <= 10:
    #                     continue
    #                 day_after_10 = day_data.iloc[11:]
    #                 high = day_after_10["High"].max()
    #                 current = day_data["Close"].iloc[-1]
    #                 drop = (high - current) / high * 100
    #                 daily_data.append((date, current, high, drop))
                
    #             if not daily_data:
    #                 continue
                
    #             # Filter by threshold and calculate averages
    #             filtered_data = [d for d in daily_data if d[3] >= threshold]
    #             if not filtered_data:
    #                 continue
                
    #             avg_drop = sum(d[3] for d in filtered_data) / len(filtered_data)
    #             avg_high = sum(d[2] for d in filtered_data) / len(filtered_data)
    #             avg_current = sum(d[1] for d in filtered_data) / len(filtered_data)
                
    #             # Add parent row with summary
    #             parent = self.add_parent_row(self.tree, 
    #                                         (sym, f"${avg_current:.2f}", f"${avg_high:.2f}", f"{avg_drop:.2f}%", f"{avg_drop:.2f}%"),
    #                                         3, threshold, reverse=True)
                
    #             # Add child rows with daily data
    #             for date, current, high, drop in filtered_data:
    #                 self.add_child_row(self.tree, parent, (f"  {date}", f"${current:.2f}", f"${high:.2f}", f"{drop:.2f}%", ""))
                
    #         except Exception as e:
    #             print(f"Error processing {sym}: {str(e)}")
        
    #     self.update_progress(total_symbols, total_symbols)
    #     self.reset_progress(success=True)


class EarlySessionTab(BaseTab):
    """Tab 3: Early Session Performance Analyzer with Opening Cross Analysis"""
    
    def __init__(self, notebook, universe, app):
        super().__init__(notebook, universe, app)
        self.stored_data = {}  # Store data for view mode switching
        self.start_time_var = tk.StringVar(value="09:40")  # Default start time
        self.build_ui()

    def build_ui(self):
        controls = self.create_control_frame("Dynamic Anchor Analysis")
        
        # Start Time input
        tk.Label(controls, text="Start Time:", bg="#ffffff", font=("Helvetica", 10)).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        start_time_entry = tk.Entry(controls, textvariable=self.start_time_var, width=10, font=("Helvetica", 10))
        start_time_entry.grid(row=0, column=1, padx=5, pady=5)
        self.create_help_button(controls, "start_time", row=0, column=2)
        
        # Update description label dynamically
        self.desc_label = tk.Label(controls, text="", bg="#ffffff", font=("Helvetica", 9), fg="#64748b")
        self.desc_label.grid(row=0, column=3, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self._update_description()
        
        # Bind to update description and column headers when time changes
        def update_all():
            self._update_description()
            self._update_column_headers()
        
        start_time_entry.bind('<FocusOut>', lambda e: update_all())
        start_time_entry.bind('<Return>', lambda e: update_all())
        
        # Analyze button with help
        analyze_btn_frame = tk.Frame(controls, bg="#ffffff")
        analyze_btn_frame.grid(row=1, column=0, columnspan=3, padx=15, pady=10, sticky=tk.W)
        tk.Button(analyze_btn_frame, text="📊 Analyze", bg="#3b82f6", fg="white",
                 font=("Helvetica", 10, "bold"), command=self.run, padx=20, pady=8,
                 relief="flat", cursor="hand2").pack(side=tk.LEFT)
        self.create_help_button(analyze_btn_frame, "run_calculate")
        
        # Add date and interval controls
        self.create_date_interval_controls(self.frame)
        
        self.create_progress_bar()
        
        # Unified column model so we can show different subsets per view mode.
        # Column headers will be updated dynamically based on start time
        start_time = self.start_time_var.get()
        self.columns = (
            "Symbol",
            "Date",
            f"Price at {start_time}",  # Dynamic column name
            "Indication",
            "Highest value",
            "Lowest value",
            "Direction",
            "% Gain",
            "Remarks",
        )
        self.tree = self.create_treeview(self.columns)

        # Direction-based styling (green for HIGH, red for LOW)
        self.tree.tag_configure(
            "dir_high",
            background="#dcfce7",  # greenish
            foreground="#065f46",
        )
        self.tree.tag_configure(
            "dir_low",
            background="#fee2e2",  # reddish
            foreground="#991b1b",
        )
    
    def _update_description(self):
        """Update the description label with current start time"""
        start_time = self.start_time_var.get()
        self.desc_label.config(text=f"Anchors at {start_time}, then compares post-{start_time} highs/lows vs that price")
    
    def _update_column_headers(self):
        """Update column headers to reflect current start time"""
        start_time = self.start_time_var.get()
        # Rebuild columns with new start time
        self.columns = (
            "Symbol",
            "Date",
            f"Price at {start_time}",
            "Indication",
            "Highest value",
            "Lowest value",
            "Direction",
            "% Gain",
            "Remarks",
        )
        # Update the column header if tree exists
        if hasattr(self, 'tree') and self.tree:
            try:
                # Find the price column (should be index 2 in data columns)
                price_col = self.columns[2]
                self.tree.heading(price_col, text=price_col)
            except Exception as e:
                print(f"Warning: Could not update column header: {e}")
    
    def _parse_start_time(self):
        """Parse start time string and return as HH:MM format"""
        time_str = self.start_time_var.get().strip()
        # Handle various formats: "9:40", "09:40", "9:40 AM", "09:40am", etc.
        time_str = time_str.upper().replace("AM", "").replace("PM", "").strip()
        try:
            # Try parsing as HH:MM
            parts = time_str.split(":")
            if len(parts) == 2:
                hour = int(parts[0])
                minute = int(parts[1])
                # Validate range
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return f"{hour:02d}:{minute:02d}"
        except ValueError:
            pass
        # Default to 09:40 if parsing fails
        messagebox.showwarning("Invalid Time", f"Invalid time format: {time_str}. Using default 09:40")
        self.start_time_var.set("09:40")
        return "09:40"
    
    def _validate_interval(self):
        """
        Ensure we are using a 1-minute or 5-minute interval so that the start time
        is properly captured.
        """
        interval = self.app.interval_var.get().strip()
        if interval not in ("1m", "5m"):
            messagebox.showwarning(
                "Interval Adjusted",
                "Early-Session analysis requires a 1m or 5m interval. "
                "Switching interval to 1m.",
            )
            interval = "1m"
            self.app.interval_var.set(interval)
        return interval

    def run(self):
        """Run anchor analysis for the active symbol universe using dynamic start time."""
        # Rebuild treeview with updated columns if start time changed
        start_time = self.start_time_var.get()
        current_price_col = self.columns[2] if len(self.columns) > 2 else ""
        if f"Price at {start_time}" != current_price_col:
            # Recreate treeview with new column names
            self.tree.destroy()
            self.columns = (
                "Symbol",
                "Date",
                f"Price at {start_time}",
                "Indication",
                "Highest value",
                "Lowest value",
                "Direction",
                "% Gain",
                "Remarks",
            )
            self.tree = self.create_treeview(self.columns)
            # Reapply styling
            self.tree.tag_configure("dir_high", background="#dcfce7", foreground="#065f46")
            self.tree.tag_configure("dir_low", background="#fee2e2", foreground="#991b1b")
        
        # Use active_symbols if available, otherwise load from CSV
        symbols = self.app.active_symbols if self.app.active_symbols else self.universe.load_symbols()
        self._run_analysis(symbols)

    def _run_analysis(self, symbols):
        """Core analysis routine shared by normal and sample-test runs."""
        self.tree.delete(*self.tree.get_children())
        self.expanded_items.clear()
        total_symbols = len(symbols)
        
        if not symbols:
            messagebox.showwarning("No Symbols", "Please load symbols first")
            return
        
        start_date, end_date = self.get_date_range()
        self.stored_data = {}

        interval = self._validate_interval()
        start_time = self._parse_start_time()  # Get dynamic start time
        
        for idx, sym in enumerate(symbols):
            self.update_progress(idx, total_symbols)
            try:
                # Fetch data using date range
                ticker = yf.Ticker(sym)
                df = ticker.history(start=start_date, end=end_date + timedelta(days=1), interval=interval)
                
                if df.empty:
                    continue
                
                df["date"] = df.index.date
                daily_records = []
                
                for d, day_df in df.groupby("date"):
                    # Filter for regular market hours (09:30 - 16:00)
                    day_df = day_df.between_time("09:30", "16:00")

                    if day_df.empty:
                        continue

                    # Anchor price at the user-defined start time
                    anchor_bar = day_df.between_time(start_time, start_time)
                    if anchor_bar.empty:
                        # If start time bar is missing (e.g. data gaps), skip this day
                        continue

                    anchor_ts = anchor_bar.index[0]
                    price_at_start = anchor_bar["Close"].iloc[0]

                    # Post-start-time session (including the start time bar)
                    post_df = day_df[day_df.index >= anchor_ts]
                    if post_df.empty:
                        continue

                    post_high = post_df["High"].max()
                    post_low = post_df["Low"].min()

                    # Track timestamps for highest and lowest post-start-time values
                    high_row = post_df[post_df["High"] == post_high].iloc[0]
                    low_row = post_df[post_df["Low"] == post_low].iloc[0]
                    high_time = high_row.name.strftime("%H:%M")
                    low_time = low_row.name.strftime("%H:%M")

                    # Dynamic selection logic:
                    # If post-session high is above the start time price, treat the move as HIGH.
                    # Otherwise, treat it as LOW, using the post-session low.
                    if post_high > price_at_start:
                        selected_price = post_high
                        direction = "HIGH"
                    else:
                        selected_price = post_low
                        direction = "LOW"

                    pct_gain = (
                        (selected_price - price_at_start) / price_at_start * 100 if price_at_start > 0 else 0
                    )

                    daily_records.append(
                        {
                            "date": d,
                            "price_at_start": price_at_start,
                            "post_high": post_high,
                            "post_low": post_low,
                            "selected_price": selected_price,
                            "direction": direction,
                            "high_time": high_time,
                            "low_time": low_time,
                            "pct_gain": pct_gain,
                        }
                    )
                
                if not daily_records:
                    continue
                
                # Store data for view mode switching
                self.stored_data[sym] = daily_records

                # Build UI rows for this symbol
                self._add_symbol_rows(sym, daily_records)
                
            except Exception as e:
                print(f"Error processing {sym}: {str(e)}")
        
        self.update_progress(total_symbols, total_symbols)
        self.reset_progress(success=True)

    def _compute_summary(self, daily_records):
        """Compute aggregated metrics used for the collapsed/summary row."""
        n = len(daily_records)
        if n == 0:
            return None

        avg_start = sum(r["price_at_start"] for r in daily_records) / n
        avg_high = sum(r["post_high"] for r in daily_records) / n
        avg_low = sum(r["post_low"] for r in daily_records) / n

        # Collapsed-row selection logic
        if avg_high > avg_start:
            summary_direction = "HIGH"
            summary_price = avg_high
        else:
            summary_direction = "LOW"
            summary_price = avg_low

        pct_gain = (
            (summary_price - avg_start) / avg_start * 100 if avg_start > 0 else 0
        )

        return {
            "avg_start": avg_start,
            "avg_high": avg_high,
            "avg_low": avg_low,
            "summary_price": summary_price,
            "summary_direction": summary_direction,
            "pct_gain": pct_gain,
            "days": n,
        }

    def _add_symbol_rows(self, sym, daily_records):
        """
        Add the parent (collapsed) row and all child (per-day) rows for a symbol,
        applying direction-based coloring.
        """
        summary = self._compute_summary(daily_records)
        if summary is None:
            return

        # Collapsed/summary parent row
        parent_values = (
            sym,                                   # Symbol
            f"{summary['days']} days",             # Date (summary)
            f"${summary['avg_start']:.2f}",        # Price at start time
            summary["summary_direction"],          # Indication
            f"${summary['avg_high']:.2f}",         # Highest value (avg)
            f"${summary['avg_low']:.2f}",          # Lowest value (avg)
            "",                                    # Direction (not used on parent)
            f"{summary['pct_gain']:.2f}%",         # % Gain
            "",                                    # Remarks
        )

        parent = self.add_parent_row(self.tree, parent_values)

        # Apply collapsed-row color purely based on summary direction
        if summary["summary_direction"] == "HIGH":
            self.tree.item(parent, tags=("dir_high",))
        else:
            self.tree.item(parent, tags=("dir_low",))

        # Detailed child rows (per trading day)
        for record in daily_records:
            remarks = (
                f"HIGH: ${record['post_high']:.2f} @ {record['high_time']} | "
                f"LOW: ${record['post_low']:.2f} @ {record['low_time']}"
            )

            child_values = (
                f"  {record['date']}",                              # Symbol column (#0)
                str(record["date"]),                                # Date
                f"${record['price_at_start']:.2f}",                 # Price at start time
                record["direction"],                                # Indication
                f"${record['post_high']:.2f} @ {record['high_time']}",  # Highest value
                f"${record['post_low']:.2f} @ {record['low_time']}",    # Lowest value
                record["direction"],                                # Direction
                f"{record['pct_gain']:.2f}%",                       # % Gain
                remarks,                                            # Remarks (for average view)
            )

            child = self.add_child_row(self.tree, parent, child_values)

            # Apply per-row coloring based on the day-level selection
            if record["direction"] == "HIGH":
                self.tree.item(child, tags=("dir_high",))
            else:
                self.tree.item(child, tags=("dir_low",))
    
    def toggle_view_mode(self):
        """Switch between detailed and average views by showing/hiding columns."""
        mode = self.view_mode.get()

        if mode == "average":
            # Hide detailed-only columns
            for col in ("Highest value", "Lowest value", "Direction"):
                self.tree.column(col, width=0, stretch=False)

            # Key columns for average view
            start_time = self.start_time_var.get()
            price_col_name = f"Price at {start_time}"
            for col, width in [
                ("Date", 120),
                (price_col_name, 120),
                ("Indication", 100),
                ("% Gain", 90),
                ("Remarks", 260),
            ]:
                self.tree.column(col, width=width, stretch=True)

            # Collapse parents; user can expand to see row-level remarks
            for parent in self.tree.get_children():
                self.tree.item(parent, open=False)
        else:
            # Detailed view: show all analytical columns; remarks is optional.
            start_time = self.start_time_var.get()
            price_col_name = f"Price at {start_time}"
            for col, width in [
                ("Date", 120),
                (price_col_name, 120),
                ("Indication", 90),
                ("Highest value", 170),
                ("Lowest value", 170),
                ("Direction", 90),
                ("% Gain", 90),
            ]:
                self.tree.column(col, width=width, stretch=True)

            # Keep remarks narrow but present
            self.tree.column("Remarks", width=40, stretch=False)


class ReversalCycleTab(BaseTab):
    """Tab 4: n% Price Reversal Cycle Counter"""
    
    def __init__(self, notebook, universe, app):
        super().__init__(notebook, universe, app)
        self.n_pct = tk.DoubleVar(value=2.0)
        self.build_ui()

    def build_ui(self):
        controls = self.create_control_frame("Reversal Cycle Settings")
        
        tk.Label(controls, text="Reversal %:", bg="#ffffff", font=("Helvetica", 10)).grid(row=0, column=0, padx=5)
        tk.Entry(controls, textvariable=self.n_pct, width=8, font=("Helvetica", 10)).grid(row=0, column=1, padx=5)
        self.create_help_button(controls, "reversal_pct", row=0, column=2)
        
        cycle_btn_frame = tk.Frame(controls, bg="#ffffff")
        cycle_btn_frame.grid(row=0, column=3, padx=15)
        tk.Button(cycle_btn_frame, text="🔄 Count Cycles", bg="#ef4444", fg="white",
                 font=("Helvetica", 10, "bold"), command=self.run, padx=20, pady=8,
                 relief="flat", cursor="hand2").pack(side=tk.LEFT)
        self.create_help_button(cycle_btn_frame, "run_calculate")
        
        # Add date and interval controls
        self.create_date_interval_controls(self.frame)
        
        self.create_progress_bar()
        
        self.tree = self.create_treeview(("Symbol", "Total Cycles", "Avg Cycles/Day", "Daily Breakdown"))

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