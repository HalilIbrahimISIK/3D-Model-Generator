"""
Main application window.
"""

import os
import shutil
import datetime
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextBrowser, QTextEdit, QPushButton, QLabel,
    QFileDialog, QProgressBar, QSplitter, QFrame,
    QSizePolicy, QStatusBar, QMessageBox, QScrollArea,
    QGridLayout,
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
            self.finished.emit(self.agent.chat(self.message, self.image_path))
        except Exception as e:
            self.error.emit(str(e))


class ConversionWorker(QThread):
    """Background thread for TripoSR image-to-STL conversion."""
    finished = pyqtSignal(str)       # output path
    error = pyqtSignal(str)
    progress = pyqtSignal(int)       # 0–100
    status = pyqtSignal(str)         # status text

    def __init__(self, converter: ImageToSTLConverter, image_paths: List[str], output_path: str):
        super().__init__()
        self.converter = converter
        self.image_paths = image_paths
        self.output_path = output_path

    def run(self):
        def cb(pct: int, msg: str):
            self.progress.emit(pct)
            self.status.emit(msg)
        try:
            self.finished.emit(self.converter.convert(self.image_paths, self.output_path, cb))
        except Exception as e:
            self.error.emit(str(e))


# ─────────────────────────────────────────────────────────────
#  Multi-image thumbnail card
# ─────────────────────────────────────────────────────────────

