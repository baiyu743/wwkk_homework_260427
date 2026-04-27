import sys
import pyodbc
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QMessageBox, \
    QStackedWidget, QHBoxLayout, QInputDialog
from PyQt5.QtCore import Qt
from teacher_modules import (GradeEntryWindow, GradeSearchWindow, StudentManagementWindow, CourseQueryWindow,
                             TeacherPasswordWindow)
from student_modules import (StudentDashboard)
from admin_modules import (StudentInfoModule,  GradeInfoModule, CourseInfoModule,
                           PasswordManagementModule, AwardsInfoModule)
# 连接到 SQL Server 数据库
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

# 登录界面
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('用户登录')
        self.setGeometry(100, 100, 1800, 1000)

        self.init_background()
        self.initUI()

    def init_background(self):
        # 底层背景图设置
        self.bg_label = QLabel(self)
        pixmap = QPixmap("D:/student_management_system/华水图书馆.jpg")
        self.bg_label.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        self.bg_label.setGeometry(0, 0, self.width(), self.height())

    def initUI(self):
        # 整体垂直布局
        main_layout = QVBoxLayout()
        self.title_label = QLabel('学生管理系统登录', self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            font: 48px Arial; 
            color: #FFFFFF;
            font-weight: bold;
            text-shadow: 3px 3px 0px #000000, 6px 6px 0px rgba(0,0,0,0.5);
            text-shadow: 2px 2px 4px #000000;
        """)
        main_layout.addWidget(self.title_label, alignment=Qt.AlignTop | Qt.AlignHCenter)

        # 用户名
        username_layout = QHBoxLayout()
        username_layout.addStretch(1)
        self.username_label = QLabel('用户名:', self)
        self.username_label.setStyleSheet("""
            font: 28px Arial; 
            color: #FFFFFF;
            font-weight: bold;
            background-color: rgba(0,0,0,0.3);
            padding: 5px 10px;
        """)
        self.username_label.setFixedWidth(120)
        username_layout.addWidget(self.username_label)
        username_layout.addSpacing(5)

        self.username_input = QLineEdit(self)
        self.username_input.setStyleSheet("""
            font: 28px Arial; 
            padding: 15px 20px;
            background-color: rgba(255,255,255,0.9);
            border: 2px solid #4CAF50;
            box-shadow: inset 0 0 5px rgba(0,0,0,0.2);
            border-radius: 5px;
        """)
        self.username_input.setFixedWidth(400)
        username_layout.addWidget(self.username_input)

        username_layout.addStretch(1)
        main_layout.addLayout(username_layout)

        # 密码
        password_layout = QHBoxLayout()
        password_layout.addStretch(1)

        self.password_label = QLabel('密码:', self)
        self.password_label.setStyleSheet("""
            font: 28px Arial; 
            color: #FFFFFF;
            font-weight: bold;
            background-color: rgba(0,0,0,0.3);
            padding: 5px 10px;
        """)
        self.password_label.setFixedWidth(120)
        password_layout.addWidget(self.password_label)
        password_layout.addSpacing(5)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            font: 24px Arial; 
            padding: 15px; 
            background-color: rgba(255,255,255,0.9);
            border: 2px solid #4CAF50;
            border-radius: 5px;
        """)
        self.password_input.setFixedWidth(400)
        password_layout.addWidget(self.password_input)
        password_layout.addStretch(1)
        main_layout.addLayout(password_layout)

        # 登录
        self.login_button = QPushButton('登录', self)
        self.login_button.setStyleSheet("""
            background-color: #4CAF50; 
            color: white; 
            font: 24px Arial; 
            padding: 20px; 
            border-radius: 10px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
        """)
        self.login_button.setFixedWidth(200)
        #连接按钮的点击事件到 check_login 方法。点击登录按钮时，会调用 check_login 方法进行用户名和密码的验证。
        self.login_button.clicked.connect(self.check_login)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.login_button)
        button_layout.addStretch(1)
        main_layout.addLayout(button_layout)

        # 上层容器（不变）
        self.top_widget = QWidget(self)
        self.top_widget.setStyleSheet("background-color: transparent;")
        self.top_widget.setLayout(main_layout)
        self.top_widget.setGeometry(0, 0, self.width(), self.height())

    def get_student_info_by_id(self, conn, cursor, student_id):
        """根据学生学号查询PStudents表，返回学生完整信息字典"""
        try:
            # 查询学生学籍信息（根据学号精准匹配）
            cursor.execute("""
                SELECT StudentID, Name, Gender, Major, Class, PhoneNumber 
                FROM PStudents 
                WHERE StudentID = ?
            """, (student_id,))
            student_data = cursor.fetchone()

            if student_data:
                # 构造学生信息字典（供 StudentDashboard 使用）
                student_info_dict = {
                    "student_id": student_data[0],  # 学号
                    "name": student_data[1],  # 姓名
                    "gender": student_data[2],  # 性别
                    "major": student_data[3],  # 专业
                    "Class": student_data[4],  # 年级
                    "phone": student_data[5]  # 联系方式
                }
                return student_info_dict
            else:
                self.show_message("提示", "未查询到该学生的学籍信息")
                return None
        except Exception as e:
            self.show_message("错误", f"查询学生信息失败：{str(e)}")
            return None

    def check_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        #strip()方法去除字符串两端的空格，确保输入的用户名和密码没有多余的空格。
        if not username or not password:
            self.show_message("错误", "用户名和密码不能为空")
            return
        #connect_to_db() 方法用于连接数据库，返回一个数据库连接对象 conn。
        conn = connect_to_db()
        if not conn:
            return

        try:
            cursor = conn.cursor()
