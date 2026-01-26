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
            tab = TabClass(notebook, self.universe)
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


class BaseTab:
    """Base class for analysis tabs with common UI elements"""
    
    def __init__(self, notebook, universe):
        self.universe = universe
        self.frame = tk.Frame(notebook, bg="#f8fafc")
        self.is_running = False

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

    def create_treeview(self, columns):
        """Create results treeview"""
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


class SwingCounterTab(BaseTab):
    """Tab 1: Daily Stock Swing Counter"""
    
    def __init__(self, notebook, universe):
        super().__init__(notebook, universe)
        self.swing_pct = tk.DoubleVar(value=5.0)
        self.build_ui()

    def build_ui(self):
        controls = self.create_control_frame("Swing Analysis Settings")
        
        tk.Label(controls, text="Swing %:", bg="#ffffff", font=("Helvetica", 10)).grid(row=0, column=0, padx=5)
        tk.Entry(controls, textvariable=self.swing_pct, width=10, font=("Helvetica", 10)).grid(row=0, column=1, padx=5)
        
        tk.Button(controls, text="▶ Run Analysis", bg="#3b82f6", fg="white",
                 font=("Helvetica", 10, "bold"), command=self.run, padx=20, pady=8,
                 relief="flat", cursor="hand2").grid(row=0, column=2, padx=15)
        
        self.tree = self.create_treeview(("Symbol", "Up Swings", "Down Swings", "Total Swings"))

    def run(self):
        self.tree.delete(*self.tree.get_children())
        symbols = self.universe.load_symbols()
        
        for sym in symbols:
            try:
                data = yf.Ticker(sym).history(period="1d", interval="1m")
                if data.empty:
                    continue

                prices = data["Close"].values
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

                total = up + down
                self.add_colored_row(self.tree, (sym, up, down, total), 3, 5)
                
            except Exception as e:
                print(f"Error processing {sym}: {str(e)}")


class DownFromHighTab(BaseTab):
    """Tab 2: n% Down From Day's High Scanner"""
    
    def __init__(self, notebook, universe):
        super().__init__(notebook, universe)
        self.n_pct = tk.DoubleVar(value=3.0)
        self.build_ui()

    def build_ui(self):
        controls = self.create_control_frame("Scanner Settings")
        
        tk.Label(controls, text="% Down From High:", bg="#ffffff", font=("Helvetica", 10)).grid(row=0, column=0, padx=5)
        tk.Entry(controls, textvariable=self.n_pct, width=10, font=("Helvetica", 10)).grid(row=0, column=1, padx=5)
        
        tk.Button(controls, text="🔍 Scan Now", bg="#10b981", fg="white",
                 font=("Helvetica", 10, "bold"), command=self.run, padx=20, pady=8,
                 relief="flat", cursor="hand2").grid(row=0, column=2, padx=15)
        
        self.tree = self.create_treeview(("Symbol", "Current Price", "Day High", "% Down"))

    def run(self):
        self.tree.delete(*self.tree.get_children())
        symbols = self.universe.load_symbols()
        threshold = self.n_pct.get()
        
        for sym in symbols:
            try:
                df = yf.Ticker(sym).history(period="1d", interval="1m")
                if df.empty:
                    continue

                high = df["High"].max()
                current = df["Close"].iloc[-1]
                drop = (high - current) / high * 100

                if drop >= threshold:
                    self.add_colored_row(self.tree, 
                                       (sym, f"${current:.2f}", f"${high:.2f}", f"{drop:.2f}%"),
                                       3, threshold, reverse=True)
            except Exception as e:
                print(f"Error processing {sym}: {str(e)}")


class EarlySessionTab(BaseTab):
    """Tab 3: Early Session Performance Analyzer"""
    
    def __init__(self, notebook, universe):
        super().__init__(notebook, universe)
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
        
        self.tree = self.create_treeview(("Symbol", "Date", "10-Min Price", "Day High", "% Gain"))

    def run(self):
        self.tree.delete(*self.tree.get_children())
        symbols = self.universe.load_symbols()
        days = min(self.days.get(), MAX_DAYS_1M)
        
        if self.days.get() > MAX_DAYS_1M:
            messagebox.showwarning("Limit Exceeded", 
                                  f"Yahoo Finance allows max {MAX_DAYS_1M} days for 1-minute data. Using {MAX_DAYS_1M} days.")
        
        for sym in symbols:
            try:
                df = yf.Ticker(sym).history(period=f"{days}d", interval="1m")
                if df.empty:
                    continue

                df["date"] = df.index.date
                for d, day in df.groupby("date"):
                    if len(day) < 11:
                        continue
                    
                    p10 = day.iloc[10]["Close"]
                    high = day["High"].max()
                    pct = (high - p10) / p10 * 100
                    
                    self.add_colored_row(self.tree,
                                       (sym, d, f"${p10:.2f}", f"${high:.2f}", f"{pct:.2f}%"),
                                       4, 0)
            except Exception as e:
                print(f"Error processing {sym}: {str(e)}")


class ReversalCycleTab(BaseTab):
    """Tab 4: n% Price Reversal Cycle Counter"""
    
    def __init__(self, notebook, universe):
        super().__init__(notebook, universe)
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
        
        self.tree = self.create_treeview(("Symbol", "Total Cycles", "Avg Cycles/Day"))

    def run(self):
        self.tree.delete(*self.tree.get_children())
        symbols = self.universe.load_symbols()
        days = min(self.days.get(), MAX_DAYS_1M)
        
        if self.days.get() > MAX_DAYS_1M:
            messagebox.showwarning("Limit Exceeded",
                                  f"Yahoo Finance allows max {MAX_DAYS_1M} days for 1-minute data. Using {MAX_DAYS_1M} days.")
        
        for sym in symbols:
            try:
                df = yf.Ticker(sym).history(period=f"{days}d", interval="1m")
                if df.empty:
                    continue

                cycles = 0
                ref = df["Open"].iloc[0]
                direction = None

                for p in df["Close"]:
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

                avg_cycles = cycles / days if days > 0 else 0
                self.add_colored_row(self.tree, (sym, cycles, f"{avg_cycles:.2f}"), 1, 5)
                
            except Exception as e:
                print(f"Error processing {sym}: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = StockAnalysisApp(root)
    root.mainloop()
