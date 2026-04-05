"""
Settings Dialog for API key and model configuration.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QGroupBox, QSpinBox, QDialogButtonBox, QTabWidget, QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from utils.config_manager import load_config, save_config
from agent.llm_agent import LLMAgent


class SettingsDialog(QDialog):
    """Dialog for configuring API keys, models, and app settings."""

    settings_saved = pyqtSignal()

    TEXT_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "llama3-70b-8192",
    ]
    VISION_MODELS = [
        "llama-3.2-11b-vision-preview",
        "llama-3.2-90b-vision-preview",
        "llava-v1.5-7b-4096-preview",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️  Ayarlar")
        self.setMinimumWidth(520)
        self.setModal(True)
        self.config = load_config()
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("⚙️  Uygulama Ayarları")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        title.setStyleSheet("color: #c8b8ff;")
        layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._api_tab(), "🔑  API & Modeller")
        tabs.addTab(self._conversion_tab(), "🔧  Dönüştürme")
        layout.addWidget(tabs)

        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._save)
        btn_box.rejected.connect(self.reject)
        save_btn = btn_box.button(QDialogButtonBox.StandardButton.Save)
        save_btn.setText("💾  Kaydet")
        cancel_btn = btn_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_btn.setText("İptal")
        layout.addWidget(btn_box)

    def _api_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 12, 0, 0)

        # Groq group
        groq_group = QGroupBox("Groq API Yapılandırması")
        groq_group.setStyleSheet("QGroupBox { color: #9a9acc; font-weight: 600; }")
        form = QFormLayout(groq_group)
        form.setSpacing(10)

        # API Key
        key_layout = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("gsk_xxxxxxxxxxxxxxxxxxxxxxxx")
        key_layout.addWidget(self.api_key_input)

        show_btn = QPushButton("👁")
        show_btn.setFixedWidth(36)
        show_btn.setCheckable(True)
        show_btn.setToolTip("API anahtarını göster/gizle")
        show_btn.toggled.connect(
            lambda checked: self.api_key_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        key_layout.addWidget(show_btn)
        form.addRow("API Anahtarı:", key_layout)

        # Link
        link = QLabel(
            '<a href="https://console.groq.com/" style="color:#7c6af7;">'
            "Ücretsiz API anahtarı al →</a>"
        )
        link.setOpenExternalLinks(True)
        link.setStyleSheet("font-size: 12px;")
        form.addRow("", link)

        layout.addWidget(groq_group)

        # Model group
        model_group = QGroupBox("Model Seçimi")
        model_group.setStyleSheet("QGroupBox { color: #9a9acc; font-weight: 600; }")
        mform = QFormLayout(model_group)
        mform.setSpacing(10)

        self.text_model_combo = QComboBox()
        self.text_model_combo.addItems(self.TEXT_MODELS)
        mform.addRow("Metin Modeli:", self.text_model_combo)

        self.vision_model_combo = QComboBox()
        self.vision_model_combo.addItems(self.VISION_MODELS)
        mform.addRow("Görsel Modeli:", self.vision_model_combo)

        note = QLabel("ℹ️  Görsel yüklendiğinde otomatik olarak Vision modeli kullanılır.")
        note.setStyleSheet("color: #6a6a9a; font-size: 11px;")
        note.setWordWrap(True)
        mform.addRow("", note)

        layout.addWidget(model_group)
        layout.addStretch()
        return widget

    def _conversion_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 12, 0, 0)

        conv_group = QGroupBox("3D Dönüştürme Ayarları")
        conv_group.setStyleSheet("QGroupBox { color: #9a9acc; font-weight: 600; }")
        form = QFormLayout(conv_group)
        form.setSpacing(10)

        self.resolution_spin = QSpinBox()
        self.resolution_spin.setRange(64, 512)
        self.resolution_spin.setSingleStep(32)
        self.resolution_spin.setValue(256)
        self.resolution_spin.setToolTip(
            "Daha yüksek çözünürlük = daha iyi kalite ama daha yavaş ve fazla bellek"
        )
        form.addRow("Mesh Çözünürlüğü:", self.resolution_spin)

        res_note = QLabel(
            "⚡ 128 = Hızlı | 256 = Dengeli | 512 = Yüksek Kalite (GPU önerilir)"
        )
        res_note.setStyleSheet("color: #6a6a9a; font-size: 11px;")
        res_note.setWordWrap(True)
        form.addRow("", res_note)

        layout.addWidget(conv_group)

        # TripoSR install info
        info_group = QGroupBox("TripoSR Kurulum Durumu")
        info_group.setStyleSheet("QGroupBox { color: #9a9acc; font-weight: 600; }")
        info_layout = QVBoxLayout(info_group)

        try:
            from tsr.system import TSR  # noqa
            status_text = "✅ TripoSR kurulu ve hazır."
            status_style = "color: #7affc4;"
        except ImportError:
            status_text = (
                "❌ TripoSR kurulu değil.\n\n"
                "Kurmak için terminalde çalıştırın:\n"
                "pip install git+https://github.com/VAST-AI-Research/TripoSR.git"
            )
            status_style = "color: #ff7a7a;"

        status_lbl = QLabel(status_text)
        status_lbl.setStyleSheet(status_style + " font-size: 12px;")
        status_lbl.setWordWrap(True)
        info_layout.addWidget(status_lbl)

        layout.addWidget(info_group)
        layout.addStretch()
        return widget

    def _load_values(self):
        """Populate UI with current config values."""
        self.api_key_input.setText(self.config.get("groq_api_key", ""))

        text_model = self.config.get("text_model", "llama-3.3-70b-versatile")
        idx = self.text_model_combo.findText(text_model)
        if idx >= 0:
            self.text_model_combo.setCurrentIndex(idx)

        vision_model = self.config.get("vision_model", "llama-3.2-11b-vision-preview")
        idx = self.vision_model_combo.findText(vision_model)
        if idx >= 0:
            self.vision_model_combo.setCurrentIndex(idx)

        self.resolution_spin.setValue(self.config.get("mesh_resolution", 256))

    def _save(self):
        """Save configuration."""
        self.config["groq_api_key"] = self.api_key_input.text().strip()
        self.config["text_model"] = self.text_model_combo.currentText()
        self.config["vision_model"] = self.vision_model_combo.currentText()
        self.config["mesh_resolution"] = self.resolution_spin.value()
        save_config(self.config)
        self.settings_saved.emit()
        self.accept()