#conn.cursor() 创建一个数据库游标 cursor，用于执行 SQL 查询。cursor.execute() 执行一个 SQL 查询，查询 PUsers 表中是否存在与输入的 username 和 password 匹配的记录。
            cursor.execute("SELECT * FROM PUsers WHERE Username=? AND Password=?", (username, password))
            user = cursor.fetchone()
#cursor.fetchone() 方法返回查询结果的第一条记录。
            if user:
                user_role = user[3]  # 获取角色（Admin、Teacher、Student）

                self.show_message("成功", f"欢迎，{user_role}登录成功！")

                if user_role == 'Admin':
                    self.open_admin_dashboard()
                elif user_role == 'Teacher':
                    self.open_teacher_dashboard(username)
                elif user_role == 'Student':
                # 2.  学生角色：根据关联ID（学号）查询PStudents表，获取学生完整信息
                    student_info = self.get_student_info_by_id(conn, cursor, username)
                # 3.  传递学生信息给 StudentDashboard
                    self.open_student_dashboard(student_info)
                else:
                    self.show_message("提示", f"未知角色：{user_role}，无法跳转")
                    return

                self.close()  # 关闭登录窗口
            else:
                self.show_message("错误", "用户名或密码错误")
        except Exception as e:
            self.show_message("查询失败", f"错误信息：{str(e)}")
        finally:
            if conn:
                conn.close()

    def show_message(self, title, message):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()
    def open_admin_dashboard(self):
        # 定义管理员的主界面窗口
        self.admin_window = AdminDashboard()
        self.admin_window.show()
    def open_teacher_dashboard(self, teacher_username):
        # 定义教师的主界面窗口
        self.teacher_window = TeacherDashboard(teacher_username)
        self.teacher_window.show()

    def open_student_dashboard(self, student_info=None):
        # 这里需要定义学生的主界面窗口
        self.student_window = StudentDashboard(user_info=student_info)
        self.student_window.show()



