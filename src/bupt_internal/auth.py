"""认证模块，负责处理用户登录和会话管理。"""
import requests
from bs4 import BeautifulSoup
import re
from loguru import logger


class AuthManager:
    """认证管理器，负责处理用户登录和会话验证"""
    
    LOGIN_URL = "https://jwgl.bupt.edu.cn/Logon.do"
    MAIN_PAGE_URL = "https://jwgl.bupt.edu.cn/framework/xsMain_bjyddx.jsp"
    BASE_URL = "https://jwgl.bupt.edu.cn"
    
    def __init__(self, username: str, password: str):
        """
        初始化认证管理器
        
        Args:
            username: 用户名
            password: 密码
        """
        self.username = username
        self.password = password
    
    def login(self) -> requests.Session:
        """
        执行登录操作
        
        Returns:
            requests.Session: 登录后的会话对象
        """
        session = requests.Session()
        
        # 获取编码参数
        code = f"{self.username}%%%{self.password}"
        scode_response = session.post(
            f"{self.LOGIN_URL}?method=logon&flag=sess"
        )
        scode, sxh = scode_response.text.split("#")
        
        # 编码密码
        encoded = ''
        for i in range(len(code)):
            if i < 20:
                encoded += code[i:i + 1] + scode[:int(sxh[i:i + 1])]
                scode = scode[int(sxh[i:i + 1]):]
            else:
                encoded += code[i:]
                break
        
        # 执行登录
        response = session.post(
            f"{self.LOGIN_URL}?method=logon",
            data={"encoded": encoded}
        )
        
        if "选课" in response.text:
            logger.success("登录成功")
        else:
            logger.warning("登录可能失败，请检查账号密码")
        
        return session
    
    @staticmethod
    def verify_session(session: requests.Session) -> requests.Session:
        """
        验证并激活选课会话
        
        需要访问选课网页才能激活会话
        
        Args:
            session: 登录后的会话
            
        Returns:
            requests.Session: 验证后的会话
        """
        cookie_dict = {cookie.name: cookie.value for cookie in session.cookies}
        
        while True:
            try:
                # 获取主页面
                main_page_response = requests.get(
                    AuthManager.MAIN_PAGE_URL, 
                    cookies=cookie_dict
                )
                main_page_html = main_page_response.text
                
                # 解析正常选课链接
                soup = BeautifulSoup(main_page_html, 'html.parser')
                normal_course_div = soup.find('div', text="正常选课")
                
                if not normal_course_div or not normal_course_div.parent:
                    raise ValueError("未找到正常选课入口")
                
                first_step_url = normal_course_div.parent.get('data-src')
                
                # 访问第一个页面
                first_page_response = requests.get(
                    f"{AuthManager.BASE_URL}{first_step_url}", 
                    cookies=cookie_dict
                )
                first_page_html = first_page_response.text
                
                # 解析进入选课链接
                enter_link = BeautifulSoup(first_page_html, 'html.parser').find(
                    'a', text="进入选课"
                )
                
                if not enter_link:
                    raise ValueError("未找到进入选课链接")
                
                second_page_url = enter_link.get('href')
                
                # 访问第二个页面
                second_page_response = requests.get(
                    f"{AuthManager.BASE_URL}{second_page_url}", 
                    cookies=cookie_dict
                )
                second_page_html = second_page_response.text
                
                # 解析最终选课页面 URL
                final_url_match = re.findall(
                    r'<a.+href="(.*?)".+>进入选课</a>', 
                    second_page_html
                )
                
                if not final_url_match:
                    raise ValueError("未找到最终选课页面链接")
                
                final_url = final_url_match[0]
                
                # 访问最终选课页面
                requests.get(
                    f"{AuthManager.BASE_URL}{final_url}", 
                    cookies=cookie_dict
                )
                
                logger.success("进入选课页面成功")
                break
                
            except Exception as e:
                logger.error(f"进入选课页面失败，重新访问等待选课开始... ({e})")
                continue
        
        return session
    
    def login_with_verify(self) -> requests.Session:
        """
        执行登录并验证会话
        
        Returns:
            requests.Session: 验证后的会话对象
        """
        session = self.login()
        return self.verify_session(session)
