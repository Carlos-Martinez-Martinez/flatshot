import os
import numpy as np
from pathlib import Path
from PIL import Image
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame, 
                             QSlider, QDoubleSpinBox, QSpinBox, QDialogButtonBox, QFileDialog, 
                             QFormLayout, QLineEdit, QComboBox, QCheckBox, QColorDialog, QGroupBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QPen
from flatshot.ui.widgets import CurveGraphWidget
from flatshot.core.models import ExportConfig
from flatshot.ui.styles import COLORS

class CurveEditorDialog(QDialog):
    def __init__(self, current_curve, folder_path, current_padding, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calibrar escala - Control geométrico")
        self.resize(1350, 850) 
        self.curve = current_curve.copy() 
        self.folder_path = None  # Don't inherit from main - let user choose
        self.padding_percent = current_padding
        self.samples = {} 
        
        self.init_ui()
        # Start with abstract samples, don't auto-load
        self.create_abstract_samples()
    
    def _set_label_class(self, label: QLabel, class_name: str):
        label.setProperty("class", class_name)
        try:
            label.style().unpolish(label)
            label.style().polish(label)
        except Exception:
            pass

    def init_ui(self):
        self.setProperty("class", "dialog")
        main_layout = QVBoxLayout(self)
        
        info_card = QFrame()
        info_card.setProperty("class", "dialog-card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(10, 8, 10, 8)
        info = QLabel(f"<b>Sistema de 5 Puntos:</b> Control basado en la geometría de la imagen.<br>"
                      "Las imágenes se clasifican automáticamente desde <b>Formato Vertical</b> hasta <b>Formato Horizontal</b>.")
        info.setProperty("class", "dialog-text")
        info.setWordWrap(True)
        info_layout.addWidget(info)
        main_layout.addWidget(info_card)

        # Folder selection row
        folder_row = QHBoxLayout()
        btn_load = QPushButton("Cargar muestras reales")
        btn_load.setProperty("class", "primary")
        btn_load.clicked.connect(self.select_sample_folder)
        folder_row.addWidget(btn_load)
        
        self.lbl_folder = QLabel("Ninguna carpeta cargada")
        self.lbl_folder.setProperty("class", "muted")
        folder_row.addWidget(self.lbl_folder)
        folder_row.addStretch()
        main_layout.addLayout(folder_row)

        cards_layout = QHBoxLayout(); cards_layout.setSpacing(10)
        self.inputs = {}

        cats = [
            ('c1_narrow',   'ESTRECHO',       "Vertical (Pantalones / Vestidos)", 0.98),
            ('c2_semi',     'SEMI-ESTRECHO',  "Vertical Corto (Camisetas)",     0.75), 
            ('c3_regular',  'REGULAR',        "Cuadrado (Jerséis / Sudaderas)",   0.85),
            ('c4_wide',     'ANCHO',          "Horizontal (Chaquetas)",         0.90),
            ('c5_xwide',    'MUY ANCHO',      "Panorámico (Oversize)",          0.95)
        ]
        
        saved_fp = self.curve.get('fp', [])
        if len(saved_fp) != 5:
            saved_fp = [0.98, 0.75, 0.85, 0.90, 0.95]
        
        for i, (key, title, sub, def_val) in enumerate(cats):
            frame = QFrame(); frame.setProperty("class", "card")
            l = QVBoxLayout(frame); l.setContentsMargins(5,5,5,5)
            
            l.addWidget(QLabel(f"<b>{title}</b>"))
            sub_lbl = QLabel(sub); sub_lbl.setProperty("class", "accent-text")
            l.addWidget(sub_lbl)
            
            img_lbl = QLabel("..."); img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_lbl.setMinimumSize(220, 300) 
            img_lbl.setProperty("class", "image-swatch")
            l.addWidget(img_lbl)
            
            slider_h = QHBoxLayout()
            sl = QSlider(Qt.Orientation.Vertical)
            sl.setRange(50, 120); sl.setFixedHeight(150)
            
            val = saved_fp[i]
            sl.setValue(int(val * 100))
            
            sp = QDoubleSpinBox(); sp.setRange(0.5, 1.2); sp.setSingleStep(0.01)
            sp.setValue(val); sp.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            sp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            sl.valueChanged.connect(lambda v, s=sp: s.setValue(v/100.0))
            sp.valueChanged.connect(lambda v, s=sl: s.setValue(int(v*100)))
            
            slider_h.addWidget(sl); slider_h.addWidget(sp)
            l.addLayout(slider_h)
            
            sp.valueChanged.connect(self.refresh_preview)
            self.inputs[key] = {'lbl': img_lbl, 'spin': sp, 'ar': 0.5} 
            cards_layout.addWidget(frame)

        main_layout.addLayout(cards_layout)
        
        self.graph = CurveGraphWidget()
        main_layout.addWidget(self.graph)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        btn_save = btns.button(QDialogButtonBox.StandardButton.Save)
        if btn_save:
            btn_save.setProperty("class", "primary")
        btn_cancel = btns.button(QDialogButtonBox.StandardButton.Cancel)
        if btn_cancel:
            btn_cancel.setProperty("class", "ghost")
        main_layout.addWidget(btns)

    def select_sample_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Carpeta")
        if d: self.folder_path = d; self.load_samples()

    def load_samples(self):
        if not self.folder_path: self.create_abstract_samples(); return
        try:
            exts = {'.png', '.jpg', '.jpeg'}
            files = [f for f in Path(self.folder_path).iterdir() if f.suffix.lower() in exts]
            if not files: return
            
            data = []
            for f in files[:150]:
                try:
                    with Image.open(f) as im:
                        bbox = im.getbbox()
                        if bbox:
                            w = bbox[2]-bbox[0]; h = bbox[3]-bbox[1]
                            data.append({'ar': w/h, 'img': im.copy(), 'path': f})
                except: pass
            
            if not data: return
            data.sort(key=lambda x: x['ar'])
            
            targets = [0.35, 0.60, 0.85, 1.10, 1.40]
            keys = ['c1_narrow', 'c2_semi', 'c3_regular', 'c4_wide', 'c5_xwide']
            
            # Use each image only once - remove after selection
            available = data.copy()
            for key, target in zip(keys, targets):
                if not available:
                    break
                closest = min(available, key=lambda x: abs(x['ar'] - target))
                self.samples[key] = closest
                self.inputs[key]['ar'] = closest['ar']
                available.remove(closest)  # Remove so it can't be used again
            
            # Update UI with folder info
            folder_name = Path(self.folder_path).name
            self.setWindowTitle(f"Calibrar escala - {folder_name}")
            self.lbl_folder.setText(f"📁 {self.folder_path}")
            self._set_label_class(self.lbl_folder, "success-text")
            
            self.refresh_preview()
        except Exception as e: 
            print(e)
            self.create_abstract_samples()

    def create_abstract_samples(self):
        keys = ['c1_narrow', 'c2_semi', 'c3_regular', 'c4_wide', 'c5_xwide']
        ars = [0.35, 0.60, 0.85, 1.10, 1.40]
        colors = [(100,120,140), (100,140,160), (120,160,120), (160,140,100), (160,100,100)]
        
        for k, ar, col in zip(keys, ars, colors):
            im = Image.new("RGBA", (600, 800), (0,0,0,0))
            w = int(500 * ar) if ar < 1 else 500
            h = int(500 / ar) if ar > 1 else 500
            
            rect = Image.new("RGBA", (w,h), (*col, 255))
            im.paste(rect, ((600-w)//2, (800-h)//2))
            
            self.samples[k] = {'ar': ar, 'img': im}
        self.refresh_preview()

    def get_current_curve(self):
        keys = ['c1_narrow', 'c2_semi', 'c3_regular', 'c4_wide', 'c5_xwide']
        
        xp = [0.35, 0.60, 0.85, 1.10, 1.40]
        fp = [self.inputs[k]['spin'].value() for k in keys]
        
        final_xp = [0.0] + xp + [3.0]
        final_fp = [fp[0]] + fp + [fp[-1]]
        
        return {'xp': final_xp, 'fp': final_fp}

    def refresh_preview(self, *args):
        curve = self.get_current_curve()
        self.graph.update_data(curve)
        
        canvas_w, canvas_h = 220, 300
        pad = self.padding_percent / 100.0
        safe_w = int(canvas_w * (1.0 - pad))
        safe_h = int(canvas_h * (1.0 - pad))
        
        keys = ['c1_narrow', 'c2_semi', 'c3_regular', 'c4_wide', 'c5_xwide']
        
        for key in keys:
            if key not in self.samples or not self.samples[key]: continue
            item = self.samples[key]
            img = item['img']
            real_ar = item['ar']
            
            s_fit_h = safe_h / img.height
            s_fit_w = safe_w / img.width
            mix = np.interp(real_ar, [0.4, 1.0], [0.0, 1.0])
            base_scale = s_fit_h * (1-mix) + s_fit_w * mix
            
            adj = np.interp(real_ar, curve['xp'], curve['fp'])
            final_scale = base_scale * adj
            
            pw = img.width * final_scale; ph = img.height * final_scale
            if pw > safe_w: final_scale = safe_w / img.width
            if ph > safe_h: final_scale = min(final_scale, safe_h / img.height)
            
            tgt_w = int(img.width * final_scale)
            tgt_h = int(img.height * final_scale)
            
            base = QImage(canvas_w, canvas_h, QImage.Format.Format_RGB32)
            base.fill(QColor("#21252B"))
            p = QPainter(base)
            
            pen = QPen(QColor("#E06C75")); pen.setStyle(Qt.PenStyle.DashLine)
            p.setPen(pen)
            off_x = (canvas_w - safe_w)//2; off_y = (canvas_h - safe_h)//2
            p.drawRect(off_x, off_y, safe_w, safe_h)
            
            resized = img.resize((max(1,tgt_w), max(1,tgt_h)), Image.Resampling.NEAREST)
            if resized.mode == "RGBA":
                d = resized.tobytes("raw", "RGBA")
                qim = QImage(d, resized.width, resized.height, resized.width * 4, QImage.Format.Format_RGBA8888).copy()
            else:
                resized_rgba = resized.convert("RGBA")
                d = resized_rgba.tobytes("raw", "RGBA")
                qim = QImage(d, resized_rgba.width, resized_rgba.height, resized_rgba.width * 4, QImage.Format.Format_RGBA8888).copy()
            
            x = (canvas_w - tgt_w)//2; y = (canvas_h - tgt_h)//2
            p.drawImage(x, y, qim)
            p.end()
            
            self.inputs[key]['lbl'].setPixmap(QPixmap.fromImage(base))

class ExportConfigDialog(QDialog):
    """Dialog for configuring export settings."""
    
    SIZE_PRESETS = {
        "Estándar (1800×2400)": (1800, 2400),
        "Amazon (1500×2000)": (1500, 2000),
        "Web pequeño (1200×1600)": (1200, 1600),
        "Alta resolución (2400×3200)": (2400, 3200),
        "Personalizado": None
    }
    
    def __init__(self, current_settings: ExportConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de exportación")
        self.setMinimumWidth(480)
        self.settings = current_settings
        self.init_ui()

    def init_ui(self):
        self.setProperty("class", "dialog")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # === OUTPUT SIZE ===
        size_group = QGroupBox("📐 Tamaño de salida")
        size_layout = QFormLayout(size_group)
        size_layout.setSpacing(10)
        
        self.cmb_size_preset = QComboBox()
        self.cmb_size_preset.addItems(self.SIZE_PRESETS.keys())
        self.cmb_size_preset.currentTextChanged.connect(self._on_size_preset_changed)
        size_layout.addRow("Preset:", self.cmb_size_preset)
        
        size_row = QHBoxLayout()
        self.spin_width = QSpinBox()
        self.spin_width.setRange(100, 10000)
        self.spin_width.setValue(self.settings.output_width)
        self.spin_width.setSuffix(" px")
        size_row.addWidget(QLabel("Ancho:"))
        size_row.addWidget(self.spin_width)
        size_row.addSpacing(20)
        size_row.addWidget(QLabel("Alto:"))
        self.spin_height = QSpinBox()
        self.spin_height.setRange(100, 10000)
        self.spin_height.setValue(self.settings.output_height)
        self.spin_height.setSuffix(" px")
        size_row.addWidget(self.spin_height)
        size_row.addStretch()
        size_layout.addRow("", size_row)
        
        layout.addWidget(size_group)
        
        # === NAMING ===
        naming_group = QGroupBox("📝 Nomenclatura")
        naming_layout = QFormLayout(naming_group)
        naming_layout.setSpacing(10)
        
        self.txt_folder = QLineEdit(self.settings.output_folder_name)
        naming_layout.addRow("Carpeta salida:", self.txt_folder)
        
        self.txt_suffix = QLineEdit(self.settings.suffix)
        self.txt_suffix.textChanged.connect(self._update_naming_preview)
        naming_layout.addRow("Sufijo:", self.txt_suffix)
        
        self.txt_template = QLineEdit(self.settings.naming_template)
        self.txt_template.setPlaceholderText("{original}{suffix}")
        self.txt_template.textChanged.connect(self._update_naming_preview)
        naming_layout.addRow("Plantilla:", self.txt_template)
        
        help_text = QLabel("Tokens: {original}, {suffix}, {folder}, {index}")
        help_text.setProperty("class", "muted")
        naming_layout.addRow("", help_text)
        
        self.lbl_naming_preview = QLabel("")
        self.lbl_naming_preview.setProperty("class", "accent-text")
        naming_layout.addRow("Ejemplo:", self.lbl_naming_preview)
        
        layout.addWidget(naming_group)
        
        # === FORMAT ===
        format_group = QGroupBox("🖼️ Formato")
        format_layout = QFormLayout(format_group)
        format_layout.setSpacing(10)
        
        self.cmb_format = QComboBox()
        self.cmb_format.addItems(["JPG", "PNG"])
        self.cmb_format.setCurrentText(self.settings.format)
        self.cmb_format.currentTextChanged.connect(self._toggle_transparency)
        format_layout.addRow("Formato:", self.cmb_format)
        
        self.chk_transparent = QCheckBox("Fondo transparente (solo PNG)")
        self.chk_transparent.setChecked(self.settings.transparent_bg)
        self.chk_transparent.toggled.connect(self._toggle_color)
        format_layout.addRow("", self.chk_transparent)
        
        color_row = QHBoxLayout()
        self.btn_color = QPushButton()
        self.btn_color.setFixedSize(80, 28)
        self.btn_color.setProperty("class", "swatch")
        self.current_color = tuple(self.settings.bg_color) if isinstance(self.settings.bg_color, list) else self.settings.bg_color
        self._update_color_btn()
        self.btn_color.clicked.connect(self._pick_color)
        color_row.addWidget(self.btn_color)
        color_row.addStretch()
        format_layout.addRow("Color fondo:", color_row)
        
        layout.addWidget(format_group)
        
        # Buttons
        layout.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        btn_ok = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if btn_ok:
            btn_ok.setProperty("class", "primary")
        btn_cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if btn_cancel:
            btn_cancel.setProperty("class", "ghost")
        layout.addWidget(buttons)
        
        # Init state
        self._detect_size_preset()
        self._toggle_transparency(self.settings.format)
        self._toggle_color()
        self._update_naming_preview()
    
    def _detect_size_preset(self):
        current = (self.settings.output_width, self.settings.output_height)
        for name, size in self.SIZE_PRESETS.items():
            if size == current:
                self.cmb_size_preset.setCurrentText(name)
                return
        self.cmb_size_preset.setCurrentText("Personalizado")
    
    def _on_size_preset_changed(self, preset_name: str):
        size = self.SIZE_PRESETS.get(preset_name)
        if size:
            self.spin_width.setValue(size[0])
            self.spin_height.setValue(size[1])
            self.spin_width.setEnabled(False)
            self.spin_height.setEnabled(False)
        else:
            self.spin_width.setEnabled(True)
            self.spin_height.setEnabled(True)
    
    def _update_naming_preview(self):
        template = self.txt_template.text() or "{original}{suffix}"
        suffix = self.txt_suffix.text()
        result = template.replace("{original}", "producto_001").replace("{suffix}", suffix).replace("{folder}", "Camisetas").replace("{index}", "001")
        fmt = self.cmb_format.currentText().lower()
        self.lbl_naming_preview.setText(f"{result}.{fmt}")

    def _update_color_btn(self):
        c = self.current_color
        self.btn_color.setStyleSheet(f"background-color: rgb({c[0]},{c[1]},{c[2]});")
    
    def _pick_color(self):
        c = self.current_color
        new_col = QColorDialog.getColor(QColor(c[0], c[1], c[2]), self, "Seleccionar fondo")
        if new_col.isValid():
            self.current_color = (new_col.red(), new_col.green(), new_col.blue())
            self._update_color_btn()
    
    def _toggle_transparency(self, fmt):
        if fmt == "JPG":
            self.chk_transparent.setChecked(False)
            self.chk_transparent.setEnabled(False)
        else:
            self.chk_transparent.setEnabled(True)
    
    def _toggle_color(self):
        self.btn_color.setEnabled(not self.chk_transparent.isChecked())
    
    def get_settings(self) -> ExportConfig:
        return ExportConfig(
            output_folder_name=self.txt_folder.text(),
            suffix=self.txt_suffix.text(),
            format=self.cmb_format.currentText(),
            transparent_bg=self.chk_transparent.isChecked(),
            bg_color=self.current_color,
            output_width=self.spin_width.value(),
            output_height=self.spin_height.value(),
            naming_template=self.txt_template.text() or "{original}{suffix}"
        )

