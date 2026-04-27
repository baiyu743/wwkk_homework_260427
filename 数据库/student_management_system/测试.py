# 数据库连接测试脚本（单独运行，排查核心问题）
import pyodbc  # 如果你用MySQL则换import pymysql


def test_db_connection():
    # ========== 重点：替换成你实际的数据库配置 ==========
    # SQL Server配置示例
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=你的数据库IP/localhost;'  # 比如 localhost\SQLEXPRESS
        'DATABASE=你的数据库名;'  # 比如 student_manage
        'UID=你的用户名;'  # 比如 sa（如果是Windows认证则删这行，加 Trusted_Connection=yes;）
        'PWD=你的密码;'  # 数据库密码
    )

    try:
        # 1. 测试连接
        conn = pyodbc.connect(conn_str)
        print("✅ 数据库连接成功！")

        # 2. 测试查询PUsers表的T001数据
        cursor = conn.cursor()
        # 注意：表名PUsers要和数据库中完全一致（区分大小写！）
        cursor.execute("SELECT Username, Password FROM PUsers WHERE Username=?", ("T001",))
        result = cursor.fetchone()

        if result:
            print(f"✅ 查到PUsers表数据：用户名={result[0]}, 密码={result[1]}")
        else:
            print("❌ 没查到T001的记录！检查PUsers表是否有该用户")

        conn.close()
    except Exception as e:
        print(f"❌ 数据库操作失败：{str(e)}")


# 运行测试
test_db_connection()