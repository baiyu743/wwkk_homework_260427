from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox,
                             QFileDialog, QInputDialog, QAbstractItemView)
from PyQt5.QtGui import QPdfWriter, QPainter, QFont, QPageSize, QPageLayout
from PyQt5.QtCore import Qt, QDateTime, QRect, QMarginsF, QItemSelectionModel
import pyodbc

def connect_to_db():
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=localhost;'
            'DATABASE=student_project;'
            'Trusted_Connection=yes;'
        )
        return conn
    except Exception as e:
        QMessageBox.warning(None, "数据库连接失败", f"错误信息：{str(e)}")
        return None

def ensure_graduation_review_tables():
    conn = connect_to_db()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            IF OBJECT_ID(N'dbo.PGraduationReviews', N'U') IS NULL
            BEGIN
                CREATE TABLE dbo.PGraduationReviews(
                    StudentID varchar(10) NOT NULL PRIMARY KEY,
                    InitiatedAt datetime2 NULL,
                    InitiatedBy nvarchar(50) NULL,
                    ClassCheckStatus nvarchar(20) NULL,
                    ClassCheckedAt datetime2 NULL,
                    FinalReviewStatus nvarchar(20) NULL,
                    FinalReviewedAt datetime2 NULL,
                    GraduationStatus nvarchar(20) NULL,
                    FailureReason nvarchar(max) NULL,
                    ArchiveGeneratedAt datetime2 NULL
                );
            END
        """)
        conn.commit()
        return True
    except Exception as e:
        QMessageBox.warning(None, "数据库初始化失败", f"错误信息：{str(e)}")
        return False
    finally:
        conn.close()

def export_table_to_csv(table_widget, file_path):
    headers = []
    for c in range(table_widget.columnCount()):
        header_item = table_widget.horizontalHeaderItem(c)
        headers.append(header_item.text() if header_item else "")

    with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(",".join([h.replace('\"', '\"\"') for h in headers]) + "\n")
        for r in range(table_widget.rowCount()):
            row_values = []
            for c in range(table_widget.columnCount()):
                item = table_widget.item(r, c)
                value = item.text() if item else ""
                value = value.replace('\"', '\"\"')
                if "," in value or "\n" in value or "\r" in value:
                    value = f"\"{value}\""
                row_values.append(value)
            f.write(",".join(row_values) + "\n")

def export_table_to_pdf(table_widget, file_path, title):
    writer = QPdfWriter(file_path)
    writer.setResolution(120)
    writer.setPageSize(QPageSize(QPageSize.A4))
    try:
        writer.setPageMargins(QMarginsF(15, 15, 15, 15), QPageLayout.Millimeter)
    except Exception:
        pass
    painter = QPainter(writer)
    painter.setPen(Qt.black)

    paint_rect = writer.pageLayout().paintRectPixels(writer.resolution())
    left = paint_rect.left()
    top = paint_rect.top()
    available_width = paint_rect.width()
    available_height = paint_rect.height()
    bottom_limit = top + available_height

    x = left
    y = top

    painter.setFont(QFont("Arial", 14))
    title_height = painter.fontMetrics().height() + 12
    painter.drawText(QRect(x, y, available_width, title_height), Qt.AlignLeft | Qt.AlignVCenter, title)
    y += title_height + 8

    painter.setFont(QFont("Arial", 10))
    base_font_metrics = painter.fontMetrics()
    cell_padding_v = 6
    cell_padding_h = 6
    min_col_width = 60

    headers = []
    for c in range(table_widget.columnCount()):
        header_item = table_widget.horizontalHeaderItem(c)
        headers.append(header_item.text() if header_item else "")

    col_count = max(1, table_widget.columnCount())
    screen_widths = []
    total_screen_width = 0
    for c in range(col_count):
        w = table_widget.columnWidth(c)
        w = w if w and w > 0 else 1
        screen_widths.append(w)
        total_screen_width += w

    col_widths = []
    for c in range(col_count):
        w = int(available_width * screen_widths[c] / total_screen_width) if total_screen_width else int(available_width / col_count)
        col_widths.append(max(min_col_width, w))

    sum_col_widths = sum(col_widths)
    if sum_col_widths > available_width and sum_col_widths > 0:
        scale = available_width / sum_col_widths
        col_widths = [max(40, int(w * scale)) for w in col_widths]

    if sum(col_widths) < available_width and col_widths:
        col_widths[-1] += available_width - sum(col_widths)

    def draw_header_row(current_y):
        header_font = QFont("Arial", 10)
        header_font.setBold(True)
        painter.setFont(header_font)
        header_height = painter.fontMetrics().height() + cell_padding_v * 2
        cx = x
        for i in range(col_count):
            rect = QRect(cx, current_y, col_widths[i], header_height)
            painter.drawRect(rect)
            painter.drawText(
                QRect(rect.left() + cell_padding_h, rect.top() + cell_padding_v, rect.width() - cell_padding_h * 2, rect.height() - cell_padding_v * 2),
                Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap,
                headers[i] if i < len(headers) else ""
            )
            cx += col_widths[i]
        painter.setFont(QFont("Arial", 10))
        return header_height

    def new_page_and_header():
        writer.newPage()
        painter.setFont(QFont("Arial", 10))
        return top, draw_header_row(top)

    header_height = draw_header_row(y)
    y += header_height

    text_flags = Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap
    for r in range(table_widget.rowCount()):
        row_texts = []
        for c in range(col_count):
            item = table_widget.item(r, c)
            row_texts.append(item.text() if item else "")

        row_height = 0
        for c in range(col_count):
            content_rect = QRect(0, 0, max(1, col_widths[c] - cell_padding_h * 2), 10000)
            h = base_font_metrics.boundingRect(content_rect, text_flags, row_texts[c]).height() + cell_padding_v * 2
            row_height = max(row_height, h)
        row_height = max(row_height, base_font_metrics.height() + cell_padding_v * 2)

        if y + row_height > bottom_limit:
            y, header_height = new_page_and_header()
            y += header_height

        cx = x
        for c in range(col_count):
            rect = QRect(cx, y, col_widths[c], row_height)
            painter.drawRect(rect)
            painter.drawText(
                QRect(rect.left() + cell_padding_h, rect.top() + cell_padding_v, rect.width() - cell_padding_h * 2, rect.height() - cell_padding_v * 2),
                text_flags,
                row_texts[c]
            )
            cx += col_widths[c]
        y += row_height

    painter.end()

# 1.学生管理模块
class StudentInfoModule(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel('学生信息管理', self)
        title.setStyleSheet("font: 24px Arial; color: #4CAF50; text-align: center;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # 输入区域：15个字段的输入框
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_widget.setStyleSheet("padding: 10px; border: 1px solid #E0E0E0; border-radius: 5px;")

        # 第一行：学号、姓名、性别
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self.student_id_input = QLineEdit(self)
        self.student_id_input.setPlaceholderText("学生ID（如S001）*")
        self.student_id_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row1.addWidget(QLabel("学号：", self))
        row1.addWidget(self.student_id_input)

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("姓名*")
        self.name_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row1.addWidget(QLabel("姓名：", self))
        row1.addWidget(self.name_input)

        self.gender_input = QLineEdit(self)
        self.gender_input.setPlaceholderText("性别（男/女）*")
        self.gender_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row1.addWidget(QLabel("性别：", self))
        row1.addWidget(self.gender_input)
        input_layout.addLayout(row1)

        # 第二行：出生日期、民族、身份证号
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        self.birth_input = QLineEdit(self)
        self.birth_input.setPlaceholderText("出生日期（2000-01-01）")
        self.birth_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row2.addWidget(QLabel("出生日期：", self))
        row2.addWidget(self.birth_input)

        self.ethnicity_input = QLineEdit(self)
        self.ethnicity_input.setPlaceholderText("民族（如汉）")
        self.ethnicity_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row2.addWidget(QLabel("民族：", self))
        row2.addWidget(self.ethnicity_input)

        self.id_number_input = QLineEdit(self)
        self.id_number_input.setPlaceholderText("身份证号")
        self.id_number_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row2.addWidget(QLabel("身份证号：", self))
        row2.addWidget(self.id_number_input)
        input_layout.addLayout(row2)

        # 第三行：联系方式、电子邮件、地址
        row3 = QHBoxLayout()
        row3.setSpacing(10)
        self.phone_input = QLineEdit(self)
        self.phone_input.setPlaceholderText("联系方式")
        self.phone_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row3.addWidget(QLabel("联系方式：", self))
        row3.addWidget(self.phone_input)

        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("电子邮件")
        self.email_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row3.addWidget(QLabel("电子邮件：", self))
        row3.addWidget(self.email_input)

        self.address_input = QLineEdit(self)
        self.address_input.setPlaceholderText("地址")
        self.address_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row3.addWidget(QLabel("地址：", self))
        row3.addWidget(self.address_input)
        input_layout.addLayout(row3)

        # 第四行：入学年份、年级、专业
        row4 = QHBoxLayout()
        row4.setSpacing(10)
        self.enroll_year_input = QLineEdit(self)
        self.enroll_year_input.setPlaceholderText("入学年份（2023）")
        self.enroll_year_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row4.addWidget(QLabel("入学年份：", self))
        row4.addWidget(self.enroll_year_input)

        self.class_input = QLineEdit(self)
        self.class_input.setPlaceholderText("年级/班级")
        self.class_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row4.addWidget(QLabel("年级：", self))
        row4.addWidget(self.class_input)

        self.major_input = QLineEdit(self)
        self.major_input.setPlaceholderText("专业*")
        self.major_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row4.addWidget(QLabel("专业：", self))
        row4.addWidget(self.major_input)
        input_layout.addLayout(row4)

        # 第五行：学制、入学状态、学费状态
        row5 = QHBoxLayout()
        row5.setSpacing(10)
        self.duration_input = QLineEdit(self)
        self.duration_input.setPlaceholderText("学制（4年）")
        self.duration_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row5.addWidget(QLabel("学制：", self))
        row5.addWidget(self.duration_input)

        self.enroll_status_input = QLineEdit(self)
        self.enroll_status_input.setPlaceholderText("入学状态（在读）")
        self.enroll_status_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row5.addWidget(QLabel("入学状态：", self))
        row5.addWidget(self.enroll_status_input)

        self.tuition_status_input = QLineEdit(self)
        self.tuition_status_input.setPlaceholderText("学费状态（已缴）")
        self.tuition_status_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row5.addWidget(QLabel("学费状态：", self))
        row5.addWidget(self.tuition_status_input)
        input_layout.addLayout(row5)

        main_layout.addWidget(input_widget)


        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.add_btn = QPushButton('增加学生', self)
        self.add_btn.setStyleSheet(
            'background-color: #4CAF50; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.add_btn.clicked.connect(self.add_student)
        btn_layout.addWidget(self.add_btn)

        self.delete_btn = QPushButton('删除学生', self)
        self.delete_btn.setStyleSheet(
            'background-color: #F44336; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.delete_btn.clicked.connect(self.delete_student)
        btn_layout.addWidget(self.delete_btn)

        self.edit_btn = QPushButton('编辑学生信息', self)
        self.edit_btn.setStyleSheet(
            'background-color: #FF9800; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.edit_btn.clicked.connect(self.edit_student)
        btn_layout.addWidget(self.edit_btn)

        self.query_btn = QPushButton('查询学生信息', self)
        self.query_btn.setStyleSheet(
            'background-color: #2196F3; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.query_btn.clicked.connect(self.query_student)
        btn_layout.addWidget(self.query_btn)

        # 查询所有学生按钮
        self.query_all_btn = QPushButton('查询所有学生', self)
        self.query_all_btn.setStyleSheet(
            'background-color: #673AB7; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.query_all_btn.clicked.connect(self.query_all_students)
        btn_layout.addWidget(self.query_all_btn)

        self.clear_btn = QPushButton('清空输入', self)
        self.clear_btn.setStyleSheet(
            'background-color: #9E9E9E; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.clear_btn.clicked.connect(self.clear_inputs)
        btn_layout.addWidget(self.clear_btn)
        main_layout.addLayout(btn_layout)

        # 表格区域：展示15个字段
        self.student_table = QTableWidget(self)
        # 表格列名（对应15个字段）
        headers = ['学号', '姓名', '性别', '出生日期', '民族', '身份证号',
                   '联系方式', '电子邮件', '地址', '入学年份', '年级', '专业',
                   '学制', '入学状态', '学费状态']
        self.student_table.setColumnCount(len(headers))
        self.student_table.setHorizontalHeaderLabels(headers)
        self.student_table.setStyleSheet("font: 20px Arial;")
        self.student_table.horizontalHeader().setStyleSheet("font: 16px Arial; color: #4CAF50; font-weight: bold;")
        self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.student_table.setColumnWidth(5, 180)  # 身份证号列
        self.student_table.setColumnWidth(8, 200)  # 地址列
        self.student_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 绑定表格行选中事件
        self.student_table.clicked.connect(self.on_table_row_clicked)

        main_layout.addWidget(self.student_table)
        self.setLayout(main_layout)
        # 初始化加载所有学生
        self.query_all_students()

    def show_message(self, title, message):
        QMessageBox.information(self, title, message)

    def on_table_row_clicked(self, index):
        """表格行被选中时，自动将该行数据填充到输入框"""
        selected_row = index.row()  # 获取选中行的索引
        if selected_row == -1:
            return

        # 从表格中获取选中行的15个字段数据
        student_id = self.student_table.item(selected_row, 0).text()
        name = self.student_table.item(selected_row, 1).text()
        gender = self.student_table.item(selected_row, 2).text()
        birth = self.student_table.item(selected_row, 3).text()
        ethnicity = self.student_table.item(selected_row, 4).text()
        id_number = self.student_table.item(selected_row, 5).text()
        phone = self.student_table.item(selected_row, 6).text()
        email = self.student_table.item(selected_row, 7).text()
        address = self.student_table.item(selected_row, 8).text()
        enroll_year = self.student_table.item(selected_row, 9).text()
        class_val = self.student_table.item(selected_row, 10).text()
        major = self.student_table.item(selected_row, 11).text()
        duration = self.student_table.item(selected_row, 12).text()
        enroll_status = self.student_table.item(selected_row, 13).text()
        tuition_status = self.student_table.item(selected_row, 14).text()

        # 将数据填充到输入框（注意：学号设为只读，避免修改）
        self.student_id_input.setText(student_id)
        self.student_id_input.setReadOnly(True)  # 学号不可编辑
        self.name_input.setText(name)
        self.gender_input.setText(gender)
        self.birth_input.setText(birth)
        self.ethnicity_input.setText(ethnicity)
        self.id_number_input.setText(id_number)
        self.phone_input.setText(phone)
        self.email_input.setText(email)
        self.address_input.setText(address)
        self.enroll_year_input.setText(enroll_year)
        self.class_input.setText(class_val)
        self.major_input.setText(major)
        self.duration_input.setText(duration)
        self.enroll_status_input.setText(enroll_status)
        self.tuition_status_input.setText(tuition_status)

    # 增加学生
    def add_student(self):
        # 获取所有输入框的值
        student_id = self.student_id_input.text().strip()
        name = self.name_input.text().strip()
        gender = self.gender_input.text().strip()
        birth = self.birth_input.text().strip() or "未填写"
        ethnicity = self.ethnicity_input.text().strip() or "未填写"
        id_number = self.id_number_input.text().strip() or "未填写"
        phone = self.phone_input.text().strip() or "未填写"
        email = self.email_input.text().strip() or "未填写"
        address = self.address_input.text().strip() or "未填写"
        enroll_year = self.enroll_year_input.text().strip() or "未填写"
        class_val = self.class_input.text().strip() or "未填写"
        major = self.major_input.text().strip()
        duration = self.duration_input.text().strip() or "未填写"
        enroll_status = self.enroll_status_input.text().strip() or "未填写"
        tuition_status = self.tuition_status_input.text().strip() or "未填写"

        # 必填字段校验（学号、姓名、性别、专业）
        if not student_id or not name or not gender or not major:
            QMessageBox.warning(self, "错误", "学号、姓名、性别、专业为必填字段！")
            return

        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            # 检查学号是否已存在
            cursor.execute("SELECT * FROM PStudents WHERE StudentID=?", (student_id,))
            if cursor.fetchone():
                QMessageBox.warning(self, "错误", "该学生ID已存在！")
                return
            # 插入15个字段到数据库
            cursor.execute("""
                INSERT INTO PStudents (
                    StudentID, Name, Gender, DateOfBirth, Ethnicity, IDNumber,
                    PhoneNumber, Email, Address, EnrollmentYear, Class, Major,
                    StudyDuration, EnrollmentStatus, TuitionStatus
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (student_id, name, gender, birth, ethnicity, id_number,
                  phone, email, address, enroll_year, class_val, major,
                  duration, enroll_status, tuition_status))
            conn.commit()
            QMessageBox.information(self, "成功", "学生信息添加成功！")
            self.clear_inputs()
            self.query_student()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加失败：{str(e)}")
        finally:
            conn.close()

    # 删除学生
    def delete_student(self):
        selected_row = self.student_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "提示", "请先选中要删除的学生！")
            return
        student_id = self.student_table.item(selected_row, 0).text()

        if QMessageBox.question(self, "确认", f"确定删除学生【{student_id}】的所有信息吗？",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            # 先删除关联的成绩、奖惩记录（可选，避免外键约束报错）
            cursor.execute("DELETE FROM PGrades WHERE StudentID=?", (student_id,))
            cursor.execute("DELETE FROM PAwardsAndDisciplinaryActions WHERE StudentID=?", (student_id,))
            # 删除学生主表信息
            cursor.execute("DELETE FROM PStudents WHERE StudentID=?", (student_id,))
            conn.commit()
            QMessageBox.information(self, "成功", "学生信息删除成功！")
            self.query_student()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败：{str(e)}")
        finally:
            conn.close()

    # 编辑学生信息
    def edit_student(self):
        selected_row = self.student_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "提示", "请先选中要编辑的学生！")
            return
        student_id = self.student_table.item(selected_row, 0).text()  # 学号不可修改

        # 获取输入框的新值
        name = self.name_input.text().strip()
        gender = self.gender_input.text().strip()
        birth = self.birth_input.text().strip() or "未填写"
        ethnicity = self.ethnicity_input.text().strip() or "未填写"
        id_number = self.id_number_input.text().strip() or "未填写"
        phone = self.phone_input.text().strip() or "未填写"
        email = self.email_input.text().strip() or "未填写"
        address = self.address_input.text().strip() or "未填写"
        enroll_year = self.enroll_year_input.text().strip() or "未填写"
        class_val = self.class_input.text().strip() or "未填写"
        major = self.major_input.text().strip()
        duration = self.duration_input.text().strip() or "未填写"
        enroll_status = self.enroll_status_input.text().strip() or "未填写"
        tuition_status = self.tuition_status_input.text().strip() or "未填写"

        # 必填字段校验
        if not name or not gender or not major:
            QMessageBox.warning(self, "错误", "姓名、性别、专业为必填字段！")
            return

        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            # 更新14个字段（学号不变）
            cursor.execute("""
                UPDATE PStudents 
                SET Name=?, Gender=?, DateOfBirth=?, Ethnicity=?, IDNumber=?,
                    PhoneNumber=?, Email=?, Address=?, EnrollmentYear=?, Class=?, Major=?,
                    StudyDuration=?, EnrollmentStatus=?, TuitionStatus=?
                WHERE StudentID=?
            """, (name, gender, birth, ethnicity, id_number,
                  phone, email, address, enroll_year, class_val, major,
                  duration, enroll_status, tuition_status, student_id))
            conn.commit()
            QMessageBox.information(self, "成功", "学生信息编辑成功！")
            self.clear_inputs()
            self.query_student()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"编辑失败：{str(e)}")
        finally:
            conn.close()

    # 条件查询学生
    def query_student(self):
        """查询学生信息（适配完整PStudents表：支持学号/姓名/性别多条件查询，展示所有字段）"""
        # 1. 获取所有查询条件（去空格）
        student_id = self.student_id_input.text().strip()
        student_name = self.name_input.text().strip()  # 姓名模糊查询
        student_gender = self.gender_input.text().strip()  # 性别精准查询

        # 2. 基础校验：至少输入一个查询条件
        if not student_id and not student_name and not student_gender:
            self.show_message("错误", "请至少输入学号、姓名、性别中的一个查询条件！")
            return

        # 3. 连接数据库
        conn = connect_to_db()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            # 4. 动态拼接SQL查询语句和参数（适配PStudents完整字段）
            sql = "SELECT * FROM PStudents WHERE 1=1"
            params = []

            # 学号：精准匹配
            if student_id:
                sql += " AND StudentID=?"
                params.append(student_id)

            # 姓名：模糊匹配（支持中文，NVARCHAR字段不影响）
            if student_name:
                sql += " AND Name LIKE ?"
                params.append(f"%{student_name}%")

            # 性别：精准匹配（表中Gender是CHAR(1)，比如'男'/'女'或'M'/'F'）
            if student_gender:
                sql += " AND Gender=?"
                params.append(student_gender)

            # 5. 执行查询（获取所有符合条件的结果）
            cursor.execute(sql, tuple(params))
            student_data_list = cursor.fetchall()

            # 6. 处理查询结果：清空表格 → 填充所有字段
            self.student_table.setRowCount(0)  # 清空原有数据
            if student_data_list:
                # 遍历每条结果，逐行填充表格
                for row_idx, student_data in enumerate(student_data_list):
                    self.student_table.insertRow(row_idx)
                    # 按PStudents表字段顺序填充（共15个字段）
                    self.student_table.setItem(row_idx, 0, QTableWidgetItem(str(student_data[0])))  # StudentID
                    self.student_table.setItem(row_idx, 1, QTableWidgetItem(str(student_data[1])))  # Name
                    self.student_table.setItem(row_idx, 2, QTableWidgetItem(str(student_data[2])))  # Gender
                    self.student_table.setItem(row_idx, 3, QTableWidgetItem(str(student_data[3])))  # DateOfBirth
                    self.student_table.setItem(row_idx, 4, QTableWidgetItem(str(student_data[4])))  # Ethnicity
                    self.student_table.setItem(row_idx, 5, QTableWidgetItem(str(student_data[5])))  # IDNumber
                    self.student_table.setItem(row_idx, 6, QTableWidgetItem(str(student_data[6])))  # PhoneNumber
                    self.student_table.setItem(row_idx, 7, QTableWidgetItem(str(student_data[7])))  # Email
                    self.student_table.setItem(row_idx, 8, QTableWidgetItem(str(student_data[8])))  # Address
                    self.student_table.setItem(row_idx, 9, QTableWidgetItem(str(student_data[9])))  # EnrollmentYear
                    self.student_table.setItem(row_idx, 10, QTableWidgetItem(str(student_data[10])))  # Class
                    self.student_table.setItem(row_idx, 11, QTableWidgetItem(str(student_data[11])))  # Major
                    self.student_table.setItem(row_idx, 12, QTableWidgetItem(str(student_data[12])))  # StudyDuration
                    self.student_table.setItem(row_idx, 13, QTableWidgetItem(str(student_data[13])))  # EnrollmentStatus
                    self.student_table.setItem(row_idx, 14, QTableWidgetItem(str(student_data[14])))  # TuitionStatus

                # 若只有一条结果，填充到对应输入框
                if len(student_data_list) == 1:
                    self.student_id_input.setText(str(student_data_list[0][0]))  # 学号
                    self.name_input.setText(str(student_data_list[0][1]))  # 姓名
                    self.gender_input.setText(str(student_data_list[0][2]))  # 性别

            else:
                self.show_message("提示", "未查询到符合条件的学生信息！")
                # 清空输入框
                self.student_id_input.clear()
                self.name_input.clear()
                self.gender_input.clear()

        except Exception as e:
            self.show_message("错误", f"查询学生信息失败：{str(e)}")
        finally:
            # 确保数据库连接关闭
            if conn:
                conn.close()

    # 查询所有学生
    def query_all_students(self):
        """无条件查询所有学生信息"""
        conn = connect_to_db()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM PStudents")
            student_data_list = cursor.fetchall()

            # 清空表格并填充数据
            self.student_table.setRowCount(0)
            if student_data_list:
                for row_idx, student_data in enumerate(student_data_list):
                    self.student_table.insertRow(row_idx)
                    for col_idx in range(15):
                        self.student_table.setItem(row_idx, col_idx, QTableWidgetItem(str(student_data[col_idx])))
        except Exception as e:
            self.show_message("错误", f"查询所有学生失败：{str(e)}")
        finally:
            if conn:
                conn.close()

    # 清空输入框
    def clear_inputs(self):
        self.student_id_input.clear()
        self.student_id_input.setReadOnly(False)  # 清空后恢复学号输入框可编辑
        self.name_input.clear()
        self.gender_input.clear()
        self.birth_input.clear()
        self.ethnicity_input.clear()
        self.id_number_input.clear()
        self.phone_input.clear()
        self.email_input.clear()
        self.address_input.clear()
        self.enroll_year_input.clear()
        self.class_input.clear()
        self.major_input.clear()
        self.duration_input.clear()
        self.enroll_status_input.clear()
        self.tuition_status_input.clear()


