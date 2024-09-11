from bupt_internal import BUPT
BUPT.init()
session = BUPT.login_with_verify()
# BUPT.grab_all_course(session)
a = BUPT.get_chosen_courses(session)
print(a)
BUPT.unchoose_course(session,"虚拟仪器")