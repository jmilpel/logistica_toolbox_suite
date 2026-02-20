import customtkinter as ctk
import pyperclip
import re
import os
import pandas as pd
from tkinter import messagebox, filedialog, ttk
from datetime import datetime

# Configuración de apariencia
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Logistica Toolbox Suite")
        self.geometry("1000x700")

        # Configuración de Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Kyros ToolBox", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_gen = ctk.CTkButton(self.sidebar_frame, text="IMEI / ICCID Gen", command=self.show_generator)
        self.btn_gen.grid(row=1, column=0, padx=20, pady=10)

        self.btn_ascii = ctk.CTkButton(self.sidebar_frame, text="Ascii2Hex Converter",
                                       command=self.show_ascii_converter)
        self.btn_ascii.grid(row=2, column=0, padx=20, pady=10)

        self.btn_finder = ctk.CTkButton(self.sidebar_frame, text="Log Filter IMEI", command=self.show_imei_finder)
        self.btn_finder.grid(row=3, column=0, padx=20, pady=10)

        self.btn_merger = ctk.CTkButton(self.sidebar_frame, text="Merger Excel", command=self.show_merger)
        self.btn_merger.grid(row=4, column=0, padx=20, pady=10)

        # --- CONTENEDOR PRINCIPAL ---
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.current_frame = None
        self.show_generator()  # Pantalla inicial

    def clear_frame(self):
        if self.current_frame is not None:
            self.current_frame.destroy()

    # ==========================================
    # HERRAMIENTA 1: IMEI/ICCID GENERATOR
    # ==========================================
    def show_generator(self):
        self.clear_frame()
        self.current_frame = ctk.CTkTabview(self.main_container)
        self.current_frame.pack(fill="both", expand=True)

        tab_imei = self.current_frame.add("IMEIs")
        tab_iccid = self.current_frame.add("ICCIDs")

        # UI IMEI
        ctk.CTkLabel(tab_imei, text="Pegue listado de IMEIs (15 dígitos):").pack(pady=5)
        txt_imei = ctk.CTkTextbox(tab_imei, height=200)
        txt_imei.pack(padx=20, pady=5, fill="both", expand=True)
        res_imei = ctk.CTkEntry(tab_imei, placeholder_text="Resultado...")
        res_imei.pack(padx=20, pady=5, fill="x")

        def run_imei():
            lines = txt_imei.get("1.0", "end-1c").splitlines()
            valid = [l.strip() for l in lines if len(l.strip()) == 15 and l.strip().isdigit()]
            if valid:
                res_imei.delete(0, "end")
                res_imei.insert(0, " -e " + " -e ".join(valid))

        ctk.CTkButton(tab_imei, text="Execute", command=run_imei).pack(pady=5)
        ctk.CTkButton(tab_imei, text="Copiar", border_width=1,
                      command=lambda: pyperclip.copy(res_imei.get())).pack(pady=5)

        # UI ICCID
        ctk.CTkLabel(tab_iccid, text="Pegue listado de ICCIDs (19 dígitos):").pack(pady=5)
        txt_iccid = ctk.CTkTextbox(tab_iccid, height=200)
        txt_iccid.pack(padx=20, pady=5, fill="both", expand=True)
        res_iccid = ctk.CTkEntry(tab_iccid, placeholder_text="URL resultante...")
        res_iccid.pack(padx=20, pady=5, fill="x")

        def run_iccid():
            lines = txt_iccid.get("1.0", "end-1c").splitlines()
            valid = [l.strip() for l in lines if len(l.strip()) == 19 and l.strip().isdigit()]
            if valid:
                url = f"https://iot.truphone.com/sms/?preselect={valid[0]}"
                if len(valid) > 1: url += "&preselect=" + "&preselect=".join(valid[1:])
                res_iccid.delete(0, "end")
                res_iccid.insert(0, url)

        ctk.CTkButton(tab_iccid, text="Execute", command=run_iccid).pack(pady=5)
        ctk.CTkButton(tab_iccid, text="Copiar", border_width=1,
                      command=lambda: pyperclip.copy(res_iccid.get())).pack(pady=5)

    # ==========================================
    # HERRAMIENTA 2: ASCII2HEX CONVERTER
    # ==========================================
    def show_ascii_converter(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(self.current_frame, text="Ascii2Hex Converter", font=("Arial", 16, "bold")).pack(pady=10)

        input_txt = ctk.CTkEntry(self.current_frame, placeholder_text="Introduce el texto ASCII...", width=400)
        input_txt.pack(pady=20)

        output_txt = ctk.CTkTextbox(self.current_frame, height=150)
        output_txt.pack(padx=20, pady=10, fill="x")

        def calculate_crc16_arc(hex_data):
            data = bytes.fromhex(hex_data)
            crc = 0x0000
            for byte in data:
                crc = (crc ^ byte) & 0xFFFF
                for _ in range(8):
                    if crc & 1:
                        crc = (crc >> 1) ^ 0xA001
                    else:
                        crc = crc >> 1
            return f"{crc:04X}"

        def execute_convert():
            text = input_txt.get()
            if not text: return
            hex_payload = ''.join(f'{ord(c):02x}' for c in text)

            codec_id, q1, cmd_type, q2 = "0C", "01", "05", "01"
            cmd_size = format(int(len(hex_payload) / 2), 'x').zfill(8)
            crc_base = codec_id + q1 + cmd_type + cmd_size + hex_payload + q2
            crc16 = calculate_crc16_arc(crc_base).zfill(8)
            data_size = format(int(len(crc_base) / 2), 'x').zfill(8)

            final_cmd = ("00000000" + data_size + crc_base + crc16).upper()
            output_txt.delete("1.0", "end")
            output_txt.insert("1.0", final_cmd)

        ctk.CTkButton(self.current_frame, text="Convertir", command=execute_convert).pack(pady=10)
        ctk.CTkButton(self.current_frame, text="Copiar Hex", fg_color="transparent", border_width=1,
                      command=lambda: pyperclip.copy(output_txt.get("1.0", "end-1c"))).pack()

    # ==========================================
    # HERRAMIENTA 3: LOG FILTER IMEI
    # ==========================================
    def show_imei_finder(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(self.current_frame, text="Log Filter IMEI", font=("Arial", 16, "bold")).pack(pady=10)
        ctk.CTkLabel(self.current_frame, text="Extrae IMEIs únicos en formato [123...] de un .txt",
                     font=("Arial", 10)).pack()

        def procesar():
            path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
            if not path: return
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                found = sorted(set(re.findall(r"\[(\d{15})\]", content)))

                if found:
                    out_path = os.path.join(os.path.expanduser("~"), "Downloads",
                                            f"{os.path.basename(path)[:-4]}_IMEIs_unicos.txt")
                    with open(out_path, "w") as f:
                        f.write("\n".join(found))
                    messagebox.showinfo("Éxito", f"Guardado en Descargas: {len(found)} IMEIs")
                else:
                    messagebox.showwarning("Aviso", "No se encontraron IMEIs con formato [dígitos]")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(self.current_frame, text="Seleccionar Archivo y Filtrar", command=procesar, height=50).pack(
            pady=40)

    # ==========================================
    # HERRAMIENTA 4: MERGER EXCEL
    # ==========================================
    def show_merger(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self.main_container)
        self.current_frame.pack(fill="both", expand=True)

        paths = [None, None, None]
        labels = []

        ctk.CTkLabel(self.current_frame, text="Merger Excel (Cruce por IMEI)", font=("Arial", 16, "bold")).pack(pady=10)

        def sel(i):
            p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
            if p:
                paths[i] = p
                labels[i].configure(text=os.path.basename(p), text_color="#4CAF50")

        for i, name in enumerate(["Informe GPS/CAN", "Archivo Vehículos", "Archivo Dispositivos"]):
            f = ctk.CTkFrame(self.current_frame)
            f.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(f, text=name, width=150, anchor="w").pack(side="left", padx=10)
            btn = ctk.CTkButton(f, text="Seleccionar", width=100, command=lambda x=i: sel(x))
            btn.pack(side="right", padx=10)
            lbl = ctk.CTkLabel(f, text="No seleccionado", text_color="gray")
            lbl.pack(side="right")
            labels.append(lbl)

        def merge():
            if not all(paths):
                messagebox.showerror("Error", "Faltan archivos")
                return
            try:
                df1, df2, df3 = pd.read_excel(paths[0]), pd.read_excel(paths[1]), pd.read_excel(paths[2])
                res = pd.merge(df1, df2, on='IMEI', how='left').merge(df3, on='IMEI', how='left')
                out = os.path.join(os.path.expanduser("~"), "Downloads",
                                   f"Merged_{datetime.now().strftime('%H%M%S')}.xlsx")
                res.to_excel(out, index=False)
                messagebox.showinfo("Éxito", f"Excel generado en Descargas")
            except Exception as e:
                messagebox.showerror("Error", f"Asegúrate de que todos tengan columna 'IMEI'\n{e}")

        ctk.CTkButton(self.current_frame, text="FUSIONAR ARCHIVOS", fg_color="#27ae60", height=40, command=merge).pack(
            pady=20)


if __name__ == "__main__":
    app = App()
    app.mainloop()