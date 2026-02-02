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
        
        btn_frame = tk.Frame(toolbar, bg="#e2e8f0")
        btn_frame.pack()
        
        buttons = [
            ("📁 Upload CSV", self.upload_csv, "#3b82f6"),
            ("➕ Add Symbol", self.add_symbol, "#10b981"),
            ("✏️ Edit Symbols", self.edit_symbols, "#f59e0b"),
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
                     padx=15,
                     pady=8,
                     cursor="hand2").pack(side=tk.LEFT, padx=5)
            
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
* **Expand/Collapse:** Double click on the symbol name in the results table to expand/collapse detailed daily data under each symbol.

---

## 📑 Analysis Tabs

### 🔄 Swing Counter

Tracks intraday price swings based on your custom **Swing %**. It identifies moves that deviate from the last reference point by your specified threshold using the selected interval.

### 📉 n% Down From High

A real-time "dip" scanner. Filters for symbols currently trading at least **n% below** their daily high. Perfect for spotting intraday pullbacks.

### ⏰ Early-Session Performance

Analyzes the "opening drive." It compares the price at the **10th minute** of the session to the daily high to gauge early momentum.

* *Uses **Days to Analyze** for historical context.*

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
                                            mode='determinate')
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
        item = tree.insert("", tk.END, values=values, open=False)
        
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
        
        tk.Button(controls, text="▶ Run Analysis", bg="#3b82f6", fg="white",
                 font=("Helvetica", 10, "bold"), command=self.run, padx=20, pady=8,
                 relief="flat", cursor="hand2").grid(row=0, column=2, padx=15)
        
        self.create_progress_bar()
        
        self.tree = self.create_treeview(("Symbol", "Up Swings", "Down Swings", "Total Swings", "Avg Daily"))

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
        
        self.update_progress(total_symbols, total_symbols)
        self.reset_progress()


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
        
        self.tree = self.create_treeview(("Symbol", "Current Price", "Day High", "% Down", "Avg %"))

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
        
        self.update_progress(total_symbols, total_symbols)
        self.reset_progress()


class EarlySessionTab(BaseTab):
    """Tab 3: Early Session Performance Analyzer"""
    
    def __init__(self, notebook, universe, app):
        super().__init__(notebook, universe, app)
        self.days = tk.IntVar(value=5)
        self.build_ui()

    def build_ui(self):
        controls = self.create_control_frame("Analysis Settings (Max 7 days due to Yahoo Finance API limits)")
        
        tk.Label(controls, text="Days to Analyze:", bg="#ffffff", font=("Helvetica", 10)).grid(row=0, column=0, padx=5)
        
        spinbox = tk.Spinbox(controls, from_=1, to=MAX_DAYS_1M, textvariable=self.days, 
                            width=8, font=("Helvetica", 10))
        spinbox.grid(row=0, column=1, padx=5)
        
        tk.Button(controls, text="📊 Analyze", bg="#3b82f6", fg="white",
                 font=("Helvetica", 10, "bold"), command=self.run, padx=20, pady=8,
                 relief="flat", cursor="hand2").grid(row=0, column=2, padx=15)
        
        self.create_progress_bar()
        
        self.tree = self.create_treeview(("Symbol", "Date", "10-Min Price", "Day High", "% Gain", "Avg %"))

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
                daily_records = []
                
                for d, day in df.groupby("date"):
                    if len(day) < 12:
                        continue
                    p10 = day.iloc[10]["Close"]
                    
                    day_after_10 = day.iloc[11:]
                    high = day_after_10["High"].max()
                    pct = (high - p10) / p10 * 100
                    daily_records.append((d, p10, high, pct))
                
                if not daily_records:
                    continue
                
                # Calculate averages
                avg_pct = sum(r[3] for r in daily_records) / len(daily_records)
                avg_p10 = sum(r[1] for r in daily_records) / len(daily_records)
                avg_high = sum(r[2] for r in daily_records) / len(daily_records)
                
                # Add parent row with summary
                parent = self.add_parent_row(self.tree,
                                            (sym, "SUMMARY", f"${avg_p10:.2f}", f"${avg_high:.2f}", f"{avg_pct:.2f}%", f"{avg_pct:.2f}%"),
                                            4, 0)
                
                # Add child rows with daily data
                for d, p10, high, pct in daily_records:
                    self.add_child_row(self.tree, parent, (f"  {d}", f"{d}", f"${p10:.2f}", f"${high:.2f}", f"{pct:.2f}%", ""))
                    
            except Exception as e:
                print(f"Error processing {sym}: {str(e)}")
        
        self.update_progress(total_symbols, total_symbols)
        self.reset_progress()


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
        
        self.tree = self.create_treeview(("Symbol", "Total Cycles", "Avg Cycles/Day", "Daily Breakdown"))

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
        
        self.update_progress(total_symbols, total_symbols)
        self.reset_progress()




if __name__ == "__main__":
    root = tk.Tk()
    app = StockAnalysisApp(root)
    root.mainloop()