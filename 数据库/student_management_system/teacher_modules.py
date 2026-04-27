import pyodbc
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

# 教师成绩录入界面
class GradeEntryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('成绩录入')
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.title_label = QLabel('成绩录入', self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font: 24px Arial; color: #4CAF50;")
        layout.addWidget(self.title_label)

        self.student_id_label = QLabel('学生ID:', self)
        self.student_id_label.setStyleSheet("font: 20px Arial;")
        layout.addWidget(self.student_id_label)
        self.student_id_input = QLineEdit(self)
        self.student_id_input.setStyleSheet("font: 18px Arial; padding: 10px;")
        layout.addWidget(self.student_id_input)

        self.course_id_label = QLabel('课程ID:', self)
        self.course_id_label.setStyleSheet("font: 20px Arial;")
        layout.addWidget(self.course_id_label)
        self.course_id_input = QLineEdit(self)
        self.course_id_input.setStyleSheet("font: 18px Arial; padding: 10px;")
        layout.addWidget(self.course_id_input)

        self.semester_label = QLabel('学期:', self)
        self.semester_label.setStyleSheet("font: 20px Arial;")
        layout.addWidget(self.semester_label)
        self.semester_input = QLineEdit(self)
        self.semester_input.setStyleSheet("font: 18px Arial; padding: 10px;")
        layout.addWidget(self.semester_input)

        self.grade_label = QLabel('成绩:', self)
        self.grade_label.setStyleSheet("font: 20px Arial;")
        layout.addWidget(self.grade_label)
        self.grade_input = QLineEdit(self)
        self.grade_input.setStyleSheet("font: 18px Arial; padding: 10px;")
        layout.addWidget(self.grade_input)

        self.submit_button = QPushButton('提交', self)
        self.submit_button.setStyleSheet('background-color: #4CAF50; color: white; font: 20px Arial; padding: 15px; border-radius: 5px;')
        self.submit_button.clicked.connect(self.submit_grade)
        layout.addWidget(self.submit_button)
        self.setLayout(layout)

    def submit_grade(self):
        student_id = self.student_id_input.text().strip()
        course_id = self.course_id_input.text().strip()
        semester = self.semester_input.text().strip()
        grade = self.grade_input.text().strip()

        if not student_id or not course_id or not semester or not grade:
            self.show_message("错误", "所有字段均不能为空")
            return

        conn = connect_to_db()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM PGrades WHERE StudentID=? AND CourseID=?", (student_id, course_id))
            existing_grade = cursor.fetchone()

            if existing_grade:
                cursor.execute("UPDATE PGrades SET Grade=?, Semester=? WHERE StudentID=? AND CourseID=?",
                               (grade, semester, student_id, course_id))
                self.show_message("成功", "成绩更新成功！")
            else:
                cursor.execute("INSERT INTO PGrades (StudentID, CourseID, Semester, Grade) VALUES (?, ?, ?, ?)",
                               (student_id, course_id, semester, grade))
                self.show_message("成功", "成绩录入成功！")
            conn.commit()
        except Exception as e:
            self.show_message("错误", f"操作失败，错误信息：{str(e)}")
        finally:
            conn.close()

    def show_message(self, title, message):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()


class GradeSearchWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('成绩查询')
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # 标题
        self.title_label = QLabel('成绩查询', self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font: 24px Arial; color: #4CAF50;")
        layout.addWidget(self.title_label)

        # 学生ID输入框布局
        student_id_h_layout = QHBoxLayout()
        self.student_id_label = QLabel('学生ID:', self)
        self.student_id_label.setStyleSheet("font: 20px Arial;")
        self.student_id_label.setFixedWidth(80)
        student_id_h_layout.addWidget(self.student_id_label)
        self.student_id_input = QLineEdit(self)
        self.student_id_input.setStyleSheet("font: 18px Arial; padding: 10px;")
        self.student_id_input.setPlaceholderText("输入学生ID，支持留空")
        student_id_h_layout.addWidget(self.student_id_input)
        layout.addLayout(student_id_h_layout)

        # 课程ID输入框布局
        course_id_h_layout = QHBoxLayout()
        self.course_id_label = QLabel('课程ID:', self)
        self.course_id_label.setStyleSheet("font: 20px Arial;")
        self.course_id_label.setFixedWidth(80)
        course_id_h_layout.addWidget(self.course_id_label)
        self.course_id_input = QLineEdit(self)
        self.course_id_input.setStyleSheet("font: 18px Arial; padding: 10px;")
        self.course_id_input.setPlaceholderText("输入课程ID，支持留空")
        course_id_h_layout.addWidget(self.course_id_input)
        layout.addLayout(course_id_h_layout)

        # 查询按钮
        self.search_button = QPushButton('查询', self)
        self.search_button.setStyleSheet('background-color: #4CAF50; color: white; font: 20px Arial; padding: 15px; border-radius: 5px;')
        self.search_button.clicked.connect(self.search_grade)#将按钮的点击事件与 search_grade 方法连接。
        layout.addWidget(self.search_button)

        # 创建表格来展示查询结果
        self.grade_table = QTableWidget(self)
        self.grade_table.setColumnCount(3)  # 设置3列：学生ID、课程ID、成绩
        self.grade_table.setHorizontalHeaderLabels(['学生ID', '课程ID', '成绩'])
        self.grade_table.setStyleSheet('font: 16px Arial;')  # 设置字体样式
        self.grade_table.horizontalHeader().setStyleSheet("font: 18px Arial; color: #4CAF50; font-weight: bold;")
        self.grade_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁用编辑功能
        self.grade_table.setColumnWidth(0, 150)  # 设置第一列的宽度
        self.grade_table.setColumnWidth(1, 150)  # 设置第二列的宽度
        self.grade_table.setColumnWidth(2, 150)  # 设置第三列的宽度
        layout.addWidget(self.grade_table)

        self.setLayout(layout)

    def search_grade(self):
        student_id = self.student_id_input.text().strip()
        course_id = self.course_id_input.text().strip()

        if not student_id and not course_id:
            self.show_message("错误", "请至少填写学生ID或课程ID作为查询条件！")
            return

        conn = connect_to_db()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            sql = "SELECT StudentID, CourseID, Grade FROM PGrades WHERE 1=1"
            params = []
            if student_id:
                sql += " AND StudentID = ?"
                params.append(student_id)
            if course_id:
                sql += " AND CourseID = ?"
                params.append(course_id)

            cursor.execute(sql, params)
            grade_data = cursor.fetchall()

            if grade_data:
                self.grade_table.setRowCount(len(grade_data))  # 设置表格行数为查询到的记录数
                for row_idx, (s_id, c_id, grade) in enumerate(grade_data):
                    self.grade_table.setItem(row_idx, 0, QTableWidgetItem(s_id))  # 设置学生ID列
                    self.grade_table.setItem(row_idx, 1, QTableWidgetItem(c_id))  # 设置课程ID列
                    self.grade_table.setItem(row_idx, 2, QTableWidgetItem(str(grade)))  # 设置成绩列
                self.show_message("查询成功", f"共找到 {len(grade_data)} 条成绩记录！")
            else:
                self.show_message("未找到成绩", "暂无匹配的成绩记录，请调整查询条件！")
        except Exception as e:
            self.show_message("错误", f"查询失败，错误信息：{str(e)}")
        finally:
            if conn:
                conn.close()

    def show_message(self, title, message):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()

# 教师学生管理功能
class StudentManagementWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('学生管理')
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.title_label = QLabel('学生信息', self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font: 24px Arial; color: #4CAF50;")
        layout.addWidget(self.title_label)

        # 学生ID布局
        student_id_h_layout = QHBoxLayout()
        self.student_id_label = QLabel('学生ID:', self)
        self.student_id_label.setStyleSheet("font: 20px Arial;")
        self.student_id_label.setFixedWidth(80)
        student_id_h_layout.addWidget(self.student_id_label)
        self.student_id_input = QLineEdit(self)
        self.student_id_input.setStyleSheet("font: 18px Arial; padding: 10px;")
        self.student_id_input.setPlaceholderText("输入学生ID查询信息")
        student_id_h_layout.addWidget(self.student_id_input)
        layout.addLayout(student_id_h_layout)

        self.search_button = QPushButton('查看学生信息', self)
        self.search_button.setStyleSheet('background-color: #4CAF50; color: white; font: 20px Arial; padding: 15px; border-radius: 5px;')
        self.search_button.clicked.connect(self.view_student_info)
        layout.addWidget(self.search_button)

        # 学生信息表格
        self.student_table = QTableWidget(self)
        self.student_table.setColumnCount(4)
        self.table_headers = ['学生ID', '姓名', '性别', '专业']
        self.student_table.setHorizontalHeaderLabels(self.table_headers)
        self.student_table.setStyleSheet("font: 16px Arial;")
        self.student_table.horizontalHeader().setStyleSheet("font: 18px Arial; color: #4CAF50; font-weight: bold;")
        self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.student_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.student_table.setRowCount(0)
        layout.addWidget(self.student_table)
        self.setLayout(layout)

    def view_student_info(self):
        student_id = self.student_id_input.text().strip()
        if not student_id:
            self.show_message("错误", "学生ID不能为空")
            return

        self.student_table.setRowCount(0)
        conn = connect_to_db()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT StudentID, Name, Gender, Major FROM PStudents WHERE StudentID=?", (student_id,))
            student = cursor.fetchone()
## 遍历查询到的学生信息（student是一个包含学生各个字段的元组）
            if student:
                self.student_table.setRowCount(1)## 设置表格的行数为1，准备展示查询到的学生信息
                for col_idx, col_data in enumerate(student):#enumerate会返回字段的索引（col_idx）和数据（col_data）
                    item = QTableWidgetItem(str(col_data) if col_data else "未填写")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.student_table.setItem(0, col_idx, item)#填到0行col_idx列
                self.show_message("查询成功", "已在表格中展示该学生信息！")
            else:
                self.show_message("未找到学生", "没有找到该学生的信息")
        except Exception as e:
            self.show_message("错误", f"查询失败，错误信息：{str(e)}")
        finally:
            if conn:
                conn.close()

    def show_message(self, title, message):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()

# 课程信息查询
class CourseQueryWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle('课程信息查询')
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.title_label = QLabel('课程详情查询', self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font: 24px Arial; color: #4CAF50;")
        layout.addWidget(self.title_label)

        # 课程ID输入框
        self.course_id_label = QLabel('课程ID（精准查询）:', self)
        self.course_id_label.setStyleSheet("font: 20px Arial;")
        layout.addWidget(self.course_id_label)
        self.course_id_input = QLineEdit(self)
        self.course_id_input.setStyleSheet("font: 18px Arial; padding: 10px;")
        self.course_id_input.setPlaceholderText("输入课程ID可精准查询，支持留空")
        layout.addWidget(self.course_id_input)

        # 课程名称输入框
        self.course_name_label = QLabel('课程名称（模糊查询）:', self)
        self.course_name_label.setStyleSheet("font: 20px Arial;")
        layout.addWidget(self.course_name_label)
        self.course_name_input = QLineEdit(self)
        self.course_name_input.setStyleSheet("font: 18px Arial; padding: 10px;")
        self.course_name_input.setPlaceholderText("输入课程名称关键词（如：数学），支持模糊匹配")
        layout.addWidget(self.course_name_input)

        # 查询按钮
        self.search_button = QPushButton('查询课程详情', self)
        self.search_button.setStyleSheet(
            'background-color: #4CAF50; color: white; font: 20px Arial; padding: 15px; border-radius: 5px;')
        self.search_button.clicked.connect(self.query_course_detail)
        layout.addWidget(self.search_button)

        # 课程表格
        self.course_table = QTableWidget(self)
        self.course_table.setStyleSheet("font: 16px Arial;")
        self.course_headers = ['课程ID', '课程名称', '教师编号', '学分', '课程类别', '授课学期']
        self.course_table.setColumnCount(6)#setColumnCount(6)：设置表格的列数为 6，
        self.course_table.setHorizontalHeaderLabels(self.course_headers)
        self.course_table.horizontalHeader().setStyleSheet("font: 18px Arial; color: #4CAF50; font-weight: bold;")
        self.course_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.course_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.course_table)
        self.setLayout(layout)

    def query_course_detail(self):
        course_id = self.course_id_input.text().strip()
        course_name = self.course_name_input.text().strip()

        if not course_id and not course_name:
            self.show_message("错误", "请至少填写课程ID或课程名称作为查询条件！")
            return

        self.course_table.setRowCount(0)
        conn = connect_to_db()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            sql = "SELECT CourseID, CourseName, InstructorID, Credits, CourseCategory, SemesterOffered FROM PCourses WHERE 1=1"
            params = []
            if course_id:
                sql += " AND CourseID = ?"
                params.append(course_id)
            if course_name:
                sql += " AND CourseName LIKE ?"
                params.append(f"%{course_name}%")

            cursor.execute(sql, params)
            course_data = cursor.fetchall()

            if course_data and len(course_data) > 0:
                self.course_table.setRowCount(len(course_data))
                for row_idx, course in enumerate(course_data):
                    for col_idx, col_data in enumerate(course):
                        item = QTableWidgetItem(str(col_data) if col_data else "未设置")
                        item.setTextAlignment(Qt.AlignCenter)
                        self.course_table.setItem(row_idx, col_idx, item)
                self.show_message("查询成功", f"共找到 {len(course_data)} 条课程详情记录！")
            else:
                self.show_message("未找到记录", "暂无匹配的课程信息，请调整查询条件！")
        except Exception as e:
            self.show_message("错误", f"课程查询失败：{str(e)}")
        finally:
            if conn:
                conn.close()

    def show_message(self, title, message):
        msg = QMessageBox(self)
        if "错误" in title:
            msg.setIcon(QMessageBox.Critical)
        elif "成功" in title:
            msg.setIcon(QMessageBox.Information)
        elif "未找到" in title:
            msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setFixedWidth(400)
        msg.exec_()

# 教师修改密码
class TeacherPasswordWindow(QWidget):

    def __init__(self, teacher_username: str, parent=None):
        super().__init__(parent)
        self.teacher_username = teacher_username

        self.setWindowTitle("修改密码")
        self.setGeometry(300, 200, 500, 320)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        title = QLabel(f"修改密码（用户：{self.teacher_username}）", self)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font: 20px Arial; font-weight: bold; color: #4CAF50;")
        layout.addWidget(title)

        # 原密码
        self.old_pwd_input = QLineEdit(self)
        self.old_pwd_input.setPlaceholderText("请输入原密码")
        self.old_pwd_input.setEchoMode(QLineEdit.Password)
        self.old_pwd_input.setStyleSheet("font: 16px Arial; padding: 10px;")
        layout.addWidget(self.old_pwd_input)

        # 新密码
        self.new_pwd_input = QLineEdit(self)
        self.new_pwd_input.setPlaceholderText("请输入新密码（至少6位）")
        self.new_pwd_input.setEchoMode(QLineEdit.Password)
        self.new_pwd_input.setStyleSheet("font: 16px Arial; padding: 10px;")
        layout.addWidget(self.new_pwd_input)

        # 确认新密码
        self.confirm_pwd_input = QLineEdit(self)
        self.confirm_pwd_input.setPlaceholderText("请再次输入新密码")
        self.confirm_pwd_input.setEchoMode(QLineEdit.Password)
        self.confirm_pwd_input.setStyleSheet("font: 16px Arial; padding: 10px;")
        layout.addWidget(self.confirm_pwd_input)

        # 按钮区
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        self.submit_btn = QPushButton("提交修改", self)
        self.submit_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font: 16px Arial; padding: 10px; border-radius: 5px;"
        )
        self.submit_btn.clicked.connect(self.submit_modify)

        self.cancel_btn = QPushButton("取消", self)
        self.cancel_btn.setStyleSheet(
            "background-color: #F44336; color: white; font: 16px Arial; padding: 10px; border-radius: 5px;"
        )
        self.cancel_btn.clicked.connect(self.close)

        btn_layout.addWidget(self.submit_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def submit_modify(self):
        old_pwd = self.old_pwd_input.text().strip()
        new_pwd = self.new_pwd_input.text().strip()
        confirm_pwd = self.confirm_pwd_input.text().strip()

        # 1) 基础校验
        if not old_pwd:
            QMessageBox.warning(self, "提示", "原密码不能为空！")
            return
        if len(new_pwd) < 6:
            QMessageBox.warning(self, "提示", "新密码不能为空且至少6位！")
            return
        if new_pwd != confirm_pwd:
            QMessageBox.warning(self, "提示", "两次输入的新密码不一致！")
            return

        conn = None
        try:
            # 2) 连接数据库
            conn = connect_to_db()
            if not conn:
                return
            cursor = conn.cursor()

            # 3) 查当前密码
            cursor.execute("SELECT Password FROM PUsers WHERE Username=?", (self.teacher_username,))
            row = cursor.fetchone()
            if not row:
                QMessageBox.critical(self, "错误", f"数据库中未找到用户【{self.teacher_username}】")
                return

            db_password = (row[0] or "").strip()
            if old_pwd != db_password:
                QMessageBox.critical(self, "错误", "原密码输入错误！无法继续修改")
                return

            # 4) 更新新密码
            cursor.execute(
                "UPDATE PUsers SET Password=? WHERE Username=?",
                (new_pwd, self.teacher_username)
            )
            conn.commit()

            QMessageBox.information(self, "成功", "密码修改成功！请使用新密码登录。")
            self.close()

        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            QMessageBox.critical(self, "错误", f"操作失败：{str(e)}")
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass

# # 教师主界面
# class TeacherMainWindow(QWidget):
#     def __init__(self, teacher_id="T001"):
#         super().__init__()
#         self.teacher_id = teacher_id
#         self.setWindowTitle('教师管理系统')
#         self.setGeometry(50, 50, 1000, 700)
#         self.initUI()
#
#     def initUI(self):
#         layout = QVBoxLayout()
#
#         title = QLabel('教师管理系统', self)
#         title.setAlignment(Qt.AlignCenter)
#         title.setStyleSheet("font: 28px Arial; color: #4CAF50; font-weight: bold;")
#         layout.addWidget(title)
#
#         # 功能按钮布局
#         btn_layout = QHBoxLayout()
#         btn_layout.setSpacing(20)
#         btn_layout.setAlignment(Qt.AlignCenter)
#
#         # 1. 成绩录入
#         grade_entry_btn = QPushButton('成绩录入', self)
#         grade_entry_btn.setStyleSheet('''
#             background-color: #4CAF50;
#             color: white;
#             font: 20px Arial;
#             padding: 20px 30px;
#             border-radius: 5px;
#             min-width: 150px;
#         ''')
#         grade_entry_btn.clicked.connect(self.open_grade_entry)
#         btn_layout.addWidget(grade_entry_btn)
#
#         # 2. 成绩查询
#         grade_search_btn = QPushButton('成绩查询', self)
#         grade_search_btn.setStyleSheet('''
#             background-color: #2196F3;
#             color: white;
#             font: 20px Arial;
#             padding: 20px 30px;
#             border-radius: 5px;
#             min-width: 150px;
#         ''')
#         grade_search_btn.clicked.connect(self.open_grade_search)
#         btn_layout.addWidget(grade_search_btn)
#
#         # 3. 学生管理
#         student_manage_btn = QPushButton('学生管理', self)
#         student_manage_btn.setStyleSheet('''
#             background-color: #FF9800;
#             color: white;
#             font: 20px Arial;
#             padding: 20px 30px;
#             border-radius: 5px;
#             min-width: 150px;
#         ''')
#         student_manage_btn.clicked.connect(self.open_student_manage)
#         btn_layout.addWidget(student_manage_btn)
#
#         # 4. 课程查询
#         course_query_btn = QPushButton('课程查询', self)
#         course_query_btn.setStyleSheet('''
#             background-color: #9C27B0;
#             color: white;
#             font: 20px Arial;
#             padding: 20px 30px;
#             border-radius: 5px;
#             min-width: 150px;
#         ''')
#         course_query_btn.clicked.connect(self.open_course_query)
#         btn_layout.addWidget(course_query_btn)
#
#         # 5. 修改密码
#         pwd_modify_btn = QPushButton('修改密码', self)
#         pwd_modify_btn.setStyleSheet('''
#             background-color: #F44336;
#             color: white;
#             font: 20px Arial;
#             padding: 20px 30px;
#             border-radius: 5px;
#             min-width: 150px;
#         ''')
#         pwd_modify_btn.clicked.connect(self.open_pwd_modify)
#         btn_layout.addWidget(pwd_modify_btn)
#
#         layout.addLayout(btn_layout)
#         self.setLayout(layout)
#
#
#     def open_grade_entry(self):
#         self.grade_entry_win = GradeEntryWindow()
#         self.grade_entry_win.show()
#
#     def open_grade_search(self):
#         self.grade_search_win = GradeSearchWindow()
#         self.grade_search_win.show()
#
#     def open_student_manage(self):
#         self.student_manage_win = StudentManagementWindow()
#         self.student_manage_win.show()
#
#     def open_course_query(self):
#         self.course_query_win = CourseQueryWindow()
#         self.course_query_win.show()
#
#     def open_pwd_modify(self):
#         # 传入教师ID到密码修改窗口
#         self.pwd_modify_win = TeacherPasswordWindow(self.teacher_id)
#         self.pwd_modify_win.show()
#

