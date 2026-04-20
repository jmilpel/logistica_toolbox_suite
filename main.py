import customtkinter as ctk
import pyperclip
import requests
import re
import os
import ast
import pandas as pd
import matplotlib.pyplot as plt
from tkinter import messagebox, filedialog, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import ctypes
from datetime import datetime

from matplotlib.pyplot import autoscale
from tkcalendar import DateEntry

# Nueva importación para la herramienta de conductores
import tachosync_api as api

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "apikey.txt"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Logistica ToolBox Suite v3.4")
        self.geometry("1150x850")

        # Fuentes para la nueva herramienta
        self.font_label = ctk.CTkFont(size=16, weight="bold")
        self.font_ui = ctk.CTkFont(size=13)
        self.font_table = ("Segoe UI", 13)

        self.icon_path = "kyros.ico"
        if os.path.exists(self.icon_path):
            self.iconbitmap(self.icon_path)
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("logistica.toolbox.suite.v3.4")
            except:
                pass

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Kyros ToolBox",
                                       font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Botones (Añadido "Drivers updated" al final)
        buttons = [
            ("IMEI / ICCID Gen", self.show_generator),
            ("Send SMS", self.show_send_sms),  # Nueva Herramienta
            ("Ascii2Hex Converter", self.show_ascii_converter),
            ("IMEI Log Filter", self.show_imei_finder),
            ("Speeds Comparator", self.show_speeds_comparator),
            ("24V devices", self.show_24v_devices),
            ("0 satellites", self.show_0_satellites),
            ("Merger Excel", self.show_merger),
            ("Drivers updated", self.show_drivers_updated)  # Nueva Herramienta
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

    # --- FUNCIONES DE APOYO API CONDUCTORES ---
    def load_api_key(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return f.read().strip()
        return ""

    def save_api_key(self, entry_widget):
        key = entry_widget.get()
        with open(CONFIG_FILE, "w") as f:
            f.write(key)
        messagebox.showinfo("Éxito", "API Key guardada en apikey.txt")

    def copy_table_selection(self, tree):
        selection = tree.selection()
        if not selection: return
        lines = []
        for item_id in selection:
            values = tree.item(item_id, "values")
            lines.append("\t".join(values))
        pyperclip.copy("\n".join(lines))
        messagebox.showinfo("Copiado", "Datos copiados al portapapeles.")


    # --- 1. GENERATOR (RESTO DE TUS FUNCIONES ORIGINALES SIGUEN AQUÍ SIN CAMBIOS) ---
    def show_generator(self):
        self.clear_frame()
        self.current_frame = ctk.CTkTabview(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        t1 = self.current_frame.add("IMEIs")
        t2 = self.current_frame.add("ICCIDs")

        # Pestaña IMEIs
        txt = ctk.CTkTextbox(t1, height=300)
        txt.pack(padx=20, pady=10, fill="both", expand=True)

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
        res = ctk.CTkEntry(t1)
        res.pack(padx=20, pady=5, fill="x")
        ctk.CTkButton(t1, text="Copy", command=lambda: pyperclip.copy(res.get())).pack()

        # Pestaña ICCIDs
        txt_iccid = ctk.CTkTextbox(t2, height=300)
        txt_iccid.pack(padx=20, pady=10, fill="both", expand=True)

        def run_iccid():
            v = [l.strip() for l in txt_iccid.get("1.0", "end-1c").splitlines() if len(l.strip()) >= 18]
            if v:
                url = f"https://iot.truphone.com/sms/?preselect={v[0]}"
                for i in v[1:]: url += f"&preselect={i}"
                res_iccid.delete(0, "end")
                res_iccid.insert(0, url)

        def run_iccid_2():
            v = [l.strip() for l in txt_iccid.get("1.0", "end-1c").splitlines() if len(l.strip()) >= 18]
            if v:
                lista = f"{v[0]}"
                for i in v[1:]: lista += f", {i}"
                res_iccid.delete(0, "end")
                res_iccid.insert(0, lista)

        ctk.CTkButton(t2, text="Generate URL", command=run_iccid).pack(pady=5)
        ctk.CTkButton(t2, text="Generate list", command=run_iccid_2).pack(pady=5)
        res_iccid = ctk.CTkEntry(t2)
        res_iccid.pack(padx=20, pady=5, fill="x")
        ctk.CTkButton(t2, text="Copy", command=lambda: pyperclip.copy(res_iccid.get())).pack()

    # --- 2. ASCII CONVERTER ---
    def show_ascii_converter(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="Ascii2Hex Converter", font=("Arial", 18, "bold")).pack(pady=20)

        inp = ctk.CTkEntry(self.current_frame, width=400, placeholder_text="Insert ASCII command (ie: setparam 1234)")
        inp.pack(pady=10)

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
        out = ctk.CTkTextbox(self.current_frame, height=200)
        out.pack(padx=20, pady=10, fill="x")

    # --- 3. LOG FILTER IMEI ---
    def show_imei_finder(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="Extract unique IMEIs", font=("Arial", 18, "bold")).pack(pady=20)

        result_container = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        txt_preview = ctk.CTkTextbox(result_container, height=300, width=400, font=("Courier New", 12))

        def run_filter():
            path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
            if not path: return
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                imeis = sorted(set(re.findall(r"\[(\d{15})\]", content)))
                if imeis:
                    out_path = os.path.join(os.path.expanduser("~"), "Downloads", "imeis_extraidos.txt")
                    with open(out_path, "w") as f:
                        f.write("\n".join(imeis))
                    result_container.pack(fill="both", expand=True, padx=20, pady=10)
                    txt_preview.delete("1.0", "end");
                    txt_preview.insert("end", "\n".join(imeis))
                    txt_preview.pack(pady=10);
                    btn_copy_res.pack(pady=5)
                    messagebox.showinfo("Success", f"Extracted {len(imeis)} IMEIs.")
                else:
                    messagebox.showinfo("Info", "No IMEIs found.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        def copy_to_clipboard():
            pyperclip.copy(txt_preview.get("1.0", "end-1c"))
            # messagebox.showinfo("Copied", "Copied to clipboard.")

        ctk.CTkButton(self.current_frame, text="Select Log and Extract", fg_color="#1f77b4",
                      command=run_filter).pack(pady=10)
        btn_copy_res = ctk.CTkButton(result_container, text="Copy List", fg_color="#2ecc71", command=copy_to_clipboard)

    # --- 4. SPEEDS COMPARATOR ---
    def show_speeds_comparator(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="Speeds Comparator (OBD vs GPS)", font=("Arial", 18, "bold")).pack(
            pady=10)

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
                # Forzamos la conversión a datetime asegurando que la unidad sea milisegundos
                df["datetime"] = pd.to_datetime(df["t"], unit='ms')

                graph_frame = ctk.CTkFrame(content_container, fg_color="white")
                graph_frame.pack(fill="both", expand=True, pady=(0, 10))

                fig, ax = plt.subplots(figsize=(8, 3.5), dpi=100)
                ax.plot(df["datetime"], df["obd"], label="OBD (37)", color='#1f77b4', marker='o', markersize=3)
                ax.plot(df["datetime"], df["gps"], label="GPS (24)", color='#ff7f0e', marker='o', markersize=3)

                # Ajuste automático del eje X al rango real de los datos
                ax.set_xlim(df["datetime"].min(), df["datetime"].max())

                ax.legend()
                ax.grid(True, alpha=0.3)
                fig.tight_layout()

                # --- Elementos interactivos (Línea y Tooltip) ---
                v_line = ax.axvline(color='gray', linestyle='--', alpha=0.7, visible=False)
                annot = ax.annotate("", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
                                    bbox=dict(boxstyle="round", fc="w", ec="0.5", alpha=0.9),
                                    arrowprops=dict(arrowstyle="->"))
                annot.set_visible(False)

                def hover(event):
                    if event.inaxes == ax:
                        # Convertimos la posición X del ratón a datetime
                        try:
                            target_dt = plt.matplotlib.dates.num2date(event.xdata).replace(tzinfo=None)
                            idx = (df['datetime'] - target_dt).abs().idxmin()
                            row = df.loc[idx]

                            v_line.set_xdata([row['datetime']])
                            v_line.set_visible(True)

                            annot.xy = (row['datetime'], max(row['obd'], row['gps']))
                            annot.set_text(
                                f"Hora: {row['datetime'].strftime('%H:%M:%S')}\nOBD: {row['obd']} km/h\nGPS: {row['gps']} km/h")
                            annot.set_visible(True)
                            canvas.draw_idle()
                        except:
                            pass
                    else:
                        v_line.set_visible(False)
                        annot.set_visible(False)
                        canvas.draw_idle()

                # --- Función de Zoom con Scroll ---
                def zoom(event):
                    if event.inaxes != ax: return
                    base_scale = 1.5
                    cur_xlim = ax.get_xlim()
                    cur_ylim = ax.get_ylim()

                    xdata = event.xdata
                    ydata = event.ydata

                    if event.button == 'up':  # Zoom in
                        scale_factor = 1 / base_scale
                    elif event.button == 'down':  # Zoom out
                        scale_factor = base_scale
                    else:
                        scale_factor = 1

                    new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
                    new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

                    rel_x = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
                    rel_y = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

                    ax.set_xlim([xdata - new_width * (1 - rel_x), xdata + new_width * (rel_x)])
                    ax.set_ylim([ydata - new_height * (1 - rel_y), ydata + new_height * (rel_y)])
                    canvas.draw_idle()

                canvas = FigureCanvasTkAgg(fig, master=graph_frame)
                # Conectar eventos
                canvas.mpl_connect("motion_notify_event", hover)
                canvas.mpl_connect("scroll_event", zoom)

                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)

                # --- Tabla de datos ---
                table_frame = ctk.CTkFrame(content_container)
                table_frame.pack(fill="both", expand=True)
                txt_table = ctk.CTkTextbox(table_frame, font=("Courier New", 12))
                txt_table.pack(fill="both", expand=True, padx=10, pady=5)
                txt_table.insert("end", f"{'TIME':<25} | {'OBD':<10} | {'GPS':<10}\n" + "-" * 50 + "\n")
                for _, r in df.iterrows():
                    txt_table.insert("end",
                                     f"{r['datetime'].strftime('%H:%M:%S'):<25} | {r['obd']:<10} | {r['gps']:<10}\n")
                txt_table.configure(state="disabled")

        ctk.CTkButton(self.current_frame, text="Load Log", command=analyze).pack(pady=5)
        content_container = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        content_container.pack(fill="both", expand=True, padx=20, pady=10)

    # --- 5. 24V DEVICES ---
    def show_24v_devices(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="24V devices filter", font=("Arial", 18, "bold")).pack(pady=20)
        result_container = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        txt_preview = ctk.CTkTextbox(result_container, height=300, width=500, font=("Courier New", 12))

        def run_24v():
            p = filedialog.askopenfilename(filetypes=[("Log", "*.txt")])
            if not p: return
            out, seen = [], set()
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        s = line.find("{");
                        d = ast.literal_eval(line[s:line.rfind("}") + 1])
                        if float(d.get('battery_voltage', 0)) > 20.0:
                            imei = d.get('imei')
                            if imei and imei not in seen:
                                out.append(f"IMEI: {imei} | Vehicle: {d.get('vehicle_license', 'N/A')}")
                                seen.add(imei)
                    except:
                        continue
            if out:
                result_container.pack(fill="both", expand=True, padx=20, pady=10)
                txt_preview.delete("1.0", "end");
                txt_preview.insert("end", "\n".join(out))
                txt_preview.pack(pady=10);
                btn_copy.pack(pady=5)
            else:
                messagebox.showinfo("Info", "No devices found.")

        ctk.CTkButton(self.current_frame, text="Process Log", height=50, command=run_24v).pack(pady=10)
        btn_copy = ctk.CTkButton(result_container, text="Copy Results", fg_color="#2ecc71",
                                 command=lambda: pyperclip.copy(txt_preview.get("1.0", "end-1c")))

    # --- 6. 0 SATELLITES ---
    def show_0_satellites(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="0 Satellites devices", font=("Arial", 18, "bold")).pack(pady=20)
        result_container = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        txt_preview = ctk.CTkTextbox(result_container, height=300, width=500, font=("Courier New", 12))

        def run_0sat():
            p = filedialog.askopenfilename(filetypes=[("Log", "*.txt")])
            if not p: return
            out, seen = [], set()
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        s = line.find("{");
                        d = ast.literal_eval(line[s:line.rfind("}") + 1])
                        if d.get('satellites') == 0:
                            imei = d.get('imei')
                            if imei and imei not in seen:
                                out.append(f"IMEI: {imei} | Vehicle: {d.get('vehicle_license', 'N/A')}")
                                seen.add(imei)
                    except:
                        continue
            if out:
                result_container.pack(fill="both", expand=True, padx=20, pady=10)
                txt_preview.delete("1.0", "end");
                txt_preview.insert("end", "\n".join(out))
                txt_preview.pack(pady=10);
                btn_copy.pack(pady=5)
            else:
                messagebox.showinfo("Info", "No devices found.")

        ctk.CTkButton(self.current_frame, text="Process Log for 0 Sat", height=50, command=run_0sat).pack(pady=10)
        btn_copy = ctk.CTkButton(result_container, text="Copy Results", fg_color="#2ecc71",
                                 command=lambda: pyperclip.copy(txt_preview.get("1.0", "end-1c")))

    # --- 7. MERGER EXCEL ---
    def show_merger(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        paths = [None, None, None];
        labels = []
        ctk.CTkLabel(self.current_frame, text="Excel Merger by IMEI", font=("Arial", 18, "bold")).pack(pady=15)

        def sel(i):
            p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
            if p: paths[i] = p; labels[i].configure(text=os.path.basename(p), text_color="green")

        for n in ["Gps/Can", "Device", "Vehicles"]:
            f = ctk.CTkFrame(self.current_frame);
            f.pack(fill="x", padx=40, pady=5)
            ctk.CTkLabel(f, text=n, width=120).pack(side="left")
            ctk.CTkButton(f, text="Select", width=80, command=lambda x=len(labels): sel(x)).pack(side="right")
            lbl = ctk.CTkLabel(f, text="Waiting file...", text_color="gray");
            lbl.pack(side="right");
            labels.append(lbl)

        def fusion():
            if not all(paths): return messagebox.showwarning("Warning", "Attach 3 files")
            try:
                df1, df2, df3 = pd.read_excel(paths[0]), pd.read_excel(paths[1]), pd.read_excel(paths[2])
                res = pd.merge(df1, df2, on='IMEI', how='left').merge(df3, on='IMEI', how='left')
                res.to_excel(os.path.join(os.path.expanduser("~"), "Downloads", "Kyros_Merged.xlsx"), index=False)
                messagebox.showinfo("Success", "Merged into Downloads.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(self.current_frame, text="MERGE", fg_color="green", command=fusion).pack(pady=20)

    # --- 8. DRIVERS UPDATED ---
    def show_drivers_updated(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.current_frame.pack(fill="both", expand=True)

        # 1. Frame Superior (API Key)
        api_f = ctk.CTkFrame(self.current_frame)
        api_f.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(api_f, text="X-Api-Key:").pack(side="left", padx=10)
        api_entry = ctk.CTkEntry(api_f, width=350, font=self.font_ui)
        api_entry.insert(0, self.load_api_key())
        api_entry.pack(side="left", padx=10, pady=10)

        ctk.CTkButton(api_f, text="Guardar Key", width=100, command=lambda: self.save_api_key(api_entry)).pack(
            side="left", padx=5)

        # 2. Frame Filtros (Calendario y Ejecutar)
        filter_f = ctk.CTkFrame(self.current_frame)
        filter_f.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(filter_f, text="Filtrar desde (UpdatedAt >=):").pack(side="left", padx=10)
        cal = DateEntry(filter_f, width=15, background='darkblue', foreground='white',
                        borderwidth=2, date_pattern='yyyy-mm-dd', font=self.font_ui)
        cal.pack(side="left", padx=10, pady=10)

        # 3. Tabla (Treeview)
        table_f = ctk.CTkFrame(self.current_frame)
        table_f.pack(fill="both", expand=True, padx=10, pady=10)

        style = ttk.Style()
        style.configure("Custom.Treeview", background="#ffffff", foreground="black",
                        fieldbackground="#2b2b2b", rowheight=30, font=self.font_table)
        style.configure("Custom.Treeview.Heading", background="#65C9EB", font=("Segoe UI", 12, "bold"))
        style.map("Custom.Treeview", background=[('selected', '#1f538d')])

        cols = ("Updated At", "Company", "Card Number", "Card Name")
        tree = ttk.Treeview(table_f, columns=cols, show='headings', style="Custom.Treeview")
        for col in cols:
            tree.heading(col, text=col.format()) #text=col.capitalize()
            tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(table_f, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Botón Ejecutar (en el frame de filtros)
        def run_api_process():
            for i in tree.get_children(): tree.delete(i)
            key = api_entry.get()
            if not key: return messagebox.showwarning("Error", "Falta API Key")

            headers = {'X-Api-Key': key}
            limit_date = datetime.strptime(cal.get(), "%Y-%m-%d")

            try:
                companies = api.get_companies(headers)
                drivers = api.get_drivers_ordered(headers, api.get_drivers_url, "UpdatedAt", "true", 1, 100, companies)

                for d_id, d in drivers.items():
                    d_date = datetime.strptime(d['updatedAt'][:10], "%Y-%m-%d")
                    if d_date >= limit_date:
                        tree.insert("", "end",
                                    values=(d['updatedAt'], d['company']['name'], d['cardNumber'], d['cardName']))
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(filter_f, text="EJECUTAR", fg_color="green", command=run_api_process).pack(
            side="right", padx=20)

        # Tip para copiar
        tree.bind("<Control-c>", lambda e: self.copy_table_selection(tree))
        ctk.CTkLabel(self.current_frame, text="Tip: Selecciona filas y pulsa Ctrl+C para copiar",
                     font=("Arial", 14)).pack(pady=5)

    # --- 9. SEND SMS ---
    def show_send_sms(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.current_frame.pack(fill="both", expand=True)

        # --- CONFIGURACIÓN INTERNA ---
        API_TOKEN = "862ae9c8ec06879708eb511b52cf225bf14df1b9"
        BASE_URL = "https://iot.truphone.com/api/v2.0"

        # --- INTERFAZ GRÁFICA ---
        label = ctk.CTkLabel(self.current_frame, text="Envío Masivo de SMS", font=("Arial", 18, "bold"))
        label.pack(pady=20)

        target_entry = ctk.CTkEntry(
            self.current_frame,
            placeholder_text="ICCIDs (separa varios con comas). Ej: 89441001, 89441002...",
            width=1000,
            height=30
        )
        target_entry.pack(pady=5)

        desc_msg = ctk.CTkLabel(self.current_frame, text="Mensaje personalizado:", font=("Arial", 14, "bold"))
        desc_msg.pack(anchor="w", padx=50, pady=(10, 0))

        message_text = ctk.CTkTextbox(self.current_frame, width=800, height=60, border_width=1)
        message_text.pack(pady=10)

        status_label = ctk.CTkLabel(self.current_frame, text="Listo para enviar", font=("Arial", 14, "bold"),
                                    text_color="gray")

        # --- LÓGICA DE ENVÍO REUTILIZABLE ---
        def send_sms_action(preset_text=None):
            # 1. Procesar ICCIDs (Siempre se necesitan)
            raw_input = target_entry.get().strip()
            iccid_list = [item.strip() for item in raw_input.split(",") if item.strip()]

            # 2. Obtener mensaje: Priorizamos el botón rápido, si no, leemos la caja
            if preset_text:
                message = preset_text
            else:
                message = message_text.get("1.0", "end-1c").rstrip()

            # Validación
            if not iccid_list:
                messagebox.showwarning("Error", "Debes introducir al menos un ICCID.")
                return
            if not message:
                messagebox.showwarning("Error", "El mensaje está vacío.")
                return

            # 3. Request
            headers = {
                "Authorization": f"Token {API_TOKEN}",
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json"
            }
            payload = {"iccid": iccid_list, "text": message}
            url = f"{BASE_URL}/sims/send_sms/"

            try:
                status_label.configure(text=f"Enviando: '{message}'...", text_color="orange")
                response = requests.post(url, json=payload, headers=headers, timeout=20)

                if response.status_code in [200, 201, 202]:
                    messagebox.showinfo("Éxito", f"SMS enviado: {message}")
                    # Solo borramos la caja de texto si no usamos un botón rápido
                    if not preset_text:
                        message_text.delete("1.0", "end")
                    status_label.configure(text="Enviado correctamente", text_color="green")
                else:
                    status_label.configure(text=f"Error {response.status_code}", text_color="red")
                    messagebox.showerror("Error API", f"Status: {response.status_code}")

            except Exception as e:
                messagebox.showerror("Error", str(e))
                status_label.configure(text="Error de conexión", text_color="red")

        # Botón principal (Mensaje personalizado)
        send_button = ctk.CTkButton(
            self.current_frame,
            text="Enviar SMS Personalizado",
            # fg_color="#2c3e50",
            command=send_sms_action  # Llama sin argumentos, por lo que preset_text es None
        )
        send_button.pack(pady=10)

        # --- SECCIÓN DE BOTONES RÁPIDOS ---
        desc_fast = ctk.CTkLabel(self.current_frame, text="Comandos rápidos (dispositivos Teltonika):", font=("Arial", 14, "bold"))
        desc_fast.pack(anchor="w", padx=50, pady=(20, 5))

        # Creamos un frame contenedor para los botones
        fast_buttons_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        fast_buttons_frame.pack(fill="x", padx=50)

        comandos = [
            ("CPU Reset", "  cpureset"),
            ("OEM Reset", "  oemreset"),
            ("DB6 Debug", "  runcmd:@com_obd_oem_dbg:6"),
            ("Web Connect", "  web_connect"),
            ("Tacho Connect", "  tacho_connect"),
            ("Tacho Check", "  tachocheck"),
            ("Activar filtros", "  log2sdfilterset 0;3;4;2;1"),
            ("SD format", "  sdformat"),
            ("OEM Info", "  oeminfo"),
            ("OBD Info", "  obdinfo"),
            ("Get Info", "  getinfo"),
            ("Get Version", "  getver"),
            ("Get Status", "  getstatus"),
            ("Get GPS info", "  getgps")
        ]

        # Configuración de la cuadrícula
        columnas_maximas = 4  # Ajusta este número según el ancho de tu app

        for indice, (nombre, comando) in enumerate(comandos):
            # Calculamos en qué fila y columna va cada botón
            fila = indice // columnas_maximas
            columna = indice % columnas_maximas

            btn = ctk.CTkButton(
                fast_buttons_frame,
                text=nombre,
                width=140,  # Ancho fijo para que se vean ordenados
                command=lambda c=comando.rstrip(): send_sms_action(c)
            )
            # Usamos grid en lugar de pack
            btn.grid(row=fila, column=columna, padx=5, pady=5, sticky="nsew")

        # (Opcional) Hacer que las columnas se expandan equitativamente
        for i in range(columnas_maximas):
            fast_buttons_frame.grid_columnconfigure(i, weight=1)

        status_label.pack(side="bottom", pady=20)

if __name__ == "__main__":
    App().mainloop()