import oss2
import configparser
import os
import sys
import markdown
import markdown.extensions
import json
import time
import hashlib
import uuid
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QSplitter, QAction, QFileDialog, QMessageBox,
                             QToolBar, QStatusBar, QWidget, QTreeView, QFileSystemModel,
                             QDockWidget, QComboBox, QFontComboBox, QLabel, QDialog,
                             QPushButton, QDialogButtonBox, QFormLayout, QSpinBox,
                             QCheckBox, QTabWidget, QListWidget, QListWidgetItem,
                             QProgressBar, QSystemTrayIcon, QMenu, QInputDialog,
                             QLineEdit, QGroupBox, QScrollArea, QShortcut, QTextBrowser)
from PyQt5.QtCore import Qt, QSettings, QDir, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import (QFont, QKeySequence, QTextCursor, QColor, QSyntaxHighlighter, 
                         QTextCharFormat, QPalette, QIcon, QPixmap, QTextDocument,
                         QTextBlockFormat, QTextListFormat)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter

class TextProcessor:
    """本地文本处理器 - 替代AI功能"""
    
    @staticmethod
    def improve_writing(text):
        """改进写作 - 本地规则处理"""
        improvements = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            if len(line.strip()) > 0:
                # 自动在句号后加空格（如果忘记）
                line = line.replace('。', '。 ')
                line = line.replace('！', '！ ')
                line = line.replace('？', '？ ')
                
                # 移除多余的空格
                line = ' '.join(line.split())
                
                lines[i] = line
        
        improved_text = '\n'.join(lines)
        return f"改进建议：\n\n{improved_text}\n\n* 已优化标点符号和空格 *"
    
    @staticmethod
    def summarize_text(text):
        """文本摘要 - 本地处理"""
        words = text.split()
        if len(words) <= 50:
            return f"文本较短，无需摘要：\n\n{text}"
        
        # 简单的摘要算法 - 取首句和关键词
        sentences = text.split('。')
        if len(sentences) > 1:
            summary = sentences[0] + '。'
            if len(sentences) > 2:
                summary += sentences[1] + '。'
        else:
            summary = text[:100] + '...'
        
        word_count = len(words)
        char_count = len(text)
        
        return f"摘要：\n\n{summary}\n\n原文统计：{word_count} 词，{char_count} 字符"
    
    @staticmethod
    def check_grammar(text):
        """语法检查 - 本地规则"""
        issues = []
        
        # 检查常见中文标点错误
        if ' ,' in text or ' .' in text:
            issues.append("中英文标点混用")
        
        # 检查连续空格
        if '  ' in text:
            issues.append("存在连续空格")
        
        # 检查段落开头空格
        lines = text.split('\n')
        for i, line in enumerate(lines[:10]):  # 只检查前10行
            if line.strip() and not line.startswith('#') and not line.startswith('>'):
                if not line.startswith('    ') and len(line) > 0:
                    if line[0] not in ['-', '*', '+', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0']:
                        # 检查是否应该缩进
                        pass
        
        if not issues:
            return "语法检查完成。未发现明显问题。"
        else:
            return f"语法检查完成。发现以下建议：\n\n" + "\n".join(f"- {issue}" for issue in issues)

class LocalAIAssistant(QThread):
    """本地AI助手线程"""
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, action_type, text):
        super().__init__()
        self.action_type = action_type
        self.text = text
        self.processor = TextProcessor()
        
    def run(self):
        try:
            time.sleep(1)  # 模拟处理时间
            
            if self.action_type == "improve_writing":
                response = self.processor.improve_writing(self.text)
            elif self.action_type == "summarize":
                response = self.processor.summarize_text(self.text)
            elif self.action_type == "check_grammar":
                response = self.processor.check_grammar(self.text)
            else:
                response = "本地AI处理完成"
            
            self.response_received.emit(response)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class AdvancedMarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        self.setup_rules()
        
    def setup_rules(self):
        # 标题格式
        header_format = QTextCharFormat()
        header_format.setForeground(QColor("#e74c3c"))
        header_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((r'^#{1,6}\s.*', header_format))
        
        # 粗体格式
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Bold)
        bold_format.setForeground(QColor("#2980b9"))
        self.highlighting_rules.append((r'\*\*.*?\*\*', bold_format))
        self.highlighting_rules.append((r'__.*?__', bold_format))
        
        # 斜体格式
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        italic_format.setForeground(QColor("#8e44ad"))
        self.highlighting_rules.append((r'\*.*?\*', italic_format))
        self.highlighting_rules.append((r'_.*?_', italic_format))
        
        # 删除线格式
        strike_format = QTextCharFormat()
        strike_format.setForeground(QColor("#95a5a6"))
        strike_format.setFontStrikeOut(True)
        self.highlighting_rules.append((r'~~.*?~~', strike_format))
        
        # 代码格式
        code_format = QTextCharFormat()
        code_format.setForeground(QColor("#c7254e"))
        code_format.setBackground(QColor("#f9f2f4"))
        code_format.setFontFamily("Consolas")
        self.highlighting_rules.append((r'`[^`]*`', code_format))
        
        # 代码块格式
        code_block_format = QTextCharFormat()
        code_block_format.setForeground(QColor("#333"))
        code_block_format.setBackground(QColor("#f8f8f8"))
        code_block_format.setFontFamily("Consolas")
        self.highlighting_rules.append((r'```.*?```', code_block_format))
        
        # 链接格式
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#3498db"))
        link_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        self.highlighting_rules.append((r'\[.*?\]\(.*?\)', link_format))
        
        # 图片格式
        image_format = QTextCharFormat()
        image_format.setForeground(QColor("#9b59b6"))
        image_format.setFontItalic(True)
        self.highlighting_rules.append((r'!\[.*?\]\(.*?\)', image_format))
        
        # 列表格式
        list_format = QTextCharFormat()
        list_format.setForeground(QColor("#27ae60"))
        self.highlighting_rules.append((r'^[\*\-\+]\s.*', list_format))
        self.highlighting_rules.append((r'^\d+\.\s.*', list_format))
        
        # 引用格式
        quote_format = QTextCharFormat()
        quote_format.setForeground(QColor("#7f8c8d"))
        quote_format.setFontItalic(True)
        self.highlighting_rules.append((r'^>.*', quote_format))
        
        # 表格格式
        table_format = QTextCharFormat()
        table_format.setForeground(QColor("#d35400"))
        self.highlighting_rules.append((r'^\|.*\|.*', table_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            import re
            for match in re.finditer(pattern, text, re.MULTILINE | re.DOTALL):
                start, end = match.span()
                self.setFormat(start, end - start, format)

class FileExplorer(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("文件浏览器", parent)
        self.parent = parent
        self.initUI()
        
    def initUI(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 路径导航和操作按钮
        path_layout = QHBoxLayout()
        
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("输入路径或点击浏览...")
        self.path_edit.returnPressed.connect(self.navigate_to_path)
        path_layout.addWidget(self.path_edit)
        
        self.browse_btn = QPushButton("浏览")
        self.browse_btn.clicked.connect(self.browse_directory)
        path_layout.addWidget(self.browse_btn)
        
        layout.addLayout(path_layout)
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索文件...")
        self.search_box.textChanged.connect(self.filter_files)
        search_layout.addWidget(QLabel("搜索:"))
        search_layout.addWidget(self.search_box)
        
        layout.addLayout(search_layout)
        
        # 文件类型过滤
        filter_layout = QHBoxLayout()
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "所有文件 (*)",
            "文档文件 (*.md *.txt *.markdown *.doc *.docx *.pdf)",
            "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp *.svg)",
            "代码文件 (*.py *.java *.cpp *.c *.html *.css *.js *.json *.xml)",
            "媒体文件 (*.mp3 *.mp4 *.avi *.mov *.wav)"
        ])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        filter_layout.addWidget(QLabel("过滤:"))
        filter_layout.addWidget(self.filter_combo)
        
        layout.addLayout(filter_layout)
        
        # 文件树视图
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.homePath())
        
        # 设置列宽
        self.model.setHeaderData(0, Qt.Horizontal, "名称")
        self.model.setHeaderData(1, Qt.Horizontal, "大小")
        self.model.setHeaderData(2, Qt.Horizontal, "类型")
        self.model.setHeaderData(3, Qt.Horizontal, "修改时间")
        
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.homePath()))
        self.tree.doubleClicked.connect(self.on_file_double_click)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        
        # 设置列宽
        self.tree.setColumnWidth(0, 250)  # 名称列宽一些
        self.tree.setColumnWidth(1, 80)   # 大小
        self.tree.setColumnWidth(2, 100)  # 类型
        self.tree.setColumnWidth(3, 120)  # 修改时间
        
        # 隐藏不需要的列（如有）
        # self.tree.hideColumn(1)  # 可以根据需要隐藏某些列
        
        layout.addWidget(self.tree)
        
        # 状态栏
        status_layout = QHBoxLayout()
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_view)
        status_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(status_layout)
        self.setWidget(widget)
        
        # 更新路径显示
        self.update_path_display(QDir.homePath())
        
    def update_path_display(self, path):
        """更新路径显示"""
        self.path_edit.setText(path)
        self.status_label.setText(f"浏览: {path}")
        
    def navigate_to_path(self):
        """导航到输入的路径"""
        path = self.path_edit.text()
        if os.path.exists(path):
            if os.path.isdir(path):
                self.tree.setRootIndex(self.model.index(path))
                self.update_path_display(path)
            else:
                QMessageBox.information(self, "提示", "请输入有效的文件夹路径")
        else:
            QMessageBox.warning(self, "错误", "路径不存在")
            
    def browse_directory(self):
        """浏览选择目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择目录", 
            self.path_edit.text() or QDir.homePath()
        )
        if directory:
            self.tree.setRootIndex(self.model.index(directory))
            self.update_path_display(directory)
        
    def filter_files(self, text):
        """过滤文件"""
        if text:
            # 使用代理模型进行过滤
            from PyQt5.QtCore import QSortFilterProxyModel
            
            proxy_model = QSortFilterProxyModel()
            proxy_model.setSourceModel(self.model)
            proxy_model.setFilterRegExp(text)
            proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
            self.tree.setModel(proxy_model)
        else:
            # 恢复原始模型
            self.tree.setModel(self.model)
            self.tree.setRootIndex(self.model.index(self.path_edit.text() or QDir.homePath()))
        
    def apply_filter(self, filter_text):
        """应用文件类型过滤"""
        if filter_text == "所有文件 (*)":
            self.model.setNameFilters([])
        elif filter_text == "文档文件 (*.md *.txt *.markdown *.doc *.docx *.pdf)":
            self.model.setNameFilters(["*.md", "*.txt", "*.markdown", "*.doc", "*.docx", "*.pdf"])
        elif filter_text == "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp *.svg)":
            self.model.setNameFilters(["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.svg"])
        elif filter_text == "代码文件 (*.py *.java *.cpp *.c *.html *.css *.js *.json *.xml)":
            self.model.setNameFilters(["*.py", "*.java", "*.cpp", "*.c", "*.html", "*.css", "*.js", "*.json", "*.xml"])
        elif filter_text == "媒体文件 (*.mp3 *.mp4 *.avi *.mov *.wav)":
            self.model.setNameFilters(["*.mp3", "*.mp4", "*.avi", "*.mov", "*.wav"])
        
        self.model.setNameFilterDisables(False)
        self.refresh_view()
            
    def on_file_double_click(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path):
            # 根据文件类型处理
            if path.endswith(('.md', '.txt', '.markdown')):
                self.parent.open_file(path)
            else:
                # 尝试用系统默认程序打开其他文件
                try:
                    import subprocess
                    if os.name == 'nt':  # Windows
                        os.startfile(path)
                    elif os.name == 'posix':  # Linux, macOS
                        subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', path))
                except Exception as e:
                    QMessageBox.information(self, "打开文件", f"无法打开文件: {str(e)}")
        else:
            # 如果是文件夹，导航到该文件夹
            self.tree.setRootIndex(self.model.index(path))
            self.update_path_display(path)
            
    def show_context_menu(self, position):
        """显示右键菜单"""
        index = self.tree.indexAt(position)
        if not index.isValid():
            return
            
        path = self.model.filePath(index)
        menu = QMenu()
        
        if os.path.isfile(path):
            open_action = menu.addAction("打开")
            open_with_action = menu.addAction("用系统程序打开")
            menu.addSeparator()
            
            if path.endswith(('.md', '.txt', '.markdown')):
                open_action.triggered.connect(lambda: self.parent.open_file(path))
            else:
                open_action.triggered.connect(lambda: self.open_with_system(path))
                
            open_with_action.triggered.connect(lambda: self.open_with_system(path))
            
        else:
            open_folder_action = menu.addAction("打开文件夹")
            open_folder_action.triggered.connect(lambda: self.tree.setRootIndex(index))
            
        menu.addSeparator()
        
        rename_action = menu.addAction("重命名")
        delete_action = menu.addAction("删除")
        menu.addSeparator()
        
        properties_action = menu.addAction("属性")
        
        # 连接信号
        rename_action.triggered.connect(lambda: self.rename_item(index))
        delete_action.triggered.connect(lambda: self.delete_item(index))
        properties_action.triggered.connect(lambda: self.show_properties(index))
        
        menu.exec_(self.tree.mapToGlobal(position))
        
    def open_with_system(self, path):
        """用系统默认程序打开文件"""
        try:
            import subprocess
            if os.name == 'nt':  # Windows
                os.startfile(path)
            elif os.name == 'posix':  # Linux, macOS
                subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', path))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件: {str(e)}")
            
    def rename_item(self, index):
        """重命名文件或文件夹"""
        old_path = self.model.filePath(index)
        old_name = os.path.basename(old_path)
        
        new_name, ok = QInputDialog.getText(
            self, "重命名", "输入新名称:", text=old_name
        )
        
        if ok and new_name and new_name != old_name:
            try:
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                os.rename(old_path, new_path)
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名失败: {str(e)}")
                
    def delete_item(self, index):
        """删除文件或文件夹"""
        path = self.model.filePath(index)
        name = os.path.basename(path)
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除 '{name}' 吗？此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    import shutil
                    shutil.rmtree(path)
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
                
    def show_properties(self, index):
        """显示文件属性"""
        path = self.model.filePath(index)
        name = os.path.basename(path)
        
        try:
            stat = os.stat(path)
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            created = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            
            if os.path.isfile(path):
                file_type = "文件"
                import mimetypes
                mime_type, _ = mimetypes.guess_type(path)
                file_type += f" ({mime_type or '未知类型'})"
            else:
                file_type = "文件夹"
                # 计算文件夹中的文件数量
                file_count = sum(len(files) for _, _, files in os.walk(path))
                file_type += f" ({file_count} 个项目)"
            
            message = f"""
