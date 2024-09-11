# BUPT
## 用法举例
```python
from bupt_internal import BUPT

# 初始化
BUPT.init()
session = BUPT.login_with_verify()

# 第一次启动会提示输入要抢的课以及登录教育管理网站需要的账号密码生成配置文件，后续可以直接在配置文件中修改
BUPT.grab_all_course(session)  

BUPT.unchoose_course(session, "射电", "虚拟现实") # 退选
```