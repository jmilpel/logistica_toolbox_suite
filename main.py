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
            ("Speeds Comparator", self.show_speeds_comparator),
            ("24V Devices", self.show_24v_devices),
            ("Merger Excel", self.show_merger)
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
        ctk.CTkButton(t1, text="Copiar", fg_color="transparent", border_width=1,
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
        ctk.CTkButton(t2, text="Copiar", fg_color="transparent", border_width=1,
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

    # --- HERRAMIENTA: SPEEDS COMPARATOR (CON TOOLTIPS) ---
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
            data = []
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    s, e = line.find("{"), line.rfind("}")
                    if s != -1:
                        try:
                            d = ast.literal_eval(line[s:e + 1])
                            avl = d.get("avl", {})
                            v37 = int(str(avl.get("37", 0)), 16) if avl.get("37") else 0
                            v24 = int(str(avl.get("24", 0)), 16) if avl.get("24") else 0
                            data.append(
                                {"t": datetime.fromtimestamp(d["msg_timestamp"] / 1000.0), "obd": v37, "gps": v24})
                        except:
                            continue
            if data:
                df = pd.DataFrame(data).sort_values("t")
                fig, ax = plt.subplots(figsize=(8, 4))
                line_obd, = ax.plot(df["t"], df["obd"], label="OBD (37)", marker='o', color='#1f77b4', markersize=4)
                line_gps, = ax.plot(df["t"], df["gps"], label="GPS (24)", marker='o', color='#ff7f0e', markersize=4)
                ax.grid(True, linestyle='--', alpha=0.7)
                ax.legend();
                ax.set_ylabel("Km/h")
                plt.xticks(rotation=30)
                fig.tight_layout()

                # Tooltip dinámico
                annot = ax.annotate("", xy=(0, 0), xytext=(10, 10), textcoords="offset points",
                                    bbox=dict(boxstyle="round", fc="w", ec="0.5", alpha=0.9),
                                    arrowprops=dict(arrowstyle="->"))
                annot.set_visible(False)

                def hover(event):
                    if event.inaxes == ax:
                        vis = annot.get_visible()
                        # Buscar en ambas líneas
                        for line in [line_obd, line_gps]:
                            cont, ind = line.contains(event)
                            if cont:
                                pos = line.get_offsets()[ind["ind"][0]]
                                annot.xy = pos
                                label = "OBD" if line == line_obd else "GPS"
                                annot.set_text(f"{label}: {pos[1]} Km/h")
                                annot.set_visible(True)
                                fig.canvas.draw_idle()
                                return
                        if vis:
                            annot.set_visible(False)
                            fig.canvas.draw_idle()

                canvas = FigureCanvasTkAgg(fig, master=container)
                canvas.draw();
                canvas.get_tk_widget().pack(fill="both", expand=True)
                fig.canvas.mpl_connect("motion_notify_event", hover)

        ctk.CTkButton(self.current_frame, text="Cargar Log y Ver Gráfica", command=analyze).pack(pady=10)

    # --- HERRAMIENTA: 24V DEVICES (LOGICA CORREGIDA) ---
    def show_24v_devices(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="24V & 0 Satellites Detector", font=("Arial", 18, "bold")).pack(pady=20)

        def proc_24v():
            p = filedialog.askopenfilename(filetypes=[("Log", "*.txt")])
            if not p: return
            res = []
            seen = set()

            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    # Extraer IMEI y Matricula con Regex para evitar fallos de posición
                    imei_match = re.search(r"'imei':\s*'(\d{15})'", line)
                    license_match = re.search(r"'vehicle_license':\s*'([^']*)'", line)

                    if imei_match:
                        imei = imei_match.group(1)
                        lic = license_match.group(1) if license_match else "N/A"

                        # Criterio 1: Cero Satélites
                        is_zero_sat = "'satellites': 0" in line

                        # Criterio 2: Voltaje > 20
                        is_24v = False
                        volt_match = re.search(r"'battery_voltage':\s*(\d+\.?\d*)", line)
                        if volt_match:
                            if float(volt_match.group(1)) > 20:
                                is_24v = True

                        if (is_zero_sat or is_24v) and imei not in seen:
                            tipo = "0_SAT" if is_zero_sat else "24V"
                            if is_zero_sat and is_24v: tipo = "AMBOS"
                            res.append(f"{imei}\t{lic}\t{tipo}")
                            seen.add(imei)

            if res:
                path_out = os.path.join(os.path.expanduser("~"), "Downloads",
                                        f"reporte_24v_0sat_{datetime.now().strftime('%H%M')}.txt")
                with open(path_out, "w") as f:
                    f.write("IMEI\tMATRICULA\tMOTIVO\n")
                    f.write("\n".join(res))
                messagebox.showinfo("Completado", f"Se encontraron {len(res)} dispositivos.\nGuardado en Descargas.")
            else:
                messagebox.showinfo("Info", "No hay coincidencias.")

        ctk.CTkButton(self.current_frame, text="Analizar Log (Filtro 24V / 0 Sat)", height=50, command=proc_24v).pack(
            pady=20)

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

        for n in ["Gps/Can", "Vehículos", "Dispositivos"]:
            f = ctk.CTkFrame(self.current_frame);
            f.pack(fill="x", padx=40, pady=5)
            ctk.CTkLabel(f, text=n, width=120).pack(side="left")
            ctk.CTkButton(f, text="Elegir", width=80, command=lambda x=len(labels): sel(x)).pack(side="right")
            lbl = ctk.CTkLabel(f, text="---", text_color="gray");
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