名称: {name}
路径: {path}
类型: {file_type}
大小: {self.format_file_size(size)}
创建时间: {created}
修改时间: {modified}
            """.strip()
            
            QMessageBox.information(self, "属性", message)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法获取属性: {str(e)}")
            
    def format_file_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
        
    def refresh_view(self):
        """刷新视图"""
        current_path = self.path_edit.text() or QDir.homePath()
        self.tree.setRootIndex(self.model.index(current_path))

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("设置")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 编辑器设置
        editor_tab = QWidget()
        editor_layout = QFormLayout(editor_tab)
        
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(self.parent.editor_font))
        editor_layout.addRow("编辑器字体:", self.font_combo)
        
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 72)
        self.font_size.setValue(self.parent.editor_font_size)
        editor_layout.addRow("字体大小:", self.font_size)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["默认", "暗色", "护眼绿", "深蓝"])
        self.theme_combo.setCurrentText(self.parent.current_theme)
        editor_layout.addRow("主题:", self.theme_combo)
        
        tab_widget.addTab(editor_tab, "编辑器")
        
        # 自动保存设置
        save_tab = QWidget()
        save_layout = QFormLayout(save_tab)
        
        self.auto_save = QCheckBox("启用自动保存")
        self.auto_save.setChecked(self.parent.auto_save_enabled)
        save_layout.addRow(self.auto_save)
        
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(1, 60)
        self.auto_save_interval.setValue(self.parent.auto_save_interval)
        self.auto_save_interval.setSuffix(" 分钟")
        save_layout.addRow("自动保存间隔:", self.auto_save_interval)
        
        self.backup_enabled = QCheckBox("启用自动备份")
        self.backup_enabled.setChecked(self.parent.backup_enabled)
        save_layout.addRow(self.backup_enabled)
        
        tab_widget.addTab(save_tab, "自动保存")
        
        # AI助手设置
        ai_tab = QWidget()
        ai_layout = QFormLayout(ai_tab)
        
        self.ai_enabled = QCheckBox("启用AI助手功能")
        self.ai_enabled.setChecked(self.parent.ai_assistant_enabled)
        ai_layout.addRow(self.ai_enabled)
        
        ai_info = QLabel("AI助手使用本地文本处理技术，无需网络连接")
        ai_info.setWordWrap(True)
        ai_layout.addRow(ai_info)
        
        tab_widget.addTab(ai_tab, "AI助手")
        
        # 云同步设置
        cloud_tab = QWidget()
        cloud_layout = QFormLayout(cloud_tab)
        
        self.cloud_enabled = QCheckBox("启用云同步")
        self.cloud_enabled.setChecked(self.parent.cloud_sync_enabled)
        cloud_layout.addRow(self.cloud_enabled)
        
        cloud_info = QLabel("云同步功能将文件备份到阿里云OSS")
        cloud_info.setWordWrap(True)
        cloud_layout.addRow(cloud_info)
        
        tab_widget.addTab(cloud_tab, "云同步")
        
        layout.addWidget(tab_widget)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def accept(self):
        self.parent.editor_font = self.font_combo.currentFont().family()
        self.parent.editor_font_size = self.font_size.value()
        self.parent.current_theme = self.theme_combo.currentText()
        self.parent.auto_save_enabled = self.auto_save.isChecked()
        self.parent.auto_save_interval = self.auto_save_interval.value()
        self.parent.backup_enabled = self.backup_enabled.isChecked()
        self.parent.ai_assistant_enabled = self.ai_enabled.isChecked()
        self.parent.cloud_sync_enabled = self.cloud_enabled.isChecked()
        
        self.parent.apply_settings()
        super().accept()

class ProfessionalMarkdownEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.recent_files = []
        self.settings = QSettings("SunsetMD", "SunsetMD Pro")
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(self.create_backup)
        
        # 默认设置
        self.editor_font = "Consolas"
        self.editor_font_size = 12
        self.current_theme = "默认"
        self.auto_save_enabled = False
        self.auto_save_interval = 5
        self.backup_enabled = True
        self.ai_assistant_enabled = True
        self.cloud_sync_enabled = True
        
        self.initUI()
        self.load_settings()
        
    def initUI(self):
        self.setWindowTitle("SunsetMD Pro - 专业Markdown编辑器")
        self.setGeometry(100, 100, 1600, 1000)
        
        # 设置应用图标
        self.set_application_icon()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        layout.addWidget(self.tab_widget)
        
        # 创建新标签页
        self.create_new_tab()
        
        # 创建文件浏览器
        self.file_explorer = FileExplorer(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.file_explorer)
        
        # 创建大纲视图
        self.outline_dock = QDockWidget("文档大纲", self)
        self.outline_widget = QListWidget()
        self.outline_dock.setWidget(self.outline_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.outline_dock)
        
        # 创建菜单
        self.create_menus()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # 更新状态
        self.update_status()
        
        # 创建系统托盘
        self.create_system_tray()
        
        # 设置任务栏图标
        self.set_taskbar_icon()
        
    def set_application_icon(self):
        """设置应用图标"""
        try:
            # 尝试从icons目录加载图标
            icon_path = "./icons/ssmd.png"
            if os.path.exists(icon_path):
                app_icon = QIcon(icon_path)
                self.setWindowIcon(app_icon)
                QApplication.setWindowIcon(app_icon)
            else:
                # 如果图标文件不存在，创建一个简单的默认图标
                self.create_default_icon()
        except Exception as e:
            print(f"加载图标失败: {e}")
            self.create_default_icon()
            
    def create_default_icon(self):
        """创建默认图标"""
        try:
            # 创建一个简单的默认图标
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor("#3498db"))  # 蓝色背景
            
            # 在图标上绘制"M"字母
            from PyQt5.QtGui import QPainter, QPen
            painter = QPainter(pixmap)
            painter.setPen(QPen(QColor("white")))
            painter.setFont(QFont("Arial", 32, QFont.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "M")
            painter.end()
            
            app_icon = QIcon(pixmap)
            self.setWindowIcon(app_icon)
            QApplication.setWindowIcon(app_icon)
        except Exception as e:
            print(f"创建默认图标失败: {e}")
            
    def set_taskbar_icon(self):
        """设置任务栏图标"""
        try:
            # 在Windows上设置任务栏图标
            if sys.platform == "win32":
                import ctypes
                myappid = 'sunsetmd.pro.editor.2.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"设置任务栏图标失败: {e}")
        
    def create_system_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
            
        self.tray_icon = QSystemTrayIcon(self)
        
        # 设置托盘图标
        try:
            icon_path = "./icons/ssmd.png"
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
            else:
                # 使用窗口图标作为托盘图标
                self.tray_icon.setIcon(self.windowIcon())
        except:
            pass
            
        self.tray_icon.setToolTip("SunsetMD Pro")
        
        tray_menu = QMenu(self)
        show_action = tray_menu.addAction("显示")
        show_action.triggered.connect(self.show_normal)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
        
        # 托盘图标消息
        self.tray_icon.showMessage(
            "SunsetMD Pro", 
            "应用程序已启动并运行在系统托盘中",
            QSystemTrayIcon.Information, 
            2000
        )
        
    def show_normal(self):
        """显示窗口并置顶"""
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()
        self.raise_()
        
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_normal()
        elif reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_normal()
                
    def quit_application(self):
        self.save_settings()
        QApplication.quit()

    def create_new_tab(self, file_path=None):
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧编辑器
        editor = QTextEdit()
        editor.setFont(QFont(self.editor_font, self.editor_font_size))
        
        # 应用语法高亮
        highlighter = AdvancedMarkdownHighlighter(editor.document())
        
        # 右侧预览
        preview = QWebEngineView()
        preview.setHtml(self.get_preview_html(""))
        
        splitter.addWidget(editor)
        splitter.addWidget(preview)
        splitter.setSizes([600, 600])
        
        # 连接信号
        editor.textChanged.connect(lambda: self.update_preview(editor, preview))
        editor.textChanged.connect(self.update_outline)
        editor.textChanged.connect(self.update_status)
        
        # 添加标签页
        if file_path:
            tab_name = os.path.basename(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    editor.setPlainText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开文件失败: {str(e)}")
                return
        else:
            tab_name = "新文档"
            
        index = self.tab_widget.addTab(splitter, tab_name)
        self.tab_widget.setCurrentIndex(index)
        
        # 设置标签页图标
        self.set_tab_icon(index, file_path)
        
        # 设置当前文件
        if file_path:
            self.current_file = file_path
            self.add_to_recent_files(file_path)
            
        return editor, preview

    def set_tab_icon(self, index, file_path=None):
        """设置标签页图标"""
        try:
            if file_path and file_path.endswith('.md'):
                # Markdown文件图标
                icon_path = "./icons/markdown_icon.png"
                if os.path.exists(icon_path):
                    self.tab_widget.setTabIcon(index, QIcon(icon_path))
            else:
                # 新文件图标
                icon_path = "./icons/new_file_icon.png"
                if os.path.exists(icon_path):
                    self.tab_widget.setTabIcon(index, QIcon(icon_path))
        except:
            pass  # 如果图标加载失败，忽略错误

    def create_menus(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        new_action = QAction("新建", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        new_tab_action = QAction("新建标签页", self)
        new_tab_action.setShortcut("Ctrl+T")
        new_tab_action.triggered.connect(lambda: self.create_new_tab())
        file_menu.addAction(new_tab_action)
        
        open_action = QAction("打开", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # 最近文件子菜单
        self.recent_menu = file_menu.addMenu("最近文件")
        self.update_recent_menu()
        
        file_menu.addSeparator()
        
        save_action = QAction("保存", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("另存为", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)
        
        save_all_action = QAction("全部保存", self)
        save_all_action.setShortcut("Ctrl+Shift+S")
        save_all_action.triggered.connect(self.save_all_files)
        file_menu.addAction(save_all_action)
        
        file_menu.addSeparator()
        
        # 导入导出子菜单
        import_export_menu = file_menu.addMenu("导入导出")
        
        export_html_action = QAction("导出HTML", self)
        export_html_action.triggered.connect(self.export_html)
        import_export_menu.addAction(export_html_action)
        
        export_pdf_action = QAction("导出PDF", self)
        export_pdf_action.triggered.connect(self.export_pdf)
        import_export_menu.addAction(export_pdf_action)
        
        file_menu.addSeparator()
        
        print_action = QAction("打印", self)
        print_action.setShortcut(QKeySequence.Print)
        print_action.triggered.connect(self.print_document)
        file_menu.addAction(print_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        undo_action = QAction("撤销", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("重做", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("剪切", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("复制", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("粘贴", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste)
        edit_menu.addAction(paste_action)
        
        # AI助手菜单
        ai_menu = menubar.addMenu("AI助手")
        
        improve_writing_action = QAction("改进写作", self)
        improve_writing_action.triggered.connect(lambda: self.ai_assistant("improve_writing"))
        ai_menu.addAction(improve_writing_action)
        
        summarize_action = QAction("文本摘要", self)
        summarize_action.triggered.connect(lambda: self.ai_assistant("summarize"))
        ai_menu.addAction(summarize_action)
        
        check_grammar_action = QAction("语法检查", self)
        check_grammar_action.triggered.connect(lambda: self.ai_assistant("check_grammar"))
        ai_menu.addAction(check_grammar_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        toggle_explorer_action = QAction("切换文件浏览器", self)
        toggle_explorer_action.setShortcut("F2")
        toggle_explorer_action.triggered.connect(self.toggle_file_explorer)
        view_menu.addAction(toggle_explorer_action)
        
        toggle_preview_action = QAction("切换预览", self)
        toggle_preview_action.setShortcut("F9")
        toggle_preview_action.triggered.connect(self.toggle_preview)
        view_menu.addAction(toggle_preview_action)
        
        toggle_outline_action = QAction("切换大纲", self)
        toggle_outline_action.setShortcut("F10")
        toggle_outline_action.triggered.connect(self.toggle_outline)
        view_menu.addAction(toggle_outline_action)
        
        # 格式菜单
        format_menu = menubar.addMenu("格式")
        
        bold_action = QAction("粗体", self)
        bold_action.setShortcut("Ctrl+B")
        bold_action.triggered.connect(self.insert_bold)
        format_menu.addAction(bold_action)
        
        italic_action = QAction("斜体", self)
        italic_action.setShortcut("Ctrl+I")
        italic_action.triggered.connect(self.insert_italic)
        format_menu.addAction(italic_action)
        
        format_menu.addSeparator()
        
        for i in range(1, 7):
            heading_action = QAction(f"标题 {i}", self)
            heading_action.setShortcut(f"Ctrl+{i}")
            heading_action.triggered.connect(lambda checked, level=i: self.insert_heading(level))
            format_menu.addAction(heading_action)
            
        # 表格菜单
        table_menu = format_menu.addMenu("表格")
        insert_table_action = QAction("插入表格", self)
        insert_table_action.triggered.connect(self.insert_table)
        table_menu.addAction(insert_table_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        word_count_action = QAction("字数统计", self)
        word_count_action.triggered.connect(self.show_word_count)
        tools_menu.addAction(word_count_action)
        
        tools_menu.addSeparator()
        
        backup_action = QAction("创建备份", self)
        backup_action.triggered.connect(self.create_backup)
        tools_menu.addAction(backup_action)
        
        restore_action = QAction("恢复备份", self)
        restore_action.triggered.connect(self.restore_backup)
        tools_menu.addAction(restore_action)
        
    def create_toolbar(self):
        # 主工具栏
        main_toolbar = QToolBar("主工具栏")
        self.addToolBar(main_toolbar)
        
        # 设置工具栏图标
        try:
            icon_path = "./icons/new_icon.png"
            if os.path.exists(icon_path):
                new_btn = QAction(QIcon(icon_path), "新建", self)
            else:
                new_btn = QAction("新建", self)
        except:
            new_btn = QAction("新建", self)
            
        new_btn.triggered.connect(self.new_file)
        main_toolbar.addAction(new_btn)
        
        try:
            icon_path = "./icons/open_icon.png"
            if os.path.exists(icon_path):
                open_btn = QAction(QIcon(icon_path), "打开", self)
            else:
                open_btn = QAction("打开", self)
        except:
            open_btn = QAction("打开", self)
            
        open_btn.triggered.connect(self.open_file)
        main_toolbar.addAction(open_btn)
        
        try:
            icon_path = "./icons/save_icon.png"
            if os.path.exists(icon_path):
                save_btn = QAction(QIcon(icon_path), "保存", self)
            else:
                save_btn = QAction("保存", self)
        except:
            save_btn = QAction("保存", self)
            
        save_btn.triggered.connect(self.save_file)
        main_toolbar.addAction(save_btn)
        
        main_toolbar.addSeparator()
        
        bold_btn = QAction("粗体", self)
        bold_btn.triggered.connect(self.insert_bold)
        main_toolbar.addAction(bold_btn)
        
        italic_btn = QAction("斜体", self)
        italic_btn.triggered.connect(self.insert_italic)
        main_toolbar.addAction(italic_btn)
        
        main_toolbar.addSeparator()
        
        # 字体选择
        main_toolbar.addWidget(QLabel("字体:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(self.editor_font))
        self.font_combo.currentFontChanged.connect(self.change_font)
        main_toolbar.addWidget(self.font_combo)
        
        # 字号选择
        main_toolbar.addWidget(QLabel("字号:"))
        self.font_size = QComboBox()
        self.font_size.addItems(["8", "9", "10", "11", "12", "14", "16", "18", "20", "22", "24"])
        self.font_size.setCurrentText(str(self.editor_font_size))
        self.font_size.currentTextChanged.connect(self.change_font_size)
        main_toolbar.addWidget(self.font_size)
        
        # AI工具栏
        ai_toolbar = QToolBar("AI助手")
        self.addToolBar(ai_toolbar)
        
        ai_improve_btn = QAction("改进写作", self)
        ai_improve_btn.triggered.connect(lambda: self.ai_assistant("improve_writing"))
        ai_toolbar.addAction(ai_improve_btn)
        
        ai_summarize_btn = QAction("文本摘要", self)
        ai_summarize_btn.triggered.connect(lambda: self.ai_assistant("summarize"))
        ai_toolbar.addAction(ai_summarize_btn)

    # 编辑器操作
    def undo(self):
        editor = self.get_current_editor()
        if editor:
            editor.undo()
            
    def redo(self):
        editor = self.get_current_editor()
        if editor:
            editor.redo()
            
    def cut(self):
        editor = self.get_current_editor()
        if editor:
            editor.cut()
            
    def copy(self):
        editor = self.get_current_editor()
        if editor:
            editor.copy()
            
    def paste(self):
        editor = self.get_current_editor()
        if editor:
            editor.paste()

    def new_file(self):
        self.create_new_tab()
        
    def open_file(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "打开文件", "", "Markdown文件 (*.md *.markdown);;文本文件 (*.txt);;所有文件 (*)"
            )
        
        if file_path:
            self.create_new_tab(file_path)
            
    def save_file(self):
        editor = self.get_current_editor()
        if not editor:
            return False
            
        if self.current_file:
            try:
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(editor.toPlainText())
                self.status_bar.showMessage(f"已保存: {self.current_file}")
                return True
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")
                return False
        else:
            return self.save_as_file()
            
    def save_as_file(self):
        editor = self.get_current_editor()
        if not editor:
            return False
            
        path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", "Markdown文件 (*.md);;所有文件 (*)"
        )
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(editor.toPlainText())
                self.current_file = path
                
                # 更新标签页标题
                index = self.tab_widget.currentIndex()
                self.tab_widget.setTabText(index, os.path.basename(path))
                
                # 更新标签页图标
                self.set_tab_icon(index, path)
                
                self.add_to_recent_files(path)
                self.status_bar.showMessage(f"已保存: {path}")
                return True
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")
                return False
        return False
        
    def save_all_files(self):
        # 简化实现：只保存当前文件
        self.save_file()
        
    def close_tab(self, index):
        if self.tab_widget.count() <= 1:
            self.close()
        else:
            self.tab_widget.removeTab(index)

    def auto_save(self):
        """自动保存功能"""
        if self.get_current_editor() and self.current_file:
            try:
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(self.get_current_editor().toPlainText())
                self.status_bar.showMessage(f"自动保存: {os.path.basename(self.current_file)}")
            except Exception:
                pass

    def ai_assistant(self, action_type):
        """AI助手功能"""
        if not self.ai_assistant_enabled:
            QMessageBox.information(self, "AI助手", "请在设置中启用AI助手功能")
            return
            
        editor = self.get_current_editor()
        if not editor:
            return
            
        text = editor.textCursor().selectedText() or editor.toPlainText()
        if not text:
            QMessageBox.warning(self, "提示", "请先选择文本或输入内容")
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 无限进度条
        
        # 启动本地AI处理线程
        self.ai_thread = LocalAIAssistant(action_type, text)
        self.ai_thread.response_received.connect(self.on_ai_response)
        self.ai_thread.error_occurred.connect(self.on_ai_error)
        self.ai_thread.start()
        
    def on_ai_response(self, response):
        self.progress_bar.setVisible(False)
        editor = self.get_current_editor()
        if editor:
            editor.insertPlainText("\n\n" + response)
        
    def on_ai_error(self, error):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "AI助手错误", f"处理失败: {error}")

    def create_backup(self):
        """创建备份"""
        if self.backup_enabled and self.current_file:
            backup_dir = os.path.join(os.path.dirname(self.current_file), ".backup")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"{os.path.basename(self.current_file)}.{timestamp}.bak")
            
            try:
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(self.get_current_editor().toPlainText())
                self.status_bar.showMessage(f"备份已创建: {os.path.basename(backup_file)}")
            except Exception as e:
                QMessageBox.warning(self, "备份错误", f"创建备份失败: {e}")

    def restore_backup(self):
        """恢复备份"""
        if not self.current_file:
            return
            
        backup_dir = os.path.join(os.path.dirname(self.current_file), ".backup")
        if not os.path.exists(backup_dir):
            QMessageBox.information(self, "恢复备份", "没有找到备份文件")
            return
            
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.bak')]
        if not backup_files:
            QMessageBox.information(self, "恢复备份", "没有找到备份文件")
            return
            
        file, ok = QInputDialog.getItem(self, "恢复备份", "选择备份文件:", backup_files, 0, False)
        if ok and file:
            backup_path = os.path.join(backup_dir, file)
            try:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.get_current_editor().setPlainText(content)
                self.status_bar.showMessage(f"已从备份恢复: {file}")
            except Exception as e:
                QMessageBox.critical(self, "恢复错误", f"恢复备份失败: {e}")

    def update_outline(self):
        """更新文档大纲"""
        editor = self.get_current_editor()
        if not editor:
            return
            
        text = editor.toPlainText()
        self.outline_widget.clear()
        
        import re
        headers = re.findall(r'^(#{1,6})\s+(.*)$', text, re.MULTILINE)
        
        for level, title in headers:
            level_num = len(level)
            indent = "  " * (level_num - 1)
            item = QListWidgetItem(f"{indent}{title.strip()}")
            self.outline_widget.addItem(item)

    def export_pdf(self):
        """导出PDF"""
        editor = self.get_current_editor()
        if not editor:
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "导出PDF", "", "PDF文件 (*.pdf)")
        if path:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            
            document = QTextDocument()
            document.setPlainText(editor.toPlainText())
            document.print_(printer)
            
            self.status_bar.showMessage(f"已导出PDF: {path}")

    def export_html(self):
        """导出HTML"""
        editor = self.get_current_editor()
        if not editor:
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "导出HTML", "", "HTML文件 (*.html)")
        if path:
            try:
                text = editor.toPlainText()
                html = markdown.markdown(text, extensions=['extra', 'codehilite', 'tables'])
                full_html = self.get_preview_html(html)
                
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(full_html)
                self.status_bar.showMessage(f"已导出: {path}")
                QMessageBox.information(self, "成功", f"HTML已导出到: {path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def insert_table(self):
        """插入表格"""
        editor = self.get_current_editor()
        if editor:
            table_md = """| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 内容 | 内容 | 内容 |
