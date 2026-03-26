"""测试脚本 - 演示重构后的 BUPT 工具使用方式"""
from bupt_internal import BUPT

# 初始化配置（首次运行会创建 config.ini）
BUPT.init()

# 登录并验证选课会话
session = BUPT.login_with_verify()

# 抢所有配置的课程
BUPT.grab_all_course(session)

# 获取已选课程列表
chosen_courses = BUPT.get_chosen_courses(session)
print(f"已选课程：{chosen_courses}")

# 退课示例（取消注释以使用）
# BUPT.unchoose_course(session, "电路综合设计")