# 教师主界面
class TeacherDashboard(QWidget):
    def __init__(self, teacher_username, parent=None):
        super().__init__(parent, Qt.Window)

        self.setWindowTitle('学生管理')
        self.setGeometry(100, 100, 1800, 1000)
        self.current_teacher_username = teacher_username
        self.init_background()
        self.initUI()

    def init_background(self):
        self.bg_label = QLabel(self)
        pixmap = QPixmap("D:/student_management_system/湖.png")
        self.bg_label.setPixmap(pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        ))
        self.bg_label.setGeometry(0, 0, self.width(), self.height())

    def initUI(self):
        layout = QVBoxLayout()
        title_h_layout = QHBoxLayout()
        title_h_layout.addStretch(1)

        self.title_label = QLabel(f'欢迎您，{self.current_teacher_username}老师', self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            "font: 50px Arial; font-weight: bold; color: #4CAF50;"
            "text-shadow: 2px 2px 4px rgba(0,0,0,0.2); margin-top: 20px;"
            "border: 3px solid #4CAF50; border-radius: 15px;"
            "background-color: rgba(76, 175, 80, 0.1);"
            "padding: 10px 20px;"
        )

        title_h_layout.addWidget(self.title_label)
        title_h_layout.addStretch(1)
        layout.addLayout(title_h_layout)

        layout.addStretch(1)

        # 成绩录入按钮
        grade_entry_h_layout = QHBoxLayout()
        grade_entry_h_layout.addStretch(1)
        self.add_grade_button = QPushButton('成绩录入', self)
        self.add_grade_button.setStyleSheet(
            'background-color: #F0AD4E; color: white; font: 50px Arial; padding: 8px 15px; border-radius: 5px; width: 300px; height:50px;')
        self.add_grade_button.clicked.connect(self.add_grade)
        grade_entry_h_layout.addWidget(self.add_grade_button)
        grade_entry_h_layout.addStretch(1)
        layout.addLayout(grade_entry_h_layout)

        # 成绩查询按钮
        grade_search_h_layout = QHBoxLayout()
        grade_search_h_layout.addStretch(1)
        self.search_grade_button = QPushButton('成绩查询', self)
        self.search_grade_button.setStyleSheet(
            'background-color: #428BCA; color: white; font: 50px Arial; padding: 8px 15px; border-radius: 5px; width: 300px; height:50px;')
        self.search_grade_button.clicked.connect(self.search_grade)
        grade_search_h_layout.addWidget(self.search_grade_button)
        grade_search_h_layout.addStretch(1)
        layout.addLayout(grade_search_h_layout)

        # 学生管理按钮
        student_manage_h_layout = QHBoxLayout()
        student_manage_h_layout.addStretch(1)
        self.student_management_button = QPushButton('学生管理', self)
        self.student_management_button.setStyleSheet(
            'background-color: #5CB85C; color: white; font: 50px Arial; padding: 8px 15px; border-radius: 5px; width:300px; height: 50px;')
        self.student_management_button.clicked.connect(self.manage_students)
        student_manage_h_layout.addWidget(self.student_management_button)
        student_manage_h_layout.addStretch(1)
        layout.addLayout(student_manage_h_layout)

        # 课程信息按钮
        course_manage_h_layout = QHBoxLayout()
        course_manage_h_layout.addStretch(1)
        self.course_management_button = QPushButton('课程信息', self)
        self.course_management_button.setStyleSheet(
            'background-color: #4CAF50; color: white; font:50px Arial; padding: 8px 15px; border-radius: 5px; width:300px; height:50px;'
        )
        self.course_management_button.clicked.connect(self.manage_courses)
        course_manage_h_layout.addWidget(self.course_management_button)
        course_manage_h_layout.addStretch(1)
        layout.addLayout(course_manage_h_layout)

        # 修改密码按钮
        password_h_layout = QHBoxLayout()
        password_h_layout.addStretch(1)
        self.modify_password_button = QPushButton('修改密码', self)
        self.modify_password_button.setStyleSheet(
            'background-color: #E74C3C; color: white; font:50px Arial; padding: 8px 15px; border-radius: 5px; width:300px; height:50px;'
        )
        self.modify_password_button.clicked.connect(self.modify_password)
        password_h_layout.addWidget(self.modify_password_button)
        password_h_layout.addStretch(1)
        layout.addLayout(password_h_layout)

        layout.addSpacing(20)
        self.setLayout(layout)

    def add_grade(self):
        self.grade_entry_window = GradeEntryWindow()
        self.grade_entry_window.show()

    def search_grade(self):
        self.grade_search_window = GradeSearchWindow()
        self.grade_search_window.show()

    def manage_students(self):
        self.student_management_window = StudentManagementWindow()
        self.student_management_window.show()

    def manage_courses(self):
        self.course_query_window = CourseQueryWindow()
        self.course_query_window.show()

    def modify_password(self):
        self.modify_password_window = TeacherPasswordWindow(self.current_teacher_username)
        self.modify_password_window.show()

