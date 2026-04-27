import pyodbc
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QTableWidget,
                             QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
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

class StudentDashboard(QWidget):
    # 接收用户信息字典（至少包含学号用于数据库查询）
    def __init__(self, user_info=None):
        super().__init__()
        self.setObjectName("StudentDashboard")
        # 初始化用户信息，默认空字典避免报错
        self.user_info = user_info if user_info else {}
        self.student_id = self.user_info.get("student_id", None)
        self.student_name = self.user_info.get("name", None)
        # self.password = self.user_info.get("password", None)

        # 学籍信息初始化为空，后续通过数据库查询填充
        self.student_info = {
            # "gender": None,
            # "major": None,
            # "grade": None,
            # "phone": None
        }

        self.setWindowTitle('学生主界面')
        self.setGeometry(100, 100, 1800, 1000)
        self.init_background()
        self.initUI()
        self.query_student_info_from_db()
    # 背景设置及缩放
    def init_background(self):
        self.bg_label = QLabel(self)
        pixmap = QPixmap("D:/student_management_system/华水图书馆.jpg")
        self.bg_label.setPixmap(pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        ))
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.bg_label.lower()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'bg_label'):
            pixmap = QPixmap("D:/student_management_system/华水教学楼.jpg")
            self.bg_label.setPixmap(pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            ))
            self.bg_label.setGeometry(0, 0, self.width(), self.height())

    def initUI(self):
        layout = QVBoxLayout()

        # 标题栏
        welcome_text = f"欢迎，{self.student_name if self.student_name else '学生'}"
        self.title_label = QLabel(welcome_text, self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font: 36px Arial; font-weight: bold; color: #4CAF50; margin: 20px 0;")
        layout.addWidget(self.title_label)

        # 核心功能按钮区域
        func_button_layout = QHBoxLayout()
        func_button_layout.setSpacing(20)

        func_button_layout.setAlignment(Qt.AlignCenter)

        # 1. 学籍信息查看/修改按钮
        self.info_btn = QPushButton('学籍信息查看/修改', self)
        self.info_btn.setStyleSheet('''
            background-color: #428BCA; 
            color: white; 
            font: 22px Arial; 
            padding: 20px 40px; 
            border-radius: 10px;
            min-width: 200px;
        ''')
        self.info_btn.clicked.connect(self.view_modify_student_info)
        func_button_layout.addWidget(self.info_btn)

        # 2. 课程成绩查询按钮
        self.grade_btn = QPushButton('课程成绩查询', self)
        self.grade_btn.setStyleSheet('''
            background-color: #4CAF50; 
            color: white; 
            font: 22px Arial; 
            padding: 20px 40px; 
            border-radius: 10px;
            min-width: 200px;
        ''')
        self.grade_btn.clicked.connect(self.query_course_grade)
        func_button_layout.addWidget(self.grade_btn)

        # 3. 更改密码按钮
        self.pwd_btn = QPushButton('更改密码', self)
        self.pwd_btn.setStyleSheet('''
            background-color: #F0AD4E; 
            color: white; 
            font: 22px Arial; 
            padding: 20px 40px; 
            border-radius: 10px;
            min-width: 200px;
        ''')
        self.pwd_btn.clicked.connect(self.modify_password)
        func_button_layout.addWidget(self.pwd_btn)

        # 4. 奖惩记录按钮
        self.awards_btn = QPushButton('奖惩记录', self)
        self.awards_btn.setStyleSheet(''' 
                background-color: #E91E63; 
                color: white; 
                font: 22px Arial; 
                padding: 20px 40px; 
                border-radius: 10px;
                min-width: 200px;
            ''')
        self.awards_btn.clicked.connect(self.view_awards_and_disciplinary_actions)
        func_button_layout.addWidget(self.awards_btn)

        layout.addLayout(func_button_layout)

        # 内容展示区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)

        self.content_widget.setStyleSheet(
            "margin: 30px; padding: 20px; border: 2px solid #E0E0E0; border-radius: 10px;")
        layout.addWidget(self.content_widget)

        self.setLayout(layout)
        self.clear_content_area()

        self.awards_table = QTableWidget(self)
        self.awards_table.setColumnCount(3)
        self.awards_table.setHorizontalHeaderLabels(['类型', '描述', '日期'])
        self.awards_table.setStyleSheet("font: 16px Arial;")
        self.awards_table.horizontalHeader().setStyleSheet("font: 18px Arial; color: #4CAF50; font-weight: bold;")
        self.awards_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.awards_table.setEditTriggers(QTableWidget.NoEditTriggers)

    # 清除内容
    def clear_content_area(self):
        keep_widgets = []
        if hasattr(self, 'awards_table') and self.awards_table:
            keep_widgets.append(self.awards_table)
        if hasattr(self, 'grade_table') and self.grade_table:
            keep_widgets.append(self.grade_table)

        while self.content_layout.count() > 0:
            item = self.content_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                if widget not in keep_widgets:
                    widget.deleteLater()
                else:
                    widget.hide()
            elif item.layout():
                sub_layout = item.layout()
                while sub_layout.count() > 0:
                    sub_item = sub_layout.takeAt(0)
                    if sub_item.widget():
                        sub_widget = sub_item.widget()
                        if sub_widget not in keep_widgets:
                            sub_widget.deleteLater()
                        else:
                            sub_widget.hide()
                sub_layout.deleteLater()
        self.content_layout.setSpacing(10)
        self.content_layout.setContentsMargins(10, 10, 10, 10)

    def view_awards_and_disciplinary_actions(self):
        self.clear_content_area()

        if not hasattr(self, 'awards_table'):
            # 初始化奖惩表格
            self.awards_table = QTableWidget(self)
            self.awards_table.setColumnCount(3)
            self.awards_table.setHorizontalHeaderLabels(['奖惩类型', '详细描述', '发生日期'])
            self.awards_table.setStyleSheet("font: 16px Arial;")
            self.awards_table.horizontalHeader().setStyleSheet(
                "font: 18px Arial; color: #4CAF50; font-weight: bold;")
            self.awards_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.awards_table.setEditTriggers(QTableWidget.NoEditTriggers)
            self.awards_table.hide()

        # 关键2：清空表格数据
        self.awards_table.setRowCount(0)

        conn = None
        try:
            conn = connect_to_db()
            if not conn:
                return

            cursor = conn.cursor()
            awards_sql = """
                SELECT Type, Description, Date
                FROM PAwardsAndDisciplinaryActions
                WHERE StudentID = ?
            """
            cursor.execute(awards_sql, (self.student_id,))
            awards_data = cursor.fetchall()

            # 填充数据
            self.awards_table.setRowCount(len(awards_data))
            for row_idx, (type_val, description, date) in enumerate(awards_data):
                type_item = QTableWidgetItem(type_val if type_val else "未知")
                desc_item = QTableWidgetItem(description if description else "未知")
                date_item = QTableWidgetItem(str(date) if date else "未知")

                for item in [type_item, desc_item, date_item]:
                    item.setTextAlignment(Qt.AlignCenter)

                self.awards_table.setItem(row_idx, 0, type_item)
                self.awards_table.setItem(row_idx, 1, desc_item)
                self.awards_table.setItem(row_idx, 2, date_item)

            if len(awards_data) == 0:
                self.show_message("提示", "暂无奖惩记录！")
            else:
                awards_title = QLabel('奖惩记录', self)
                awards_title.setStyleSheet(
                    "font: 30px Arial; color: #2E7D32;margin-top: 40px;margin-bottom: 20px; text-align: center;background-color: #E3F2FD;")
                self.content_layout.addWidget(awards_title, alignment=Qt.AlignHCenter)

            self.awards_table.show()
            self.content_layout.addWidget(self.awards_table)

        except Exception as e:
            self.show_message("错误", f"加载奖惩记录失败：{str(e)}")
            print(f"Error: {str(e)}")
        finally:
            if conn:
                conn.close()

    def query_student_info_from_db(self):
        """根据登录学号，从数据库学生表中检索原始学籍信息"""
        if not self.student_id:
            self.show_message("错误", "未获取到学生学号，无法查询学籍信息！")
            return

        conn = None
        try:
            conn = connect_to_db()
            if not conn:
                return

            cursor = conn.cursor()
            query_sql = """
                SELECT StudentID, Name, Gender, DateOfBirth, Ethnicity, IDNumber, 
                       PhoneNumber, Email, Address, EnrollmentYear, Class, Major, 
                       StudyDuration, EnrollmentStatus, TuitionStatus
                FROM PStudents 
                WHERE StudentID = ?
            """
            cursor.execute(query_sql, (self.student_id,))
            student_data = cursor.fetchone()

            if student_data:
                # 将查询结果填充到学籍信息字典中
                self.student_info["student_id"] = student_data[0] if student_data[0] else "未填写"
                self.student_info["name"] = student_data[1] if student_data[1] else "未填写"
                self.student_info["gender"] = student_data[2] if student_data[2] else "未填写"
                self.student_info["date_of_birth"] = student_data[3] if student_data[3] else "未填写"
                self.student_info["ethnicity"] = student_data[4] if student_data[4] else "未填写"
                self.student_info["id_number"] = student_data[5] if student_data[5] else "未填写"
                self.student_info["phone"] = student_data[6] if student_data[6] else "未填写"
                self.student_info["email"] = student_data[7] if student_data[7] else "未填写"
                self.student_info["address"] = student_data[8] if student_data[8] else "未填写"
                self.student_info["enrollment_year"] = student_data[9] if student_data[9] else "未填写"
                self.student_info["class"] = student_data[10] if student_data[10] else "未填写"
                self.student_info["major"] = student_data[11] if student_data[11] else "未填写"
                self.student_info["study_duration"] = student_data[12] if student_data[12] else "未填写"
                self.student_info["enrollment_status"] = student_data[13] if student_data[13] else "未填写"
                self.student_info["tuition_status"] = student_data[14] if student_data[14] else "未填写"
                # 同步学生姓名
                self.student_name = self.student_info["name"]
                self.title_label.setText(f"欢迎，{self.student_name}")
            else:
                self.show_message("提示", "未在数据库中查询到该学生的学籍信息！")
        except Exception as e:
            self.show_message("错误", f"查询学籍信息失败：{str(e)}")
        finally:
            if conn:
                conn.close()

    def view_modify_student_info(self):
        """学籍信息查看/修改（完整功能：展示信息+保存+退出）"""
        self.clear_content_area()

        # 先判断学籍信息是否已查询
        if all(value is None for value in self.student_info.values()):
            self.show_message("提示", "请先获取学籍信息！")
            self.query_student_info_from_db()
            return

        info_title = QLabel('我的学籍信息', self)
        info_title.setStyleSheet(
            "font: 30px Arial; color: #2E7D32;margin-top: 40px;margin-bottom: 20px; text-align: center;background-color: #E3F2FD;")
        self.content_layout.addWidget(info_title, alignment=Qt.AlignHCenter)
        self.content_layout.setSpacing(1)

        # 学籍信息配置：
        info_config = [
            ("学号", self.student_info["student_id"], False),
            ("姓名", self.student_info["name"], False),
            ("性别", self.student_info["gender"], False),
            ("出生日期", self.student_info["date_of_birth"], False),
            ("民族", self.student_info["ethnicity"], False),
            ("身份证号", self.student_info["id_number"], False),
            ("联系方式", self.student_info["phone"], True),
            ("电子邮件", self.student_info["email"], True),
            ("地址", self.student_info["address"], True),
            ("入学年份", self.student_info["enrollment_year"], False),
            ("年级", self.student_info["class"], False),
            ("专业", self.student_info["major"], False),
            ("学制", self.student_info["study_duration"], False),
            ("入学状态", self.student_info["enrollment_status"], False),
            ("学费状态", self.student_info["tuition_status"], False),
        ]

        # 存储输入框对象，用于后续保存
        self.info_inputs = {}
        # 创建水平布局，确保每两个字段并排展示
        for i in range(0, len(info_config), 2):
            h_layout = QHBoxLayout()
            h_layout.setSpacing(8)
            h_layout.setContentsMargins(0, 1, 0, 1)

            for j in range(2):
                if i + j < len(info_config):
                    label_text, value, editable = info_config[i + j]
                    label = QLabel(f"{label_text}：", self)
                    label.setStyleSheet(
                        "font: 20px Arial; min-width: 100px;background-color:#E3F2FD;border: 1px solid #428BCA;")
                    input_box = QLineEdit(self)
                    input_box.setText(str(value) if value else "未填写")
                    input_box.setStyleSheet("font: 18px Arial; padding: 10px; min-width: 300px;")
                    input_box.setReadOnly(not editable)  # 不可编辑字段设为只读
                    h_layout.addWidget(label)
                    h_layout.addWidget(input_box)
                    self.info_inputs[label_text] = (input_box, editable)

            # 将每一行（两个字段）添加到内容布局中
            self.content_layout.addLayout(h_layout)

        self.content_layout.addSpacing(5)


        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(30)
        btn_layout.setAlignment(Qt.AlignCenter)

        # 保存修改按钮
        save_btn = QPushButton('保存修改', self)
        save_btn.setStyleSheet(''' 
            background-color: #4CAF50; 
            color: white; 
            font: 25px Arial; 
            padding: 15px 25px; 
            border-radius: 5px; 
            font-weight: bold;
        ''')
        save_btn.clicked.connect(self.save_student_info_to_db)
        btn_layout.addWidget(save_btn)
        self.content_layout.addLayout(btn_layout)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

    def save_student_info_to_db(self):
        """核心：将修改后的学籍信息（仅可编辑字段）同步回数据库"""
        if not self.student_id:
            self.show_message("错误", "未获取到学生学号，无法保存信息！")
            return

        # 获取可编辑字段的新值
        new_phone = None
        new_email = None
        new_address = None
        #(input_box, editable)：是一个元组，包含两个元素： 输入框对象 是否可以编辑
        for label_text, (input_box, editable) in self.info_inputs.items():
            if editable:
                #input_box.text()：获取用户在 QLineEdit 输入框中的文本内容。
                text_val = input_box.text().strip()
                if not text_val:
                    self.show_message("提示", f"{label_text}不能为空！")
                    return
                if label_text == "联系方式":
                    new_phone = text_val
                elif label_text == "电子邮件":
                    new_email = text_val
                elif label_text == "地址":
                    new_address = text_val

        conn = None
        try:
            conn = connect_to_db()
            if not conn:
                return

            cursor = conn.cursor()
            update_sql = """
                UPDATE PStudents 
                SET PhoneNumber = ?, Email = ?, Address = ?
                WHERE StudentID = ?
            """
            cursor.execute(update_sql, (new_phone, new_email, new_address, self.student_id))
            conn.commit()
            # 更新本地学籍信息
            self.student_info["phone"] = new_phone
            self.student_info["email"] = new_email
            self.student_info["address"] = new_address
            self.student_info["PhoneNumber"] = new_phone
            self.show_message("成功", "学籍信息修改并同步到数据库成功！")
        except Exception as e:
            if conn:
                conn.rollback()  # 出错时回滚事务
            self.show_message("错误", f"保存学籍信息失败：{str(e)}")
        finally:
            if conn:
                conn.close()

    def show_message(self, title, content):
        """弹出提示信息框"""
        QMessageBox.information(self, title, content)

    def query_course_grade(self):
        """课程成绩查询（新增：课程号精准查询+默认显示全部）"""
        self.clear_content_area()

        if not self.student_id:
            self.show_message("错误", "未获取到学生学号，无法查询成绩！")
            return

        # 标题
        grade_title = QLabel('我的课程成绩', self)
        grade_title.setStyleSheet(
            "font: 30px Arial; color: #2E7D32; margin-bottom: 20px; text-align: center; background-color: #E3F2FD;")
        self.content_layout.addWidget(grade_title, alignment=Qt.AlignHCenter)

        # 课程号查询输入框+按钮布局
        search_layout = QHBoxLayout()
        search_layout.setSpacing(15)
        search_layout.setAlignment(Qt.AlignCenter)
        search_layout.setContentsMargins(0, 0, 0, 20)

        search_label = QLabel("输入课程号查询：", self)
        search_label.setStyleSheet("""
            font: 20px Arial;  /* 字体大小 */
            font-weight: bold; color: #FFFFFF;
            background-color: #00B4D8; /* 背景色 */
            padding: 8px 15px; /* 内边距 */
            border-radius: 5px;/* 圆角 */
            /* 文字高亮：添加浅色阴影，模拟高亮效果（可选2种高亮方式） */
            text-shadow: 0 0 3px #FFFFFF; /* 方式1：白色柔光高亮（推荐） */
            /* text-shadow: 1px 1px 0 #FFFFFF, -1px -1px 0 #FFFFFF; */ /* 方式2：白色描边高亮 */
        """)
        search_layout.addWidget(search_label)

        # 课程号输入框
        self.course_id_input = QLineEdit(self)
        self.course_id_input.setPlaceholderText("例如：C001（留空显示全部）")
        self.course_id_input.setStyleSheet("""
            font: 18px Arial; 
            padding: 8px 15px; 
            min-width: 200px; 
            border: 1px solid #ddd; 
            border-radius: 5px;
        """)
        search_layout.addWidget(self.course_id_input)

        # 精准查询按钮
        search_btn = QPushButton('查询该课程成绩', self)
        search_btn.setStyleSheet('''
            background-color: #428BCA; 
            color: white; 
            font: 18px Arial; 
            padding: 8px 20px; 
            border-radius: 5px; 
            font-weight: bold;
        ''')
        # 绑定查询按钮事件（点击后筛选课程号）
        search_btn.clicked.connect(self.filter_grade_by_course_id)
        search_layout.addWidget(search_btn)

        # 重置按钮（可选：清空输入框，恢复显示全部）
        reset_btn = QPushButton('显示全部成绩', self)
        reset_btn.setStyleSheet('''
            background-color: #F0AD4E; 
            color: white; 
            font: 18px Arial; 
            padding: 8px 20px; 
            border-radius: 5px; 
            font-weight: bold;
        ''')
        reset_btn.clicked.connect(self.reset_grade_table)
        search_layout.addWidget(reset_btn)

        # 将搜索布局添加到内容布局
        self.content_layout.addLayout(search_layout)

        # 成绩表格
        grade_table = QTableWidget(self)
        grade_table.setColumnCount(4)
        grade_table.setHorizontalHeaderLabels(['课程ID', '课程名称', '学期', '成绩'])

        # 表格样式
        grade_table.setStyleSheet("""
            QTableWidget {
                font: 16px Arial; 
                background-color: #ffffff;
                border: none;
            }
            QHeaderView::section {
                font: 18px Arial; 
                color: #4CAF50; 
                font-weight: bold; 
                background-color: #E3F2FD;
                padding: 8px; 
                border: 1px solid #ddd;
            }
            QTableWidget::item:selected {
                color: #000000; 
                background-color: #BBDDF6;
            }
        """)

        grade_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        grade_table.setEditTriggers(QTableWidget.NoEditTriggers)
        # 保存表格对象到实例，方便后续筛选/重置操作
        self.grade_table = grade_table
        # 保存全部成绩数据，方便后续筛选
        self.all_grade_data = []

        # 初始化加载全部成绩
        self.load_grade_data()

        self.content_layout.addWidget(grade_table)

    # 加载成绩数据（核心：支持筛选/全部显示）
    def load_grade_data(self, course_id_filter=None):
        """加载成绩数据（course_id_filter=None 显示全部，否则筛选指定课程号）"""
        conn = None
        try:
            conn = connect_to_db()
            if not conn:
                return

            cursor = conn.cursor()
            grade_sql = """
                SELECT g.CourseID, c.CourseName, g.Semester, g.Grade
                FROM PGrades g
                LEFT JOIN PCourses c ON g.CourseID = c.CourseID
                WHERE g.StudentID = ?
            """
            # 筛选课程号：拼接SQL条件
            params = [self.student_id]#params首先将学生学号（self.student_id）加入参数列表。
            if course_id_filter and course_id_filter.strip():
                grade_sql += " AND g.CourseID = ?"#：如果传入了 course_id_filter，并且这个课程号不是空字符串，说明需要按课程号进行筛选。
                params.append(course_id_filter.strip())

            cursor.execute(grade_sql, params)
            grade_data = cursor.fetchall()
            # 保存全部数据（用于重置）
            if not course_id_filter:#if not course_id_filter:：只有当用户没有输入课程号进行筛选时，才会将所有的成绩数据保存在 self.all_grade_data 中
                self.all_grade_data = grade_data

            # 清空表格并填充数据
            self.grade_table.setRowCount(0)  # 先清空原有数据
            self.grade_table.setRowCount(len(grade_data))
            for row_idx, (course_id, course_name, semester, grade) in enumerate(grade_data):
                self.grade_table.setItem(row_idx, 0, QTableWidgetItem(course_id if course_id else "未知"))
                self.grade_table.setItem(row_idx, 1, QTableWidgetItem(course_name if course_name else "未知"))
                self.grade_table.setItem(row_idx, 2, QTableWidgetItem(semester if semester else "未知"))
                self.grade_table.setItem(row_idx, 3, QTableWidgetItem(str(grade) if grade else "未录入"))
                for col_idx in range(4):
                    self.grade_table.item(row_idx, col_idx).setTextAlignment(Qt.AlignCenter)

            if len(grade_data) == 0:
                tip = "暂无课程成绩记录！" if not course_id_filter else f"未查询到课程号为【{course_id_filter}】的成绩！"
                self.show_message("提示", tip)
        except Exception as e:
            self.show_message("错误", f"加载成绩失败：{str(e)}")
        finally:
            if conn:
                conn.close()

    # 按课程号筛选成绩
    def filter_grade_by_course_id(self):
        """根据输入的课程号筛选成绩"""
        course_id = self.course_id_input.text().strip()
        self.load_grade_data(course_id)


    # 重置表格显示全部成绩
    def reset_grade_table(self):
        """清空输入框，恢复显示全部成绩"""
        self.course_id_input.clear()
        self.load_grade_data()

    def modify_password(self):
        self.clear_content_area()
        pwd_container = QWidget(self)
        pwd_container.setStyleSheet("max-width: 500px;")
        pwd_layout = QVBoxLayout(pwd_container)
        pwd_layout.setAlignment(Qt.AlignCenter)
        pwd_layout.setSpacing(20)

        pwd_title = QLabel('修改登录密码', self)
        pwd_title.setStyleSheet(
            "font: 28px Arial; color: #FFFFFF; background-color: #F57C00; padding: 10px 30px; border-radius: 5px; font-weight: bold;")
        pwd_layout.addWidget(pwd_title, alignment=Qt.AlignCenter)

        label_style = "font: 20px Arial; font-weight: bold; color: #FFFFFF; background-color: #F57C00; padding: 12px 0; min-width: 120px; max-width: 120px; min-height: 45px; max-height: 45px; border-radius: 5px; text-align: center;"
        input_style = "font: 18px Arial; padding: 12px 15px; min-width: 200px; max-width: 200px; min-height: 45px; max-height: 45px; border: 1px solid #ddd; border-radius: 5px;"
        # 原密码行
        old_pwd_row = QHBoxLayout()
        old_pwd_row.setSpacing(15)
        old_pwd_row.setAlignment(Qt.AlignCenter)
        old_pwd_label = QLabel("原密码：", self)
        old_pwd_label.setStyleSheet(label_style)
        self.old_pwd_input = QLineEdit(self)
        self.old_pwd_input.setStyleSheet(input_style)
        self.old_pwd_input.setEchoMode(QLineEdit.Password)
        old_pwd_row.addWidget(old_pwd_label)
        old_pwd_row.addWidget(self.old_pwd_input)
        pwd_layout.addLayout(old_pwd_row)
        # 新密码行
        new_pwd_row = QHBoxLayout()
        new_pwd_row.setSpacing(15)
        new_pwd_row.setAlignment(Qt.AlignCenter)
        new_pwd_label = QLabel("新密码：", self)
        new_pwd_label.setStyleSheet(label_style)
        self.new_pwd_input = QLineEdit(self)
        self.new_pwd_input.setStyleSheet(input_style)
        self.new_pwd_input.setEchoMode(QLineEdit.Password)
        new_pwd_row.addWidget(new_pwd_label)
        new_pwd_row.addWidget(self.new_pwd_input)
        pwd_layout.addLayout(new_pwd_row)
        # 确认新密码行
        confirm_pwd_row = QHBoxLayout()
        confirm_pwd_row.setSpacing(15)
        confirm_pwd_row.setAlignment(Qt.AlignCenter)
        confirm_pwd_label = QLabel("确认新密码：", self)
        confirm_pwd_label.setStyleSheet(label_style)
        self.confirm_pwd_input = QLineEdit(self)
        self.confirm_pwd_input.setStyleSheet(input_style)
        self.confirm_pwd_input.setEchoMode(QLineEdit.Password)
        confirm_pwd_row.addWidget(confirm_pwd_label)
        confirm_pwd_row.addWidget(self.confirm_pwd_input)
        pwd_layout.addLayout(confirm_pwd_row)
        # 提交按钮
        submit_pwd_btn = QPushButton('提交修改', self)
        submit_pwd_btn.setStyleSheet(
            "background-color: #F57C00; color: #FFFFFF; font: 20px Arial; font-weight: bold; padding: 12px 30px; border-radius: 8px;")
        submit_pwd_btn.clicked.connect(self.submit_password_modify_to_db)
        pwd_layout.addWidget(submit_pwd_btn, alignment=Qt.AlignCenter)
        # 添加容器到主布局
        self.content_layout.addWidget(pwd_container, alignment=Qt.AlignCenter)

    def submit_password_modify_to_db(self):
        """提交密码修改（同步到数据库PUsers表）"""
        old_pwd = self.old_pwd_input.text().strip()
        new_pwd = self.new_pwd_input.text().strip()
        confirm_pwd = self.confirm_pwd_input.text().strip()

        # 基础校验
        if not old_pwd or not new_pwd or not confirm_pwd:
            self.show_message("错误", "所有密码输入框不能为空！")
            return
        if new_pwd != confirm_pwd:
            self.show_message("错误", "新密码与确认密码不一致！")
            return
        if len(new_pwd) < 6:
            self.show_message("提示", "新密码长度不能少于6位！")
            return

        # 先验证原密码是否与数据库中的一致
        if not self.verify_old_password_in_db(old_pwd):
            self.show_message("错误", "原密码输入错误！")
            return

        # 同步新密码到数据库（修改为PUsers表）
        conn = None
        try:
            conn = connect_to_db()
            if not conn:
                return

            cursor = conn.cursor()
            # 改为更新PUsers表的Password字段（Username关联学生ID）
            update_pwd_sql = """
                UPDATE PUsers 
                SET Password = ? 
                WHERE Username = ?
            """
            cursor.execute(update_pwd_sql, (new_pwd, self.student_id))
            conn.commit()

            # 更新本地密码
            self.password = new_pwd
            self.show_message("成功", "密码修改成功！下次登录请使用新密码。")
            # 清空输入框
            self.old_pwd_input.clear()
            self.new_pwd_input.clear()
            self.confirm_pwd_input.clear()
        except Exception as e:
            if conn:
                conn.rollback()
            self.show_message("错误", f"修改密码失败：{str(e)}")
        finally:
            if conn:
                conn.close()

    def verify_old_password_in_db(self, old_pwd):
        """验证原密码是否与数据库PUsers表中的一致"""
        if not self.student_id or not old_pwd:
            return False

        conn = None
        try:
            conn = connect_to_db()
            if not conn:
                return False

            cursor = conn.cursor()
            # 改为查询PUsers表（Username关联学生ID）
            verify_sql = "SELECT Password FROM PUsers WHERE Username = ?"
            cursor.execute(verify_sql, (self.student_id,))
            pwd_data = cursor.fetchone()

            if pwd_data and pwd_data[0] == old_pwd:
                return True
            return False
        except Exception as e:
            self.show_message("错误", f"验证原密码失败：{str(e)}")
            return False
        finally:
            if conn:
                conn.close()

    def show_message(self, title, message):
        """弹窗提示"""
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
