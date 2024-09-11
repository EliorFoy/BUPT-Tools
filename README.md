# BUPT
> 注意：本项目还未经过抢课真正测试，不过你可以试一试。
> 如果有bug那也正常，提一下issue就好
## 1.用法举例
### ①直接使用此仓库
```python
from bupt_internal import BUPT

# 初始化
BUPT.init()
session = BUPT.login_with_verify()

# 第一次启动会提示输入要抢的课以及登录教育管理网站需要的账号密码生成配置文件，后续可以直接在配置文件中修改
BUPT.grab_all_course(session)  

BUPT.unchoose_course(session, "射电", "虚拟现实") # 退选
```
### ②使用pip包
本包已经发布，可以直接使用`pip install BUTP-Tools`安装后执行以上代码即可