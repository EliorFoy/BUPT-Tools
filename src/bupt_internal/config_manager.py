"""配置管理模块，负责处理用户配置文件的读写操作。"""
import configparser
import os
from pathlib import Path
from loguru import logger
from dataclasses import dataclass, field
from typing import List


@dataclass
class CourseConfig:
    """课程配置数据类"""
    public_courses: List[str] = field(default_factory=list)
    required_courses: List[str] = field(default_factory=list)
    optional_courses: List[str] = field(default_factory=list)


@dataclass
class Credentials:
    """凭证数据类"""
    username: str = ""
    password: str = ""


class ConfigManager:
    """配置管理器，负责处理配置文件的读写"""
    
    DEFAULT_CONFIG_FILE = "config.ini"
    
    def __init__(self, config_file: str = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认为 config.ini
        """
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self._config = configparser.ConfigParser()
        self._credentials = Credentials()
        self._course_config = CourseConfig()
    
    def load_or_create(self) -> bool:
        """
        加载现有配置或创建新配置
        
        Returns:
            bool: 是否成功加载或创建配置
        """
        if os.path.exists(self.config_file):
            return self._load_existing()
        else:
            return self._create_new()
    
    def _load_existing(self) -> bool:
        """加载现有配置文件"""
        try:
            self._config.read(self.config_file)
            
            # 加载凭证
            if 'Credentials' in self._config:
                self._credentials.username = self._config.get('Credentials', 'username', fallback='')
                self._credentials.password = self._config.get('Credentials', 'password', fallback='')
            
            # 加载课程配置
            if 'Course' in self._config:
                course_section = self._config['Course']
                self._course_config.public_courses = self._parse_course_list(
                    course_section.get('public_course', '')
                )
                self._course_config.required_courses = self._parse_course_list(
                    course_section.get('required_course', '')
                )
                self._course_config.optional_courses = self._parse_course_list(
                    course_section.get('optional_course', '')
                )
            
            self._log_loaded_config()
            return True
            
        except Exception as e:
            logger.error(f"加载配置文件失败：{e}")
            raise
    
    def _create_new(self) -> bool:
        """创建新的配置文件"""
        print('config.ini 文件不存在，请输入账号密码自动配置')
        
        self._config['Credentials'] = {}
        self._credentials.username = input("输入用户名：")
        self._credentials.password = input("输入密码：")
        
        self._config['Credentials']['username'] = self._credentials.username
        self._config['Credentials']['password'] = self._credentials.password
        
        self._setup_course_config()
        self._save()
        return True
    
    def _setup_course_config(self):
        """设置课程配置"""
        self._config['Course'] = {}
        print("如果想抢多个课，请用空格隔开~;如果没有想抢的课，留空即可~")
        
        # 公选课
        public_input = input("输入想要抢的公选课:").strip()
        self._course_config.public_courses = self._parse_course_list(public_input)
        self._config['Course']['public_course'] = public_input.replace(" ", ",")
        
        # 必修课
        required_input = input("输入想要抢的必修课：").strip()
        self._course_config.required_courses = self._parse_course_list(required_input)
        self._config['Course']['required_course'] = required_input.replace(" ", ",")
        
        # 选修课
        optional_input = input("输入想要抢的选修课：").strip()
        self._course_config.optional_courses = self._parse_course_list(optional_input)
        self._config['Course']['optional_course'] = optional_input.replace(" ", ",")
    
    @staticmethod
    def _parse_course_list(course_string: str) -> List[str]:
        """解析课程列表字符串"""
        if not course_string:
            return []
        return [course.strip() for course in course_string.split(",") if course.strip()]
    
    def _log_loaded_config(self):
        """记录已加载的配置"""
        logger.info(f"待抢公选课:{self._course_config.public_courses}")
        logger.info(f"待抢必修课:{self._course_config.required_courses}")
        logger.info(f"待抢选修课:{self._course_config.optional_courses}")
        logger.success("配置文件已加载")
    
    def _save(self):
        """保存配置到文件"""
        with open(self.config_file, 'w', encoding='utf-8') as config_file:
            self._config.write(config_file)
        logger.success("配置文件已更新")
    
    def save(self):
        """公开保存方法"""
        self._save()
    
    @property
    def credentials(self) -> Credentials:
        """获取凭证信息"""
        return self._credentials
    
    @property
    def course_config(self) -> CourseConfig:
        """获取课程配置"""
        return self._course_config