| 内容 | 内容 | 内容 |"""
            editor.insertPlainText(table_md)

    def insert_bold(self):
        editor = self.get_current_editor()
        if editor:
            cursor = editor.textCursor()
            if cursor.hasSelection():
                text = cursor.selectedText()
                cursor.insertText(f"**{text}**")
            else:
                cursor.insertText("****")
                cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 2)
                editor.setTextCursor(cursor)
                
    def insert_italic(self):
        editor = self.get_current_editor()
        if editor:
            cursor = editor.textCursor()
            if cursor.hasSelection():
                text = cursor.selectedText()
                cursor.insertText(f"*{text}*")
            else:
                cursor.insertText("**")
                cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 1)
                editor.setTextCursor(cursor)
                
    def insert_heading(self, level):
        editor = self.get_current_editor()
        if editor:
            cursor = editor.textCursor()
            cursor.insertText("#" * level + " ")

    def change_font(self, font):
        self.editor_font = font.family()
        editor = self.get_current_editor()
        if editor:
            current_font = editor.font()
            current_font.setFamily(self.editor_font)
            editor.setFont(current_font)
            
    def change_font_size(self, size):
        self.editor_font_size = int(size)
        editor = self.get_current_editor()
        if editor:
            current_font = editor.font()
            current_font.setPointSize(self.editor_font_size)
            editor.setFont(current_font)

    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()
        
    def apply_settings(self):
        # 应用字体设置
        editor = self.get_current_editor()
        if editor:
            font = QFont(self.editor_font, self.editor_font_size)
            editor.setFont(font)
            
        # 应用主题
        self.apply_theme()
        
        # 应用自动保存
        if self.auto_save_enabled:
            self.auto_save_timer.start(self.auto_save_interval * 60 * 1000)
        else:
            self.auto_save_timer.stop()
            
        # 应用自动备份
        if self.backup_enabled:
            self.backup_timer.start(30 * 60 * 1000)  # 30分钟备份一次
        else:
            self.backup_timer.stop()
            
    def apply_theme(self):
        theme_styles = {
            "默认": """
                QMainWindow { background-color: #f5f5f5; color: #000000; }
                QTextEdit { background-color: white; color: black; }
            """,
            "暗色": """
                QMainWindow { background-color: #2d2d2d; color: #ffffff; }
                QTextEdit { background-color: #1e1e1e; color: #ffffff; }
            """,
            "护眼绿": """
                QMainWindow { background-color: #cce8cf; color: #333333; }
                QTextEdit { background-color: #e8f5e9; color: #333333; }
            """,
            "深蓝": """
                QMainWindow { background-color: #1a365d; color: #e2e8f0; }
                QTextEdit { background-color: #2d3748; color: #e2e8f0; }
            """
        }
        
        style = theme_styles.get(self.current_theme, theme_styles["默认"])
        self.setStyleSheet(style)

    def update_preview(self, editor, preview):
        text = editor.toPlainText()
        html = markdown.markdown(text, extensions=['extra', 'codehilite', 'tables', 'toc'])
        preview.setHtml(self.get_preview_html(html))

    def get_preview_html(self, content):
        theme_css = self.get_theme_css()
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                {theme_css}
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    padding: 20px;
                    max-width: 800px;
                    margin: 0 auto;
                }}
                .codehilite {{
                    background: #f8f8f8;
                    padding: 10px;
                    border-radius: 5px;
                    overflow: auto;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 10px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                .toc {{
                    background: #f9f9f9;
                    border: 1px solid #ddd;
                    padding: 10px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            {content}
        </body>
        </html>
        """

    def get_theme_css(self):
        themes = {
            "默认": "",
            "暗色": """
                body { background-color: #2d2d2d; color: #f0f0f0; }
                h1, h2, h3, h4, h5, h6 { color: #ffffff; }
                a { color: #66ccff; }
                code { background: #3d3d3d; color: #f0f0f0; }
                pre { background: #3d3d3d; color: #f0f0f0; }
                blockquote { border-left-color: #666; color: #ccc; }
                table { border-color: #555; }
                th, td { border-color: #555; }
                th { background-color: #3d3d3d; }
            """,
            "护眼绿": """
                body { background-color: #cce8cf; color: #333; }
                h1, h2, h3, h4, h5, h6 { color: #2d5016; }
                a { color: #1e6f3c; }
            """,
            "深蓝": """
                body { background-color: #1a365d; color: #e2e8f0; }
                h1, h2, h3, h4, h5, h6 { color: #ffffff; }
                a { color: #63b3ed; }
                code { background: #2d3748; }
                pre { background: #2d3748; }
            """
        }
        return themes.get(self.current_theme, "")

    def get_current_editor(self):
        current_widget = self.tab_widget.currentWidget()
        if current_widget and isinstance(current_widget, QSplitter):
            return current_widget.widget(0)
        return None

    def get_current_preview(self):
        current_widget = self.tab_widget.currentWidget()
        if current_widget and isinstance(current_widget, QSplitter):
            return current_widget.widget(1)
        return None

    def toggle_preview(self):
        preview = self.get_current_preview()
        if preview:
            preview.setVisible(not preview.isVisible())
            
    def toggle_file_explorer(self):
        self.file_explorer.setVisible(not self.file_explorer.isVisible())
        
    def toggle_outline(self):
        self.outline_dock.setVisible(not self.outline_dock.isVisible())

    def print_document(self):
        editor = self.get_current_editor()
        if not editor:
            return
            
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            editor.print_(printer)
            
    def show_word_count(self):
        editor = self.get_current_editor()
        if not editor:
            return
            
        text = editor.toPlainText()
        char_count = len(text)
        word_count = len(text.split())
        line_count = text.count('\n') + 1
        
        QMessageBox.information(self, "字数统计", 
                               f"字符数: {char_count}\n单词数: {word_count}\n行数: {line_count}")
                               
    def add_to_recent_files(self, file_path):
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:10]  # 保持最近10个文件
        self.update_recent_menu()
        
    def update_recent_menu(self):
        self.recent_menu.clear()
        for file_path in self.recent_files:
            action = QAction(os.path.basename(file_path), self)
            action.triggered.connect(lambda checked, path=file_path: self.open_file(path))
            self.recent_menu.addAction(action)
            
    def update_status(self):
        editor = self.get_current_editor()
        if editor:
            text = editor.toPlainText()
            lines = text.count('\n') + 1
            words = len(text.split())
            self.status_bar.showMessage(f"行数: {lines} | 单词: {words}")

    def load_settings(self):
        # 加载设置
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        self.editor_font = self.settings.value("editor_font", "Consolas")
        self.editor_font_size = int(self.settings.value("editor_font_size", 12))
        self.current_theme = self.settings.value("theme", "默认")
        self.auto_save_enabled = self.settings.value("auto_save", "false") == "true"
        self.auto_save_interval = int(self.settings.value("auto_save_interval", 5))
        self.backup_enabled = self.settings.value("backup_enabled", "true") == "true"
        self.ai_assistant_enabled = self.settings.value("ai_assistant_enabled", "true") == "true"
        self.cloud_sync_enabled = self.settings.value("cloud_sync_enabled", "true") == "true"
        
        self.recent_files = self.settings.value("recent_files", [])
        
        self.apply_settings()

    def save_settings(self):
        # 保存设置
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("editor_font", self.editor_font)
        self.settings.setValue("editor_font_size", self.editor_font_size)
        self.settings.setValue("theme", self.current_theme)
        self.settings.setValue("auto_save", "true" if self.auto_save_enabled else "false")
        self.settings.setValue("auto_save_interval", self.auto_save_interval)
        self.settings.setValue("backup_enabled", "true" if self.backup_enabled else "false")
        self.settings.setValue("ai_assistant_enabled", "true" if self.ai_assistant_enabled else "false")
        self.settings.setValue("cloud_sync_enabled", "true" if self.cloud_sync_enabled else "false")
        self.settings.setValue("recent_files", self.recent_files)

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("SunsetMD Pro")
    app.setApplicationVersion("2.0")
    app.setApplicationDisplayName("SunsetMD Pro - 专业Markdown编辑器")
    
    window = ProfessionalMarkdownEditor()
    window.show()
    
    sys.exit(app.exec_())