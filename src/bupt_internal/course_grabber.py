"""课程抢课模块，负责处理课程的搜索、选择和退选操作。"""
from typing import Dict, List, Tuple, Optional
from bs4 import BeautifulSoup
import requests
import json
from loguru import logger
from deprecation import deprecated


class CourseGrabber:
    """课程抢课器，负责处理课程的搜索、选择和退选"""
    
    # 搜索课程参数配置
    SEARCH_PARAMS = {
        "xsxkBxxk": (
            ('skxq_xx0103', ''),
            ('kcxx', 'undefined'),
            ('skls', 'undefined'),
            ('skxq', 'undefined'),
            ('skjc', 'undefined'),
            ('sfym', 'false'),
            ('sfct', 'false'),
            ('sfxx', 'false'),
            ('glyx', 'false'),
        ),
        "xsxkXxxk": (
            ('skxq_xx0103', ''),
            ('kcxx', 'undefined'),
            ('skls', 'undefined'),
            ('skxq', 'undefined'),
            ('skjc', 'undefined'),
            ('sfym', 'false'),
            ('sfct', 'false'),
            ('sfxx', 'false'),
            ('glyx', 'false'),
        ),
        "xsxkGgxxkxk": lambda name="": (
            ('kcxx', name),
            ('skls', ''),
            ('skxq', ''),
            ('skjc', ''),
            ('sfym', 'false'),
            ('sfct', 'false'),
            ('szjylb', ''),
            ('sfxx', 'true'),
        )
    }
    
    # 搜索课程数据配置
    SEARCH_DATA_TEMPLATES = {
        "xsxkBxxk": {
            'sEcho': '1',
            'iColumns': '11',
            'sColumns': '',
            'iDisplayStart': '0',
            'iDisplayLength': '15',
            'mDataProp_0': 'kch',
            'mDataProp_1': 'kcmc',
            'mDataProp_2': 'fzmc',
            'mDataProp_3': 'ktmc',
            'mDataProp_4': 'xf',
            'mDataProp_5': 'skls',
            'mDataProp_6': 'sksj',
            'mDataProp_7': 'skdd',
            'mDataProp_8': 'xqmc',
            'mDataProp_9': 'ctsm',
            'mDataProp_10': 'czOper'
        },
        "xsxkXxxk": {
            'sEcho': '1',
            'iColumns': '11',
            'sColumns': '',
            'iDisplayStart': '0',
            'iDisplayLength': '15',
            'mDataProp_0': 'kch',
            'mDataProp_1': 'kcmc',
            'mDataProp_2': 'fzmc',
            'mDataProp_3': 'ktmc',
            'mDataProp_4': 'xf',
            'mDataProp_5': 'skls',
            'mDataProp_6': 'sksj',
            'mDataProp_7': 'skdd',
            'mDataProp_8': 'xqmc',
            'mDataProp_9': 'ctsm',
            'mDataProp_10': 'czOper'
        },
        "xsxkGgxxkxk": {
            'sEcho': '1',
            'iColumns': '13',
            'sColumns': '',
            'iDisplayStart': '0',
            'iDisplayLength': '15',
            'mDataProp_0': 'kch',
            'mDataProp_1': 'kcmc',
            'mDataProp_2': 'xf',
            'mDataProp_3': 'skls',
            'mDataProp_4': 'sksj',
            'mDataProp_5': 'skdd',
            'mDataProp_6': 'xqmc',
            'mDataProp_7': 'xxrs',
            'mDataProp_8': 'xkrs',
            'mDataProp_9': 'syrs',
            'mDataProp_10': 'ctsm',
            'mDataProp_11': 'szkcflmc',
            'mDataProp_12': 'czOper'
        }
    }
    
    BASE_URL = "https://jwgl.bupt.edu.cn"
    
    def __init__(self):
        """初始化课程抢课器"""
        pass
    
    @staticmethod
    def _get_search_params(course_type: str, course_name: str = "") -> tuple:
        """获取搜索课程的参数"""
        params_func = CourseGrabber.SEARCH_PARAMS.get(course_type)
        if callable(params_func):
            return params_func(course_name)
        return params_func
    
    @staticmethod
    def _get_search_data(course_type: str, start: int = 0) -> dict:
        """获取搜索课程的数据"""
        data_template = CourseGrabber.SEARCH_DATA_TEMPLATES.get(course_type, {}).copy()
        data_template['iDisplayStart'] = str(start)
        return data_template
    
    def search_courses(
        self, 
        session: requests.Session, 
        course_type: str, 
        course_name: str
    ) -> List[Dict]:
        """
        搜索课程
        
        Args:
            session: 登录会话
            course_type: 课程类型 (xsxkBxxk, xsxkXxxk, xsxkGgxxkxk)
            course_name: 课程名称
            
        Returns:
            匹配的课程列表
        """
        matched_courses = []
        start = 0
        total = 0
        
        while True:
            params = self._get_search_params(course_type, course_name)
            data = self._get_search_data(course_type, start)
            
            url = f'{self.BASE_URL}/jsxsd/xsxkkc/{course_type}'
            response = session.post(url=url, params=params, data=data)
            
            if response.status_code != 200:
                logger.error(f"网页还未开启选课！code={response.status_code} ({course_name})")
                return []
            
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                return []
            
            total = response_json.get('iTotalRecords', 0)
            
            for item in response_json.get("aaData", []):
                kcmc = item.get("kcmc", "")
                if course_name in kcmc:
                    matched_courses.append({
                        'name': kcmc,
                        'kcid': item.get("jx02id"),
                        'jx0404id': item.get("jx0404id")
                    })
            
            if start + 15 >= total:
                break
            start += 15
        
        return matched_courses
    
    def select_course(
        self, 
        session: requests.Session, 
        course_type: str, 
        course_name: str
    ) -> bool:
        """
        选择课程
        
        Args:
            session: 登录会话
            course_type: 课程类型
            course_name: 课程名称
            
        Returns:
            bool: 是否成功选择课程
        """
        matched_courses = self.search_courses(session, course_type, course_name)
        
        if not matched_courses:
            logger.error(f"获取匹配课程名称失败，请检查是否有该课程！({course_name})")
            return True
        
        logger.info(f"获取匹配课程名称:{[c['name'] for c in matched_courses]}")
        
        course = matched_courses[0]
        params = (
            ('kcid', course['kcid']),
            ('cfbs', 'null'),
            ('jx0404id', course['jx0404id']),
            ('xkzy', ''),
            ('trjf', ''),
        )
        
        operation_type = course_type.replace("xsxk", "").lower()
        url = f'{self.BASE_URL}/jsxsd/xsxkkc/{operation_type}Oper'
        
        response = session.get(url, params=params)
        
        try:
            result = response.json()
            message = result.get("message", "")
            success = result.get("success", False)
            
            logger.info(f"{message} ({course['name']})")
            
            if "人数已满" in message:
                logger.error("人数已满，居然没抢到...")
                return False
            
            return success
        except json.JSONDecodeError:
            logger.error(f"响应解析失败 ({course['name']})")
            return False
    
    def get_chosen_courses(self, session: requests.Session) -> Dict[str, str]:
        """
        获取已选课程列表
        
        Args:
            session: 登录会话
            
        Returns:
            课程名称到课程 ID 的映射字典
        """
        url = f"{self.BASE_URL}/jsxsd/xsxkjg/comeXkjglb"
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        course_rows = soup.find_all('tr')[1:]  # 跳过表头
        course_dict = {}
        
        for row in course_rows:
            cells = row.find_all('td')
            if len(cells) > 1:
                course_name = cells[1].text
                div_element = row.find('div')
                if div_element and 'id' in div_element.attrs:
                    course_id = div_element['id'].replace('div_', '')
                    course_dict[course_name] = course_id
        
        return course_dict
    
    def find_chosen_course(
        self, 
        session: requests.Session, 
        course_name: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        根据课程名称查找已选课程
        
        Args:
            session: 登录会话
            course_name: 课程名称
            
        Returns:
            (课程名称，课程 ID) 或 (None, None)
        """
        chosen_courses = self.get_chosen_courses(session)
        
        for name, course_id in chosen_courses.items():
            if course_name in name:
                return name, course_id
        
        return None, None
    
    def drop_course(
        self, 
        session: requests.Session, 
        *course_names: str
    ) -> None:
        """
        退选课程
        
        Args:
            session: 登录会话
            *course_names: 要退选的课程名称列表
        """
        for course_name in course_names:
            matched_name, course_id = self.find_chosen_course(session, course_name)
            
            if not course_id or not matched_name:
                logger.error(f"推选失败！未找到课程 ({course_name}),请确定已选该课程")
                continue
            
            url = f"{self.BASE_URL}/jsxsd/xsxkjg/xstkOper"
            params = {"jx0404id": course_id, "tkyy": ""}
            
            response = session.get(url, params=params)
            
            try:
                result = response.json()
                if result.get("success"):
                    logger.success(f"退课成功!({matched_name})")
                else:
                    logger.error(f"退课失败!({matched_name})")
            except json.JSONDecodeError:
                logger.error(f"退课失败!({matched_name})")
