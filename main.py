import customtkinter as ctk
import pyperclip
import re
import os
import ast
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from tkinter import messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import ctypes

# Configuración de apariencia
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Logistica ToolBox Suite")
        self.geometry("1100x800")

        # Configuración del icono
        self.icon_path = "kyros.ico"
        if os.path.exists(self.icon_path):
            self.iconbitmap(self.icon_path)
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("logistica.toolbox.suite.v2")
            except:
                pass

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Kyros ToolBox",
                                       font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        buttons = [
            ("IMEI / ICCID Gen", self.show_generator),
            ("Ascii2Hex Converter", self.show_ascii_converter),
            ("Log Filter IMEI", self.show_imei_finder),
            ("Merger Excel", self.show_merger),
            ("Speeds Comparator", self.show_speeds_comparator),
            ("24V Devices", self.show_24v_tool),
            ("0 Satellites Detector", self.show_zero_sat_tool)
        ]

        for i, (name, cmd) in enumerate(buttons, start=1):
            btn = ctk.CTkButton(self.sidebar_frame, text=name, command=cmd)
            btn.grid(row=i, column=0, padx=20, pady=10)

        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.current_frame = None
        self.show_generator()

    def clear_frame(self):
        if self.current_frame is not None:
            self.current_frame.destroy()

    # --- HERRAMIENTA: IMEI/ICCID ---
    def show_generator(self):
        self.clear_frame()
        self.current_frame = ctk.CTkTabview(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        t1, t2 = self.current_frame.add("IMEIs"), self.current_frame.add("ICCIDs")

        # IMEI Logic
        ctk.CTkLabel(t1, text="Listado IMEIs (15 dígitos):").pack(pady=5)
        txt = ctk.CTkTextbox(t1, height=250);
        txt.pack(padx=20, pady=5, fill="both", expand=True)
        res = ctk.CTkEntry(t1);
        res.pack(padx=20, pady=5, fill="x")

        def run():
            v = [l.strip() for l in txt.get("1.0", "end-1c").splitlines() if len(l.strip()) == 15]
            if v: res.delete(0, "end"); res.insert(0, " -e " + " -e ".join(v))

        ctk.CTkButton(t1, text="Execute", command=run).pack(pady=5)
        ctk.CTkButton(t1, text="Copiar", border_width=1,
                      command=lambda: pyperclip.copy(res.get())).pack(pady=5)

        # ICCID Logic
        ctk.CTkLabel(t2, text="Listado ICCIDs (19 dígitos):").pack(pady=5)
        txt2 = ctk.CTkTextbox(t2, height=250);
        txt2.pack(padx=20, pady=5, fill="both", expand=True)
        res2 = ctk.CTkEntry(t2);
        res2.pack(padx=20, pady=5, fill="x")

        def run2():
            v = [l.strip() for l in txt2.get("1.0", "end-1c").splitlines() if len(l.strip()) == 19]
            if v:
                url = f"https://iot.truphone.com/sms/?preselect={v[0]}"
                if len(v) > 1: url += "&preselect=" + "&preselect=".join(v[1:])
                res2.delete(0, "end");
                res2.insert(0, url)

        ctk.CTkButton(t2, text="Execute", command=run2).pack(pady=5)
        ctk.CTkButton(t2, text="Copiar", border_width=1,
                      command=lambda: pyperclip.copy(res2.get())).pack(pady=5)

    # --- HERRAMIENTA: ASCII2HEX ---
    def show_ascii_converter(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="Ascii2Hex Converter", font=("Arial", 18, "bold")).pack(pady=15)
        inp = ctk.CTkEntry(self.current_frame, placeholder_text="Texto ASCII...", width=450);
        inp.pack(pady=10)
        out = ctk.CTkTextbox(self.current_frame, height=200);
        out.pack(padx=30, pady=10, fill="x")

        def calc_crc(hd):
            d = bytes.fromhex(hd);
            c = 0x0000
            for b in d:
                c = (c ^ b) & 0xFFFF
                for _ in range(8):
                    if c & 1:
                        c = (c >> 1) ^ 0xA001
                    else:
                        c = c >> 1
            return f"{c:04X}"

        def conv():
            t = inp.get()
            if not t: return
            hp = ''.join(f'{ord(c):02x}' for c in t)
            base = "0C0105" + format(len(hp) // 2, 'x').zfill(8) + hp + "01"
            crc = calc_crc(base).zfill(8)
            final = ("00000000" + format(len(base) // 2, 'x').zfill(8) + base + crc).upper()
            out.delete("1.0", "end");
            out.insert("1.0", final)

        ctk.CTkButton(self.current_frame, text="Convertir", command=conv).pack(pady=10)

    # --- HERRAMIENTA: LOG FILTER IMEI ---
    def show_imei_finder(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="Log Filter IMEI", font=("Arial", 18, "bold")).pack(pady=20)

        def proc():
            p = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
            if not p: return
            with open(p, "r", encoding="utf-8") as f:
                c = f.read()
            found = sorted(set(re.findall(r"\[(\d{15})\]", c)))
            if found:
                out = os.path.join(os.path.expanduser("~"), "Downloads", "imeis_extraidos.txt")
                with open(out, "w") as f: f.write("\n".join(found))
                messagebox.showinfo("Éxito", f"Guardado en Descargas. Encontrados: {len(found)}")

        ctk.CTkButton(self.current_frame, text="Seleccionar Log", command=proc).pack(pady=30)

    # --- HERRAMIENTA: SPEEDS COMPARATOR (TOOLTIP DUAL) ---
    def show_speeds_comparator(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="Speeds Comparator (OBD vs GPS)", font=("Arial", 18, "bold")).pack(
            pady=10)
        container = ctk.CTkFrame(self.current_frame, fg_color="white")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        def analyze():
            p = filedialog.askopenfilename(filetypes=[("Log", "*.txt")])
            if not p: return
            rows = []
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.find("{")
                    if s != -1:
                        try:
                            d = ast.literal_eval(line[s:line.rfind("}") + 1])
                            avl = d.get("avl", {})
                            v37 = int(str(avl.get("37", 0)), 16) if avl.get("37") else 0
                            v24 = int(str(avl.get("24", 0)), 16) if avl.get("24") else 0
                            rows.append({"t": d["msg_timestamp"], "obd": v37, "gps": v24})
                        except:
                            continue
            if rows:
                df = pd.DataFrame(rows).sort_values("t")
                df["datetime"] = pd.to_datetime(df["t"], unit='ms')
                fig, ax = plt.subplots(figsize=(8, 4))
                l1, = ax.plot(df["datetime"], df["obd"], label="OBD (37)", marker='o', markersize=5)
                l2, = ax.plot(df["datetime"], df["gps"], label="GPS (24)", marker='o', markersize=5)
                ax.grid(True, linestyle='--', alpha=0.6);
                ax.legend()

                annot = ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                                    bbox=dict(boxstyle="round", fc="w", ec="0.5", alpha=0.9),
                                    arrowprops=dict(arrowstyle="->"))
                annot.set_visible(False)

                def hover(event):
                    if event.inaxes == ax:
                        cont1, ind1 = l1.contains(event)
                        cont2, ind2 = l2.contains(event)
                        if cont1 or cont2:
                            idx = ind1["ind"][0] if cont1 else ind2["ind"][0]
                            x = df["datetime"].iloc[idx]
                            y_obd = df["obd"].iloc[idx]
                            y_gps = df["gps"].iloc[idx]
                            annot.xy = (x, y_obd if cont1 else y_gps)
                            annot.set_text(f"Hora: {x.strftime('%H:%M:%S')}\nOBD: {y_obd} km/h\nGPS: {y_gps} km/h")
                            annot.set_visible(True)
                            fig.canvas.draw_idle()
                            return
                    if annot.get_visible():
                        annot.set_visible(False);
                        fig.canvas.draw_idle()

                canvas = FigureCanvasTkAgg(fig, master=container)
                canvas.draw();
                canvas.get_tk_widget().pack(fill="both", expand=True)
                fig.canvas.mpl_connect("motion_notify_event", hover)

        ctk.CTkButton(self.current_frame, text="Cargar Log y Graficar", command=analyze).pack(pady=10)

    # --- HERRAMIENTA: 24V DEVICES ---
    def show_24v_tool(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="Filtro Dispositivos 24V", font=("Arial", 18, "bold")).pack(pady=20)

        def run():
            p = filedialog.askopenfilename(filetypes=[("Log", "*.txt")])
            if not p: return
            out = []
            seen = set()
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        s = line.find("{")
                        d = ast.literal_eval(line[s:line.rfind("}") + 1])
                        if float(d.get('battery_voltage', 0)) > 20.0:
                            imei = d.get('imei')
                            if imei not in seen:
                                out.append(f"'imei': {imei}  'vehicle_license': '{d.get('vehicle_license', 'N/A')}'")
                                seen.add(imei)
                    except:
                        continue
            if out:
                path = os.path.join(os.path.expanduser("~"), "Downloads",
                                    f"24V_Devices_{datetime.now().strftime('%H%M')}.txt")
                with open(path, "w") as f: f.write("\n".join(out))
                messagebox.showinfo("Éxito", f"Archivo generado en Descargas ({len(out)} equipos)")

        ctk.CTkButton(self.current_frame, text="Procesar Log (Batería > 20V)", height=50, command=run).pack(pady=20)

    # --- HERRAMIENTA: 0 SATELITES ---
    def show_zero_sat_tool(self):
        self.clear_frame();
        self.current_frame = ctk.CTkFrame(self.main_container);
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="Detector 0 Satélites", font=("Arial", 18, "bold")).pack(pady=20)

        def run():
            p = filedialog.askopenfilename(filetypes=[("Log", "*.txt")])
            if not p: return
            out = []
            seen = set()
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        s = line.find("{")
                        d = ast.literal_eval(line[s:line.rfind("}") + 1])
                        if d.get('satellites') == 0:
                            imei = d.get('imei')
                            if imei not in seen:
                                out.append(f"'imei': {imei}  'vehicle_license': '{d.get('vehicle_license', 'N/A')}'")
                                seen.add(imei)
                    except:
                        continue
            if out:
                path = os.path.join(os.path.expanduser("~"), "Downloads",
                                    f"ZeroSat_Devices_{datetime.now().strftime('%H%M')}.txt")
                with open(path, "w") as f: f.write("\n".join(out))
                messagebox.showinfo("Éxito", "Archivo generado en Descargas")

        ctk.CTkButton(self.current_frame, text="Procesar Log (Satélites = 0)", height=50, command=run).pack(pady=20)

    # --- HERRAMIENTA: MERGER EXCEL ---
    def show_merger(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        paths = [None, None, None];
        labels = []
        ctk.CTkLabel(self.current_frame, text="Excel Merger por IMEI", font=("Arial", 18, "bold")).pack(pady=15)

        def sel(i):
            p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
            if p: paths[i] = p; labels[i].configure(text=os.path.basename(p), text_color="green")

        for n in ["Gps/Can", "Vehículos", "Localizadores"]:
            f = ctk.CTkFrame(self.current_frame);
            f.pack(fill="x", padx=40, pady=5)
            ctk.CTkLabel(f, text=n, width=120).pack(side="left")
            ctk.CTkButton(f, text="Elegir", width=80, command=lambda x=len(labels): sel(x)).pack(side="right")
            lbl = ctk.CTkLabel(f, text="Pendiente adjuntar.....", text_color="gray");
            lbl.pack(side="right");
            labels.append(lbl)

        def fusion():
            if not all(paths): return
            df1, df2, df3 = pd.read_excel(paths[0]), pd.read_excel(paths[1]), pd.read_excel(paths[2])
            res = pd.merge(df1, df2, on='IMEI', how='left').merge(df3, on='IMEI', how='left')
            res.to_excel(os.path.join(os.path.expanduser("~"), "Downloads", "Merge_Final.xlsx"), index=False)
            messagebox.showinfo("OK", "Archivo en Descargas.")

        ctk.CTkButton(self.current_frame, text="FUSIONAR", fg_color="green", command=fusion).pack(pady=20)


if __name__ == "__main__":
    App().mainloop()