class AdminDashboard(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('管理员主界面')
        self.setGeometry(100, 100, 1800, 1000)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # 标题标签
        self.title_label = QLabel('欢迎，管理员', self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font: 24px Arial; color: #4CAF50;")
        layout.addWidget(self.title_label)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        # 1. 学生管理按钮
        self.student_manage_button = QPushButton('学生管理', self)
        self.student_manage_button.setStyleSheet(
            'background-color: #4CAF50; color: white; font: 22px Arial; padding: 15px 30px; border-radius: 5px;')
        self.student_manage_button.clicked.connect(self.manage_students)
        button_layout.addWidget(self.student_manage_button)

        # 2. 课程管理按钮
        self.course_manage_button = QPushButton('课程管理', self)
        self.course_manage_button.setStyleSheet(
            'background-color: #FF9800; color: white; font: 22px Arial; padding: 15px 30px; border-radius: 5px;')
        self.course_manage_button.clicked.connect(self.manage_courses)
        button_layout.addWidget(self.course_manage_button)

        # 3. 成绩管理按钮
        self.grade_query_button = QPushButton('成绩管理', self)
        self.grade_query_button.setStyleSheet(
            'background-color: #9C27B0; color: white; font: 22px Arial; padding: 15px 30px; border-radius: 5px;')
        self.grade_query_button.clicked.connect(self.manage_grades)
        button_layout.addWidget(self.grade_query_button)

        # 4. 奖惩记录管理按钮
        self.award_management_btn = QPushButton('奖惩记录管理', self)
        self.award_management_btn.setStyleSheet(
            'background-color: #2196F3; color: white; font: 22px Arial; padding: 15px 30px; border-radius: 5px;')
        self.award_management_btn.clicked.connect(self.manage_awards_and_disciplinary_actions)
        button_layout.addWidget(self.award_management_btn)

        # 5. 修改密码按钮
        self.password_manage_button = QPushButton('修改密码', self)
        self.password_manage_button.setStyleSheet(
            'background-color: #F44336; color: white; font: 22px Arial; padding: 15px 30px; border-radius: 5px;')
        self.password_manage_button.clicked.connect(self.modify_password)
        button_layout.addWidget(self.password_manage_button)

        layout.addLayout(button_layout)

        # 创建QStackedWidget用于切换不同模块
        self.stacked_widget = QStackedWidget(self)
        layout.addWidget(self.stacked_widget)

        # 初始化各模块
        self.student_info_module = StudentInfoModule()
        self.grade_management_module = GradeInfoModule()
        self.course_management_module = CourseInfoModule()
        self.password_management_module = PasswordManagementModule()
        self.awards_management_module = AwardsInfoModule()

        # 将模块添加到stacked widget中
        self.stacked_widget.addWidget(self.student_info_module)
        self.stacked_widget.addWidget(self.grade_management_module)
        self.stacked_widget.addWidget(self.course_management_module)
        self.stacked_widget.addWidget(self.password_management_module)
        self.stacked_widget.addWidget(self.awards_management_module)

        # 退出按钮
        self.exit_button = QPushButton('退出', self)
        self.exit_button.setStyleSheet(
            'background-color: #F44336; color: white; font: 20px Arial; padding: 15px; border-radius: 5px;')
        self.exit_button.clicked.connect(self.close)
        layout.addWidget(self.exit_button, alignment=Qt.AlignRight)

        self.setLayout(layout)

    def manage_students(self):
        """学生管理功能"""
        self.stacked_widget.setCurrentWidget(self.student_info_module)

    def manage_courses(self):
        """课程管理功能"""
        self.stacked_widget.setCurrentWidget(self.course_management_module)

    def manage_grades(self):
        """成绩管理功能"""
        self.stacked_widget.setCurrentWidget(self.grade_management_module)

    def manage_awards_and_disciplinary_actions(self):
        """奖惩记录管理功能"""
        self.stacked_widget.setCurrentWidget(self.awards_management_module)

    def modify_password(self):
        """修改密码功能"""
        self.stacked_widget.setCurrentWidget(self.password_management_module)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
