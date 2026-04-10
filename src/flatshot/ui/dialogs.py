import os
import numpy as np
from pathlib import Path
from PIL import Image
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame, 
                             QSlider, QDoubleSpinBox, QSpinBox, QDialogButtonBox, QFileDialog, 
                             QFormLayout, QLineEdit, QComboBox, QCheckBox, QGroupBox,
                             QGridLayout, QRadioButton)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QPen
from flatshot.ui.widgets import CurveGraphWidget
from flatshot.core.models import ExportConfig
from flatshot.ui.styles import COLORS
from flatshot.workers.export_worker import apply_naming_template

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

    COLOR_SWATCHES = [
        ("Gris FlatShot", (230, 230, 230)),
        ("Blanco puro", (255, 255, 255)),
        ("Marfil", (246, 244, 239)),
        ("Arena", (234, 229, 219)),
        ("Gris frío", (216, 221, 227)),
        ("Piedra", (204, 204, 204)),
        ("Grafito", (36, 38, 41)),
        ("Negro", (12, 12, 12)),
    ]
    
    def __init__(self, current_settings: ExportConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de exportación")
        self.setMinimumWidth(620)
        self.settings = current_settings
        self.current_color = tuple(self.settings.bg_color) if isinstance(self.settings.bg_color, list) else self.settings.bg_color
        self.custom_output_path = Path(self.settings.custom_output_path) if self.settings.custom_output_path else None
        self._updating_size_fields = False
        self.init_ui()

    def init_ui(self):
        self.setProperty("class", "dialog")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("Configuración de exportación")
        header.setProperty("class", "dialog-title")
        layout.addWidget(header)

        subtitle = QLabel(
            "Configura tamaño, destino, nombre de archivo y fondo en un único panel."
        )
        subtitle.setProperty("class", "dialog-text")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        summary_card = QFrame()
        summary_card.setProperty("class", "dialog-card")
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(12, 10, 12, 10)
        summary_layout.setSpacing(4)
        summary_title = QLabel("Resumen")
        summary_title.setProperty("class", "dialog-section")
        summary_layout.addWidget(summary_title)
        self.lbl_summary = QLabel("")
        self.lbl_summary.setProperty("class", "dialog-text")
        self.lbl_summary.setWordWrap(True)
        summary_layout.addWidget(self.lbl_summary)
        self.lbl_summary_example = QLabel("")
        self.lbl_summary_example.setProperty("class", "accent-text")
        self.lbl_summary_example.setWordWrap(True)
        summary_layout.addWidget(self.lbl_summary_example)
        layout.addWidget(summary_card)

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
        self.spin_width.valueChanged.connect(self._on_custom_size_changed)
        size_row.addWidget(QLabel("Ancho:"))
        size_row.addWidget(self.spin_width)
        size_row.addSpacing(20)
        size_row.addWidget(QLabel("Alto:"))
        self.spin_height = QSpinBox()
        self.spin_height.setRange(100, 10000)
        self.spin_height.setValue(self.settings.output_height)
        self.spin_height.setSuffix(" px")
        self.spin_height.valueChanged.connect(self._on_custom_size_changed)
        size_row.addWidget(self.spin_height)
        size_row.addStretch()
        size_layout.addRow("", size_row)
        
        layout.addWidget(size_group)
        
        # === NAMING ===
        naming_group = QGroupBox("📝 Nomenclatura")
        naming_layout = QFormLayout(naming_group)
        naming_layout.setSpacing(10)
        
        self.txt_folder = QLineEdit(self.settings.output_folder_name)
        self.txt_folder.textChanged.connect(self._update_summary)
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

        # === DESTINATION ===
        destination_group = QGroupBox("📦 Destino")
        destination_layout = QVBoxLayout(destination_group)
        destination_layout.setSpacing(10)

        self.rb_dest_subfolder = QRadioButton("Crear una subcarpeta dentro de cada carpeta de origen")
        self.rb_dest_subfolder.toggled.connect(self._toggle_destination_mode)
        destination_layout.addWidget(self.rb_dest_subfolder)

        custom_row = QHBoxLayout()
        custom_row.setSpacing(8)
        self.rb_dest_custom = QRadioButton("Enviar todas las exportaciones a una carpeta fija")
        self.rb_dest_custom.toggled.connect(self._toggle_destination_mode)
        custom_row.addWidget(self.rb_dest_custom, 1)

        self.btn_choose_dest = QPushButton("Elegir carpeta…")
        self.btn_choose_dest.setProperty("class", "secondary")
        self.btn_choose_dest.clicked.connect(self._choose_custom_destination)
        custom_row.addWidget(self.btn_choose_dest)
        destination_layout.addLayout(custom_row)

        self.lbl_custom_dest = QLabel("")
        self.lbl_custom_dest.setProperty("class", "muted")
        self.lbl_custom_dest.setWordWrap(True)
        destination_layout.addWidget(self.lbl_custom_dest)

        layout.addWidget(destination_group)
        
        # === FORMAT ===
        format_group = QGroupBox("🖼️ Formato")
        format_layout = QFormLayout(format_group)
        format_layout.setSpacing(10)
        
        self.cmb_format = QComboBox()
        self.cmb_format.addItems(["JPG", "PNG"])
        self.cmb_format.setCurrentText(self.settings.format)
        self.cmb_format.currentTextChanged.connect(self._toggle_transparency)
        self.cmb_format.currentTextChanged.connect(self._update_naming_preview)
        format_layout.addRow("Formato:", self.cmb_format)
        
        self.chk_transparent = QCheckBox("Fondo transparente (solo PNG)")
        self.chk_transparent.setChecked(self.settings.transparent_bg)
        self.chk_transparent.toggled.connect(self._toggle_color)
        format_layout.addRow("", self.chk_transparent)
        
        color_row = QHBoxLayout()
        self.btn_color = QPushButton()
        self.btn_color.setFixedSize(110, 30)
        self.btn_color.setProperty("class", "swatch")
        self.lbl_color_value = QLabel("")
        self.lbl_color_value.setProperty("class", "muted")
        self.swatch_buttons = []
        self._update_color_btn()
        self.btn_color.clicked.connect(self._pick_color)
        color_row.addWidget(self.btn_color)
        color_row.addWidget(self.lbl_color_value)
        color_row.addStretch()
        format_layout.addRow("Color fondo:", color_row)

        swatch_container = QFrame()
        swatch_container.setProperty("class", "swatch-group")
        swatch_layout = QGridLayout(swatch_container)
        swatch_layout.setContentsMargins(8, 8, 8, 8)
        swatch_layout.setHorizontalSpacing(6)
        swatch_layout.setVerticalSpacing(6)
        for index, (label, color) in enumerate(self.COLOR_SWATCHES):
            btn = QPushButton("")
            btn.setCheckable(True)
            btn.setToolTip(label)
            btn.setProperty("class", "swatch-btn")
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(
                "QPushButton {"
                f"background-color: rgb({color[0]}, {color[1]}, {color[2]});"
                f"border: 1px solid {COLORS['border']};"
                "border-radius: 6px;"
                "}"
            )
            btn.clicked.connect(lambda _checked=False, swatch=color: self._select_quick_color(swatch))
            self.swatch_buttons.append((btn, color))
            swatch_layout.addWidget(btn, index // 4, index % 4)
        format_layout.addRow("Colores rápidos:", swatch_container)
        
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
        if self.settings.output_destination == "custom":
            self.rb_dest_custom.setChecked(True)
        else:
            self.rb_dest_subfolder.setChecked(True)
        self._toggle_transparency(self.settings.format)
        self._toggle_destination_mode()
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
        self._updating_size_fields = True
        if size:
            self.spin_width.setValue(size[0])
            self.spin_height.setValue(size[1])
            self.spin_width.setEnabled(False)
            self.spin_height.setEnabled(False)
        else:
            self.spin_width.setEnabled(True)
            self.spin_height.setEnabled(True)
        self._updating_size_fields = False
        self._update_summary()

    def _on_custom_size_changed(self):
        if self._updating_size_fields:
            return
        current = (self.spin_width.value(), self.spin_height.value())
        matched = "Personalizado"
        for name, size in self.SIZE_PRESETS.items():
            if size == current:
                matched = name
                break
        self.cmb_size_preset.blockSignals(True)
        self.cmb_size_preset.setCurrentText(matched)
        self.cmb_size_preset.blockSignals(False)
        self.spin_width.setEnabled(matched == "Personalizado")
        self.spin_height.setEnabled(matched == "Personalizado")
        self._update_summary()
    
    def _update_naming_preview(self):
        template = self.txt_template.text() or "{original}{suffix}"
        suffix = self.txt_suffix.text()
        try:
            result = apply_naming_template(
                template,
                "producto_001",
                suffix,
                "Camisetas",
                1,
            )
        except Exception:
            result = "Plantilla no válida"
        fmt = self.cmb_format.currentText().lower()
        self.lbl_naming_preview.setText(f"{result}.{fmt}")
        self._update_summary()

    def _update_color_btn(self):
        c = self.current_color
        self.btn_color.setText("Seleccionar")
        self.btn_color.setStyleSheet(
            "QPushButton {"
            f"background-color: rgb({c[0]},{c[1]},{c[2]});"
            f"border: 1px solid {COLORS['border']};"
            "border-radius: 6px;"
            f"color: {'#111111' if sum(c) > 540 else COLORS['text_primary']};"
            "font-weight: 600;"
            "}"
        )
        self.lbl_color_value.setText(self._color_to_hex(c))
        for btn, swatch in self.swatch_buttons:
            btn.blockSignals(True)
            btn.setChecked(tuple(swatch) == tuple(self.current_color))
            btn.blockSignals(False)
    
    def _pick_color(self):
        dialog = ColorPickerDialog(self.current_color, self)
        if dialog.exec():
            self.current_color = dialog.get_color()
            self._update_color_btn()
            self._update_summary()

    def _select_quick_color(self, color: tuple[int, int, int]):
        self.current_color = color
        self._update_color_btn()
        self._update_summary()
    
    def _toggle_transparency(self, fmt):
        if fmt == "JPG":
            self.chk_transparent.setChecked(False)
            self.chk_transparent.setEnabled(False)
        else:
            self.chk_transparent.setEnabled(True)
        self._update_summary()
    
    def _toggle_color(self):
        is_enabled = not self.chk_transparent.isChecked()
        self.btn_color.setEnabled(is_enabled)
        for btn, _swatch in self.swatch_buttons:
            btn.setEnabled(is_enabled)
        self.lbl_color_value.setEnabled(is_enabled)
        self._update_summary()

    def _toggle_destination_mode(self):
        use_custom = self.rb_dest_custom.isChecked()
        self.btn_choose_dest.setEnabled(use_custom)
        has_path = bool(self.custom_output_path)
        if use_custom and has_path:
            self.lbl_custom_dest.setText(str(self.custom_output_path))
            self.lbl_custom_dest.show()
        elif use_custom:
            self.lbl_custom_dest.setText("No has elegido una carpeta de destino todavía.")
            self.lbl_custom_dest.show()
        else:
            self.lbl_custom_dest.hide()
        self._update_summary()

    def _choose_custom_destination(self):
        initial_dir = str(self.custom_output_path) if self.custom_output_path else str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Elegir carpeta de destino", initial_dir)
        if folder:
            self.custom_output_path = Path(folder)
            self.lbl_custom_dest.setText(folder)
            self.lbl_custom_dest.show()
            self._update_summary()

    def _update_summary(self):
        size_text = f"{self.spin_width.value()} × {self.spin_height.value()} px"
        format_text = self.cmb_format.currentText()
        if self.chk_transparent.isChecked():
            bg_text = "Fondo transparente"
        else:
            bg_text = f"Fondo {self._color_to_hex(self.current_color)}"
        if self.rb_dest_custom.isChecked():
            if self.custom_output_path:
                destination_text = f"Carpeta fija: {self.custom_output_path}"
            else:
                destination_text = "Carpeta fija pendiente de elegir"
        else:
            folder_name = self.txt_folder.text().strip() or "_SALIDA_PRO"
            destination_text = f"Subcarpeta por origen: {folder_name}"

        self.lbl_summary.setText(
            f"{size_text} · {format_text} · {bg_text}\n{destination_text}"
        )
        self.lbl_summary_example.setText(f"Salida de ejemplo: {self.lbl_naming_preview.text()}")

    @staticmethod
    def _color_to_hex(color: tuple[int, int, int]) -> str:
        return "#{:02X}{:02X}{:02X}".format(*color)
    
    def get_settings(self) -> ExportConfig:
        return ExportConfig(
            output_folder_name=self.txt_folder.text(),
            suffix=self.txt_suffix.text(),
            format=self.cmb_format.currentText(),
            transparent_bg=self.chk_transparent.isChecked(),
            bg_color=self.current_color,
            output_width=self.spin_width.value(),
            output_height=self.spin_height.value(),
            naming_template=self.txt_template.text() or "{original}{suffix}",
            output_destination="custom" if self.rb_dest_custom.isChecked() else "subfolder",
            custom_output_path=str(self.custom_output_path) if self.custom_output_path else None,
        )


class ColorPickerDialog(QDialog):
    """Small in-app color picker aligned with FlatShot's visual style."""

    QUICK_COLORS = ExportConfigDialog.COLOR_SWATCHES

    def __init__(self, current_color, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar color de fondo")
        self.setMinimumWidth(420)
        self.current_color = tuple(current_color)
        self._syncing = False
        self.swatch_buttons = []
        self.init_ui()
        self._set_color(self.current_color)

    def init_ui(self):
        self.setProperty("class", "dialog")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Color de fondo")
        title.setProperty("class", "dialog-title")
        layout.addWidget(title)

        subtitle = QLabel(
            "Usa un color rápido o ajusta el valor manualmente con HEX y RGB."
        )
        subtitle.setProperty("class", "dialog-text")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        preview_card = QFrame()
        preview_card.setProperty("class", "dialog-card")
        preview_layout = QHBoxLayout(preview_card)
        preview_layout.setContentsMargins(12, 12, 12, 12)
        preview_layout.setSpacing(12)

        self.preview_chip = QFrame()
        self.preview_chip.setProperty("class", "image-swatch")
        self.preview_chip.setFixedSize(72, 72)
        preview_layout.addWidget(self.preview_chip)

        preview_text_layout = QVBoxLayout()
        self.lbl_preview_hex = QLabel("")
        self.lbl_preview_hex.setProperty("class", "accent-text")
        preview_text_layout.addWidget(self.lbl_preview_hex)
        self.lbl_preview_rgb = QLabel("")
        self.lbl_preview_rgb.setProperty("class", "muted")
        preview_text_layout.addWidget(self.lbl_preview_rgb)
        preview_text_layout.addStretch()
        preview_layout.addLayout(preview_text_layout, 1)

        layout.addWidget(preview_card)

        swatch_card = QFrame()
        swatch_card.setProperty("class", "dialog-card")
        swatch_layout = QVBoxLayout(swatch_card)
        swatch_layout.setContentsMargins(12, 12, 12, 12)
        swatch_layout.setSpacing(8)
        swatch_title = QLabel("Colores rápidos")
        swatch_title.setProperty("class", "dialog-section")
        swatch_layout.addWidget(swatch_title)

        quick_grid = QGridLayout()
        quick_grid.setHorizontalSpacing(8)
        quick_grid.setVerticalSpacing(8)
        for index, (label, color) in enumerate(self.QUICK_COLORS):
            btn = QPushButton("")
            btn.setCheckable(True)
            btn.setToolTip(label)
            btn.setProperty("class", "swatch-btn")
            btn.setFixedSize(36, 28)
            btn.setStyleSheet(
                "QPushButton {"
                f"background-color: rgb({color[0]}, {color[1]}, {color[2]});"
                f"border: 1px solid {COLORS['border']};"
                "border-radius: 6px;"
                "}"
            )
            btn.clicked.connect(lambda _checked=False, swatch=color: self._set_color(swatch))
            self.swatch_buttons.append((btn, color))
            quick_grid.addWidget(btn, index // 4, index % 4)
        swatch_layout.addLayout(quick_grid)
        layout.addWidget(swatch_card)

        manual_card = QFrame()
        manual_card.setProperty("class", "dialog-card")
        manual_layout = QFormLayout(manual_card)
        manual_layout.setContentsMargins(12, 12, 12, 12)
        manual_layout.setSpacing(10)

        self.txt_hex = QLineEdit("")
        self.txt_hex.setPlaceholderText("#E6E6E6")
        self.txt_hex.editingFinished.connect(self._apply_hex_input)
        manual_layout.addRow("HEX:", self.txt_hex)

        rgb_row = QHBoxLayout()
        rgb_row.setSpacing(8)
        self.spin_red = QSpinBox()
        self.spin_red.setRange(0, 255)
        self.spin_red.valueChanged.connect(self._apply_rgb_input)
        rgb_row.addWidget(self.spin_red)
        self.spin_green = QSpinBox()
        self.spin_green.setRange(0, 255)
        self.spin_green.valueChanged.connect(self._apply_rgb_input)
        rgb_row.addWidget(self.spin_green)
        self.spin_blue = QSpinBox()
        self.spin_blue.setRange(0, 255)
        self.spin_blue.valueChanged.connect(self._apply_rgb_input)
        rgb_row.addWidget(self.spin_blue)
        manual_layout.addRow("RGB:", rgb_row)

        layout.addWidget(manual_card)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        btn_ok = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if btn_ok:
            btn_ok.setProperty("class", "primary")
        btn_cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if btn_cancel:
            btn_cancel.setProperty("class", "ghost")
        layout.addWidget(buttons)

    def _set_color(self, color):
        self.current_color = tuple(max(0, min(255, int(component))) for component in color)
        self._syncing = True
        self.txt_hex.setText(ExportConfigDialog._color_to_hex(self.current_color))
        self.spin_red.setValue(self.current_color[0])
        self.spin_green.setValue(self.current_color[1])
        self.spin_blue.setValue(self.current_color[2])
        self._syncing = False
        self._refresh_preview()

    def _refresh_preview(self):
        color = self.current_color
        self.preview_chip.setStyleSheet(
            "QFrame {"
            f"background-color: rgb({color[0]}, {color[1]}, {color[2]});"
            f"border: 1px solid {COLORS['border']};"
            "border-radius: 8px;"
            "}"
        )
        self.lbl_preview_hex.setText(ExportConfigDialog._color_to_hex(color))
        self.lbl_preview_rgb.setText(f"RGB {color[0]}, {color[1]}, {color[2]}")
        for button, swatch in self.swatch_buttons:
            button.blockSignals(True)
            button.setChecked(tuple(swatch) == tuple(color))
            button.blockSignals(False)

    def _apply_hex_input(self):
        if self._syncing:
            return
        value = self.txt_hex.text().strip()
        if not value:
            return
        if not value.startswith("#"):
            value = f"#{value}"
        if len(value) != 7:
            self.txt_hex.setText(ExportConfigDialog._color_to_hex(self.current_color))
            return
        try:
            parsed = tuple(int(value[index:index + 2], 16) for index in (1, 3, 5))
        except ValueError:
            self.txt_hex.setText(ExportConfigDialog._color_to_hex(self.current_color))
            return
        self._set_color(parsed)

    def _apply_rgb_input(self):
        if self._syncing:
            return
        self._set_color(
            (
                self.spin_red.value(),
                self.spin_green.value(),
                self.spin_blue.value(),
            )
        )

    def get_color(self):
        return self.current_color

