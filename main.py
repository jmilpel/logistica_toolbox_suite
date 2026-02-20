import customtkinter as ctk
import pyperclip
import re
import os
import ast
import pandas as pd
import matplotlib.pyplot as plt
# from datetime import datetime
from tkinter import messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import ctypes

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Logistica ToolBox Suite")
        self.geometry("1150x850")

        self.icon_path = "kyros.ico"
        if os.path.exists(self.icon_path):
            self.iconbitmap(self.icon_path)
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("logistica.toolbox.suite.v3")
            except:
                pass

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR (CORREGIDO ESPACIADO) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Kyros ToolBox",
                                       font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Botones ordenados sin filas con peso intermedio
        buttons = [
            ("IMEI / ICCID Gen", self.show_generator),
            ("Ascii2Hex Converter", self.show_ascii_converter),
            ("IMEI Log Filter", self.show_imei_finder),
            ("Speeds Comparator", self.show_speeds_comparator),
            ("24V devices", self.show_24v_devices),
            ("0 satellites", self.show_0_satellites),
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

    # --- 1. GENERATOR ---
    def show_generator(self):
        self.clear_frame()
        self.current_frame = ctk.CTkTabview(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        t1 = self.current_frame.add("IMEIs")
        t2 = self.current_frame.add("ICCIDs")

        # Pestaña IMEIs
        txt = ctk.CTkTextbox(t1, height=300)
        txt.pack(padx=20, pady=10, fill="both", expand=True)
        res = ctk.CTkEntry(t1)
        res.pack(padx=20, pady=5, fill="x")

        def run_gen():
            v = [l.strip() for l in txt.get("1.0", "end-1c").splitlines() if len(l.strip()) == 15]
            if v:
                out = " -e " + " -e ".join(v)
                init_chain = "cat teltonika.log |grep"
                finish_chain = " |grep \"'389': \""
                out = init_chain + out + finish_chain
                res.delete(0, "end")
                res.insert(0, out)

        ctk.CTkButton(t1, text="Execute", command=run_gen).pack(pady=5)
        ctk.CTkButton(t1, text="Copiar", command=lambda: pyperclip.copy(res.get())).pack()

        # Pestaña ICCIDs
        txt_iccid = ctk.CTkTextbox(t2, height=300)
        txt_iccid.pack(padx=20, pady=10, fill="both", expand=True)
        res_iccid = ctk.CTkEntry(t2)
        res_iccid.pack(padx=20, pady=5, fill="x")

        def run_iccid():
            v = [l.strip() for l in txt_iccid.get("1.0", "end-1c").splitlines() if len(l.strip()) >= 18]
            if v:
                url = f"https://iot.truphone.com/sms/?preselect={v[0]}"
                for i in v[1:]: url += f"&preselect={i}"
                res_iccid.delete(0, "end")
                res_iccid.insert(0, url)

        ctk.CTkButton(t2, text="Generar URL", command=run_iccid).pack(pady=5)
        ctk.CTkButton(t2, text="Copiar URL", command=lambda: pyperclip.copy(res_iccid.get())).pack()

    # --- 2. ASCII CONVERTER ---
    def show_ascii_converter(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="Ascii2Hex Converter", font=("Arial", 18, "bold")).pack(pady=20)

        inp = ctk.CTkEntry(self.current_frame, width=400, placeholder_text="Insert ASCII command (ie: setparam 1234)")
        inp.pack(pady=10)
        out = ctk.CTkTextbox(self.current_frame, height=200)
        out.pack(padx=20, pady=10, fill="x")

        def calc_crc(hex_str):
            data = bytes.fromhex(hex_str)
            crc = 0x0000
            for byte in data:
                crc = (crc ^ byte) & 0xFFFF
                for _ in range(8):
                    if crc & 1:
                        crc = (crc >> 1) ^ 0xA001
                    else:
                        crc = crc >> 1
            return f"{crc:08X}"

        def convert():
            txt = inp.get()
            hex_val = ''.join(f'{ord(c):02x}' for c in txt)
            codec_part = "0C0105" + format(len(hex_val) // 2, 'x').zfill(8) + hex_val + "01"
            full_msg = "00000000" + format(len(codec_part) // 2, 'x').zfill(8) + codec_part + calc_crc(codec_part)
            out.delete("1.0", "end")
            out.insert("1.0", full_msg.upper())

        ctk.CTkButton(self.current_frame, text="Convert", command=convert).pack(pady=10)

    # --- 3. LOG FILTER IMEI ---
    def show_imei_finder(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="Obtain unique IMEIs", font=("Arial", 18, "bold")).pack(pady=20)

        def run_filter():
            path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
            if not path: return
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            imeis = sorted(set(re.findall(r"\[(\d{15})\]", content)))
            if imeis:
                out_path = os.path.join(os.path.expanduser("~"), "Downloads", "imeis_unique.txt")
                with open(out_path, "w") as f:
                    f.write("\n".join(imeis))
                messagebox.showinfo("Success", f"They have been extracted {len(imeis)} IMEIs in Downloads.")
            else:
                messagebox.showinfo("Info", "No IMEIs in the format were found [123...]")

        ctk.CTkButton(self.current_frame, text="Select Log and Extract", height=50, command=run_filter).pack(pady=20)

    # --- 4. SPEEDS COMPARATOR (GRÁFICA INTERACTIVA + TABLA + CORRECCIÓN FECHAS) ---
    def show_speeds_comparator(self):
            self.clear_frame()
            self.current_frame = ctk.CTkFrame(self.main_container)
            self.current_frame.pack(fill="both", expand=True)
            ctk.CTkLabel(self.current_frame, text="Speeds Comparator (OBD vs GPS)", font=("Arial", 18, "bold")).pack(
                pady=10)

            content_container = ctk.CTkFrame(self.current_frame, fg_color="transparent")
            content_container.pack(fill="both", expand=True, padx=20, pady=10)

            def analyze():
                p = filedialog.askopenfilename(filetypes=[("Log", "*.txt")])
                if not p: return

                for widget in content_container.winfo_children():
                    widget.destroy()

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
                    # Forzamos la conversión a datetime especificando milisegundos
                    df["datetime"] = pd.to_datetime(df["t"], unit='ms')

                    # --- GRÁFICA ---
                    graph_frame = ctk.CTkFrame(content_container, fg_color="white")
                    graph_frame.pack(fill="both", expand=True, pady=(0, 10))

                    fig, ax = plt.subplots(figsize=(8, 3.5))

                    # Usamos la columna 'datetime' directamente para el eje X
                    l1, = ax.plot(df["datetime"], df["obd"], label="OBD (37)", marker='o', markersize=4,
                                  color='#1f77b4', linestyle='-')
                    l2, = ax.plot(df["datetime"], df["gps"], label="GPS (24)", marker='o', markersize=4,
                                  color='#ff7f0e', linestyle='-')

                    ax.grid(True, linestyle='--', alpha=0.6)
                    ax.legend()

                    # Ajuste automático del eje X para evitar el error de 1970
                    ax.set_xlim(df["datetime"].min(), df["datetime"].max())

                    plt.xticks(rotation=20)
                    fig.tight_layout()

                    # Elementos del Tooltip e interactividad
                    v_line = ax.axvline(color='red', linestyle='--', alpha=0.5, visible=False)
                    annot = ax.annotate("", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
                                        bbox=dict(boxstyle="round", fc="w", ec="0.5", alpha=0.9),
                                        arrowprops=dict(arrowstyle="->"))
                    annot.set_visible(False)

                    def hover(event):
                        if event.inaxes == ax:
                            # Convertir la posición X del evento (float) a datetime
                            # Matplotlib usa días desde 1970-01-01 en punto flotante
                            try:
                                import matplotlib.dates as mdates
                                x_dt = mdates.num2date(event.xdata).replace(tzinfo=None)

                                # Encontrar el índice más cercano en el DataFrame
                                idx = (df['datetime'] - x_dt).abs().idxmin()
                                row = df.loc[idx]

                                v_line.set_xdata([row['datetime']])
                                v_line.set_visible(True)

                                annot.xy = (row['datetime'], max(row['obd'], row['gps']))
                                text = f"Hora: {row['datetime'].strftime('%H:%M:%S')}\nVel. OBD: {row['obd']} km/h\nVel. GPS: {row['gps']} km/h"
                                annot.set_text(text)
                                annot.set_visible(True)
                                fig.canvas.draw_idle()
                            except:
                                pass
                        else:
                            v_line.set_visible(False)
                            annot.set_visible(False)
                            fig.canvas.draw_idle()

                    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill="both", expand=True)
                    fig.canvas.mpl_connect("motion_notify_event", hover)

                    # --- TABLA ---
                    table_frame = ctk.CTkFrame(content_container)
                    table_frame.pack(fill="both", expand=True)

                    txt_table = ctk.CTkTextbox(table_frame, font=("Courier New", 12))
                    txt_table.pack(fill="both", expand=True, padx=10, pady=5)

                    header = f"{'TEMPORAL INSTANT':<25} | {'OBD SPEED (km/h)':<18} | {'GPS SPEED (km/h)':<18}\n"
                    txt_table.insert("end", header + ("-" * 70) + "\n")

                    for _, row in df.iterrows():
                        txt_table.insert("end",
                                         f"{row['datetime'].strftime('%Y-%m-%d %H:%M:%S'):<25} | {row['obd']:<18} | {row['gps']:<18}\n")

                    txt_table.configure(state="disabled")

            ctk.CTkButton(self.current_frame, text="Load Log and View Comparison", command=analyze).pack(pady=5)

    # --- 5. 24V DEVICES ---
    def show_24v_devices(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="24V Equipment Filter", font=("Arial", 18, "bold")).pack(pady=20)

        def run_24v():
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
                            if d.get('imei') not in seen:
                                out.append(
                                    f"'imei': {d.get('imei')}  'vehicle_license': '{d.get('vehicle_license', 'N/A')}'")
                                seen.add(d.get('imei'))
                    except:
                        continue
            if out:
                with open(os.path.join(os.path.expanduser("~"), "Downloads", "Devices_24V.txt"), "w") as f: f.write(
                    "\n".join(out))
                messagebox.showinfo("OK", "File generated in Downloads.")

        ctk.CTkButton(self.current_frame, text="Process Log for 24V devices", height=50, command=run_24v).pack(pady=20)

    # --- 6. 0 SATELLITES ---
    def show_0_satellites(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="Devices with 0 satellites", font=("Arial", 18, "bold")).pack(pady=20)

        def run_0sat():
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
                            if d.get('imei') not in seen:
                                out.append(
                                    f"'imei': {d.get('imei')}  'vehicle_license': '{d.get('vehicle_license', 'N/A')}'")
                                seen.add(d.get('imei'))
                    except:
                        continue
            if out:
                with open(os.path.join(os.path.expanduser("~"), "Downloads", "Devices_0_Sat.txt"), "w") as f: f.write(
                    "\n".join(out))
                messagebox.showinfo("OK", "File generated in Downloads.")

        ctk.CTkButton(self.current_frame, text="Process Log for 0 Sat", height=50, command=run_0sat).pack(pady=20)

    # --- 7. MERGER EXCEL ---
    def show_merger(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        paths = [None, None, None]
        labels = []
        ctk.CTkLabel(self.current_frame, text="Excel Merger by IMEI", font=("Arial", 18, "bold")).pack(pady=15)

        def sel(i):
            p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
            if p: paths[i] = p; labels[i].configure(text=os.path.basename(p), text_color="green")

        for n in ["Gps/Can", "Device", "Vehicles"]:
            f = ctk.CTkFrame(self.current_frame)
            f.pack(fill="x", padx=40, pady=5)
            ctk.CTkLabel(f, text=n, width=120).pack(side="left")
            ctk.CTkButton(f, text="Select", width=80, command=lambda x=len(labels): sel(x)).pack(side="right")
            lbl = ctk.CTkLabel(f, text="Waiting file...", text_color="gray")
            lbl.pack(side="right")
            labels.append(lbl)

        def fusion():
            if not all(paths): messagebox.showwarning("Warning", "Please attach the 3 files"); return
            try:
                df1, df2, df3 = pd.read_excel(paths[0]), pd.read_excel(paths[1]), pd.read_excel(paths[2])
                res = pd.merge(df1, df2, on='IMEI', how='left').merge(df3, on='IMEI', how='left')
                res.to_excel(os.path.join(os.path.expanduser("~"), "Downloads", "Kyros_Merged.xlsx"), index=False)
                messagebox.showinfo("Success", "Merged into Downloads.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(self.current_frame, text="MERGE", fg_color="green", command=fusion).pack(pady=20)


if __name__ == "__main__":
    App().mainloop()