class ImageThumbCard(QFrame):
    """Single 100×110 thumbnail card with index badge and ✕ button."""
    removed = pyqtSignal(str)
    THUMB = 90

    def __init__(self, image_path: str, index: int, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.setFixedSize(self.THUMB + 18, self.THUMB + 32)
        self.setStyleSheet(
            "QFrame { background:#1e1e38; border:1px solid #3a3a6a; border-radius:8px; }"
            "QFrame:hover { border-color:#7c6af7; }"
        )
        self._build(index)

    def _build(self, index: int):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 3)
        layout.setSpacing(3)

        # Thumbnail
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(
                self.THUMB, self.THUMB,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        thumb = QLabel()
        thumb.setPixmap(pixmap)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setFixedHeight(self.THUMB)
        layout.addWidget(thumb)

        # Bottom row: #index + ✕ button
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(2)
        idx_lbl = QLabel(f"#{index + 1}")
        idx_lbl.setStyleSheet("color:#7c6af7; font-size:10px; font-weight:600;")
        row.addWidget(idx_lbl)
        row.addStretch()
        rm = QPushButton("✕")
        rm.setFixedSize(22, 22)
        rm.setStyleSheet(
            "QPushButton{background:#3a1a1a;color:#ff7a7a;border:none;"
            "border-radius:4px;font-size:11px;font-weight:700;}"
            "QPushButton:hover{background:#6a1a1a;}"
        )
        rm.setToolTip("Bu görseli kaldır")
        rm.clicked.connect(lambda: self.removed.emit(self.image_path))
        row.addWidget(rm)
        layout.addLayout(row)


# ─────────────────────────────────────────────────────────────
#  Multi-image upload widget
# ─────────────────────────────────────────────────────────────

class MultiImageWidget(QWidget):
    """
    Scrollable grid of image thumbnails.
    Supports drag-and-drop and file dialog upload.
    Emits images_changed(list[str]) whenever the list changes.
    """
    images_changed = pyqtSignal(list)
    COLS = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_paths: List[str] = []
        self.setAcceptDrops(True)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ── Scroll area with thumbnail grid ──
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setMinimumHeight(180)
        self._scroll.setStyleSheet(
            "QScrollArea{background:#13132a;border:2px dashed #3a3a6a;border-radius:10px;}"
        )

        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setSpacing(8)
        self._grid.setContentsMargins(8, 8, 8, 8)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._scroll.setWidget(self._grid_host)
        root.addWidget(self._scroll, 1)

        # ── Placeholder label (shown when empty) ──
        self._placeholder = QLabel(
            "🖼️  Görsel sürükleyip bırakın\n\n"
            "veya  +Görsel Ekle  düğmesine tıklayın\n\n"
            "Farklı açılardan birden fazla görsel ekleyebilirsiniz\n"
            "Desteklenen: PNG · JPG · WEBP · BMP"
        )
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color:#4a4a7a; font-size:12px;")
        self._placeholder.setWordWrap(True)
        self._grid.addWidget(self._placeholder, 0, 0, 1, self.COLS)

        # ── Control bar ──
        bar = QHBoxLayout()
        bar.setSpacing(6)

        self._add_btn = QPushButton("➕  Görsel Ekle")
        self._add_btn.setObjectName("uploadBtn")
        self._add_btn.setFixedHeight(32)
        self._add_btn.setToolTip("PNG, JPG, WEBP... birden fazla seçebilirsiniz")
        self._add_btn.clicked.connect(self._pick_files)
        bar.addWidget(self._add_btn)

        self._clear_btn = QPushButton("🗑  Tümünü Temizle")
        self._clear_btn.setObjectName("clearBtn")
        self._clear_btn.setFixedHeight(32)
        self._clear_btn.clicked.connect(self.clear_all)
        bar.addWidget(self._clear_btn)

        bar.addStretch()

        self._count_lbl = QLabel("Görsel yüklenmedi")
        self._count_lbl.setStyleSheet("color:#6a6a9a; font-size:11px;")
        bar.addWidget(self._count_lbl)

        root.addLayout(bar)

    # ── Public API ───────────────────────────────────────────

    def add_images(self, paths: List[str]):
        """Add new paths (deduplicating) and refresh the grid."""
        config = load_config()
        uploads_dir = config.get("uploads_dir", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        for src in paths:
            filename = os.path.basename(src)
            dest = os.path.join(uploads_dir, filename)
            if os.path.abspath(src) != os.path.abspath(dest):
                shutil.copy2(src, dest)
            if dest not in self.image_paths:
                self.image_paths.append(dest)

        self._refresh()
        self.images_changed.emit(list(self.image_paths))

    def remove_image(self, path: str):
        if path in self.image_paths:
            self.image_paths.remove(path)
        self._refresh()
        self.images_changed.emit(list(self.image_paths))

    def clear_all(self):
        self.image_paths.clear()
        self._refresh()
        self.images_changed.emit([])

    def count(self) -> int:
        return len(self.image_paths)

    # ── Internal ─────────────────────────────────────────────

    def _pick_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Görseller Seç", "",
            "Görseller (*.png *.jpg *.jpeg *.bmp *.webp *.tiff *.tif);;Tüm Dosyalar (*)",
        )
        if paths:
            self.add_images(paths)

    def _refresh(self):
        """Rebuild the thumbnail grid from self.image_paths."""
        # Clear grid
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self.image_paths:
            self._grid.addWidget(self._placeholder, 0, 0, 1, self.COLS)
            self._placeholder.show()
            self._count_lbl.setText("Görsel yüklenmedi")
            self._scroll.setStyleSheet(
                "QScrollArea{background:#13132a;border:2px dashed #3a3a6a;border-radius:10px;}"
            )
        else:
            self._placeholder.hide()
            for i, path in enumerate(self.image_paths):
                card = ImageThumbCard(path, i)
                card.removed.connect(self.remove_image)
                self._grid.addWidget(card, i // self.COLS, i % self.COLS)
            n = len(self.image_paths)
            mode = "çok görsel modu 🎯" if n > 1 else "tek görsel modu"
            self._count_lbl.setText(f"{n} görsel  •  {mode}")
            self._scroll.setStyleSheet(
                "QScrollArea{background:#13132a;border:2px solid #3a5a3a;border-radius:10px;}"
            )

    # ── Drag & drop ──────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            valid = [
                u.toLocalFile() for u in event.mimeData().urls()
                if u.toLocalFile().lower().endswith(
                    (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff")
                )
            ]
            if valid:
                event.acceptProposedAction()
                self._scroll.setStyleSheet(
                    "QScrollArea{background:#13132a;border:2px solid #7c6af7;border-radius:10px;}"
                )
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._refresh()  # restore border

    def dropEvent(self, event: QDropEvent):
        paths = [
            u.toLocalFile() for u in event.mimeData().urls()
            if u.toLocalFile().lower().endswith(
                (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff")
            )
        ]
        if paths:
            self.add_images(paths)


# ─────────────────────────────────────────────────────────────
#  Main Window
# ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        ensure_directories()

        self.agent = LLMAgent()
        self.converter = ImageToSTLConverter()
        self.current_image_paths: List[str] = []
        self.current_stl_path: Optional[str] = None
        self.llm_worker: Optional[LLMWorker] = None
        self.conv_worker: Optional[ConversionWorker] = None

        self._build_ui()
        self.setStyleSheet(DARK_THEME)
        self._check_api_key()

    # ── UI construction ──────────────────────────────────────

    def _build_ui(self):
        self.setWindowTitle("🤖  3D Model Generator AI Agent  •  TRELLIS")
        self.setMinimumSize(1100, 720)
        self.resize(1320, 820)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        content = QWidget()
        cl = QHBoxLayout(content)
        cl.setContentsMargins(12, 8, 12, 8)
        cl.setSpacing(10)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_chat_panel())
        splitter.addWidget(self._build_workspace_panel())
        splitter.setSizes([600, 520])
        splitter.setChildrenCollapsible(False)
        cl.addWidget(splitter)
        root.addWidget(content, 1)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        dev = self.converter.get_device().upper()
        trellis_ok = self.converter.is_available()
        self._status_bar.showMessage(
            f"Hazır  •  TRELLIS: {'✅ Kurulu' if trellis_ok else '❌ Kurulmamış'}  •  GPU: {dev}"
        )

    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("headerFrame")
        frame.setFixedHeight(64)
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(20, 0, 20, 0)

        title = QLabel("🤖  3D Model Generator")
        title.setObjectName("titleLabel")
        lay.addWidget(title)

        sub = QLabel("AI Agent  •  TRELLIS  •  Groq LLM")
        sub.setObjectName("subtitleLabel")
        lay.addWidget(sub)
        lay.addStretch()

        settings_btn = QPushButton("⚙️  Ayarlar")
        settings_btn.setFixedSize(110, 36)
        settings_btn.clicked.connect(self._open_settings)
        lay.addWidget(settings_btn)

        clear_btn = QPushButton("🗑  Sıfırla")
        clear_btn.setObjectName("clearBtn")
        clear_btn.setFixedSize(90, 36)
        clear_btn.setToolTip("Sohbet geçmişini ve görselleri temizle")
        clear_btn.clicked.connect(self._reset_all)
        lay.addWidget(clear_btn)

        return frame

    def _build_chat_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("chatPanel")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        # Header row
        hdr = QHBoxLayout()
        lbl = QLabel("💬  SOHBET")
        lbl.setObjectName("sectionLabel")
        hdr.addWidget(lbl)
        hdr.addStretch()
        self._api_status_lbl = QLabel("● Kontrol ediliyor...")
        self._api_status_lbl.setStyleSheet("color:#6a6a9a;font-size:11px;")
        hdr.addWidget(self._api_status_lbl)
        lay.addLayout(hdr)

        # Chat display
        self._chat_display = QTextBrowser()
        self._chat_display.setObjectName("chatDisplay")
        self._chat_display.setOpenExternalLinks(True)
        self._chat_display.setReadOnly(True)
        lay.addWidget(self._chat_display, 1)

        # Typing indicator
        self._typing_lbl = QLabel("")
        self._typing_lbl.setStyleSheet("color:#7c6af7;font-size:12px;padding-left:4px;")
        lay.addWidget(self._typing_lbl)

        # Input
        inp_frame = QFrame()
        inp_lay = QVBoxLayout(inp_frame)
        inp_lay.setContentsMargins(0, 0, 0, 0)
        inp_lay.setSpacing(6)

        self._message_input = QTextEdit()
        self._message_input.setObjectName("messageInput")
        self._message_input.setFixedHeight(80)
        self._message_input.setPlaceholderText(
            "Mesajınızı yazın... (Shift+Enter = yeni satır, Enter = gönder)"
        )
        self._message_input.installEventFilter(self)
        inp_lay.addWidget(self._message_input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._send_btn = QPushButton("Gönder  ➤")
        self._send_btn.setObjectName("sendBtn")
        self._send_btn.setFixedSize(130, 36)
        self._send_btn.clicked.connect(self._send_message)
        btn_row.addWidget(self._send_btn)
        inp_lay.addLayout(btn_row)
        lay.addWidget(inp_frame)

        return frame

    def _build_workspace_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("workspacePanel")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        # Section label
        ws_lbl = QLabel("🖼️  GÖRSELLER & 3D DÖNÜŞTÜRME  (TRELLIS)")
        ws_lbl.setObjectName("sectionLabel")
        lay.addWidget(ws_lbl)

        # ── Multi-image widget ──
        self._multi_img = MultiImageWidget()
        self._multi_img.images_changed.connect(self._on_images_changed)
        lay.addWidget(self._multi_img, 1)

        # Info label
        self._img_info_lbl = QLabel("")
        self._img_info_lbl.setStyleSheet("color:#6a6a9a;font-size:11px;")
        self._img_info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._img_info_lbl)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2a2a4a;")
        lay.addWidget(sep)

        # Convert button
        self._convert_btn = QPushButton("🔄  STL'e Dönüştür  (TRELLIS)")
        self._convert_btn.setObjectName("convertBtn")
        self._convert_btn.setFixedHeight(44)
        self._convert_btn.setEnabled(False)
        self._convert_btn.setToolTip("Yüklü görselleri TRELLIS ile STL'e dönüştür")
        self._convert_btn.clicked.connect(self._start_conversion)
        lay.addWidget(self._convert_btn)

        # Progress
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        lay.addWidget(self._progress_bar)

        self._conv_status_lbl = QLabel("")
        self._conv_status_lbl.setStyleSheet("color:#9a9acc;font-size:12px;")
        self._conv_status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._conv_status_lbl.setWordWrap(True)
        lay.addWidget(self._conv_status_lbl)

        # Download
        self._download_btn = QPushButton("⬇️  STL Dosyasını İndir")
        self._download_btn.setObjectName("downloadBtn")
        self._download_btn.setFixedHeight(44)
        self._download_btn.setEnabled(False)
        self._download_btn.clicked.connect(self._download_stl)
        lay.addWidget(self._download_btn)

        self._stl_info_lbl = QLabel("")
        self._stl_info_lbl.setStyleSheet("color:#6a6a9a;font-size:11px;")
        self._stl_info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._stl_info_lbl)

        return frame

    # ── Event filter (Enter to send) ─────────────────────────

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        if obj is self._message_input and event.type() == QEvent.Type.KeyPress:
            key: QKeyEvent = event
            if (key.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
                    and not (key.modifiers() & Qt.KeyboardModifier.ShiftModifier)):
                self._send_message()
                return True
        return super().eventFilter(obj, event)

    # ── API key check ────────────────────────────────────────

    def _check_api_key(self):
        if self.agent.is_ready():
            self._api_status_lbl.setText("● Groq API Bağlı")
            self._api_status_lbl.setStyleSheet("color:#7affc4;font-size:11px;")
            self._append_bot_message(
                "Merhaba! 3D Model Generator AI Agent'ıyım. 🎉\n\n"
                "Yapabileceklerim:\n"
                "• Sorularınızı yanıtlarım 💬\n"
                "• Yüklediğiniz görselleri analiz ederim 🖼️\n"
                "• **Tek veya çok görsel** ile STL 3D model oluşturun 🖨️\n\n"
                "💡 Farklı açılardan çekilen birden fazla görsel yüklemek "
                "daha iyi 3D sonuç verir!\n\n"
                "Görselleri yüklemek için sürükleyip bırakın veya ➕ Görsel Ekle düğmesini kullanın."
            )
        else:
            self._api_status_lbl.setText("● API Anahtarı Gerekli")
            self._api_status_lbl.setStyleSheet("color:#ff7a7a;font-size:11px;")
            self._append_bot_message(
                "⚠️ **Groq API anahtarı bulunamadı.**\n\n"
                "1. ⚙️ **Ayarlar** → API anahtarını girin\n"
                "2. https://console.groq.com adresinden ücretsiz anahtar alın\n\n"
                "**TRELLIS ile görsel → STL dönüştürme API anahtarı gerektirmez!** 🎯\n"
                "Görselleri yükleyip dönüştürmeye başlayabilirsiniz."
            )

    # ── Images changed callback ──────────────────────────────

    def _on_images_changed(self, paths: List[str]):
        """Called whenever the image list is updated."""
        self.current_image_paths = paths
        n = len(paths)

        if n == 0:
            self._img_info_lbl.setText("")
            self._convert_btn.setEnabled(False)
            self._conv_status_lbl.setText("")
            return

        # Build info text
        total_kb = sum(os.path.getsize(p) / 1024 for p in paths if os.path.exists(p))
        size_str = f"{total_kb:.0f} KB" if total_kb < 1024 else f"{total_kb/1024:.1f} MB"
        mode = "Çok Görsel Modu 🎯" if n > 1 else "Tek Görsel Modu"
        self._img_info_lbl.setText(f"{n} görsel  •  {size_str}  •  {mode}")

        if self.converter.is_available():
            self._convert_btn.setEnabled(True)
            tip = (f"✅ {n} görsel yüklendi. Dönüştürmeye hazır!"
                   if n == 1 else
                   f"✅ {n} farklı açı yüklendi — çok görsel modu aktif 🎯")
            self._conv_status_lbl.setText(tip)
        else:
            self._convert_btn.setEnabled(False)
            self._conv_status_lbl.setText(
                "⚠️ TRELLIS kurulu değil.\n"
                "Ayarlar → Dönüştürme sekmesindeki kurulum adımlarını izleyin."
            )

        # Notify chat
        fnames = ", ".join(os.path.basename(p) for p in paths[:3])
        if n > 3:
            fnames += f" +{n-3} daha"
        self._append_system_message(f"📎 {n} görsel yüklendi: {fnames}")

        # Auto-analyze first image with LLM
        if self.agent.is_ready() and paths:
            self._send_auto_analyze(paths[0], n)

    # ── Chat helpers ─────────────────────────────────────────

    def _append_user_message(self, text: str, has_image: bool = False):
        tag = " 🖼️" if has_image else ""
        html = (
            f'<div style="margin:6px 0;text-align:right;">'
            f'<span style="display:inline-block;background:#3a2a7a;color:#e2e2f0;'
            f'border-radius:10px 10px 2px 10px;padding:8px 14px;'
            f'max-width:85%;font-size:13px;text-align:left;">'
            f'<b style="color:#c8b8ff;">Sen{tag}</b><br>'
            f'{self._esc(text)}</span></div>'
        )
        self._chat_display.append(html)
        self._scroll_bottom()

    def _append_bot_message(self, text: str):
        html = (
            f'<div style="margin:6px 0;">'
            f'<span style="display:inline-block;background:#1e1e38;color:#e2e2f0;'
            f'border-radius:10px 10px 10px 2px;padding:8px 14px;'
            f'max-width:90%;font-size:13px;">'
            f'<b style="color:#7c6af7;">🤖 Asistan</b><br>'
            f'{self._fmt(text)}</span></div>'
        )
        self._chat_display.append(html)
        self._scroll_bottom()

    def _append_system_message(self, text: str, color: str = "#ffc77a"):
        html = (
            f'<div style="margin:4px 0;text-align:center;">'
            f'<span style="color:{color};font-size:11px;font-style:italic;">'
            f'{self._esc(text)}</span></div>'
        )
        self._chat_display.append(html)
        self._scroll_bottom()

    def _esc(self, t: str) -> str:
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

    def _fmt(self, t: str) -> str:
        import re
        t = self._esc(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = re.sub(r"`(.+?)`",
                   r'<code style="background:#2a2a4a;padding:1px 4px;border-radius:4px;">\1</code>', t)
        return t

    def _scroll_bottom(self):
        sb = self._chat_display.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── Send message ─────────────────────────────────────────

    def _send_message(self):
        text = self._message_input.toPlainText().strip()
        if not text:
            return
        self._message_input.clear()
        self._set_input_enabled(False)

        first_img = self.current_image_paths[0] if self.current_image_paths else None
        self._append_user_message(text, has_image=bool(first_img))
        self._typing_lbl.setText("🤖 Asistan yanıt yazıyor...")

        if not self.agent.is_ready():
            if load_config().get("groq_api_key"):
                self.agent.reload()

        self.llm_worker = LLMWorker(self.agent, text, first_img)
        self.llm_worker.finished.connect(self._on_llm_response)
        self.llm_worker.error.connect(self._on_llm_error)
        self.llm_worker.finished.connect(lambda: self._set_input_enabled(True))
        self.llm_worker.error.connect(lambda: self._set_input_enabled(True))
        self.llm_worker.start()

    def _on_llm_response(self, r: str):
        self._typing_lbl.setText("")
        self._append_bot_message(r)

    def _on_llm_error(self, e: str):
        self._typing_lbl.setText("")
        self._append_system_message(f"❌ Hata: {e}", "#ff7a7a")

    def _set_input_enabled(self, enabled: bool):
        self._message_input.setEnabled(enabled)
        self._send_btn.setEnabled(enabled)
        if enabled:
            self._message_input.setFocus()

    # ── Auto-analyze ─────────────────────────────────────────

    def _send_auto_analyze(self, image_path: str, total: int):
        extra = f" ({total} farklı açıdan görsel yüklendi)" if total > 1 else ""
        prompt = (
            f"Bu görseli{extra} analiz et. 3D baskı için uygun mu? "
            "Nesneyi kısaca tanımla ve TRELLIS ile STL dönüşümü için tavsiye ver."
        )
        self._append_user_message(prompt, has_image=True)
        self._typing_lbl.setText("🤖 Asistan görseli analiz ediyor...")
        self._set_input_enabled(False)

        self.llm_worker = LLMWorker(self.agent, prompt, image_path)
        self.llm_worker.finished.connect(self._on_llm_response)
        self.llm_worker.error.connect(self._on_llm_error)
        self.llm_worker.finished.connect(lambda: self._set_input_enabled(True))
        self.llm_worker.error.connect(lambda: self._set_input_enabled(True))
        self.llm_worker.start()

    # ── STL Conversion ───────────────────────────────────────

    def _start_conversion(self):
        if not self.current_image_paths:
            QMessageBox.warning(self, "Uyarı", "Önce en az bir görsel yükleyin.")
            return
        if not self.converter.is_available():
            QMessageBox.warning(self, "TRELLIS Kurulu Değil",
                                self.converter.get_install_instructions())
            return

        config = load_config()
        output_dir = config.get("output_dir", "output")
        os.makedirs(output_dir, exist_ok=True)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        n = len(self.current_image_paths)
        tag = f"multi{n}" if n > 1 else "single"
        base = os.path.splitext(os.path.basename(self.current_image_paths[0]))[0]
        output_path = os.path.join(output_dir, f"{base}_{tag}_{ts}.stl")

        self._convert_btn.setEnabled(False)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(True)
        mode_txt = f"{n} görsel (çok açı modu)" if n > 1 else "1 görsel"
        self._conv_status_lbl.setText(f"🔄 Dönüştürme başlıyor... ({mode_txt})")
        self._append_system_message(f"🔄 TRELLIS dönüştürme başladı ({mode_txt})...")

        self.conv_worker = ConversionWorker(self.converter, self.current_image_paths, output_path)
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
        self._stl_info_lbl.setText(f"✅ {os.path.basename(stl_path)}  •  {size_str}")
        self._download_btn.setEnabled(True)
        self._status_bar.showMessage(f"✅ STL oluşturuldu: {stl_path}")
        QTimer.singleShot(3000, lambda: self._progress_bar.setVisible(False))

        self._append_system_message(f"✅ STL hazır! ({size_str})", "#7affc4")
        if self.agent.is_ready():
            self._append_bot_message(
                f"🎉 **3D model başarıyla oluşturuldu!**\n\n"
                f"📄 Dosya: `{os.path.basename(stl_path)}`\n"
                f"📦 Boyut: {size_str}\n\n"
                f"⬇️ **STL Dosyasını İndir** düğmesiyle kaydedebilirsiniz.\n"
                f"Cura, PrusaSlicer veya Meshmixer ile açabilirsiniz."
            )

    def _on_conversion_error(self, error: str):
        self._convert_btn.setEnabled(True)
        self._progress_bar.setVisible(False)
        self._conv_status_lbl.setText("❌ Dönüştürme hatası")
        self._append_system_message(f"❌ {error}", "#ff7a7a")
        QMessageBox.critical(self, "Dönüştürme Hatası", error)

    # ── Download STL ─────────────────────────────────────────

    def _download_stl(self):
        if not self.current_stl_path or not os.path.exists(self.current_stl_path):
            QMessageBox.warning(self, "Hata", "İndirilecek STL dosyası bulunamadı.")
            return
        default = os.path.basename(self.current_stl_path)
        save_path, _ = QFileDialog.getSaveFileName(
            self, "STL Dosyasını Kaydet",
            os.path.expanduser(f"~/Downloads/{default}"),
            "STL Dosyaları (*.stl);;Tüm Dosyalar (*)",
        )
        if save_path:
            try:
                shutil.copy2(self.current_stl_path, save_path)
                size_kb = os.path.getsize(save_path) / 1024
                self._append_system_message(f"⬇️ İndirildi: {save_path}", "#ffc77a")
                self._status_bar.showMessage(f"⬇️ İndirildi: {save_path}")
                QMessageBox.information(self, "İndirme Tamamlandı",
                                        f"✅ Kaydedildi:\n{save_path}\n\nBoyut: {size_kb:.1f} KB")
            except Exception as e:
                QMessageBox.critical(self, "İndirme Hatası", str(e))

    # ── Settings ─────────────────────────────────────────────

    def _open_settings(self):
        d = SettingsDialog(self)
        d.settings_saved.connect(self._on_settings_saved)
        d.exec()

    def _on_settings_saved(self):
        self.agent.reload()
        if self.agent.is_ready():
            self._api_status_lbl.setText("● Groq API Bağlı")
            self._api_status_lbl.setStyleSheet("color:#7affc4;font-size:11px;")
        else:
            self._api_status_lbl.setText("● API Anahtarı Gerekli")
            self._api_status_lbl.setStyleSheet("color:#ff7a7a;font-size:11px;")
        self._status_bar.showMessage("✅ Ayarlar kaydedildi.")

    # ── Reset ─────────────────────────────────────────────────

    def _reset_all(self):
        if QMessageBox.question(
            self, "Sıfırla",
            "Sohbet geçmişi ve tüm görseller silinecek. Devam edilsin mi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.agent.clear_history()
            self.current_image_paths = []
            self.current_stl_path = None
            self._chat_display.clear()
            self._multi_img.clear_all()
            self._img_info_lbl.setText("")
            self._stl_info_lbl.setText("")
            self._conv_status_lbl.setText("")
            self._progress_bar.setVisible(False)
            self._convert_btn.setEnabled(False)
            self._download_btn.setEnabled(False)
            self._check_api_key()