# 2.课程管理模块
class CourseInfoModule(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel('课程管理', self)
        title.setStyleSheet("font: 24px Arial; color: #4CAF50; text-align: center;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # 输入区域
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_widget.setStyleSheet("padding: 10px; border: 1px solid #E0E0E0; border-radius: 5px;")

        # 第一行：课程号、课程名称
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self.course_id_input = QLineEdit(self)
        self.course_id_input.setPlaceholderText("课程ID（如C001）*")
        self.course_id_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row1.addWidget(QLabel("课程号：", self))
        row1.addWidget(self.course_id_input)

        self.course_name_input = QLineEdit(self)
        self.course_name_input.setPlaceholderText("课程名称*")
        self.course_name_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row1.addWidget(QLabel("课程名称：", self))
        row1.addWidget(self.course_name_input)
        input_layout.addLayout(row1)

        # 第二行：学分、授课老师
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        self.credit_input = QLineEdit(self)
        self.credit_input.setPlaceholderText("学分（如3）*")
        self.credit_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row2.addWidget(QLabel("学分：", self))
        row2.addWidget(self.credit_input)

        self.teacher_input = QLineEdit(self)
        self.teacher_input.setPlaceholderText("授课老师ID*")  # 注意：这里改为“授课老师ID”，匹配表的InstructorID
        self.teacher_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row2.addWidget(QLabel("授课老师ID：", self))  # 标签也同步修改
        row2.addWidget(self.teacher_input)
        input_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.setSpacing(10)
        self.semester_input = QLineEdit(self)
        self.semester_input.setPlaceholderText("开课学期（如2023-2024上）")
        self.semester_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row3.addWidget(QLabel("开课学期：", self))
        row3.addWidget(self.semester_input)

        self.category_input = QLineEdit(self)
        self.category_input.setPlaceholderText("课程类别（如必修课）")
        self.category_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row3.addWidget(QLabel("课程类别：", self))
        row3.addWidget(self.category_input)
        input_layout.addLayout(row3)

        main_layout.addWidget(input_widget)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        # 增加课程按钮
        self.add_btn = QPushButton('增加课程', self)
        self.add_btn.setStyleSheet(
            'background-color: #4CAF50; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.add_btn.clicked.connect(self.add_course)
        btn_layout.addWidget(self.add_btn)

        # 删除课程按钮
        self.delete_btn = QPushButton('删除课程', self)
        self.delete_btn.setStyleSheet(
            'background-color: #F44336; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.delete_btn.clicked.connect(self.delete_course)
        btn_layout.addWidget(self.delete_btn)

        # 编辑课程按钮
        self.edit_btn = QPushButton('编辑课程', self)
        self.edit_btn.setStyleSheet(
            'background-color: #FF9800; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.edit_btn.clicked.connect(self.edit_course)
        btn_layout.addWidget(self.edit_btn)

        # 查询课程按钮
        self.query_btn = QPushButton('查询课程', self)
        self.query_btn.setStyleSheet(
            'background-color: #2196F3; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.query_btn.clicked.connect(self.query_course)
        btn_layout.addWidget(self.query_btn)

        # 清空输入按钮
        self.clear_btn = QPushButton('清空输入', self)
        self.clear_btn.setStyleSheet(
            'background-color: #9E9E9E; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.clear_btn.clicked.connect(self.clear_inputs)
        btn_layout.addWidget(self.clear_btn)

        main_layout.addLayout(btn_layout)

        # 表格区域
        self.course_table = QTableWidget(self)
        headers = ['课程号', '课程名称', '教师ID', '学分', '开课学期', '课程类别']
        self.course_table.setColumnCount(len(headers))
        self.course_table.setHorizontalHeaderLabels(headers)

        self.course_table.setStyleSheet("font: 20px Arial;")
        self.course_table.horizontalHeader().setStyleSheet("font: 16px Arial; color: #4CAF50; font-weight: bold;")
        self.course_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.course_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 绑定表格行选中事件
        self.course_table.clicked.connect(self.on_table_row_clicked)

        main_layout.addWidget(self.course_table)

        self.setLayout(main_layout)
        self.query_course()

    # 选中行填充输入框
    def on_table_row_clicked(self, index):
        selected_row = index.row()
        if selected_row == -1:
            return
        # 获取表格数据
        course_id = self.course_table.item(selected_row, 0).text()
        course_name = self.course_table.item(selected_row, 1).text()
        credit = self.course_table.item(selected_row, 3).text()
        teacher = self.course_table.item(selected_row, 2).text()
        semester = self.course_table.item(selected_row, 4).text()  # 新增：开课学期
        category = self.course_table.item(selected_row, 5).text()  # 新增：课程类别
        # 填充输入框
        self.course_id_input.setText(course_id)
        self.course_id_input.setReadOnly(True)  # 课程号不可修改
        self.course_name_input.setText(course_name)
        self.credit_input.setText(credit)
        self.teacher_input.setText(teacher)
        self.semester_input.setText(semester)  # 新增：填充开课学期
        self.category_input.setText(category)  # 新增：填充课程类别

    # 添加课程
    def add_course(self):
        course_id = self.course_id_input.text().strip()
        course_name = self.course_name_input.text().strip()
        instructor_id = self.teacher_input.text().strip()  # 注意：输入框名还是teacher_input，实际存的是InstructorID
        credits = self.credit_input.text().strip()
        semester = self.semester_input.text().strip()
        category = self.category_input.text().strip()

        if not course_id:  # 只有CourseID是必填，其他可选
            QMessageBox.warning(self, "错误", "课程ID为必填！")
            return

        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM PCourses WHERE CourseID=?", (course_id,))
            if cursor.fetchone():
                QMessageBox.warning(self, "错误", "该课程号已存在！")
                return
            # 插入语句匹配表的6个字段
            cursor.execute("""
                INSERT INTO PCourses (CourseID, CourseName, InstructorID, Credits, SemesterOffered, CourseCategory)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (course_id, course_name, instructor_id, credits, semester, category))
            conn.commit()
            QMessageBox.information(self, "成功", "课程添加成功！")
            self.clear_inputs()
            self.query_course()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加失败：{str(e)}")
        finally:
            conn.close()

    # 删除课程
    def delete_course(self):
        selected_row = self.course_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "提示", "请先选中要删除的课程！")
            return
        course_id = self.course_table.item(selected_row, 0).text()

        if QMessageBox.question(self, "确认", f"确定删除课程【{course_id}】吗？删除后关联成绩也会被删除！",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            # 先删除关联成绩
            cursor.execute("DELETE FROM PGrades WHERE CourseID=?", (course_id,))
            # 删除课程
            cursor.execute("DELETE FROM PCourses WHERE CourseID=?", (course_id,))
            conn.commit()
            QMessageBox.information(self, "成功", "课程删除成功！")
            self.query_course()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败：{str(e)}")
        finally:
            conn.close()

    # 编辑课程
    def edit_course(self):
        selected_row = self.course_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "提示", "请先选中要编辑的课程！")
            return
        course_id = self.course_table.item(selected_row, 0).text()

        # 获取新值
        course_name = self.course_name_input.text().strip()
        instructor_id = self.teacher_input.text().strip()
        credits = self.credit_input.text().strip()
        semester = self.semester_input.text().strip()
        category = self.category_input.text().strip()

        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            # 更新语句匹配表字段
            cursor.execute("""
                UPDATE PCourses 
                SET CourseName=?, InstructorID=?, Credits=?, SemesterOffered=?, CourseCategory=?
                WHERE CourseID=?
            """, (course_name, instructor_id, credits, semester, category, course_id))
            conn.commit()
            QMessageBox.information(self, "成功", "课程编辑成功！")
            self.clear_inputs()
            self.query_course()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"编辑失败：{str(e)}")
        finally:
            conn.close()

    # 查询课程
    def query_course(self):
        self.course_table.setRowCount(0)
        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            course_id = self.course_id_input.text().strip()
            course_name = self.course_name_input.text().strip()

            # 查询语句包含表的所有字段
            sql = """
                SELECT CourseID, CourseName, InstructorID, Credits, SemesterOffered, CourseCategory
                FROM PCourses WHERE 1=1
            """
            params = []
            if course_id:
                sql += " AND CourseID LIKE ?"
                params.append(f"%{course_id}%")
            if course_name:
                sql += " AND CourseName LIKE ?"
                params.append(f"%{course_name}%")

            cursor.execute(sql, params)
            courses = cursor.fetchall()

            # 填充表格
            for row_idx, course in enumerate(courses):
                self.course_table.insertRow(row_idx)
                for col_idx, value in enumerate(course):
                    item_text = str(value) if value else "未填写"
                    item = QTableWidgetItem(item_text)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.course_table.setItem(row_idx, col_idx, item)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"查询失败：{str(e)}")
        finally:
            conn.close()

    # 清空输入
    def clear_inputs(self):
        self.course_id_input.clear()
        self.course_id_input.setReadOnly(False)
        self.course_name_input.clear()
        self.credit_input.clear()
        self.teacher_input.clear()
        self.semester_input.clear()
        self.category_input.clear()

    # 显示所有课程
    def show_all_courses(self):
        self.clear_inputs()
        self.query_course()


# 3.成绩管理模块
class GradeInfoModule(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel('成绩管理', self)
        title.setStyleSheet("font: 24px Arial; color: #4CAF50; text-align: center;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # 输入区域
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_widget.setStyleSheet("padding: 10px; border: 1px solid #E0E0E0; border-radius: 5px;")

        # 第一行：学号、课程号
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self.student_id_input = QLineEdit(self)
        self.student_id_input.setPlaceholderText("学生ID（如S001）*")
        self.student_id_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row1.addWidget(QLabel("学号：", self))
        row1.addWidget(self.student_id_input)

        self.course_id_input = QLineEdit(self)
        self.course_id_input.setPlaceholderText("课程ID（如C001）*")
        self.course_id_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row1.addWidget(QLabel("课程号：", self))
        row1.addWidget(self.course_id_input)
        input_layout.addLayout(row1)

        # 第二行：学期、成绩
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        self.semester_input = QLineEdit(self)
        self.semester_input.setPlaceholderText("学期（如2023-2024上）*")
        self.semester_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row2.addWidget(QLabel("学期：", self))
        row2.addWidget(self.semester_input)

        self.grade_input = QLineEdit(self)
        self.grade_input.setPlaceholderText("成绩（如90）*")
        self.grade_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row2.addWidget(QLabel("成绩：", self))
        row2.addWidget(self.grade_input)
        input_layout.addLayout(row2)

        main_layout.addWidget(input_widget)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.add_btn = QPushButton('添加成绩', self)
        self.add_btn.setStyleSheet(
            'background-color: #4CAF50; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.add_btn.clicked.connect(self.add_grade)
        btn_layout.addWidget(self.add_btn)

        self.delete_btn = QPushButton('删除成绩', self)
        self.delete_btn.setStyleSheet(
            'background-color: #F44336; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.delete_btn.clicked.connect(self.delete_grade)
        btn_layout.addWidget(self.delete_btn)

        self.edit_btn = QPushButton('编辑成绩', self)
        self.edit_btn.setStyleSheet(
            'background-color: #FF9800; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.edit_btn.clicked.connect(self.edit_grade)
        btn_layout.addWidget(self.edit_btn)

        self.query_btn = QPushButton('查询成绩', self)
        self.query_btn.setStyleSheet(
            'background-color: #2196F3; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.query_btn.clicked.connect(self.query_grade)
        btn_layout.addWidget(self.query_btn)

        self.clear_btn = QPushButton('清空输入', self)
        self.clear_btn.setStyleSheet(
            'background-color: #9E9E9E; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.clear_btn.clicked.connect(self.clear_inputs)
        btn_layout.addWidget(self.clear_btn)
        main_layout.addLayout(btn_layout)

        # 表格区域
        self.grade_table = QTableWidget(self)
        headers = ['学号', '课程号', '课程名称', '学期', '成绩']
        self.grade_table.setColumnCount(len(headers))
        self.grade_table.setHorizontalHeaderLabels(headers)
        self.grade_table.setStyleSheet("font: 20px Arial;")
        self.grade_table.horizontalHeader().setStyleSheet("font: 16px Arial; color: #4CAF50; font-weight: bold;")
        self.grade_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.grade_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 绑定表格行选中事件
        self.grade_table.clicked.connect(self.on_table_row_clicked)

        main_layout.addWidget(self.grade_table)
        self.setLayout(main_layout)
        self.query_grade()

    # 选中行填充输入框
    def on_table_row_clicked(self, index):
        selected_row = index.row()
        if selected_row == -1:
            return
        # 获取表格数据
        student_id = self.grade_table.item(selected_row, 0).text()
        course_id = self.grade_table.item(selected_row, 1).text()
        semester = self.grade_table.item(selected_row, 3).text()
        grade = self.grade_table.item(selected_row, 4).text()
        # 填充输入框（课程名称不编辑，仅展示）
        self.student_id_input.setText(student_id)
        self.student_id_input.setReadOnly(True)  # 学号+课程号作为联合主键，不可修改
        self.course_id_input.setText(course_id)
        self.course_id_input.setReadOnly(True)
        self.semester_input.setText(semester)
        self.grade_input.setText(grade)

    # 添加成绩
    def add_grade(self):
        student_id = self.student_id_input.text().strip()
        course_id = self.course_id_input.text().strip()
        semester = self.semester_input.text().strip()
        grade = self.grade_input.text().strip()

        if not student_id or not course_id or not semester or not grade:
            QMessageBox.warning(self, "错误", "所有字段为必填！")
            return

        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            # 检查成绩是否已存在
            cursor.execute("SELECT * FROM PGrades WHERE StudentID=? AND CourseID=? AND Semester=?",
                           (student_id, course_id, semester))
            if cursor.fetchone():
                QMessageBox.warning(self, "错误", "该学生该学期该课程成绩已存在！")
                return
            # 插入成绩
            cursor.execute("""
                INSERT INTO PGrades (StudentID, CourseID, Semester, Grade)
                VALUES (?, ?, ?, ?)
            """, (student_id, course_id, semester, grade))
            conn.commit()
            QMessageBox.information(self, "成功", "成绩添加成功！")
            self.clear_inputs()
            self.query_grade()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加失败：{str(e)}")
        finally:
            conn.close()

    # 删除成绩
    def delete_grade(self):
        selected_row = self.grade_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "提示", "请先选中要删除的成绩！")
            return
        student_id = self.grade_table.item(selected_row, 0).text()
        course_id = self.grade_table.item(selected_row, 1).text()
        semester = self.grade_table.item(selected_row, 3).text()

        if QMessageBox.question(self, "确认", f"确定删除【{student_id}】-{course_id}-{semester}的成绩吗？",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM PGrades WHERE StudentID=? AND CourseID=? AND Semester=?",
                           (student_id, course_id, semester))
            conn.commit()
            QMessageBox.information(self, "成功", "成绩删除成功！")
            self.query_grade()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败：{str(e)}")
        finally:
            conn.close()

    # 编辑成绩
    def edit_grade(self):
        selected_row = self.grade_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "提示", "请先选中要编辑的成绩！")
            return
        student_id = self.grade_table.item(selected_row, 0).text()
        course_id = self.grade_table.item(selected_row, 1).text()
        old_semester = self.grade_table.item(selected_row, 3).text()

        # 获取新值
        new_semester = self.semester_input.text().strip()
        new_grade = self.grade_input.text().strip()

        if not new_semester or not new_grade:
            QMessageBox.warning(self, "错误", "学期和成绩为必填！")
            return

        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            # 更新成绩（学号+课程号不变，仅更新学期和成绩）
            cursor.execute("""
                UPDATE PGrades 
                SET Semester=?, Grade=?
                WHERE StudentID=? AND CourseID=? AND Semester=?
            """, (new_semester, new_grade, student_id, course_id, old_semester))
            conn.commit()
            QMessageBox.information(self, "成功", "成绩编辑成功！")
            self.clear_inputs()
            self.query_grade()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"编辑失败：{str(e)}")
        finally:
            conn.close()

    # 查询成绩（支持按学号/课程号模糊查询）
    def query_grade(self):
        self.grade_table.setRowCount(0)
        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            student_id = self.student_id_input.text().strip()
            course_id = self.course_id_input.text().strip()

            # 拼接查询条件
            sql = """
                SELECT g.StudentID, g.CourseID, c.CourseName, g.Semester, g.Grade
                FROM PGrades g
                LEFT JOIN PCourses c ON g.CourseID = c.CourseID
                WHERE 1=1
            """
            params = []
            if student_id:
                sql += " AND g.StudentID LIKE ?"
                params.append(f"%{student_id}%")
            if course_id:
                sql += " AND g.CourseID LIKE ?"
                params.append(f"%{course_id}%")

            cursor.execute(sql, params)
            grades = cursor.fetchall()

            # 填充表格
            for row_idx, grade in enumerate(grades):
                self.grade_table.insertRow(row_idx)
                for col_idx, value in enumerate(grade):
                    item_text = str(value) if value else "未知"
                    item = QTableWidgetItem(item_text)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.grade_table.setItem(row_idx, col_idx, item)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"查询失败：{str(e)}")
        finally:
            conn.close()

    # 清空输入
    def clear_inputs(self):
        self.student_id_input.clear()
        self.student_id_input.setReadOnly(False)
        self.course_id_input.clear()
        self.course_id_input.setReadOnly(False)
        self.semester_input.clear()
        self.grade_input.clear()

    # 显示所有成绩
    def show_all_grades(self):
        self.clear_inputs()
        self.query_grade()


# 4.奖惩记录管理模块
class AwardsInfoModule(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel('奖惩记录管理', self)
        title.setStyleSheet("font: 24px Arial; color: #4CAF50; text-align: center;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # 输入区域
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_widget.setStyleSheet("padding: 10px; border: 1px solid #E0E0E0; border-radius: 5px;")

        # 第一行：学号、奖惩类型
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self.student_id_input = QLineEdit(self)
        self.student_id_input.setPlaceholderText("学生ID（如S001）*")
        self.student_id_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row1.addWidget(QLabel("学号：", self))
        row1.addWidget(self.student_id_input)

        self.type_input = QLineEdit(self)
        self.type_input.setPlaceholderText("奖惩类型（如一等奖学金/警告）*")
        self.type_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row1.addWidget(QLabel("奖惩类型：", self))
        row1.addWidget(self.type_input)
        input_layout.addLayout(row1)

        # 第二行：描述、日期
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        self.desc_input = QLineEdit(self)
        self.desc_input.setPlaceholderText("详细描述*")
        self.desc_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row2.addWidget(QLabel("详细描述：", self))
        row2.addWidget(self.desc_input)

        self.date_input = QLineEdit(self)
        self.date_input.setPlaceholderText("日期（2023-01-01）*")
        self.date_input.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        row2.addWidget(QLabel("发生日期：", self))
        row2.addWidget(self.date_input)
        input_layout.addLayout(row2)

        main_layout.addWidget(input_widget)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.add_btn = QPushButton('添加奖惩记录', self)
        self.add_btn.setStyleSheet(
            'background-color: #4CAF50; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.add_btn.clicked.connect(self.add_award)
        btn_layout.addWidget(self.add_btn)

        self.delete_btn = QPushButton('删除奖惩记录', self)
        self.delete_btn.setStyleSheet(
            'background-color: #F44336; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.delete_btn.clicked.connect(self.delete_award)
        btn_layout.addWidget(self.delete_btn)

        self.edit_btn = QPushButton('编辑奖惩记录', self)
        self.edit_btn.setStyleSheet(
            'background-color: #FF9800; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.edit_btn.clicked.connect(self.edit_award)
        btn_layout.addWidget(self.edit_btn)

        self.query_btn = QPushButton('查询奖惩记录', self)
        self.query_btn.setStyleSheet(
            'background-color: #2196F3; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.query_btn.clicked.connect(self.query_award)
        btn_layout.addWidget(self.query_btn)

        self.clear_btn = QPushButton('清空输入', self)
        self.clear_btn.setStyleSheet(
            'background-color: #9E9E9E; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.clear_btn.clicked.connect(self.clear_inputs)
        btn_layout.addWidget(self.clear_btn)

        self.show_all_btn = QPushButton('显示所有奖惩记录', self)
        self.show_all_btn.setStyleSheet(
            'background-color: #795548; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.show_all_btn.clicked.connect(self.show_all_awards)
        btn_layout.addWidget(self.show_all_btn)

        main_layout.addLayout(btn_layout)

        # 表格区域
        self.award_table = QTableWidget(self)
        headers = ['学号', '奖惩类型', '详细描述', '发生日期']
        self.award_table.setColumnCount(len(headers))
        self.award_table.setHorizontalHeaderLabels(headers)
        self.award_table.setStyleSheet("font: 20px Arial;")
        self.award_table.horizontalHeader().setStyleSheet("font: 16px Arial; color: #4CAF50; font-weight: bold;")
        self.award_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.award_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 绑定表格行选中事件
        self.award_table.clicked.connect(self.on_table_row_clicked)

        main_layout.addWidget(self.award_table)
        self.setLayout(main_layout)
        self.query_award()

    # 选中行填充输入框
    def on_table_row_clicked(self, index):
        selected_row = index.row()
        if selected_row == -1:
            return
        # 获取表格数据
        student_id = self.award_table.item(selected_row, 0).text()
        type_val = self.award_table.item(selected_row, 1).text()
        desc = self.award_table.item(selected_row, 2).text()
        date = self.award_table.item(selected_row, 3).text()
        # 填充输入框（学号不可修改）
        self.student_id_input.setText(student_id)
        self.student_id_input.setReadOnly(True)
        self.type_input.setText(type_val)
        self.desc_input.setText(desc)
        self.date_input.setText(date)

    # 添加奖惩记录
    def add_award(self):
        student_id = self.student_id_input.text().strip()
        type_val = self.type_input.text().strip()
        desc = self.desc_input.text().strip()
        date = self.date_input.text().strip()

        if not student_id or not type_val or not desc or not date:
            QMessageBox.warning(self, "错误", "所有字段为必填！")
            return

        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            # 检查记录是否已存在
            cursor.execute("SELECT * FROM PAwardsAndDisciplinaryActions WHERE StudentID=? AND Date=? AND Type=?",
                           (student_id, date, type_val))
            if cursor.fetchone():
                QMessageBox.warning(self, "错误", "该学生该日期该奖惩记录已存在！")
                return
            # 插入记录
            cursor.execute("""
                INSERT INTO PAwardsAndDisciplinaryActions (StudentID, Type, Description, Date)
                VALUES (?, ?, ?, ?)
            """, (student_id, type_val, desc, date))
            conn.commit()
            QMessageBox.information(self, "成功", "奖惩记录添加成功！")
            self.clear_inputs()
            self.query_award()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加失败：{str(e)}")
        finally:
            conn.close()

    # 删除奖惩记录
    def delete_award(self):
        selected_row = self.award_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "提示", "请先选中要删除的奖惩记录！")
            return
        student_id = self.award_table.item(selected_row, 0).text()
        type_val = self.award_table.item(selected_row, 1).text()
        date = self.award_table.item(selected_row, 3).text()

        if QMessageBox.question(self, "确认", f"确定删除【{student_id}】-{type_val}-{date}的奖惩记录吗？",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM PAwardsAndDisciplinaryActions WHERE StudentID=? AND Type=? AND Date=?",
                           (student_id, type_val, date))
            conn.commit()
            QMessageBox.information(self, "成功", "奖惩记录删除成功！")
            self.query_award()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败：{str(e)}")
        finally:
            conn.close()

    # 编辑奖惩记录
    def edit_award(self):
        selected_row = self.award_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "提示", "请先选中要编辑的奖惩记录！")
            return
        student_id = self.award_table.item(selected_row, 0).text()
        old_type = self.award_table.item(selected_row, 1).text()
        old_date = self.award_table.item(selected_row, 3).text()

        # 获取新值
        new_type = self.type_input.text().strip()
        new_desc = self.desc_input.text().strip()
        new_date = self.date_input.text().strip()

        if not new_type or not new_desc or not new_date:
            QMessageBox.warning(self, "错误", "奖惩类型、描述、日期为必填！")
            return

        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            # 更新记录
            cursor.execute("""
                UPDATE PAwardsAndDisciplinaryActions 
                SET Type=?, Description=?, Date=?
                WHERE StudentID=? AND Type=? AND Date=?
            """, (new_type, new_desc, new_date, student_id, old_type, old_date))
            conn.commit()
            QMessageBox.information(self, "成功", "奖惩记录编辑成功！")
            self.clear_inputs()
            self.query_award()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"编辑失败：{str(e)}")
        finally:
            conn.close()

    # 查询奖惩记录
    def query_award(self):
        self.award_table.setRowCount(0)
        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            student_id = self.student_id_input.text().strip()
            type_val = self.type_input.text().strip()

            sql = "SELECT StudentID, Type, Description, Date FROM PAwardsAndDisciplinaryActions WHERE 1=1"
            params = []
            if student_id:
                sql += " AND StudentID LIKE ?"
                params.append(f"%{student_id}%")
            if type_val:
                sql += " AND Type LIKE ?"
                params.append(f"%{type_val}%")

            cursor.execute(sql, params)
            awards = cursor.fetchall()

            # 填充表格
            for row_idx, award in enumerate(awards):
                self.award_table.insertRow(row_idx)
                for col_idx, value in enumerate(award):
                    item_text = str(value) if value else "未知"
                    item = QTableWidgetItem(item_text)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.award_table.setItem(row_idx, col_idx, item)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"查询失败：{str(e)}")
        finally:
            conn.close()

    # 清空输入
    def clear_inputs(self):
        self.student_id_input.clear()
        self.student_id_input.setReadOnly(False)
        self.type_input.clear()
        self.desc_input.clear()
        self.date_input.clear()

    # 显示所有奖惩记录
    def show_all_awards(self):
        self.clear_inputs()
        self.query_award()


# 5.修改密码模块
class PasswordManagementModule(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        self.title_label = QLabel("修改密码", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font: 24px Arial; color: #F44336;")
        layout.addWidget(self.title_label)

        # 输入学号或工号
        self.user_id_label = QLabel('请输入学号/工号:', self)
        self.user_id_input = QLineEdit(self)
        self.user_id_input.setPlaceholderText("输入要修改密码的用户ID（如admin1/S001/T001）")
        self.user_id_input.setStyleSheet("font: 16px Arial; padding: 8px;")
        layout.addWidget(self.user_id_label)
        layout.addWidget(self.user_id_input)

        # 输入新密码
        self.new_password_label = QLabel('请输入新密码:', self)
        self.new_password_input = QLineEdit(self)
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setStyleSheet("font: 16px Arial; padding: 8px;")
        layout.addWidget(self.new_password_label)
        layout.addWidget(self.new_password_input)

        # 输入确认密码
        self.confirm_password_label = QLabel('确认新密码:', self)
        self.confirm_password_input = QLineEdit(self)
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setStyleSheet("font: 16px Arial; padding: 8px;")
        layout.addWidget(self.confirm_password_label)
        layout.addWidget(self.confirm_password_input)

        # 提交修改按钮
        self.submit_button = QPushButton("提交修改", self)
        self.submit_button.setStyleSheet(
            'background-color: #F44336; color: white; font: 20px Arial; padding: 15px; border-radius: 5px;')
        self.submit_button.clicked.connect(self.submit_password_modify)
        layout.addWidget(self.submit_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def submit_password_modify(self):
        user_id = self.user_id_input.text().strip()
        new_password = self.new_password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        # 基本校验
        if not user_id or not new_password or not confirm_password:
            self.show_message("错误", "用户ID、新密码、确认密码不能为空！")
            return
        if new_password != confirm_password:
            self.show_message("错误", "新密码与确认密码不一致！")
            return
        if len(new_password) < 6:
            self.show_message("提示", "新密码长度不能少于6位！")
            return

        # 先校验用户是否存在
        if not self.check_user_exists(user_id):
            self.show_message("错误", "该用户ID不存在！")
            return

        # 更新新密码到数据库
        if self.update_password_in_db(user_id, new_password):
            self.show_message("成功", "密码修改成功！")
            # 清空输入框
            self.user_id_input.clear()
            #self.old_password_input.clear()
            self.new_password_input.clear()
            self.confirm_password_input.clear()
        else:
            self.show_message("错误", "密码修改失败，请稍后再试！")

    # 检查用户是否存在
    def check_user_exists(self, user_id):
        conn = connect_to_db()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM PUsers WHERE Username=?", (user_id,))
            return cursor.fetchone() is not None  # 存在返回True，不存在返回False
        except Exception as e:
            self.show_message("错误", f"校验用户失败：{str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    def update_password_in_db(self, user_id, new_password):
        conn = connect_to_db()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE PUsers SET Password=? WHERE Username=?", (new_password, user_id))
            conn.commit()
            return True
        except Exception as e:
            self.show_message("错误", f"更新失败：{str(e)}")
            return False
        finally:
            conn.close()

    def show_message(self, title, message):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        if "错误" in title:
            msg.setIcon(QMessageBox.Critical)
        elif "成功" in title:
            msg.setIcon(QMessageBox.Information)
        elif "提示" in title:
            msg.setIcon(QMessageBox.Warning)
        msg.exec_()


class GraduationQualificationModule(QWidget):
    def __init__(self):
        super().__init__()
        ensure_graduation_review_tables()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel('毕业资格审核', self)
        title.setStyleSheet("font: 24px Arial; color: #4CAF50; text-align: center;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        self.student_id_filter = QLineEdit(self)
        self.student_id_filter.setPlaceholderText("学号（可选）")
        self.student_id_filter.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        filter_layout.addWidget(QLabel("学号：", self))
        filter_layout.addWidget(self.student_id_filter)

        self.class_filter = QLineEdit(self)
        self.class_filter.setPlaceholderText("班级（可选）")
        self.class_filter.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        filter_layout.addWidget(QLabel("班级：", self))
        filter_layout.addWidget(self.class_filter)

        self.major_filter = QLineEdit(self)
        self.major_filter.setPlaceholderText("专业（可选）")
        self.major_filter.setStyleSheet("font: 16px Arial; padding: 8px; min-width: 150px;")
        filter_layout.addWidget(QLabel("专业：", self))
        filter_layout.addWidget(self.major_filter)

        self.refresh_btn = QPushButton('刷新', self)
        self.refresh_btn.setStyleSheet(
            'background-color: #2196F3; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.refresh_btn.clicked.connect(self.load_students)
        filter_layout.addWidget(self.refresh_btn)

        main_layout.addLayout(filter_layout)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.initiate_btn = QPushButton('审核发起', self)
        self.initiate_btn.setStyleSheet(
            'background-color: #4CAF50; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.initiate_btn.clicked.connect(self.initiate_review)
        btn_layout.addWidget(self.initiate_btn)

        self.class_check_btn = QPushButton('班级核对', self)
        self.class_check_btn.setStyleSheet(
            'background-color: #FF9800; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.class_check_btn.clicked.connect(self.class_check)
        btn_layout.addWidget(self.class_check_btn)

        self.final_review_btn = QPushButton('终审审核', self)
        self.final_review_btn.setStyleSheet(
            'background-color: #9C27B0; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.final_review_btn.clicked.connect(self.final_review)
        btn_layout.addWidget(self.final_review_btn)

        self.auto_mark_btn = QPushButton('状态标记', self)
        self.auto_mark_btn.setStyleSheet(
            'background-color: #607D8B; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.auto_mark_btn.clicked.connect(self.auto_mark_status)
        btn_layout.addWidget(self.auto_mark_btn)

        self.archive_btn = QPushButton('档案生成', self)
        self.archive_btn.setStyleSheet(
            'background-color: #795548; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.archive_btn.clicked.connect(self.generate_archives)
        btn_layout.addWidget(self.archive_btn)

        self.exception_btn = QPushButton('异常处理', self)
        self.exception_btn.setStyleSheet(
            'background-color: #F44336; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.exception_btn.clicked.connect(self.handle_exception)
        btn_layout.addWidget(self.exception_btn)

        main_layout.addLayout(btn_layout)

        selection_layout = QHBoxLayout()
        selection_layout.setSpacing(10)

        self.select_all_btn = QPushButton('全选', self)
        self.select_all_btn.setStyleSheet(
            'background-color: #9E9E9E; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.select_all_btn.clicked.connect(self.select_all_rows)
        selection_layout.addWidget(self.select_all_btn)

        self.invert_select_btn = QPushButton('反选', self)
        self.invert_select_btn.setStyleSheet(
            'background-color: #9E9E9E; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.invert_select_btn.clicked.connect(self.invert_selection)
        selection_layout.addWidget(self.invert_select_btn)

        self.clear_select_btn = QPushButton('清空选择', self)
        self.clear_select_btn.setStyleSheet(
            'background-color: #9E9E9E; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.clear_select_btn.clicked.connect(self.clear_selection)
        selection_layout.addWidget(self.clear_select_btn)

        selection_layout.addStretch(1)
        main_layout.addLayout(selection_layout)

        self.table = QTableWidget(self)
        headers = ['学号', '姓名', '班级', '专业', '入学状态', '学费状态', '平均分', '挂科数', '审核状态', '毕业状态', '未通过原因']
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setStyleSheet("font: 18px Arial;")
        self.table.horizontalHeader().setStyleSheet("font: 16px Arial; color: #4CAF50; font-weight: bold;")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)
        self.load_students()

    def select_all_rows(self):
        self.table.clearSelection()
        model = self.table.model()
        selection_model = self.table.selectionModel()
        for r in range(self.table.rowCount()):
            selection_model.select(model.index(r, 0), QItemSelectionModel.Select | QItemSelectionModel.Rows)

    def invert_selection(self):
        selected_rows = {idx.row() for idx in self.table.selectionModel().selectedRows()}
        self.table.clearSelection()
        model = self.table.model()
        selection_model = self.table.selectionModel()
        for r in range(self.table.rowCount()):
            if r not in selected_rows:
                selection_model.select(model.index(r, 0), QItemSelectionModel.Select | QItemSelectionModel.Rows)

    def clear_selection(self):
        self.table.clearSelection()

    def get_selected_student_ids(self):
        rows = {idx.row() for idx in self.table.selectionModel().selectedRows()}
        student_ids = []
        for r in sorted(rows):
            item = self.table.item(r, 0)
            if item:
                student_ids.append(item.text())
        return student_ids

    def compute_graduation_status(self, fail_count, tuition_status, enrollment_status):
        enrollment_status = (enrollment_status or "").strip()
        tuition_status = (tuition_status or "").strip()

        if enrollment_status in {"退学", "开除"}:
            return "肄业"
        if fail_count is None:
            fail_count = 0
        if tuition_status and tuition_status not in {"已缴", "已交", "已缴费", "已交费"}:
            return "未通过"
        if fail_count == 0:
            return "毕业"
        if fail_count <= 2:
            return "结业"
        return "未通过"

    def load_students(self):
        self.table.setRowCount(0)
        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            student_id = self.student_id_filter.text().strip()
            class_val = self.class_filter.text().strip()
            major = self.major_filter.text().strip()

            sql = """
                SELECT
                    s.StudentID,
                    s.Name,
                    s.Class,
                    s.Major,
                    s.EnrollmentStatus,
                    s.TuitionStatus,
                    AVG(CAST(g.Grade AS float)) AS AvgGrade,
                    SUM(CASE WHEN g.Grade < 60 THEN 1 ELSE 0 END) AS FailCount,
                    r.FinalReviewStatus,
                    r.GraduationStatus,
                    r.FailureReason
                FROM PStudents s
                LEFT JOIN PGrades g ON g.StudentID = s.StudentID
                LEFT JOIN dbo.PGraduationReviews r ON r.StudentID = s.StudentID
                WHERE 1=1
            """
            params = []
            if student_id:
                sql += " AND s.StudentID = ?"
                params.append(student_id)
            if class_val:
                sql += " AND s.Class LIKE ?"
                params.append(f"%{class_val}%")
            if major:
                sql += " AND s.Major LIKE ?"
                params.append(f"%{major}%")

            sql += """
                GROUP BY s.StudentID, s.Name, s.Class, s.Major, s.EnrollmentStatus, s.TuitionStatus,
                         r.FinalReviewStatus, r.GraduationStatus, r.FailureReason
                ORDER BY s.StudentID
            """
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            for row_idx, row in enumerate(rows):
                (sid, name, clazz, major_val, enroll_status, tuition_status, avg_grade, fail_count,
                 final_review_status, grad_status, failure_reason) = row

                if grad_status is None:
                    grad_status = self.compute_graduation_status(fail_count, tuition_status, enroll_status)

                review_status = final_review_status if final_review_status else "未发起"

                self.table.insertRow(row_idx)
                values = [
                    sid,
                    name,
                    clazz,
                    major_val,
                    enroll_status,
                    tuition_status,
                    f"{avg_grade:.2f}" if avg_grade is not None else "",
                    str(fail_count) if fail_count is not None else "0",
                    review_status,
                    grad_status,
                    failure_reason if failure_reason else ""
                ]
                for col_idx, value in enumerate(values):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row_idx, col_idx, item)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败：{str(e)}")
        finally:
            conn.close()

    def upsert_review(self, student_id, fields):
        conn = connect_to_db()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM dbo.PGraduationReviews WHERE StudentID=?", (student_id,))
            exists = cursor.fetchone() is not None
            if not exists:
                cursor.execute("INSERT INTO dbo.PGraduationReviews (StudentID) VALUES (?)", (student_id,))
            set_clauses = []
            params = []
            for k, v in fields.items():
                set_clauses.append(f"{k}=?")
                params.append(v)
            params.append(student_id)
            cursor.execute(f"UPDATE dbo.PGraduationReviews SET {', '.join(set_clauses)} WHERE StudentID=?", params)
            conn.commit()
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新失败：{str(e)}")
            return False
        finally:
            conn.close()

    def initiate_review(self):
        student_ids = self.get_selected_student_ids()
        if not student_ids:
            QMessageBox.warning(self, "提示", "请先在表格中选中要发起审核的学生（可多选）。")
            return
        initiator, ok = QInputDialog.getText(self, "审核发起", "请输入发起人：", QLineEdit.Normal, "Admin")
        if not ok:
            return
        initiator = initiator.strip()
        if not initiator:
            initiator = "Admin"
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        for sid in student_ids:
            self.upsert_review(sid, {"InitiatedAt": now, "InitiatedBy": initiator, "FinalReviewStatus": "已发起"})
        QMessageBox.information(self, "成功", "审核已发起。")
        self.load_students()

    def get_student_problems(self, student_id):
        conn = connect_to_db()
        if not conn:
            return ["数据库连接失败"]
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Name, Gender, Major, Class, EnrollmentStatus, TuitionStatus
                FROM PStudents WHERE StudentID=?
            """, (student_id,))
            s = cursor.fetchone()
            if not s:
                return ["学籍信息不存在"]
            name, gender, major, clazz, enroll_status, tuition_status = s
            problems = []
            if not name:
                problems.append("姓名缺失")
            if not gender:
                problems.append("性别缺失")
            if not major:
                problems.append("专业缺失")
            if not clazz:
                problems.append("班级缺失")
            if tuition_status and tuition_status not in {"已缴", "已交", "已缴费", "已交费"}:
                problems.append("学费未缴清")
            if enroll_status in {"退学", "开除"}:
                problems.append("学籍异常")
            cursor.execute("SELECT COUNT(1) FROM PGrades WHERE StudentID=? AND Grade < 60", (student_id,))
            fail_count = cursor.fetchone()[0]
            if fail_count and fail_count > 0:
                problems.append(f"挂科{fail_count}门")
            return problems
        except Exception as e:
            return [f"核对失败：{str(e)}"]
        finally:
            conn.close()

    def class_check(self):
        student_ids = self.get_selected_student_ids()
        if not student_ids:
            QMessageBox.warning(self, "提示", "请先选中要班级核对的学生（可多选）。")
            return
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        for sid in student_ids:
            problems = self.get_student_problems(sid)
            status = "通过" if not problems else "不通过"
            reason = "" if not problems else "；".join(problems)
            self.upsert_review(sid, {"ClassCheckStatus": status, "ClassCheckedAt": now, "FinalReviewStatus": f"班级核对{status}", "FailureReason": reason})
        QMessageBox.information(self, "成功", "班级核对已完成。")
        self.load_students()

    def auto_mark_status(self):
        student_ids = self.get_selected_student_ids()
        if not student_ids:
            QMessageBox.warning(self, "提示", "请先选中要标记状态的学生（可多选）。")
            return
        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            for sid in student_ids:
                cursor.execute("""
                    SELECT s.EnrollmentStatus, s.TuitionStatus,
                           SUM(CASE WHEN g.Grade < 60 THEN 1 ELSE 0 END) AS FailCount
                    FROM PStudents s
                    LEFT JOIN PGrades g ON g.StudentID=s.StudentID
                    WHERE s.StudentID=?
                    GROUP BY s.EnrollmentStatus, s.TuitionStatus
                """, (sid,))
                row = cursor.fetchone()
                if row:
                    enroll_status, tuition_status, fail_count = row
                    status = self.compute_graduation_status(fail_count or 0, tuition_status, enroll_status)
                    problems = self.get_student_problems(sid)
                    reason = "" if status in {"毕业", "结业", "肄业"} and not problems else "；".join(problems)
                    self.upsert_review(sid, {"GraduationStatus": status, "FailureReason": reason})
            QMessageBox.information(self, "成功", "状态标记完成。")
            self.load_students()
        finally:
            conn.close()

    def final_review(self):
        student_ids = self.get_selected_student_ids()
        if not student_ids:
            QMessageBox.warning(self, "提示", "请先选中要终审的学生（可多选）。")
            return
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        for sid in student_ids:
            problems = self.get_student_problems(sid)
            status = "通过" if not problems else "不通过"
            grad_status = "毕业" if status == "通过" else "未通过"
            reason = "" if status == "通过" else ("；".join(problems) if problems else "未通过")
            self.upsert_review(sid, {"FinalReviewStatus": f"终审{status}", "FinalReviewedAt": now, "GraduationStatus": grad_status, "FailureReason": reason})
        QMessageBox.information(self, "成功", "终审已完成。")
        self.load_students()

    def generate_archives(self):
        student_ids = self.get_selected_student_ids()
        if not student_ids:
            QMessageBox.warning(self, "提示", "请先选中要生成档案的学生（可多选）。")
            return
        folder = QFileDialog.getExistingDirectory(self, "选择档案导出目录")
        if not folder:
            return
        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            now = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
            for sid in student_ids:
                cursor.execute("""
                    SELECT s.StudentID, s.Name, s.Gender, s.Major, s.Class, s.EnrollmentYear, s.EnrollmentStatus, s.TuitionStatus,
                           r.FinalReviewStatus, r.GraduationStatus, r.FailureReason
                    FROM PStudents s
                    LEFT JOIN dbo.PGraduationReviews r ON r.StudentID=s.StudentID
                    WHERE s.StudentID=?
                """, (sid,))
                row = cursor.fetchone()
                if not row:
                    continue
                (student_id, name, gender, major, clazz, enroll_year, enroll_status, tuition_status,
                 final_review_status, grad_status, failure_reason) = row
                safe_name = name if name else "未知"
                txt_path = f"{folder}/{student_id}_{safe_name}_毕业资格档案.txt"
                pdf_path = f"{folder}/{student_id}_{safe_name}_毕业资格档案.pdf"
                lines = [
                    f"学生ID：{student_id}",
                    f"姓名：{safe_name}",
                    f"性别：{gender or ''}",
                    f"专业：{major or ''}",
                    f"班级：{clazz or ''}",
                    f"入学年份：{enroll_year or ''}",
                    f"入学状态：{enroll_status or ''}",
                    f"学费状态：{tuition_status or ''}",
                    f"终审审核：{final_review_status or ''}",
                    f"毕业状态：{grad_status or ''}",
                    f"未通过原因：{failure_reason or ''}",
                    f"生成时间：{now}"
                ]
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))

                writer = QPdfWriter(pdf_path)
                writer.setResolution(120)
                writer.setPageSize(QPageSize(QPageSize.A4))
                try:
                    writer.setPageMargins(QMarginsF(15, 15, 15, 15), QPageLayout.Millimeter)
                except Exception:
                    pass
                painter = QPainter(writer)
                painter.setPen(Qt.black)
                painter.setFont(QFont("Arial", 12))
                paint_rect = writer.pageLayout().paintRectPixels(writer.resolution())
                x = paint_rect.left()
                y = paint_rect.top()
                available_width = paint_rect.width()
                line_spacing = painter.fontMetrics().height() + 10
                for line in lines:
                    painter.drawText(QRect(x, y, available_width, line_spacing), Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, line)
                    y += line_spacing
                    if y + line_spacing > paint_rect.top() + paint_rect.height():
                        writer.newPage()
                        y = paint_rect.top()
                painter.end()
                self.upsert_review(student_id, {"ArchiveGeneratedAt": now})

            QMessageBox.information(self, "成功", "档案已生成。")
            self.load_students()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成失败：{str(e)}")
        finally:
            conn.close()

    def handle_exception(self):
        student_ids = self.get_selected_student_ids()
        if not student_ids:
            QMessageBox.warning(self, "提示", "请先选中要处理异常的学生（可多选）。")
            return
        reason, ok = QInputDialog.getText(self, "异常处理", "请输入未通过原因：", QLineEdit.Normal, "")
        if not ok:
            return
        reason = reason.strip()
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        for sid in student_ids:
            self.upsert_review(sid, {"FinalReviewStatus": "终审不通过", "FinalReviewedAt": now, "GraduationStatus": "未通过", "FailureReason": reason})
        QMessageBox.information(self, "成功", "异常已标注。")
        self.load_students()


class DataStatisticsAnalysisModule(QWidget):
    def __init__(self):
        super().__init__()
        ensure_graduation_review_tables()
        self.current_title = ""
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel('数据统计分析', self)
        title.setStyleSheet("font: 24px Arial; color: #4CAF50; text-align: center;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.base_stats_btn = QPushButton('学籍基础统计', self)
        self.base_stats_btn.setStyleSheet(
            'background-color: #4CAF50; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.base_stats_btn.clicked.connect(self.load_base_stats)
        btn_layout.addWidget(self.base_stats_btn)

        self.change_stats_btn = QPushButton('异动数据统计', self)
        self.change_stats_btn.setStyleSheet(
            'background-color: #FF9800; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.change_stats_btn.clicked.connect(self.load_change_stats)
        btn_layout.addWidget(self.change_stats_btn)

        self.grade_stats_btn = QPushButton('成绩数据统计', self)
        self.grade_stats_btn.setStyleSheet(
            'background-color: #2196F3; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.grade_stats_btn.clicked.connect(self.load_grade_stats)
        btn_layout.addWidget(self.grade_stats_btn)

        self.grad_stats_btn = QPushButton('毕业数据统计', self)
        self.grad_stats_btn.setStyleSheet(
            'background-color: #9C27B0; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.grad_stats_btn.clicked.connect(self.load_graduation_stats)
        btn_layout.addWidget(self.grad_stats_btn)

        self.report_btn = QPushButton('报表输出', self)
        self.report_btn.setStyleSheet(
            'background-color: #607D8B; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.report_btn.clicked.connect(self.show_report_tools)
        btn_layout.addWidget(self.report_btn)

        main_layout.addLayout(btn_layout)

        export_layout = QHBoxLayout()
        export_layout.setSpacing(10)

        self.export_csv_btn = QPushButton('导出Excel(CSV)', self)
        self.export_csv_btn.setStyleSheet(
            'background-color: #795548; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.export_csv_btn.clicked.connect(self.export_csv)
        export_layout.addWidget(self.export_csv_btn)

        self.export_pdf_btn = QPushButton('导出PDF', self)
        self.export_pdf_btn.setStyleSheet(
            'background-color: #3F51B5; color: white; font: 18px Arial; padding: 10px 20px; border-radius: 5px;')
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        export_layout.addWidget(self.export_pdf_btn)

        export_layout.addStretch(1)
        main_layout.addLayout(export_layout)

        self.summary_label = QLabel('', self)
        self.summary_label.setStyleSheet("font: 18px Arial; color: #333333; padding: 10px;")
        main_layout.addWidget(self.summary_label)

        self.table = QTableWidget(self)
        self.table.setStyleSheet("font: 18px Arial;")
        self.table.horizontalHeader().setStyleSheet("font: 16px Arial; color: #4CAF50; font-weight: bold;")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)
        self.load_base_stats()

    def set_table(self, headers, rows):
        self.table.setRowCount(0)
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        for r_idx, row in enumerate(rows):
            self.table.insertRow(r_idx)
            for c_idx, v in enumerate(row):
                item = QTableWidgetItem(str(v) if v is not None else "")
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r_idx, c_idx, item)

    def load_base_stats(self):
        self.current_title = "学籍基础统计"
        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(1) FROM PStudents")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT Gender, COUNT(1) FROM PStudents GROUP BY Gender")
            gender_rows = cursor.fetchall()
            cursor.execute("SELECT Class, COUNT(1) FROM PStudents GROUP BY Class ORDER BY COUNT(1) DESC")
            class_rows = cursor.fetchall()
            cursor.execute("SELECT EnrollmentYear, COUNT(1) FROM PStudents GROUP BY EnrollmentYear ORDER BY EnrollmentYear")
            year_rows = cursor.fetchall()

            summary = f"学生总人数：{total}"
            if gender_rows:
                gender_text = "，".join([f"{g or '未知'}:{c}" for g, c in gender_rows])
                summary += f"；男女比例：{gender_text}"
            self.summary_label.setText(summary)

            headers = ["维度", "值", "人数"]
            rows = []
            for clazz, c in class_rows:
                rows.append(["班级分布", clazz or "未知", c])
            for y, c in year_rows:
                rows.append(["年级趋势(入学年份)", y if y is not None else "未知", c])
            for g, c in gender_rows:
                rows.append(["性别比例", g or "未知", c])
            self.set_table(headers, rows)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"统计失败：{str(e)}")
        finally:
            conn.close()

    def load_change_stats(self):
        self.current_title = "异动数据统计"
        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT EnrollmentStatus, COUNT(1) FROM PStudents GROUP BY EnrollmentStatus")
            enroll_rows = cursor.fetchall()
            cursor.execute("SELECT TuitionStatus, COUNT(1) FROM PStudents GROUP BY TuitionStatus")
            tuition_rows = cursor.fetchall()

            self.summary_label.setText("异动统计：按入学状态/学费状态汇总")

            headers = ["维度", "状态", "人数"]
            rows = []
            for s, c in enroll_rows:
                rows.append(["入学状态", s or "未知", c])
            for s, c in tuition_rows:
                rows.append(["学费状态", s or "未知", c])
            self.set_table(headers, rows)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"统计失败：{str(e)}")
        finally:
            conn.close()

    def load_grade_stats(self):
        self.current_title = "成绩数据统计"
        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    AVG(CAST(Grade AS float)) AS AvgGrade,
                    SUM(CASE WHEN Grade >= 90 THEN 1 ELSE 0 END) AS ExcellentCount,
                    SUM(CASE WHEN Grade < 60 THEN 1 ELSE 0 END) AS FailCount,
                    COUNT(1) AS TotalCount
                FROM PGrades
            """)
            avg_grade, excellent_count, fail_count, total_count = cursor.fetchone()
            excellent_rate = (excellent_count / total_count * 100) if total_count else 0
            fail_rate = (fail_count / total_count * 100) if total_count else 0
            self.summary_label.setText(f"平均分：{avg_grade:.2f}；优秀率(>=90)：{excellent_rate:.2f}%；挂科率(<60)：{fail_rate:.2f}%")

            cursor.execute("""
                SELECT TOP 20
                    g.StudentID,
                    s.Name,
                    AVG(CAST(g.Grade AS float)) AS AvgGrade
                FROM PGrades g
                LEFT JOIN PStudents s ON s.StudentID=g.StudentID
                GROUP BY g.StudentID, s.Name
                ORDER BY AvgGrade DESC
            """)
            top_rows = cursor.fetchall()

            headers = ["排名", "学号", "姓名", "平均分"]
            rows = []
            for idx, (sid, name, avg) in enumerate(top_rows, start=1):
                rows.append([idx, sid, name or "", f"{avg:.2f}" if avg is not None else ""])
            self.set_table(headers, rows)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"统计失败：{str(e)}")
        finally:
            conn.close()

    def load_graduation_stats(self):
        self.current_title = "毕业数据统计"
        conn = connect_to_db()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT GraduationStatus, COUNT(1)
                FROM dbo.PGraduationReviews
                GROUP BY GraduationStatus
            """)
            rows_raw = cursor.fetchall()
            cursor.execute("SELECT COUNT(1) FROM PStudents")
            total_students = cursor.fetchone()[0]
            passed = 0
            for status, c in rows_raw:
                if status in {"毕业", "结业"}:
                    passed += c
            rate = (passed / total_students * 100) if total_students else 0
            self.summary_label.setText(f"毕业相关数据：已标记通过人数(毕业/结业)：{passed}；占全部学生：{rate:.2f}%")

            headers = ["毕业状态", "人数"]
            rows = [(status or "未标记", c) for status, c in rows_raw]
            self.set_table(headers, rows)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"统计失败：{str(e)}")
        finally:
            conn.close()

    def show_report_tools(self):
        self.summary_label.setText("报表输出：可导出当前表格为 Excel(CSV) 或 PDF。")

    def export_csv(self):
        if self.table.rowCount() == 0 or self.table.columnCount() == 0:
            QMessageBox.warning(self, "提示", "当前没有可导出的数据。")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "导出为CSV", "", "CSV文件 (*.csv)")
        if not file_path:
            return
        try:
            export_table_to_csv(self.table, file_path)
            QMessageBox.information(self, "成功", "CSV导出成功。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{str(e)}")

    def export_pdf(self):
        if self.table.rowCount() == 0 or self.table.columnCount() == 0:
            QMessageBox.warning(self, "提示", "当前没有可导出的数据。")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "导出为PDF", "", "PDF文件 (*.pdf)")
        if not file_path:
            return
        try:
            export_table_to_pdf(self.table, file_path, self.current_title or "数据统计")
            QMessageBox.information(self, "成功", "PDF导出成功。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{str(e)}")
