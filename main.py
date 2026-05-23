#!/usr/bin/env python3
import customtkinter as ctk
from core.scanner import PortScanner
import threading
from tkinter import messagebox, filedialog
import socket

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class PortScannerApp:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Port Scanner By Yushie_Alya1")
        self.window.geometry("1100x700")
        self.window.minsize(900, 600)
        
        self.scanner = None
        self.scan_thread = None
        
        self.setup_ui()
        
    def setup_ui(self):
        self.grid_frame = ctk.CTkFrame(self.window)
        self.grid_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.grid_frame.grid_rowconfigure(1, weight=1)
        self.grid_frame.grid_columnconfigure(0, weight=2)
        self.grid_frame.grid_columnconfigure(1, weight=3)
        
        # Top bar (input)
        top_frame = ctk.CTkFrame(self.grid_frame, fg_color="transparent")
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        ctk.CTkLabel(top_frame, text="Target:").pack(side="left", padx=5)
        self.target_entry = ctk.CTkEntry(top_frame, width=200)
        self.target_entry.pack(side="left", padx=5)
        self.target_entry.insert(0, "scanme.nmap.org")
        
        ctk.CTkLabel(top_frame, text="Port Range:").pack(side="left", padx=5)
        self.port_range_entry = ctk.CTkEntry(top_frame, width=120)
        self.port_range_entry.pack(side="left", padx=5)
        self.port_range_entry.insert(0, "1-1024")
        
        ctk.CTkLabel(top_frame, text="Mode:").pack(side="left", padx=5)
        self.scan_mode = ctk.CTkOptionMenu(top_frame, values=["TCP Connect", "SYN (requires root)"], width=140)
        self.scan_mode.pack(side="left", padx=5)
        
        self.scan_btn = ctk.CTkButton(top_frame, text="Start Scan", command=self.start_scan, fg_color="green")
        self.scan_btn.pack(side="left", padx=20)
        
        self.export_btn = ctk.CTkButton(top_frame, text="Export Results", command=self.export_results, state="disabled", fg_color="blue")
        self.export_btn.pack(side="left", padx=5)
        
        # Left: Results tree
        left_frame = ctk.CTkFrame(self.grid_frame, corner_radius=10)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(left_frame, text="Open Ports", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        self.tree = ctk.CTkTextbox(left_frame, font=ctk.CTkFont(size=12))
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Right: Log output
        right_frame = ctk.CTkFrame(self.grid_frame, corner_radius=10)
        right_frame.grid(row=1, column=1, sticky="nsew")
        ctk.CTkLabel(right_frame, text="Scan Log", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        self.log_text = ctk.CTkTextbox(right_frame, font=ctk.CTkFont(size=11))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Bottom bar (progress)
        bottom_frame = ctk.CTkFrame(self.grid_frame, fg_color="transparent")
        bottom_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        self.progress = ctk.CTkProgressBar(bottom_frame, width=400)
        self.progress.pack(side="left", padx=10)
        self.progress.set(0)
        
        self.status_label = ctk.CTkLabel(bottom_frame, text="Ready")
        self.status_label.pack(side="left", padx=10)
        
    def log(self, msg):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.window.update()
    
    def start_scan(self):
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showerror("Error", "Target required")
            return
        try:
            # Resolve domain to IP
            ip = socket.gethostbyname(target)
            self.log(f"Target resolved: {target} -> {ip}")
        except:
            messagebox.showerror("Error", "Invalid hostname/IP")
            return
        
        port_range = self.port_range_entry.get().strip()
        try:
            if '-' in port_range:
                start, end = map(int, port_range.split('-'))
            else:
                start = end = int(port_range)
            if start < 1 or end > 65535 or start > end:
                raise ValueError
        except:
            messagebox.showerror("Error", "Invalid port range (e.g., 1-1024)")
            return
        
        mode = self.scan_mode.get()
        syn_scan = (mode == "SYN (requires root)")
        
        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.export_btn.configure(state="disabled")
        self.tree.delete("1.0", "end")
        self.log_text.delete("1.0", "end")
        self.progress.set(0)
        
        self.scanner = PortScanner(target=ip, port_start=start, port_end=end, syn=syn_scan, callback=self.update_progress, log_callback=self.log)
        self.scan_thread = threading.Thread(target=self.scanner.scan)
        self.scan_thread.daemon = True
        self.scan_thread.start()
        
        # Monitor thread completion
        self.check_scan_done()
    
    def update_progress(self, current, total, open_ports):
        percent = current / total
        self.progress.set(percent)
        self.status_label.configure(text=f"Scanning: {current}/{total} ports | Open: {len(open_ports)}")
        # Update tree with latest open ports
        self.tree.delete("1.0", "end")
        for port, banner in open_ports:
            self.tree.insert("end", f"{port:<6} open     {banner}\n")
    
    def check_scan_done(self):
        if self.scan_thread and self.scan_thread.is_alive():
            self.window.after(500, self.check_scan_done)
        else:
            self.scan_btn.configure(state="normal", text="Start Scan")
            self.export_btn.configure(state="normal")
            self.status_label.configure(text="Scan completed")
            self.log("Scan finished.")
    
    def export_results(self):
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv")])
        if not filename:
            return
        content = self.tree.get("1.0", "end")
        with open(filename, 'w') as f:
            f.write(content)
        messagebox.showinfo("Export", f"Results saved to {filename}")
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = PortScannerApp()
    app.run()