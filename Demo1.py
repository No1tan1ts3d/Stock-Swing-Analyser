"""
Daily Stock Swing Counter
A GUI application to analyze intraday price swings for S&P 500 stocks
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import threading
import csv
import pandas as pd

class StockSwingCounter:
    def __init__(self, root):
        self.root = root
        self.root.title("Daily Stock Swing Counter")
        self.root.geometry("1400x800")
        self.root.configure(bg="#1e293b")
        
        # Variables
        self.swing_percent = tk.DoubleVar(value=5.0)
        self.is_analyzing = False
        self.results = []
        self.period = tk.StringVar(value='1d')  
        self.interval = tk.StringVar(value='1m')  
        self.stop_analysis = False 
        
        # S&P 500 stocks (full list)
        self.sp500_stocks = self.get_sp500_symbols()
        
        # Create GUI
        self.create_widgets()
        
    def get_sp500_symbols(self):
        """
        Get S&P 500 stock symbols
        Note: You can enhance this by downloading the full list from Wikipedia
        """
        """Fetch S&P 500 symbols from Wikipedia"""
        
        try:
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            tables = pd.read_html(url)
            sp500_table = tables[0]
            return sp500_table['Symbol'].tolist()
        except:
        # Sample of S&P 500 stocks
            return [
                'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'GOOG', 'BRK-B', 'TSLA', 'UNH',
                'XOM', 'LLY', 'JPM', 'JNJ', 'V', 'PG', 'MA', 'AVGO', 'HD', 'CVX',
                'MRK', 'ABBV', 'COST', 'PEP', 'ADBE', 'KO', 'WMT', 'CRM', 'MCD', 'CSCO',
                'ACN', 'TMO', 'ABT', 'LIN', 'NFLX', 'NKE', 'DIS', 'TXN', 'VZ', 'WFC',
                'DHR', 'CMCSA', 'PM', 'NEE', 'AMD', 'ORCL', 'COP', 'BMY', 'INTC', 'UPS',
                'RTX', 'QCOM', 'HON', 'INTU', 'UNP', 'AMGN', 'T', 'PFE', 'SPGI', 'BA',
                'AMAT', 'LOW', 'DE', 'CAT', 'GE', 'SBUX', 'ELV', 'GS', 'AXP', 'BLK',
                'SYK', 'BKNG', 'MDLZ', 'ADI', 'GILD', 'PLD', 'ISRG', 'ADP', 'TJX', 'MMC',
                'VRTX', 'CI', 'LRCX', 'C', 'SCHW', 'AMT', 'REGN', 'MO', 'CB', 'ZTS',
                'CVS', 'SO', 'NOC', 'PYPL', 'DUK', 'ETN', 'FI', 'BDX', 'PGR', 'BSX'
            ]
    
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Header Frame
        header_frame = tk.Frame(self.root, bg="#334155", pady=20)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = tk.Label(
            header_frame,
            text="📊 Daily Stock Swing Counter",
            font=("Helvetica", 24, "bold"),
            bg="#334155",
            fg="#f1f5f9"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="Analyze intraday price swings across S&P 500 stocks",
            font=("Helvetica", 12),
            bg="#334155",
            fg="#94a3b8"
        )
        subtitle_label.pack()
        
        # Control Frame
        control_frame = tk.Frame(self.root, bg="#1e293b")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Left side - Input
        input_frame = tk.LabelFrame(
            control_frame,
            text="Settings",
            font=("Helvetica", 12, "bold"),
            bg="#334155",
            fg="#f1f5f9",
            padx=20,
            pady=15
        )
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(
            input_frame,
            text="Swing Percentage (%):",
            font=("Helvetica", 11),
            bg="#334155",
            fg="#f1f5f9"
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        swing_entry = tk.Entry(
            input_frame,
            textvariable=self.swing_percent,
            font=("Helvetica", 11),
            width=15,
            bg="#475569",
            fg="#f1f5f9",
            insertbackground="#f1f5f9"
        )
        swing_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Period selection
        tk.Label(
            input_frame,
            text="Period:",
            font=("Helvetica", 11),
            bg="#334155",
            fg="#f1f5f9"
        ).grid(row=2, column=0, sticky=tk.W, pady=5)

        period_combo = ttk.Combobox(
            input_frame,
            textvariable=self.period,
            values=['1d', '5d', '1mo', '3mo', '6mo', '1y'],
            font=("Helvetica", 11),
            width=13,
            state='readonly'
        )
        period_combo.grid(row=2, column=1, padx=10, pady=5)

        # Interval selection
        tk.Label(
            input_frame,
            text="Interval:",
            font=("Helvetica", 11),
            bg="#334155",
            fg="#f1f5f9"
        ).grid(row=3, column=0, sticky=tk.W, pady=5)

        interval_combo = ttk.Combobox(
            input_frame,
            textvariable=self.interval,
            values=['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d'],
            font=("Helvetica", 11),
            width=13,
            state='readonly'
        )
        interval_combo.grid(row=3, column=1, padx=10, pady=5)
        
        tk.Label(
            input_frame,
            text="Number of stocks to analyze:",
            font=("Helvetica", 11),
            bg="#334155",
            fg="#f1f5f9"
        ).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.stock_count_label = tk.Label(
            input_frame,
            text=f"{len(self.sp500_stocks)} stocks",
            font=("Helvetica", 11, "bold"),
            bg="#334155",
            fg="#60a5fa"
        )
        self.stock_count_label.grid(row=4, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Right side - Actions
        action_frame = tk.LabelFrame(
            control_frame,
            text="Actions",
            font=("Helvetica", 12, "bold"),
            bg="#334155",
            fg="#f1f5f9",
            padx=20,
            pady=15
        )
        action_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.run_button = tk.Button(
            action_frame,
            text="▶ Run Analysis",
            command=self.start_analysis,
            font=("Helvetica", 12, "bold"),
            bg="#3b82f6",
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2",
            relief=tk.RAISED
        )
        self.run_button.grid(row=0, column=0, padx=5, pady=5, sticky=tk.EW)

        # STOP BUTTON
        self.stop_button = tk.Button(
            action_frame,
            text="⏹ Stop Analysis",
            command=self.stop_analysis_process,
            font=("Helvetica", 12, "bold"),
            bg="#ef4444",
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2",
            relief=tk.RAISED,
            state=tk.DISABLED  # Initially disabled
        )
        self.stop_button.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        clear_button = tk.Button(
            action_frame,
            text="🔄 Clear Results",
            command=self.clear_results,
            font=("Helvetica", 11),
            bg="#64748b",
            fg="white",
            padx=15,
            pady=8,
            cursor="hand2"
        )
        clear_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.EW)
        
        export_button = tk.Button(
            action_frame,
            text="💾 Export CSV",
            command=self.export_to_csv,
            font=("Helvetica", 11),
            bg="#10b981",
            fg="white",
            padx=15,
            pady=8,
            cursor="hand2"
        )
        export_button.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.EW)
        
        # Progress Frame
        self.progress_frame = tk.Frame(self.root, bg="#334155")
        self.progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="Ready to analyze",
            font=("Helvetica", 10),
            bg="#334155",
            fg="#94a3b8"
        )
        self.progress_label.pack(side=tk.LEFT, padx=10)
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Results Frame
        results_frame = tk.Frame(self.root, bg="#1e293b")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create Treeview with scrollbars
        tree_scroll_y = tk.Scrollbar(results_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_scroll_x = tk.Scrollbar(results_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree = ttk.Treeview(
            results_frame,
            columns=("Symbol", "Market Cap", "Current Price", "Up Swings", "Down Swings", "Total Swings", "Volatility"),
            show="headings",
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            height=20
        )
        
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        
        # Define columns
        self.tree.heading("Symbol", text="Symbol")
        self.tree.heading("Market Cap", text="Market Cap")
        self.tree.heading("Current Price", text="Current Price")
        self.tree.heading("Up Swings", text="↑ Up Swings")
        self.tree.heading("Down Swings", text="↓ Down Swings")
        self.tree.heading("Total Swings", text="Total Swings")
        self.tree.heading("Volatility", text="Volatility")
        
        # Set column widths
        self.tree.column("Symbol", width=100, anchor=tk.CENTER)
        self.tree.column("Market Cap", width=150, anchor=tk.CENTER)
        self.tree.column("Current Price", width=120, anchor=tk.CENTER)
        self.tree.column("Up Swings", width=120, anchor=tk.CENTER)
        self.tree.column("Down Swings", width=120, anchor=tk.CENTER)
        self.tree.column("Total Swings", width=120, anchor=tk.CENTER)
        self.tree.column("Volatility", width=120, anchor=tk.CENTER)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Style the treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#334155",
            foreground="#f1f5f9",
            fieldbackground="#334155",
            borderwidth=0
        )
        style.configure("Treeview.Heading", background="#1e293b", foreground="#f1f5f9", font=("Helvetica", 10, "bold"))
        style.map("Treeview", background=[("selected", "#3b82f6")])
    
    def fetch_stock_data(self, symbol):
        """
        Fetch intraday stock data from Yahoo Finance
        Returns: tuple (market_cap, current_price, intraday_data)
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current price and market cap
            info = ticker.info
            market_cap = info.get('marketCap', 0)
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            # Fetch intraday data (1-minute intervals for today)
            # Note: Yahoo Finance may limit historical intraday data
            # Fetch intraday data with user-specified period and interval
            period = self.period.get()
            interval = self.interval.get()
            intraday_data = ticker.history(period=period, interval=interval)

            return market_cap, current_price, intraday_data
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return None, None, None
    
    def detect_swings(self, price_data, swing_threshold):
        """
        Detect price swings in intraday data
        
        Algorithm:
        1. Start from the first price point
        2. Track local highs and lows
        3. When price moves >= swing_threshold% from a local low, count as up-swing
        4. When price moves >= swing_threshold% from a local high, count as down-swing
        5. Reset tracking point after each swing is detected
        
        Returns: tuple (up_swings, down_swings)
        """
        if price_data is None or len(price_data) == 0:
            return 0, 0
        
        up_swings = 0
        down_swings = 0
        
        # Use closing prices
        prices = price_data['Close'].values
        
        if len(prices) < 2:
            return 0, 0
        
        # Initialize tracking variables
        reference_price = prices[0]  # Starting reference point
        current_high = prices[0]
        current_low = prices[0]
        last_swing_direction = None  # 'up' or 'down'
        
        for price in prices[1:]:
            # Update current high and low
            current_high = max(current_high, price)
            current_low = min(current_low, price)
            
            # Calculate percentage changes from reference
            pct_from_low = ((price - current_low) / current_low) * 100 if current_low > 0 else 0
            pct_from_high = ((current_high - price) / current_high) * 100 if current_high > 0 else 0
            
            # Check for up-swing (price increased >= threshold from local low)
            if pct_from_low >= swing_threshold and last_swing_direction != 'up':
                up_swings += 1
                last_swing_direction = 'up'
                # Reset tracking from this point
                reference_price = price
                current_high = price
                current_low = price
            
            # Check for down-swing (price decreased >= threshold from local high)
            elif pct_from_high >= swing_threshold and last_swing_direction != 'down':
                down_swings += 1
                last_swing_direction = 'down'
                # Reset tracking from this point
                reference_price = price
                current_high = price
                current_low = price
        
        return up_swings, down_swings
    
    def analyze_stock(self, symbol, swing_threshold):
        """
        Analyze a single stock for swings
        Returns: dict with analysis results
        """
        market_cap, current_price, intraday_data = self.fetch_stock_data(symbol)
        
        if market_cap is None:
            return None
        
        up_swings, down_swings = self.detect_swings(intraday_data, swing_threshold)
        total_swings = up_swings + down_swings
        
        # Determine volatility
        if total_swings > 8:
            volatility = "High"
        elif total_swings > 4:
            volatility = "Medium"
        else:
            volatility = "Low"
        
        # Format market cap
        if market_cap >= 1e12:
            market_cap_str = f"${market_cap/1e12:.2f}T"
        elif market_cap >= 1e9:
            market_cap_str = f"${market_cap/1e9:.2f}B"
        elif market_cap >= 1e6:
            market_cap_str = f"${market_cap/1e6:.2f}M"
        else:
            market_cap_str = f"${market_cap:,.0f}"
        
        return {
            'symbol': symbol,
            'market_cap': market_cap_str,
            'current_price': f"${current_price:.2f}" if current_price else "N/A",
            'up_swings': up_swings,
            'down_swings': down_swings,
            'total_swings': total_swings,
            'volatility': volatility,
            'market_cap_raw': market_cap  # For sorting
        }
    
    def run_analysis(self):
        """Run the analysis in a separate thread"""
        swing_threshold = self.swing_percent.get()
        
        if swing_threshold <= 0 or swing_threshold > 100:
            messagebox.showerror("Invalid Input", "Please enter a swing percentage between 0 and 100")
            self.is_analyzing = False
            return
        
        self.results = []
        total_stocks = len(self.sp500_stocks)
        
        self.progress_bar['maximum'] = total_stocks
        self.progress_bar['value'] = 0
        
        for idx, symbol in enumerate(self.sp500_stocks):
            # if not self.is_analyzing:
            #     break
                # Check if stop was requested
            if self.stop_analysis:
                self.progress_label.config(text=f"Analysis stopped by user. Analyzed {len(self.results)} stocks")
                break
            
            # Update progress
            self.progress_label.config(text=f"Analyzing {symbol}... ({idx+1}/{total_stocks})")
            self.progress_label.config(text=f"Analyzing {symbol}... ({idx+1}/{total_stocks}) | Period: {self.period.get()} | Interval: {self.interval.get()}")
            self.progress_bar['value'] = idx + 1
            self.root.update()
            
            # Analyze stock
            result = self.analyze_stock(symbol, swing_threshold)
            
            if result:
                self.results.append(result)
                # Add to treeview in real-time
                self.add_result_to_tree(result)
        
        # Sort results by total swings (descending)
        self.results.sort(key=lambda x: x['total_swings'], reverse=True)
        
        # Refresh tree with sorted results
        self.refresh_tree()
        
        self.progress_label.config(text=f"Analysis complete! Analyzed {len(self.results)} stocks")
        self.is_analyzing = False
        self.stop_analysis = False  
        self.run_button.config(state=tk.NORMAL, text="▶ Run Analysis")
        self.stop_button.config(state=tk.DISABLED)  

        if not self.stop_analysis:  # Only show message if not stopped
            messagebox.showinfo("Analysis Complete", f"Successfully analyzed {len(self.results)} stocks")
    
    def add_result_to_tree(self, result):
        """Add a single result to the treeview"""
        self.tree.insert(
            "",
            tk.END,
            values=(
                result['symbol'],
                result['market_cap'],
                result['current_price'],
                result['up_swings'],
                result['down_swings'],
                result['total_swings'],
                result['volatility']
            ),
            tags=(result['volatility'],)
        )
    
    def refresh_tree(self):
        """Refresh the treeview with sorted results"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add sorted results
        for result in self.results:
            self.add_result_to_tree(result)
    
    def start_analysis(self):
        """Start the analysis process"""
        if self.is_analyzing:
            return
        
        self.is_analyzing = True

        self.stop_analysis = False 
        self.run_button.config(state=tk.DISABLED, text="⏳ Analyzing...")
        self.stop_button.config(state=tk.NORMAL)  

        # Clear previous results
        self.clear_results()
        
        # Run analysis in a separate thread to keep GUI responsive
        analysis_thread = threading.Thread(target=self.run_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()

    def stop_analysis_process(self):
        """Stop the ongoing analysis"""
        if self.is_analyzing:
            self.stop_analysis = True
            self.progress_label.config(text="Stopping analysis...")
            self.stop_button.config(state=tk.DISABLED)
    
    def clear_results(self):
        """Clear all results"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results = []
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Ready to analyze")
    
    def export_to_csv(self):
        """Export results to CSV file"""
        if not self.results:
            messagebox.showwarning("No Data", "No results to export. Please run the analysis first.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"swing_analysis_{self.swing_percent.get()}pct_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='') as csvfile:
                    fieldnames = ['Symbol', 'Market Cap', 'Current Price', 'Up Swings', 'Down Swings', 'Total Swings', 'Volatility']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for result in self.results:
                        writer.writerow({
                            'Symbol': result['symbol'],
                            'Market Cap': result['market_cap'],
                            'Current Price': result['current_price'],
                            'Up Swings': result['up_swings'],
                            'Down Swings': result['down_swings'],
                            'Total Swings': result['total_swings'],
                            'Volatility': result['volatility']
                        })
                
                messagebox.showinfo("Export Successful", f"Results exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Error exporting to CSV: {str(e)}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = StockSwingCounter(root)
    root.mainloop()


if __name__ == "__main__":
    main()