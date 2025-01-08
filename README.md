# 本项目仅作为学习交流使用，请勿用于其它用途，否则后果自负

# BUPT
> 本项目可能存在bug，提一下issue就好
## 1.用法举例

由于只写了内网的网站，所以在校外网络下请使用[ATrust VPN](https://nic.bupt.edu.cn/info/1061/1711.htm)确保可以访问网站.
但是实测在校外网络(使用VPN)下速度比校内网络要慢得多，所以如果你想提高抢课几率，找一个在校内的同学帮你抢吧~

### ①直接使用此仓库
```python
from bupt_internal import BUPT

# 初始化
BUPT.init()
session = BUPT.login_with_verify()

# 第一次启动会提示输入要抢的课以及登录教育管理网站需要的账号密码生成配置文件，后续可以直接在配置文件即config.ini中修改
# 注意config.ini文件编码为GBK
BUPT.grab_all_course(session)  

BUPT.unchoose_course(session, "射电", "虚拟现实")  # 退选

a = BUPT.get_chosen_courses(session)  # 返回所有已选课程
```
### ②使用pip包
本包已经发布，可以直接使用`pip install BUTP-Tools`安装后执行以上代码即可