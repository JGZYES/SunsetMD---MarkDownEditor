import sys
import os
import markdown
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QSplitter, QAction, QFileDialog, QMessageBox,
                             QToolBar, QStatusBar, QWidget)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont, QKeySequence, QTextCursor
from PyQt5.QtWebEngineWidgets import QWebEngineView

class MarkdownEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.settings = QSettings("SunsetMD", "SunsetMD")
        self.initUI()
        self.load_settings()
        
    def initUI(self):
        self.setWindowTitle("SunsetMD - Markdown编辑器")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # 创建分割器（左右布局）
        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)
        
        # 左侧编辑器
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Arial", 12))
        self.editor.textChanged.connect(self.update_preview)
        self.splitter.addWidget(self.editor)
        
        # 右侧预览
        self.preview = QWebEngineView()
        self.preview.setHtml(self.get_preview_html(""))
        self.splitter.addWidget(self.preview)
        
        # 设置分割比例
        self.splitter.setSizes([600, 600])
        
        # 创建菜单
        self.create_menus()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 应用样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTextEdit {
                border: none;
                background-color: white;
                font-family: "Arial", sans-serif;
                font-size: 14px;
                padding: 10px;
            }
            QToolBar {
                background-color: #f0f0f0;
                border: none;
                spacing: 3px;
                padding: 5px;
            }
            QToolBar QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 5px;
            }
            QToolBar QToolButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
            }
        """)
        
    def create_menus(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        new_action = QAction("新建", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("保存", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("另存为", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("导出HTML", self)
        export_action.triggered.connect(self.export_html)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        undo_action = QAction("撤销", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("重做", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("剪切", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("复制", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("粘贴", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        toggle_action = QAction("切换预览", self)
        toggle_action.setShortcut("F9")
        toggle_action.triggered.connect(self.toggle_preview)
        view_menu.addAction(toggle_action)
        
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
        
        heading_action = QAction("标题", self)
        heading_action.setShortcut("Ctrl+H")
        heading_action.triggered.connect(lambda: self.insert_heading(1))
        format_menu.addAction(heading_action)
        
    def create_toolbar(self):
        toolbar = QToolBar("工具栏")
        self.addToolBar(toolbar)
        
        new_btn = QAction("新建", self)
        new_btn.triggered.connect(self.new_file)
        toolbar.addAction(new_btn)
        
        open_btn = QAction("打开", self)
        open_btn.triggered.connect(self.open_file)
        toolbar.addAction(open_btn)
        
        save_btn = QAction("保存", self)
        save_btn.triggered.connect(self.save_file)
        toolbar.addAction(save_btn)
        
        toolbar.addSeparator()
        
        bold_btn = QAction("粗体", self)
        bold_btn.triggered.connect(self.insert_bold)
        toolbar.addAction(bold_btn)
        
        italic_btn = QAction("斜体", self)
        italic_btn.triggered.connect(self.insert_italic)
        toolbar.addAction(italic_btn)
        
    def new_file(self):
        if self.check_save():
            self.editor.clear()
            self.current_file = None
            self.setWindowTitle("SunsetMD - 新文档")
            self.status_bar.showMessage("新建文档")
            
    def open_file(self):
        if self.check_save():
            path, _ = QFileDialog.getOpenFileName(
                self, "打开文件", "", "Markdown文件 (*.md);;所有文件 (*)"
            )
            if path:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        self.editor.setPlainText(f.read())
                    self.current_file = path
                    self.setWindowTitle(f"SunsetMD - {os.path.basename(path)}")
                    self.status_bar.showMessage(f"已打开: {path}")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"打开文件失败: {str(e)}")
                    
    def save_file(self):
        if self.current_file:
            try:
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(self.editor.toPlainText())
                self.status_bar.showMessage(f"已保存: {self.current_file}")
                return True
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")
                return False
        else:
            return self.save_as_file()
            
    def save_as_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", "Markdown文件 (*.md);;所有文件 (*)"
        )
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.editor.toPlainText())
                self.current_file = path
                self.setWindowTitle(f"SunsetMD - {os.path.basename(path)}")
                self.status_bar.showMessage(f"已保存: {path}")
                return True
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")
                return False
        return False
        
    def check_save(self):
        if self.editor.document().isModified():
            reply = QMessageBox.question(
                self, "保存文档", 
                "文档已修改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                return self.save_file()
            elif reply == QMessageBox.Cancel:
                return False
        return True
        
    def update_preview(self):
        text = self.editor.toPlainText()
        html = markdown.markdown(text)
        self.preview.setHtml(self.get_preview_html(html))
        
    def get_preview_html(self, content):
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    padding: 20px;
                    max-width: 800px;
                    margin: 0 auto;
                }}
                h1, h2, h3 {{
                    color: #333;
                }}
                code {{
                    background: #f4f4f4;
                    padding: 2px 4px;
                    border-radius: 3px;
                }}
                pre {{
                    background: #f4f4f4;
                    padding: 10px;
                    border-radius: 5px;
                    overflow: auto;
                }}
                blockquote {{
                    border-left: 4px solid #ddd;
                    padding-left: 15px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            {content}
        </body>
        </html>
        """
        
    def toggle_preview(self):
        if self.preview.isVisible():
            self.preview.hide()
        else:
            self.preview.show()
            
    def insert_bold(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"**{text}**")
        else:
            cursor.insertText("****")
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 2)
            self.editor.setTextCursor(cursor)
            
    def insert_italic(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"*{text}*")
        else:
            cursor.insertText("**")
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 1)
            self.editor.setTextCursor(cursor)
            
    def insert_heading(self, level):
        cursor = self.editor.textCursor()
        cursor.insertText("#" * level + " ")
        
    def export_html(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出HTML", "", "HTML文件 (*.html)")
        if path:
            try:
                text = self.editor.toPlainText()
                html = markdown.markdown(text)
                full_html = self.get_preview_html(html)
                
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(full_html)
                self.status_bar.showMessage(f"已导出: {path}")
                QMessageBox.information(self, "成功", f"HTML已导出到: {path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
                
    def load_settings(self):
        # 加载设置
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        splitter_state = self.settings.value("splitter")
        if splitter_state:
            self.splitter.restoreState(splitter_state)
            
    def save_settings(self):
        # 保存设置
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitter", self.splitter.saveState())
        
    def closeEvent(self, event):
        if self.check_save():
            self.save_settings()
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    # 设置UTF-8编码
    if hasattr(sys, 'setdefaultencoding'):
        sys.setdefaultencoding('utf-8')
    
    app = QApplication(sys.argv)
    app.setApplicationName("SunsetMD")
    
    # 创建编辑器实例
    window = MarkdownEditor()
    window.show()
    
    sys.exit(app.exec_())