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

        # HuggingFace token group
        hf_group = QGroupBox("HuggingFace Token  (TRELLIS modeli için zorunlu)")
        hf_group.setStyleSheet("QGroupBox { color: #9a9acc; font-weight: 600; }")
        hf_form = QFormLayout(hf_group)
        hf_form.setSpacing(10)

        hf_key_layout = QHBoxLayout()
        self.hf_token_input = QLineEdit()
        self.hf_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.hf_token_input.setPlaceholderText("hf_xxxxxxxxxxxxxxxxxxxxxxxx")
        hf_key_layout.addWidget(self.hf_token_input)

        hf_show_btn = QPushButton("👁")
        hf_show_btn.setFixedWidth(36)
        hf_show_btn.setCheckable(True)
        hf_show_btn.toggled.connect(
            lambda checked: self.hf_token_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        hf_key_layout.addWidget(hf_show_btn)
        hf_form.addRow("HF Token:", hf_key_layout)

        hf_steps = QLabel(
            "1. <a href='https://huggingface.co/microsoft/TRELLIS-image-large' style='color:#7c6af7;'>"
            "TRELLIS model sayfasına git</a> → \"Agree and access repository\"<br>"
            "2. <a href='https://huggingface.co/settings/tokens' style='color:#7c6af7;'>"
            "Token oluştur</a> → Read erişimi yeterli → Buraya yapıştır"
        )
        hf_steps.setOpenExternalLinks(True)
        hf_steps.setStyleSheet("color: #6a6a9a; font-size: 11px;")
        hf_steps.setWordWrap(True)
        hf_form.addRow("", hf_steps)

        layout.addWidget(hf_group)
        layout.addStretch()
        return widget

    def _conversion_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 12, 0, 0)

        conv_group = QGroupBox("TRELLIS Dönüştürme Ayarları")
        conv_group.setStyleSheet("QGroupBox { color: #9a9acc; font-weight: 600; }")
        form = QFormLayout(conv_group)
        form.setSpacing(10)

        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(8, 50)
        self.steps_spin.setSingleStep(2)
        self.steps_spin.setValue(12)
        self.steps_spin.setToolTip("Daha fazla adım = daha iyi kalite ama daha yavaş")
        form.addRow("Diffusion Adımları:", self.steps_spin)

        self.cfg_spin = QSpinBox()
        self.cfg_spin.setRange(1, 20)
        self.cfg_spin.setValue(7)
        self.cfg_spin.setToolTip("CFG strength — yüksek değer görsele daha sadık ama daha az çeşitlilik")
        form.addRow("CFG Gücü:", self.cfg_spin)

        note = QLabel("⚡ Adım: 12 = Dengeli | 20+ = Yüksek Kalite (GPU önerilir)")
        note.setStyleSheet("color: #6a6a9a; font-size: 11px;")
        note.setWordWrap(True)
        form.addRow("", note)

        layout.addWidget(conv_group)

        # TRELLIS install info
        info_group = QGroupBox("TRELLIS Kurulum Durumu")
        info_group.setStyleSheet("QGroupBox { color: #9a9acc; font-weight: 600; }")
        info_layout = QVBoxLayout(info_group)

        try:
            import sys, os
            trellis_lib = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trellis_lib")
            if trellis_lib not in sys.path:
                sys.path.insert(0, trellis_lib)
            from trellis.pipelines import TrellisImageTo3DPipeline  # noqa
            status_text = "✅ TRELLIS kurulu ve hazır."
            status_style = "color: #7affc4;"
        except Exception:
            status_text = (
                "❌ TRELLIS import edilemiyor.\n\n"
                "trellis_lib/ klasörü mevcut olmalı.\n"
                "Kurulum için setup.sh çalıştırın:\n\n"
                "⚠️  TRELLIS NVIDIA CUDA GPU gerektirir."
            )
            status_style = "color: #ff7a7a;"

        status_lbl = QLabel(status_text)
        status_lbl.setStyleSheet(status_style + " font-size: 12px;")
        status_lbl.setWordWrap(True)
        info_layout.addWidget(status_lbl)

        import torch
        try:
            dev = "CUDA ✅" if torch.cuda.is_available() else (
                "MPS (Apple) ⚠️" if (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()) else "CPU ❌ (TRELLIS desteklemiyor)"
            )
        except Exception:
            dev = "Bilinmiyor"
        gpu_lbl = QLabel(f"Mevcut cihaz: {dev}")
        gpu_lbl.setStyleSheet("color: #9a9acc; font-size: 11px;")
        info_layout.addWidget(gpu_lbl)

        layout.addWidget(info_group)
        layout.addStretch()
        return widget

    def _load_values(self):
        """Populate UI with current config values."""
        self.api_key_input.setText(self.config.get("groq_api_key", ""))
        self.hf_token_input.setText(self.config.get("hf_token", ""))

        text_model = self.config.get("text_model", "llama-3.3-70b-versatile")
        idx = self.text_model_combo.findText(text_model)
        if idx >= 0:
            self.text_model_combo.setCurrentIndex(idx)

        vision_model = self.config.get("vision_model", "llama-3.2-11b-vision-preview")
        idx = self.vision_model_combo.findText(vision_model)
        if idx >= 0:
            self.vision_model_combo.setCurrentIndex(idx)

        self.steps_spin.setValue(self.config.get("trellis_steps", 12))
        self.cfg_spin.setValue(int(self.config.get("trellis_cfg_strength", 7)))

    def _save(self):
        """Save configuration."""
        self.config["groq_api_key"] = self.api_key_input.text().strip()
        self.config["hf_token"] = self.hf_token_input.text().strip()
        self.config["text_model"] = self.text_model_combo.currentText()
        self.config["vision_model"] = self.vision_model_combo.currentText()
        self.config["trellis_steps"] = self.steps_spin.value()
        self.config["trellis_cfg_strength"] = float(self.cfg_spin.value())
        save_config(self.config)
        self.settings_saved.emit()
        self.accept()

