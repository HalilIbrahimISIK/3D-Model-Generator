"""
Main application window.
"""

import os
import shutil
import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextBrowser, QTextEdit, QPushButton, QLabel,
    QFileDialog, QProgressBar, QSplitter, QFrame,
    QSizePolicy, QStatusBar, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QDragEnterEvent, QDropEvent

from ui.styles import DARK_THEME
from ui.settings_dialog import SettingsDialog
from agent.llm_agent import LLMAgent
from converter.image_to_stl import ImageToSTLConverter
from utils.config_manager import load_config, ensure_directories


# ─────────────────────────────────────────────────────────────
#  Worker threads
# ─────────────────────────────────────────────────────────────

class LLMWorker(QThread):
    """Background thread for LLM API calls."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, agent: LLMAgent, message: str, image_path: Optional[str] = None):
        super().__init__()
        self.agent = agent
        self.message = message
        self.image_path = image_path

    def run(self):
        try:
            response = self.agent.chat(self.message, self.image_path)
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))


class ConversionWorker(QThread):
    """Background thread for TripoSR image-to-STL conversion."""
    finished = pyqtSignal(str)       # output path
    error = pyqtSignal(str)
    progress = pyqtSignal(int)       # 0–100
    status = pyqtSignal(str)         # status text

    def __init__(self, converter: ImageToSTLConverter, image_path: str, output_path: str):
        super().__init__()
        self.converter = converter
        self.image_path = image_path
        self.output_path = output_path

    def run(self):
        def progress_cb(percent: int, message: str):
            self.progress.emit(percent)
            self.status.emit(message)

        try:
            result = self.converter.convert(self.image_path, self.output_path, progress_cb)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ─────────────────────────────────────────────────────────────
#  Drop-enabled image label
# ─────────────────────────────────────────────────────────────

class DropImageLabel(QLabel):
    """Image label that accepts drag-and-drop image files."""
    image_dropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith(
                (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff")
            ):
                event.acceptProposedAction()
                self.setStyleSheet("border: 2px solid #7c6af7; border-radius: 10px;")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.image_dropped.emit(file_path)


# ─────────────────────────────────────────────────────────────
#  Main Window
# ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """Main application window for the 3D Model Generator AI Agent."""

    def __init__(self):
        super().__init__()
        ensure_directories()

        self.agent = LLMAgent()
        self.converter = ImageToSTLConverter()
        self.current_image_path: Optional[str] = None
        self.current_stl_path: Optional[str] = None
        self.llm_worker: Optional[LLMWorker] = None
        self.conv_worker: Optional[ConversionWorker] = None

        self._build_ui()
        self._apply_style()
        self._check_api_key()

    # ── Setup ────────────────────────────────────────────────

    def _build_ui(self):
        self.setWindowTitle("🤖  3D Model Generator AI Agent")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Header
        root_layout.addWidget(self._build_header())

        # Main content splitter
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(12, 8, 12, 8)
        content_layout.setSpacing(10)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_chat_panel())
        splitter.addWidget(self._build_workspace_panel())
        splitter.setSizes([580, 500])
        splitter.setChildrenCollapsible(False)
        content_layout.addWidget(splitter)
        root_layout.addWidget(content, 1)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Hazır  •  TripoSR: " + (
            "✅ Kurulu" if self.converter.is_available() else "❌ Kurulmamış"
        ))

    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("headerFrame")
        frame.setFixedHeight(64)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 0, 20, 0)

        # Logo + title
        title_lbl = QLabel("🤖  3D Model Generator")
        title_lbl.setObjectName("titleLabel")
        layout.addWidget(title_lbl)

        sub_lbl = QLabel("AI Agent  •  TripoSR  •  Groq LLM")
        sub_lbl.setObjectName("subtitleLabel")
        layout.addWidget(sub_lbl)
        layout.addStretch()

        # Settings button
        settings_btn = QPushButton("⚙️  Ayarlar")
        settings_btn.setFixedSize(110, 36)
        settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(settings_btn)

        # Clear chat button
        clear_btn = QPushButton("🗑  Sıfırla")
        clear_btn.setObjectName("clearBtn")
        clear_btn.setFixedSize(90, 36)
        clear_btn.setToolTip("Sohbet geçmişini ve yüklü görseli temizle")
        clear_btn.clicked.connect(self._reset_all)
        layout.addWidget(clear_btn)

        return frame

    def _build_chat_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("chatPanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Section header
        header = QHBoxLayout()
        lbl = QLabel("💬  SOHBET")
        lbl.setObjectName("sectionLabel")
        header.addWidget(lbl)
        header.addStretch()
        self._api_status_lbl = QLabel("● API Bağlantısı Kontrol Ediliyor...")
        self._api_status_lbl.setStyleSheet("color: #6a6a9a; font-size: 11px;")
        header.addWidget(self._api_status_lbl)
        layout.addLayout(header)

        # Chat display
        self._chat_display = QTextBrowser()
        self._chat_display.setObjectName("chatDisplay")
        self._chat_display.setOpenExternalLinks(True)
        self._chat_display.setReadOnly(True)
        layout.addWidget(self._chat_display, 1)

        # Typing indicator
        self._typing_lbl = QLabel("")
        self._typing_lbl.setStyleSheet("color: #7c6af7; font-size: 12px; padding-left: 4px;")
        layout.addWidget(self._typing_lbl)

        # Input area
        input_frame = QFrame()
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(6)

        self._message_input = QTextEdit()
        self._message_input.setObjectName("messageInput")
        self._message_input.setFixedHeight(80)
        self._message_input.setPlaceholderText(
            "Buraya mesajınızı yazın... (Shift+Enter = yeni satır, Enter = gönder)"
        )
        self._message_input.installEventFilter(self)
        input_layout.addWidget(self._message_input)

        btn_row = QHBoxLayout()
        self._upload_btn = QPushButton("📎  Görsel Yükle")
        self._upload_btn.setObjectName("uploadBtn")
        self._upload_btn.setFixedHeight(36)
        self._upload_btn.setToolTip("Resim dosyası seç (PNG, JPG, WEBP...)")
        self._upload_btn.clicked.connect(self._upload_image)
        btn_row.addWidget(self._upload_btn)

        btn_row.addStretch()

        self._send_btn = QPushButton("Gönder  ➤")
        self._send_btn.setObjectName("sendBtn")
        self._send_btn.setFixedHeight(36)
        self._send_btn.setFixedWidth(120)
        self._send_btn.clicked.connect(self._send_message)
        btn_row.addWidget(self._send_btn)

        input_layout.addLayout(btn_row)
        layout.addWidget(input_frame)

        return frame

    def _build_workspace_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("workspacePanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Section header
        ws_lbl = QLabel("🖼️  GÖRSEL & 3D DÖNÜŞTÜRME")
        ws_lbl.setObjectName("sectionLabel")
        layout.addWidget(ws_lbl)

        # Image preview
        img_frame = QFrame()
        img_frame.setObjectName("imageFrame")
        img_frame.setMinimumHeight(240)
        img_layout = QVBoxLayout(img_frame)
        img_layout.setContentsMargins(8, 8, 8, 8)

        self._image_label = DropImageLabel()
        self._image_label.setObjectName("imagePreviewLabel")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._image_label.setMinimumHeight(220)
        self._image_label.image_dropped.connect(self._load_image)
        self._set_empty_preview()
        img_layout.addWidget(self._image_label)
        layout.addWidget(img_frame, 1)

        # Image info
        self._img_info_lbl = QLabel("")
        self._img_info_lbl.setStyleSheet("color: #6a6a9a; font-size: 11px;")
        self._img_info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._img_info_lbl)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        layout.addWidget(sep)

        # Convert button
        self._convert_btn = QPushButton("🔄  STL'e Dönüştür")
        self._convert_btn.setObjectName("convertBtn")
        self._convert_btn.setFixedHeight(44)
        self._convert_btn.setEnabled(False)
        self._convert_btn.setToolTip("Yüklü görseli STL 3D dosyasına dönüştür")
        self._convert_btn.clicked.connect(self._start_conversion)
        layout.addWidget(self._convert_btn)

        # Progress
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        self._conv_status_lbl = QLabel("")
        self._conv_status_lbl.setStyleSheet("color: #9a9acc; font-size: 12px;")
        self._conv_status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._conv_status_lbl.setWordWrap(True)
        layout.addWidget(self._conv_status_lbl)

        # Download button
        self._download_btn = QPushButton("⬇️  STL Dosyasını İndir")
        self._download_btn.setObjectName("downloadBtn")
        self._download_btn.setFixedHeight(44)
        self._download_btn.setEnabled(False)
        self._download_btn.setToolTip("Oluşturulan STL dosyasını kaydet")
        self._download_btn.clicked.connect(self._download_stl)
        layout.addWidget(self._download_btn)

        # STL file info
        self._stl_info_lbl = QLabel("")
        self._stl_info_lbl.setStyleSheet("color: #6a6a9a; font-size: 11px;")
        self._stl_info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._stl_info_lbl)

        return frame

    def _apply_style(self):
        self.setStyleSheet(DARK_THEME)

    # ── Event filter (Enter to send) ─────────────────────────

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        if obj is self._message_input and event.type() == QEvent.Type.KeyPress:
            key_event: QKeyEvent = event
            if (
                key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
                and not (key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            ):
                self._send_message()
                return True
        return super().eventFilter(obj, event)

    # ── API Key check ────────────────────────────────────────

    def _check_api_key(self):
        if self.agent.is_ready():
            self._api_status_lbl.setText("● Groq API Bağlı")
            self._api_status_lbl.setStyleSheet("color: #7affc4; font-size: 11px;")
            self._append_bot_message(
                "Merhaba! Ben 3D Model Generator AI Agent'ıyım. 🎉\n\n"
                "Bana şunları yapabilirim:\n"
                "• Sorularınızı yanıtlarım 💬\n"
                "• Yüklediğiniz görseli analiz ederim 🖼️\n"
                "• Görseli STL 3D baskı dosyasına dönüştürürüm 🖨️\n\n"
                "Başlamak için bir görsel yükleyin veya mesajınızı yazın!"
            )
        else:
            self._api_status_lbl.setText("● API Anahtarı Gerekli")
            self._api_status_lbl.setStyleSheet("color: #ff7a7a; font-size: 11px;")
            self._append_bot_message(
                "⚠️ **Groq API anahtarı bulunamadı.**\n\n"
                "Başlamak için:\n"
                "1. ⚙️ **Ayarlar** düğmesine tıklayın\n"
                "2. https://console.groq.com adresinden **ücretsiz** API anahtarı alın\n"
                "3. Anahtarı yapıştırıp **Kaydet** deyin\n\n"
                "**TripoSR ile görsel → STL dönüştürme API anahtarı gerektirmez!** 🎯"
            )

    # ── Chat helpers ─────────────────────────────────────────

    def _append_user_message(self, text: str, has_image: bool = False):
        image_tag = " 🖼️" if has_image else ""
        html = (
            f'<div style="margin:6px 0; text-align:right;">'
            f'<span style="display:inline-block; background:#3a2a7a; color:#e2e2f0; '
            f'border-radius:10px 10px 2px 10px; padding:8px 14px; '
            f'max-width:85%; font-size:13px; text-align:left;">'
            f'<b style="color:#c8b8ff;">Sen{image_tag}</b><br>'
            f'{self._escape_html(text)}'
            f'</span></div>'
        )
        self._chat_display.append(html)
        self._scroll_to_bottom()

    def _append_bot_message(self, text: str):
        formatted = self._format_bot_text(text)
        html = (
            f'<div style="margin:6px 0;">'
            f'<span style="display:inline-block; background:#1e1e38; color:#e2e2f0; '
            f'border-radius:10px 10px 10px 2px; padding:8px 14px; '
            f'max-width:90%; font-size:13px;">'
            f'<b style="color:#7c6af7;">🤖 Asistan</b><br>'
            f'{formatted}'
            f'</span></div>'
        )
        self._chat_display.append(html)
        self._scroll_to_bottom()

    def _append_system_message(self, text: str, color: str = "#ffc77a"):
        html = (
            f'<div style="margin:4px 0; text-align:center;">'
            f'<span style="color:{color}; font-size:11px; font-style:italic;">'
            f'{self._escape_html(text)}'
            f'</span></div>'
        )
        self._chat_display.append(html)
        self._scroll_to_bottom()

    def _escape_html(self, text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )

    def _format_bot_text(self, text: str) -> str:
        """Lightly format bot markdown-like text for HTML display."""
        import re
        text = self._escape_html(text)
        # Bold **text**
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        # Code `inline`
        text = re.sub(
            r"`(.+?)`",
            r'<code style="background:#2a2a4a; padding:1px 4px; border-radius:4px;">\1</code>',
            text,
        )
        return text

    def _scroll_to_bottom(self):
        sb = self._chat_display.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── Send message ─────────────────────────────────────────

    def _send_message(self):
        text = self._message_input.toPlainText().strip()
        if not text:
            return

        self._message_input.clear()
        self._set_input_enabled(False)

        self._append_user_message(text, has_image=self.current_image_path is not None)
        self._typing_lbl.setText("🤖 Asistan yanıt yazıyor...")

        # Check API before firing worker
        if not self.agent.is_ready():
            config = load_config()
            if config.get("groq_api_key"):
                self.agent.reload()

        self.llm_worker = LLMWorker(self.agent, text, self.current_image_path)
        self.llm_worker.finished.connect(self._on_llm_response)
        self.llm_worker.error.connect(self._on_llm_error)
        self.llm_worker.finished.connect(lambda: self._set_input_enabled(True))
        self.llm_worker.error.connect(lambda: self._set_input_enabled(True))
        self.llm_worker.start()

    def _on_llm_response(self, response: str):
        self._typing_lbl.setText("")
        self._append_bot_message(response)

    def _on_llm_error(self, error: str):
        self._typing_lbl.setText("")
        self._append_system_message(f"❌ Hata: {error}", color="#ff7a7a")

    def _set_input_enabled(self, enabled: bool):
        self._message_input.setEnabled(enabled)
        self._send_btn.setEnabled(enabled)
        if enabled:
            self._message_input.setFocus()

    # ── Image upload ─────────────────────────────────────────

    def _upload_image(self):
        config = load_config()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Görsel Seç",
            "",
            "Görseller (*.png *.jpg *.jpeg *.bmp *.webp *.tiff *.tif);;Tüm Dosyalar (*)",
        )
        if file_path:
            self._load_image(file_path)

    def _load_image(self, file_path: str):
        """Load and display an image file."""
        try:
            config = load_config()
            uploads_dir = config.get("uploads_dir", "uploads")
            os.makedirs(uploads_dir, exist_ok=True)

            # Copy to uploads dir
            filename = os.path.basename(file_path)
            dest = os.path.join(uploads_dir, filename)
            if os.path.abspath(file_path) != os.path.abspath(dest):
                shutil.copy2(file_path, dest)

            self.current_image_path = dest
            self.current_stl_path = None
            self._download_btn.setEnabled(False)
            self._stl_info_lbl.setText("")

            # Show preview
            pixmap = QPixmap(dest)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self._image_label.width() - 16,
                    self._image_label.height() - 16,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._image_label.setPixmap(scaled)
                self._image_label.setStyleSheet("")

                # File info
                size_kb = os.path.getsize(dest) / 1024
                self._img_info_lbl.setText(
                    f"📄 {filename}  •  {pixmap.width()}×{pixmap.height()} px  •  {size_kb:.1f} KB"
                )

                # Enable convert if TripoSR available
                if self.converter.is_available():
                    self._convert_btn.setEnabled(True)
                    self._conv_status_lbl.setText("✅ Görsel yüklendi. Dönüştürmeye hazır!")
                else:
                    self._convert_btn.setEnabled(False)
                    self._conv_status_lbl.setText(
                        "⚠️ TripoSR kurulu değil.\n"
                        "Ayarlar → Dönüştürme sekmesindeki kurulum komutunu çalıştırın."
                    )

                # Notify in chat
                self._append_system_message(
                    f"📎 Görsel yüklendi: {filename}"
                )

                # Auto-analyze with LLM if API ready
                if self.agent.is_ready():
                    self._send_auto_analyze(filename)

            else:
                QMessageBox.warning(self, "Hata", "Görsel açılamadı.")

        except Exception as e:
            QMessageBox.critical(self, "Görsel Yükleme Hatası", str(e))

    def _send_auto_analyze(self, filename: str):
        """Automatically send the image to LLM for analysis."""
        prompt = (
            f"Bu görseli ({filename}) analiz et. "
            "3D baskı için ne kadar uygun? "
            "Görseldeki nesneyi kısaca tanımla ve STL dönüşümü için tavsiyeler ver."
        )
        self._append_user_message(prompt, has_image=True)
        self._typing_lbl.setText("🤖 Asistan görseli analiz ediyor...")
        self._set_input_enabled(False)

        self.llm_worker = LLMWorker(self.agent, prompt, self.current_image_path)
        self.llm_worker.finished.connect(self._on_llm_response)
        self.llm_worker.error.connect(self._on_llm_error)
        self.llm_worker.finished.connect(lambda: self._set_input_enabled(True))
        self.llm_worker.error.connect(lambda: self._set_input_enabled(True))
        self.llm_worker.start()

    def _set_empty_preview(self):
        self._image_label.setText(
            "🖼️\n\nGörsel sürükleyip bırakın\nveya\n📎 Görsel Yükle düğmesine tıklayın\n\n"
            "Desteklenen formatlar: PNG, JPG, WEBP, BMP, TIFF"
        )
        self._image_label.setStyleSheet("color: #4a4a7a; font-size: 13px;")

    # ── STL Conversion ───────────────────────────────────────

    def _start_conversion(self):
        if not self.current_image_path:
            QMessageBox.warning(self, "Uyarı", "Önce bir görsel yükleyin.")
            return

        if not self.converter.is_available():
            QMessageBox.warning(
                self,
                "TripoSR Kurulu Değil",
                self.converter.get_install_instructions(),
            )
            return

        config = load_config()
        output_dir = config.get("output_dir", "output")
        os.makedirs(output_dir, exist_ok=True)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.splitext(os.path.basename(self.current_image_path))[0]
        output_path = os.path.join(output_dir, f"{base}_{ts}.stl")

        # UI state
        self._convert_btn.setEnabled(False)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(True)
        self._conv_status_lbl.setText("🔄 Dönüştürme başlıyor...")
        self._append_system_message("🔄 STL dönüştürme başladı...")

        self.conv_worker = ConversionWorker(self.converter, self.current_image_path, output_path)
        self.conv_worker.progress.connect(self._progress_bar.setValue)
        self.conv_worker.status.connect(self._conv_status_lbl.setText)
        self.conv_worker.finished.connect(self._on_conversion_done)
        self.conv_worker.error.connect(self._on_conversion_error)
        self.conv_worker.start()

    def _on_conversion_done(self, stl_path: str):
        self.current_stl_path = stl_path
        self._progress_bar.setValue(100)
        self._convert_btn.setEnabled(True)

        size_kb = os.path.getsize(stl_path) / 1024
        size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"

        self._stl_info_lbl.setText(
            f"✅ {os.path.basename(stl_path)}  •  {size_str}"
        )
        self._download_btn.setEnabled(True)
        self._status_bar.showMessage(f"✅ STL oluşturuldu: {stl_path}")

        # Hide progress after 3 seconds
        QTimer.singleShot(3000, lambda: self._progress_bar.setVisible(False))

        self._append_system_message(
            f"✅ STL dosyası hazır! ({size_str}) — İndir düğmesine tıklayın.",
            color="#7affc4",
        )

        # Notify LLM about completion
        if self.agent.is_ready():
            self._append_bot_message(
                f"🎉 **3D model başarıyla oluşturuldu!**\n\n"
                f"📄 Dosya: `{os.path.basename(stl_path)}`\n"
                f"📦 Boyut: {size_str}\n\n"
                f"⬇️ **STL Dosyasını İndir** düğmesine tıklayarak dosyayı indirebilirsiniz.\n\n"
                f"*Not: Dosyayı bir 3D dilimleyici yazılımda (Cura, PrusaSlicer vb.) açabilirsiniz.*"
            )

    def _on_conversion_error(self, error: str):
        self._convert_btn.setEnabled(True)
        self._progress_bar.setVisible(False)
        self._conv_status_lbl.setText(f"❌ Dönüştürme hatası")
        self._append_system_message(f"❌ Dönüştürme hatası: {error}", color="#ff7a7a")
        QMessageBox.critical(self, "Dönüştürme Hatası", error)

    # ── Download STL ─────────────────────────────────────────

    def _download_stl(self):
        if not self.current_stl_path or not os.path.exists(self.current_stl_path):
            QMessageBox.warning(self, "Hata", "İndirilecek STL dosyası bulunamadı.")
            return

        default_name = os.path.basename(self.current_stl_path)
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "STL Dosyasını Kaydet",
            os.path.expanduser(f"~/Downloads/{default_name}"),
            "STL Dosyaları (*.stl);;Tüm Dosyalar (*)",
        )
        if save_path:
            try:
                shutil.copy2(self.current_stl_path, save_path)
                size_kb = os.path.getsize(save_path) / 1024
                self._append_system_message(
                    f"⬇️ STL indirildi: {save_path}",
                    color="#ffc77a",
                )
                self._status_bar.showMessage(f"⬇️ İndirildi: {save_path}")
                QMessageBox.information(
                    self,
                    "İndirme Tamamlandı",
                    f"✅ STL dosyası başarıyla kaydedildi!\n\n{save_path}\n\n"
                    f"Boyut: {size_kb:.1f} KB",
                )
            except Exception as e:
                QMessageBox.critical(self, "İndirme Hatası", str(e))

    # ── Settings ─────────────────────────────────────────────

    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec()

    def _on_settings_saved(self):
        self.agent.reload()
        self._check_api_key_status()
        self._status_bar.showMessage("✅ Ayarlar kaydedildi.")

    def _check_api_key_status(self):
        if self.agent.is_ready():
            self._api_status_lbl.setText("● Groq API Bağlı")
            self._api_status_lbl.setStyleSheet("color: #7affc4; font-size: 11px;")
        else:
            self._api_status_lbl.setText("● API Anahtarı Gerekli")
            self._api_status_lbl.setStyleSheet("color: #ff7a7a; font-size: 11px;")

    # ── Reset ─────────────────────────────────────────────────

    def _reset_all(self):
        reply = QMessageBox.question(
            self,
            "Sıfırla",
            "Sohbet geçmişi ve yüklü görsel silinecek. Devam edilsin mi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.agent.clear_history()
            self.current_image_path = None
            self.current_stl_path = None
            self._chat_display.clear()
            self._set_empty_preview()
            self._img_info_lbl.setText("")
            self._stl_info_lbl.setText("")
            self._conv_status_lbl.setText("")
            self._progress_bar.setVisible(False)
            self._convert_btn.setEnabled(False)
            self._download_btn.setEnabled(False)
            self._check_api_key()

    # ── Resize event ─────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Rescale image preview on resize
        if self.current_image_path and os.path.exists(self.current_image_path):
            pixmap = QPixmap(self.current_image_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    max(self._image_label.width() - 16, 1),
                    max(self._image_label.height() - 16, 1),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._image_label.setPixmap(scaled)
