import yfinance as yf
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import time
from datetime import datetime
import threading

class ESSpyTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("UTY CAPITAL ES-SPY Price Tracker")
        self.root.geometry("800x600")  # Increased height to accommodate the calculator
        self.root.configure(bg="#f0f0f0")
        
        # Variables
        self.es_data = pd.DataFrame()
        self.spy_data = pd.DataFrame()
        self.ratio_data = []
        self.timestamps = []
        self.running = False
        self.update_interval = 5 # Fixed at 5 seconds
        self.dark_mode = False
        self.current_ratio = 10.0  # Default ratio
        
        # Create the GUI
        self.create_widgets()
        
        # Start tracking immediately
        self.running = True
        self.update_data_loop_thread = threading.Thread(target=self.update_data_loop)
        self.update_data_loop_thread.daemon = True
        self.update_data_loop_thread.start()
        
    def create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header with title
        header = tk.Label(main_frame, text="UTY CAPITAL ES-SPY Real-Time Tracker", 
                          font=("Arial", 18, "bold"), bg="#f0f0f0")
        header.pack(pady=(0, 10))
        
        # Price display frame
        price_frame = tk.Frame(main_frame, bg="#f0f0f0", relief="ridge", bd=1)
        price_frame.pack(fill="x", pady=5)
        
        # Price display (2x2 grid)
        price_style = {"font": ("Arial", 24, "bold"), "bg": "#f0f0f0"}
        label_style = {"font": ("Arial", 12), "bg": "#f0f0f0"}
        
        # ES price
        tk.Label(price_frame, text="ES Futures", **label_style).grid(row=0, column=0, padx=20, pady=(10, 0))
        self.es_price_label = tk.Label(price_frame, text="--", **price_style)
        self.es_price_label.grid(row=1, column=0, padx=20, pady=(0, 5))
        self.es_change_label = tk.Label(price_frame, text="--", font=("Arial", 10), bg="#f0f0f0")
        self.es_change_label.grid(row=2, column=0, padx=20, pady=(0, 10))
        
        # SPY price
        tk.Label(price_frame, text="SPY ETF", **label_style).grid(row=0, column=1, padx=20, pady=(10, 0))
        self.spy_price_label = tk.Label(price_frame, text="--", **price_style)
        self.spy_price_label.grid(row=1, column=1, padx=20, pady=(0, 5))
        self.spy_change_label = tk.Label(price_frame, text="--", font=("Arial", 10), bg="#f0f0f0")
        self.spy_change_label.grid(row=2, column=1, padx=20, pady=(0, 10))
        
        # Ratio
        tk.Label(price_frame, text="ES/SPY Ratio", **label_style).grid(row=0, column=2, padx=20, pady=(10, 0))
        self.ratio_label = tk.Label(price_frame, text="--", **price_style)
        self.ratio_label.grid(row=1, column=2, padx=20, pady=(0, 5))
        self.ratio_change_label = tk.Label(price_frame, text="--", font=("Arial", 10), bg="#f0f0f0")
        self.ratio_change_label.grid(row=2, column=2, padx=20, pady=(0, 10))
        
        # Last update time and control buttons
        control_frame = tk.Frame(main_frame, bg="#f0f0f0")
        control_frame.pack(fill="x", pady=5)
        
        # Theme toggle button
        self.theme_button = tk.Button(control_frame, text="Dark Mode", 
                                     command=self.toggle_theme, bg="#333", fg="white")
        self.theme_button.pack(side="left", padx=5)
        
        # Clear data button
        clear_button = tk.Button(control_frame, text="Clear Data", 
                               command=self.clear_data)
        clear_button.pack(side="left", padx=5)
        
        # Last update time
        self.time_label = tk.Label(control_frame, text="Last update: --", 
                                  font=("Arial", 10), bg="#f0f0f0")
        self.time_label.pack(side="right")
        
        # Create the chart
        self.chart_frame = tk.Frame(main_frame, bg="#f0f0f0")
        self.chart_frame.pack(fill="both", expand=True, pady=10)
        
        self.create_chart()
        
        # NEW: Price Calculator Frame
        self.create_price_calculator(main_frame)
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Updating every 5 seconds...", 
                                  bd=1, relief=tk.SUNKEN, anchor=tk.W, 
                                  bg="#f0f0f0", font=("Arial", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_price_calculator(self, parent):
        # Price Calculator Frame
        calculator_frame = tk.LabelFrame(parent, text="Price Calculator", 
                                        font=("Arial", 12, "bold"), bg="#f0f0f0", padx=10, pady=10)
        calculator_frame.pack(fill="x", pady=10)
        
        # ES Price Entry
        es_calc_frame = tk.Frame(calculator_frame, bg="#f0f0f0")
        es_calc_frame.pack(side=tk.LEFT, padx=20, fill="x", expand=True)
        
        tk.Label(es_calc_frame, text="ES Price:", font=("Arial", 10), bg="#f0f0f0").pack(side=tk.LEFT)
        self.es_entry = tk.Entry(es_calc_frame, width=10, font=("Arial", 10))
        self.es_entry.pack(side=tk.LEFT, padx=5)
        self.es_calc_button = tk.Button(es_calc_frame, text="Calculate SPY", 
                                       command=lambda: self.calculate_price("es"))
        self.es_calc_button.pack(side=tk.LEFT, padx=5)
        
        # SPY Price Entry
        spy_calc_frame = tk.Frame(calculator_frame, bg="#f0f0f0")
        spy_calc_frame.pack(side=tk.RIGHT, padx=20, fill="x", expand=True)
        
        tk.Label(spy_calc_frame, text="SPY Price:", font=("Arial", 10), bg="#f0f0f0").pack(side=tk.LEFT)
        self.spy_entry = tk.Entry(spy_calc_frame, width=10, font=("Arial", 10))
        self.spy_entry.pack(side=tk.LEFT, padx=5)
        self.spy_calc_button = tk.Button(spy_calc_frame, text="Calculate ES", 
                                        command=lambda: self.calculate_price("spy"))
        self.spy_calc_button.pack(side=tk.LEFT, padx=5)
        
        # Results frame
        result_frame = tk.Frame(calculator_frame, bg="#f0f0f0")
        result_frame.pack(fill="x", pady=10)
        
        # Result display
        tk.Label(result_frame, text="Calculated Result:", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(side=tk.LEFT)
        self.calc_result_label = tk.Label(result_frame, text="--", font=("Arial", 10), bg="#f0f0f0")
        self.calc_result_label.pack(side=tk.LEFT, padx=10)
        
        # Using current ratio checkbox
        self.use_current_ratio_var = tk.BooleanVar(value=True)
        self.use_ratio_check = tk.Checkbutton(calculator_frame, text="Use current market ratio", 
                                             variable=self.use_current_ratio_var,
                                             bg="#f0f0f0", font=("Arial", 9))
        self.use_ratio_check.pack(anchor="w")
        
        # Custom ratio entry
        custom_ratio_frame = tk.Frame(calculator_frame, bg="#f0f0f0")
        custom_ratio_frame.pack(fill="x", pady=5)
        
        tk.Label(custom_ratio_frame, text="Custom Ratio:", font=("Arial", 9), bg="#f0f0f0").pack(side=tk.LEFT)
        self.custom_ratio_entry = tk.Entry(custom_ratio_frame, width=8, font=("Arial", 9))
        self.custom_ratio_entry.pack(side=tk.LEFT, padx=5)
        self.custom_ratio_entry.insert(0, "10.0")  # Default ratio
    
    def calculate_price(self, source):
        try:
            ratio = self.current_ratio
            
            # Use custom ratio if checkbox is not checked
            if not self.use_current_ratio_var.get():
                try:
                    ratio = float(self.custom_ratio_entry.get())
                    if ratio <= 0:
                        raise ValueError("Ratio must be positive")
                except ValueError:
                    messagebox.showerror("Error", "Please enter a valid positive number for custom ratio")
                    return
            
            # Calculate based on source
            if source == "es":
                try:
                    es_price = float(self.es_entry.get())
                    spy_price = es_price / ratio
                    self.calc_result_label.config(text=f"SPY Price: ${spy_price:.2f}")
                    self.spy_entry.delete(0, tk.END)
                    self.spy_entry.insert(0, f"{spy_price:.2f}")
                except ValueError:
                    messagebox.showerror("Error", "Please enter a valid ES price")
            
            elif source == "spy":
                try:
                    spy_price = float(self.spy_entry.get())
                    es_price = spy_price * ratio
                    self.calc_result_label.config(text=f"ES Price: ${es_price:.2f}")
                    self.es_entry.delete(0, tk.END)
                    self.es_entry.insert(0, f"{es_price:.2f}")
                except ValueError:
                    messagebox.showerror("Error", "Please enter a valid SPY price")
                    
        except Exception as e:
            self.calc_result_label.config(text=f"Error: {str(e)}")
    
    def create_chart(self):
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(8, 3))
        self.fig.set_facecolor('#f0f0f0')
        self.ax.set_facecolor('#f5f5f5')
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.fig.tight_layout(pad=3.0)
        
        # Create a twin axis for the ratio
        self.ax_ratio = self.ax.twinx()
        
        # Create the canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)
        
        # Initial plot
        self.update_chart()
    
    def update_data_loop(self):
        while self.running:
            try:
                self.status_bar.config(text="Fetching data...")
                self.fetch_data()
                self.update_display()
                self.update_chart()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.time_label.config(text=f"Last update: {now}")
                self.status_bar.config(text="Updating every 5 seconds...")
                
                # Wait for the next update
                time.sleep(self.update_interval)
                    
            except Exception as e:
                self.status_bar.config(text=f"Error: {str(e)}")
                time.sleep(5)
    
    def fetch_data(self):
        # Fetch ES data
        es_ticker = yf.Ticker("ES=F")
        es_data = es_ticker.history(period="1d", interval="1m")
        
        # Fetch SPY data
        spy_ticker = yf.Ticker("SPY")
        spy_data = spy_ticker.history(period="1d", interval="1m")
        
        if not es_data.empty and not spy_data.empty:
            # Get latest prices
            es_price = es_data["Close"].iloc[-1]
            spy_price = spy_data["Close"].iloc[-1]
            ratio = es_price / spy_price
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Update current ratio (for calculator)
            self.current_ratio = ratio
            
            # Store data
            self.es_data = pd.concat([self.es_data, es_data])
            self.spy_data = pd.concat([self.spy_data, spy_data])
            self.timestamps.append(timestamp)
            self.ratio_data.append(ratio)
            
            # Limit data to last 100 points
            if len(self.timestamps) > 100:
                self.timestamps = self.timestamps[-100:]
                self.ratio_data = self.ratio_data[-100:]
            
            return es_price, spy_price, ratio, timestamp
        else:
            raise Exception("Failed to fetch data")
    
    def update_display(self):
        if not self.es_data.empty and not self.spy_data.empty:
            # Get latest data
            es_price = self.es_data["Close"].iloc[-1]
            spy_price = self.spy_data["Close"].iloc[-1]
            ratio = es_price / spy_price
            
            # Update price display
            self.es_price_label.config(text=f"{es_price:.2f}")
            self.spy_price_label.config(text=f"{spy_price:.2f}")
            self.ratio_label.config(text=f"{ratio:.4f}")
            
            # Update current ratio in custom ratio entry if using current ratio
            if self.use_current_ratio_var.get():
                self.custom_ratio_entry.delete(0, tk.END)
                self.custom_ratio_entry.insert(0, f"{ratio:.4f}")
            
            # Calculate changes
            if len(self.es_data) > 1:
                es_change = es_price - self.es_data["Close"].iloc[-2]
                es_change_pct = (es_change / self.es_data["Close"].iloc[-2]) * 100
                es_change_color = "green" if es_change >= 0 else "red"
                self.es_change_label.config(
                    text=f"({es_change_pct:+.2f}%)",
                    fg=es_change_color
                )
            
            if len(self.spy_data) > 1:
                spy_change = spy_price - self.spy_data["Close"].iloc[-2]
                spy_change_pct = (spy_change / self.spy_data["Close"].iloc[-2]) * 100
                spy_change_color = "green" if spy_change >= 0 else "red"
                self.spy_change_label.config(
                    text=f"({spy_change_pct:+.2f}%)",
                    fg=spy_change_color
                )
            
            if len(self.ratio_data) > 1:
                ratio_change = ratio - self.ratio_data[-2]
                ratio_change_pct = (ratio_change / self.ratio_data[-2]) * 100
                ratio_change_color = "green" if ratio_change >= 0 else "red"
                self.ratio_change_label.config(
                    text=f"({ratio_change_pct:+.2f}%)",
                    fg=ratio_change_color
                )
    
    def update_chart(self):
        if hasattr(self, 'ax'):
            self.ax.clear()
            self.ax_ratio.clear()
            
            # Plot price data if available
            if len(self.timestamps) > 0:
                # Plot ES and SPY on the left y-axis
                if len(self.es_data) > 0:
                    es_data = self.es_data["Close"].iloc[-len(self.timestamps):]
                    self.ax.plot(self.timestamps, es_data, 'b-', label='ES', linewidth=1.5)
                
                if len(self.spy_data) > 0:
                    spy_data = self.spy_data["Close"].iloc[-len(self.timestamps):]
                    self.ax.plot(self.timestamps, spy_data, 'g-', label='SPY', linewidth=1.5)
                
                # Plot ratio on the right y-axis
                if len(self.ratio_data) > 0:
                    self.ax_ratio.plot(self.timestamps, self.ratio_data, 'r-', label='Ratio', linewidth=1)
            
            # Set labels
            self.ax.set_xlabel('Time')
            self.ax.set_ylabel('Price ($)')
            self.ax_ratio.set_ylabel('Ratio')
            
            # Combine legends
            lines1, labels1 = self.ax.get_legend_handles_labels()
            lines2, labels2 = self.ax_ratio.get_legend_handles_labels()
            self.ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
            
            # Rotate x-axis labels
            if len(self.timestamps) > 0:
                ticks = [self.timestamps[0]]
                if len(self.timestamps) > 5:
                    step = len(self.timestamps) // 5
                    for i in range(step, len(self.timestamps), step):
                        ticks.append(self.timestamps[i])
                if self.timestamps[-1] not in ticks:
                    ticks.append(self.timestamps[-1])
                self.ax.set_xticks(ticks)
                self.ax.tick_params(axis='x', rotation=45)
            
            # Update canvas
            self.fig.tight_layout()
            self.canvas.draw()
    
    def clear_data(self):
        if messagebox.askyesno("Clear Data", "Are you sure you want to clear all data?"):
            self.es_data = pd.DataFrame()
            self.spy_data = pd.DataFrame()
            self.ratio_data = []
            self.timestamps = []
            
            # Reset labels
            self.es_price_label.config(text="--")
            self.spy_price_label.config(text="--")
            self.ratio_label.config(text="--")
            self.time_label.config(text="Last update: --")
            self.es_change_label.config(text="--", fg="black")
            self.spy_change_label.config(text="--", fg="black")
            self.ratio_change_label.config(text="--", fg="black")
            
            # Update chart
            self.update_chart()
            
            self.status_bar.config(text="Data cleared")
    
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        
        if self.dark_mode:
            # Dark mode
            bg_color = "#2e2e2e"
            fg_color = "white"
            self.theme_button.config(text="Light Mode", bg="#f0f0f0", fg="black")
        else:
            # Light mode
            bg_color = "#f0f0f0"
            fg_color = "black"
            self.theme_button.config(text="Dark Mode", bg="#333", fg="white")
        
        # Update background colors
        self.root.configure(bg=bg_color)
        main_frame = self.root.winfo_children()[0]  # Main frame
        main_frame.configure(bg=bg_color)
        
        # Update all widgets in main_frame
        for widget in main_frame.winfo_children():
            if isinstance(widget, tk.Frame) or isinstance(widget, tk.LabelFrame):
                widget.configure(bg=bg_color)
                for child in widget.winfo_children():
                    if isinstance(child, (tk.Label, tk.Frame, tk.Checkbutton)):
                        child.configure(bg=bg_color, fg=fg_color)
                    # Handle nested frames in calculator
                    if isinstance(child, tk.Frame):
                        child.configure(bg=bg_color)
                        for subchild in child.winfo_children():
                            if isinstance(subchild, (tk.Label, tk.Checkbutton)):
                                subchild.configure(bg=bg_color, fg=fg_color)
            elif isinstance(widget, tk.Label):
                widget.configure(bg=bg_color, fg=fg_color)
        
        # Update status bar
        self.status_bar.configure(bg=bg_color, fg=fg_color)
        
        # Update chart colors
        if hasattr(self, 'fig'):
            self.fig.set_facecolor(bg_color)
            self.ax.set_facecolor(bg_color if self.dark_mode else '#f5f5f5')
            self.ax.grid(True, linestyle='--', alpha=0.7, color='gray')
            
            # Update text colors
            for text in self.ax.get_xticklabels() + self.ax.get_yticklabels():
                text.set_color(fg_color)
            
            for text in self.ax_ratio.get_yticklabels():
                text.set_color(fg_color)
            
            self.ax.xaxis.label.set_color(fg_color)
            self.ax.yaxis.label.set_color(fg_color)
            self.ax_ratio.yaxis.label.set_color(fg_color)
            
            # Update chart
            self.canvas.draw()

def main():
    root = tk.Tk()
    app = ESSpyTracker(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (setattr(app, 'running', False), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    main()