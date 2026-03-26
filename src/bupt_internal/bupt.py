"""BUPT 选课工具主模块

整合认证、配置管理和课程抢课功能，提供统一的 BUPT 类接口。
"""
import threading
from typing import List, Optional
from loguru import logger

from .config_manager import ConfigManager
from .auth import AuthManager
from .course_grabber import CourseGrabber


class BUPT:
    """BUPT 选课工具主类
    
    提供完整的选课流程支持，包括：
    - 配置管理（账号密码、课程列表）
    - 登录和会话验证
    - 课程搜索、选择和退选
    - 多线程抢课
    
    使用示例:
        >>> from bupt_internal import BUPT
        >>> BUPT.init()  # 初始化配置
        >>> session = BUPT.login_with_verify()  # 登录并验证
        >>> BUPT.grab_all_course(session)  # 抢所有配置的课程
        >>> BUPT.unchoose_course(session, "课程名")  # 退课
    """
    
    # 类级别的配置和组件实例
    _config_manager: Optional[ConfigManager] = None
    _course_grabber: Optional[CourseGrabber] = None
    
    # 课程列表（从配置加载）
    public_course_to_grab_list: List[str] = []
    required_course_to_grab_list: List[str] = []
    optional_course_to_grab_list: List[str] = []
    
    @classmethod
    def init(cls, config_file: str = None) -> None:
        """
        初始化 BUPT 抢课程序
        
        读取或创建配置文件，获取用户名、密码和课程列表。
        如果是首次运行，会提示用户输入账号密码和要抢的课程。
        
        Args:
            config_file: 配置文件路径，默认为 config.ini
            
        Example:
            >>> BUPT.init()  # 使用默认配置文件
            >>> BUPT.init("my_config.ini")  # 使用自定义配置文件
        """
        cls._config_manager = ConfigManager(config_file)
        cls._config_manager.load_or_create()
        
        # 更新课程列表
        course_config = cls._config_manager.course_config
        cls.public_course_to_grab_list = course_config.public_courses
        cls.required_course_to_grab_list = course_config.required_courses
        cls.optional_course_to_grab_list = course_config.optional_courses
        
        # 初始化课程抢课器
        cls._course_grabber = CourseGrabber()
        
        logger.info(f"待抢公选课:{cls.public_course_to_grab_list}")
        logger.info(f"待抢必修课:{cls.required_course_to_grab_list}")
        logger.info(f"待抢选修课:{cls.optional_course_to_grab_list}")
        logger.success("初始化完成")
    
    @classmethod
    def login(cls):
        """
        登录教务系统
        
        Returns:
            requests.Session: 登录后的会话对象
            
        Example:
            >>> session = BUPT.login()
        """
        if not cls._config_manager:
            logger.error("请先调用 BUPT.init() 初始化配置")
            raise RuntimeError("未初始化配置")
        
        credentials = cls._config_manager.credentials
        auth_manager = AuthManager(credentials.username, credentials.password)
        return auth_manager.login()
    
    @classmethod
    def login_with_verify(cls):
        """
        登录并验证选课会话
        
        执行登录操作后，自动访问选课页面以激活会话。
        
        Returns:
            requests.Session: 验证后的会话对象
            
        Example:
            >>> session = BUPT.login_with_verify()
        """
        if not cls._config_manager:
            logger.error("请先调用 BUPT.init() 初始化配置")
            raise RuntimeError("未初始化配置")
        
        credentials = cls._config_manager.credentials
        auth_manager = AuthManager(credentials.username, credentials.password)
        return auth_manager.login_with_verify()
    
    @classmethod
    def choose_course(cls, session, course_type: str, course_name: str) -> bool:
        """
        选择课程
        
        Args:
            session: 登录会话
            course_type: 课程类型 (xsxkBxxk, xsxkXxxk, xsxkGgxxkxk)
            course_name: 课程名称
            
        Returns:
            bool: 是否成功选择课程
        """
        if not cls._course_grabber:
            logger.error("请先调用 BUPT.init() 初始化")
            return False
        
        return cls._course_grabber.select_course(session, course_type, course_name)
    
    @classmethod
    def get_chosen_courses(cls, session):
        """
        获取已选课程列表
        
        Args:
            session: 登录会话
            
        Returns:
            dict: 课程名称到课程 ID 的映射字典
            
        Example:
            >>> courses = BUPT.get_chosen_courses(session)
            >>> print(courses)
            {'高等数学': '12345', '大学英语': '67890'}
        """
        if not cls._course_grabber:
            logger.error("请先调用 BUPT.init() 初始化")
            return {}
        
        return cls._course_grabber.get_chosen_courses(session)
    
    @classmethod
    def unchoose_course(cls, session, *course_names: str) -> None:
        """
        退选课程
        
        Args:
            session: 登录会话
            *course_names: 要退选的课程名称列表
            
        Example:
            >>> BUPT.unchoose_course(session, "高等数学", "大学英语")
        """
        if not cls._course_grabber:
            logger.error("请先调用 BUPT.init() 初始化")
            return
        
        cls._course_grabber.drop_course(session, *course_names)
    
    @classmethod
    def choose_required_course(cls, session, course_name: str) -> bool:
        """
        选择必修课程
        
        Args:
            session: 登录会话
            course_name: 课程名称
            
        Returns:
            bool: 是否成功选择课程
        """
        return cls.choose_course(session, "xsxkBxxk", course_name)
    
    @classmethod
    def grab_required_course(cls, session, course_name: str) -> None:
        """
        持续抢选必修课程
        
        循环尝试选择课程直到成功。
        
        Args:
            session: 登录会话
            course_name: 课程名称
        """
        success = False
        while not success:
            success = cls.choose_required_course(session, course_name)
    
    @classmethod
    def choose_optional_course(cls, session, course_name: str) -> bool:
        """
        选择选修课程
        
        适用于第一阶段体育选修和第二阶段专业选修。
        
        Args:
            session: 登录会话
            course_name: 课程名称
            
        Returns:
            bool: 是否成功选择课程
        """
        return cls.choose_course(session, "xsxkXxxk", course_name)
    
    @classmethod
    def grab_optional_course(cls, session, course_name: str) -> None:
        """
        持续抢选选修课程
        
        循环尝试选择课程直到成功。
        
        Args:
            session: 登录会话
            course_name: 课程名称
        """
        success = False
        while not success:
            success = cls.choose_optional_course(session, course_name)
    
    @classmethod
    def choose_public_course(cls, session, course_name: str) -> bool:
        """
        选择公选课程
        
        Args:
            session: 登录会话
            course_name: 课程名称
            
        Returns:
            bool: 是否成功选择课程
        """
        return cls.choose_course(session, "xsxkGgxxkxk", course_name)
    
    @classmethod
    def grab_public_course(cls, session, course_name: str) -> None:
        """
        持续抢选公选课程
        
        循环尝试选择课程直到成功。
        
        Args:
            session: 登录会话
            course_name: 课程名称
        """
        success = False
        while not success:
            success = cls.choose_public_course(session, course_name)
    
    @classmethod
    def grab_all_course(cls, session) -> None:
        """
        启动多线程抢选所有配置的课程
        
        根据配置文件中的课程列表，为每门课程启动一个线程进行抢课。
        
        Args:
            session: 登录会话
            
        Example:
            >>> BUPT.grab_all_course(session)
        """
        threads = []
        
        # 启动公选课抢课线程
        for course in cls.public_course_to_grab_list:
            thread = threading.Thread(
                target=cls.grab_public_course, 
                args=(session, course)
            )
            thread.start()
            threads.append(thread)
        
        # 启动选修课抢课线程
        for course in cls.optional_course_to_grab_list:
            thread = threading.Thread(
                target=cls.grab_optional_course, 
                args=(session, course)
            )
            thread.start()
            threads.append(thread)
        
        # 启动必修课抢课线程
        for course in cls.required_course_to_grab_list:
            thread = threading.Thread(
                target=cls.grab_required_course, 
                args=(session, course)
            )
            thread.start()
            threads.append(thread)
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        logger.success("所有抢课任务已完成")
    
    @classmethod
    def grab_when_class_unoccupied(
        cls, 
        old_class_name: str, 
        replace_class_name: str
    ) -> None:
        """
        当旧课程有人退课时，自动退课并抢新课程
        
        TODO: 此功能尚未实现
        
        Args:
            old_class_name: 与想选课程冲突的已选课程
            replace_class_name: 想候补的课程
        """
        # TODO: 实现自动换课逻辑
        logger.warning("此功能尚未实现")
