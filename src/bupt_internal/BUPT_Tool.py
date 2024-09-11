from bs4 import BeautifulSoup
import requests
from loguru import logger
import re
import json
import configparser
import os
import threading


class BUPT:
    _username = None
    _password = None
    public_course_to_grab_list = None
    optional_course_to_grab_list = None
    required_course_to_grab_list = None
    search_course_params_dic = lambda name="": {
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
        "xsxkGgxxkxk": (
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
    search_course_data_dic = lambda start: {
        "xsxkBxxk": {
            'sEcho': '1',
            'iColumns': '11',
            'sColumns': '',
            'iDisplayStart': str(start),
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
            'iDisplayStart': str(start),
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
            'iDisplayStart': str(start),
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

    @staticmethod
    def init():
        """
        初始化BUPT抢课程序。该函数首先读取配置文件，如果配置文件存在，则从配置文件中获取用户名和密码；如果配置文件不存在，则提示用户输入用户名和密码并创建新的配置文件。然后，该函数会检查课程配置是否存在，如果不存在，则提示用户输入想要抢的公选课、必修课和选修课，并将这些信息保存到配置文件中。最后，将获取到的课程信息写入配置文件。

        Parameters:
        无

        Returns:
        无

        Raises:
        Exception: 如果配置文件出现问题，如无法解析等，则会抛出异常。
        """
        config = configparser.ConfigParser()
        config.read('config.ini')
        if os.path.exists('config.ini'):
            BUPT._username = config.get('Credentials', 'username')
            BUPT._password = config.get('Credentials', 'password')
        else:
            print('config.ini文件不存在，请输入账号密码自动配置')
            config = configparser.ConfigParser()

            # 创建一个新的配置文件并添加一个节
            config['Credentials'] = {}
            # 获取用户输入的用户名和密码
            BUPT._username = input("输入用户名: ")
            BUPT._password = input("输入密码: ")

            # 将用户输入的用户名和密码保存到配置文件中
            config['Credentials']['username'] = BUPT._username
            config['Credentials']['password'] = BUPT._password
        if 'Course' not in config:
            config['Course'] = {}
            print("如果想抢多个课，请用空格隔开~;如果没有想抢的课，留空即可~")
            if public_courses_input := input("输入想要抢的公选课:"):
                config['Course']['public_course'] = public_courses_input.strip().replace(" ", ",")
                BUPT.public_course_to_grab_list = config['Course']['public_course'].split(",")
            else:
                config['Course']['public_course'] = ''
                BUPT.public_course_to_grab_list = []
            if required_courses_input := input("输入想要抢的必修课: "):
                config['Course']['required_course'] = required_courses_input.strip().replace(" ", ",")
                BUPT.required_course_to_grab_list = config['Course']['required_course'].split(",")
            else:
                config['Course']['required_course'] = ''
                BUPT.required_course_to_grab_list = []
            if optional_courses_input := input("输入想要抢的选修课："):
                config['Course']['optional_course'] = optional_courses_input.strip().replace(" ", ",")
                BUPT.optional_course_to_grab_list = config['Course']['optional_course'].split(",")
            else:
                config['Course']['optional_course'] = ''
                BUPT.optional_course_to_grab_list = []
        else:
            try:
                BUPT.public_course_to_grab_list = config['Course']["public_course"].split(",") if config['Course'][
                    "public_course"] else []
                BUPT.required_course_to_grab_list = config['Course']["required_course"].split(",") if config['Course'][
                    "required_course"] else []
                BUPT.optional_course_to_grab_list = config['Course']['optional_course'].split(",") if config['Course'][
                    "optional_course"] else []
            except Exception as e:
                logger.error("配置文件出现问题，请尝试删除配置文件并重新运行.")
                raise e
        # 写入配置文件
        with open('config.ini', 'w') as config_file_handle:
            config.write(config_file_handle)
        logger.info("待抢公选课:" + str(BUPT.public_course_to_grab_list))
        logger.info("待抢必修课:" + str(BUPT.required_course_to_grab_list))
        logger.info("待抢选修课:" + str(BUPT.optional_course_to_grab_list))
        logger.success("配置文件已更新")

    @staticmethod
    def login():
        """
            用于登录，并验证登录状态。

            Parameters:
            无

            Returns:
            session (requests.Session): 返回一个已经登录的requests.Session对象，可以用来进行后续的请求操作。
        """
        session = requests.Session()
        code = str(BUPT._username) + "%%%" + BUPT._password
        scode, sxh = session.post("https://jwgl.bupt.edu.cn/Logon.do?method=logon&flag=sess").text.split("#")
        encoded = ''
        for i in range(len(code)):
            if i < 20:
                encoded += code[i:i + 1] + scode[:int(sxh[i:i + 1])]
                scode = scode[int(sxh[i:i + 1]):]
            else:
                encoded += code[i:]
                break
        r = session.post("https://jwgl.bupt.edu.cn/Logon.do?method=logon", data={"encoded": encoded})
        if "选课" in r.text:
            logger.success("登录成功")
        return session

    @staticmethod
    def verify(session):
        r_stage_1 = session.get(
            "https://jwgl.bupt.edu.cn/jsxsd/xsxk/xsxk_index?jx0502zbid=7472D65463154EAEAC55ED73A6197E04")
        if "当前不在选课时间范围内" in r_stage_1.text:
            logger.error("当前不在选课第一阶段，尝试再次登录...")
            session.close()
            session_new = BUPT.login()
            r_stage_2 = session_new.get(
                "https://jwgl.bupt.edu.cn/jsxsd/xsxk/xsxk_index?jx0502zbid=F9CCB81B120B4BDAA52561C6A22489AE")
            if "当前不在选课时间范围内" in r_stage_2.text:
                logger.error("当前不在选课第二阶段，请检查是否在选课时间内！")
                raise Exception("不在选课时间内.")
            return session_new
        else:
            return session
        # TODO 这里不能同时打开，估计还要分别写一个逻辑，或者暂且就是选课第一阶段选择stage1，第二阶段选择stage2

    def verify_new(session):
        cookie_dict = {cookie.name: cookie.value for cookie in session.cookies}
        try:
            r_first = requests.get("https://jwgl.bupt.edu.cn/jsxsd/framework/xsrkxz.jsp", cookies=cookie_dict).text
            url_first = "https://jwgl.bupt.edu.cn/" + re.findall('<a href="(.*?)">进入选课</a>', r_first)[0]
            r_second = requests.get(url_first, cookies=cookie_dict).text
            url_second = "https://jwgl.bupt.edu.cn/" + re.findall('<a href="(.*?)".+>进入选课</a>', r_second)[0]
            requests.get(url_second, cookies=cookie_dict)
        except Exception as e:
            r_new = requests.get("https://jwgl.bupt.edu.cn/jsxsd/xsxk/xklc_list", cookies=cookie_dict).text
            url ="https://jwgl.bupt.edu.cn/"+ re.findall('<a.+href="(.*?)".+>进入选课</a>', r_new)[0]
            requests.get(url, cookies=cookie_dict)
        return session

    @staticmethod
    def login_with_verify():
        session = BUPT.login()
        try:
            session = BUPT.verify_new(session)
            return session
        except Exception as e:
            session = BUPT.verify(session)
            return session

    @staticmethod
    def choose_course(session, course_type, course_name: str):
        """
        选择课程。首先通过session获取课程列表。然后遍历课程列表，如果课程名称与输入的课程名称匹配，则将课程ID和jx0404id添加到相应的列表中。最后，如果找到匹配的课程,尝试选择课程。

        Parameters:
        session (requests.Session): 一个已经登录并可以发送请求的会话对象。
        course_type (str): 课程类型，已经封装好，后续能被三个choose函数调用
        course_name (str): 要选择的课程名称。

        Returns:
        bool: 如果成功选择了课程，返回True；否则返回False。
        """
        start = 0
        global total
        total = 0
        course_id = []
        course_jx0404id = []
        course_name_matched = []

        def bianli(start):
            response = session.post(url='https://jwgl.bupt.edu.cn/jsxsd/xsxkkc/' + course_type,
                                    params=BUPT.search_course_params_dic()[course_type],
                                    data=BUPT.search_course_data_dic(start)[course_type])
            # {"flag1":3,"msgContent":"您的账号在其它地方登录"}
            # TODO 处理账号再别处登录需要重置session
            if response.status_code != 200:
                logger.error(f"网页还未开启选课！ code={response.status_code} ({course_name})")
                return False
            else:
                try:
                    response.json()
                except Exception as e:
                    return False
                global total
            total = response.json()['iTotalRecords']
            # print(json.dumps(response.json(),indent=4,ensure_ascii=False))
            for item in response.json()["aaData"]:
                kcmc = item["kcmc"]
                kcid = item["jx02id"]
                jx0404id = item["jx0404id"]
                if course_name in kcmc:
                    course_name_matched.append(kcmc)
                    course_id.append(kcid)
                    course_jx0404id.append(jx0404id)
            return True

        # 如果解析出错，直接退出
        if not bianli(start):
            return False
        while start + 15 < total:
            start = start + 15
            bianli(start)

        if course_name_matched:
            logger.info(f"获取匹配课程名称:{course_name_matched}")
        else:
            logger.error(f"获取匹配课程名称失败，请检查是否有该课程！({course_name})")
            return
        params = (
            ('kcid', course_id[0]),
            ('cfbs', 'null'),
            ('jx0404id', course_jx0404id[0]),
            ('xkzy', ''),
            ('trjf', ''),
        )
        res = session.get(f'https://jwgl.bupt.edu.cn/jsxsd/xsxkkc/{course_type.replace("xsxk", "").lower()}Oper',
                          params=params)
        if res.json()["success"]:
            logger.success(res.json()["message"] + f"({course_name_matched[0]})")
            if "人数已满" in res.json()["message"]:
                return False
            return True
        else:
            logger.error(res.json()["message"] + f"({course_name_matched[0]})")
            return False

    @staticmethod
    def get_chosen_courses(session):
        """
        获取已选课程。

        Parameters:
        session (requests.Session): 一个已经登录并可以访问指定网址的requests.Session对象。

        Returns:
        dict: 返回一个字典，其中键是课程名称，值是课程对应的id。
        """
        html = session.get("https://jwgl.bupt.edu.cn/jsxsd/xsxkjg/comeXkjglb")
        soup = BeautifulSoup(html.text, 'html.parser')
        course_list = soup.find_all('tr')[1:]
        course_dic = {}
        for course in course_list:
            course_dic[course.find_all('td')[1].text] = course.find('div')['id'].replace('div_', '')
        return course_dic

    @staticmethod
    def get_chosen_course_id_by_name(session, course_name):
        """
        根据课程名称获取已选课程的ID。该函数接受一个会话和一个课程名称作为参数，通过查询BUPT.get_chosen_courses(session)获取已选课程字典，然后遍历字典查找包含指定课程名称的课程，如果找到则返回该课程及其ID，否则返回None。

        Parameters:
        session (obj): 一个会话对象，用于查询已选课程。
        course_name (str): 需要查询的课程名称。

        Returns:
        tuple: 如果找到匹配的课程，则返回一个元组，第一个元素是课程对象，第二个元素是课程ID；如果没有找到匹配的课程，则返回(None, None)。
        """
        course_chosen_dic = BUPT.get_chosen_courses(session)
        for course in course_chosen_dic:
            if course_name in course:
                return course, course_chosen_dic[course]
        return None, None

    @staticmethod
    def unchoose_course(session, *course_names):
        """
            该函数用于取消选择课程。它接受一个会话对象和一系列课程名称作为参数，然后通过会话对象向指定URL发送请求以取消选择这些课程。如果成功，将记录一条成功的日志信息；如果失败，将记录一条错误的日志信息。

            Parameters:
            session (obj): 一个会话对象，用于发送HTTP请求。
            *course_names (str): 一个或多个待取消选择的课程名称。

            Returns:
            None: 此函数没有返回值。

            Raises:
            Exception: 如果无法找到指定的课程或者退课失败，将会抛出异常。
        """
        for course_name in course_names:
            course_matched, jx0404id = BUPT.get_chosen_course_id_by_name(session, course_name)
            if not jx0404id or not course_matched:
                logger.error(f"推选失败！未找到课程({course_name}),请确定已选该课程")
            r = session.get("https://jwgl.bupt.edu.cn/jsxsd/xsxkjg/xstkOper", params={"jx0404id": jx0404id,
                                                                                      "tkyy": ""})
            try:
                if r.json()["success"]:
                    logger.success(f"退课成功!({course_matched})")
            except Exception as e:
                logger.error(f"退课失败!({course_matched})")

    @staticmethod
    def choose_required_course(session, course_name: str):
        """
        选择必修课程。

        Parameters:
        session (obj): 一个会话对象，用于与服务器进行交互。
        course_name (str): 需要选择的必修课程的名称。

        Returns:
        obj: 返回BUPT.choose_course方法的结果。
        """
        require_course_url = "xsxkBxxk"
        return BUPT.choose_course(session, require_course_url, course_name)

    @staticmethod
    def grab_required_course(session, course_name: str):
        """
            该函数用于抢选择必修课程。

            Parameters:
            session (obj): 一个会话对象，用于与服务器进行交互。
            course_name (str): 需要选择的必修课程的名称。

            Returns:
            None: 此函数没有返回值，但会改变session的状态。
        """
        flag = False
        while not flag:
            flag = BUPT.choose_required_course(session, course_name)

    @staticmethod
    def choose_optional_course(session, course_name: str):
        """
        选择选修课程。
        第一阶段选课会选择体育选修课，也是通过此方法，第二阶段选择专业选修课也是通过此方法。
        该函数接受一个会话和一个课程名称作为参数，然后通过BUPT.choose_course方法来选择必修课程。

        Parameters:
        session (obj): 一个会话对象，用于与服务器进行交互。
        course_name (str): 需要选择的选修课程的名称。

        Returns:
        obj: 返回BUPT.choose_course方法的结果。
        """
        optional_course_url = "xsxkXxxk"
        return BUPT.choose_course(session, optional_course_url, course_name)

    @staticmethod
    def grab_optional_course(session, course_name: str):
        """
            该函数用于抢选修课程。

            Parameters:
            session (obj): 一个会话对象，用于与服务器进行通信。
            course_name (str): 需要选择的课程的名称。

            Returns:
            bool: 如果成功选择了课程，则返回True，否则返回False。
            """
        flag = False
        while not flag:
            flag = BUPT.choose_optional_course(session, course_name)

    @staticmethod
    def choose_public_course(session, course_name: str):
        """
        选择公选课程。

        Parameters:
        session (obj): 一个会话对象，用于与服务器进行交互。
        course_name (str): 需要选择的课程的名称。

        Returns:
        obj: 返回BUPT.choose_course方法的返回值。
        """
        public_course_url = "xsxkGgxxkxk"
        return BUPT.choose_course(session, public_course_url, course_name)

    @staticmethod
    def grab_public_course(session, course_name: str):
        """
            该函数用于抢公共课程。

            Parameters:
            session (obj): 一个会话对象，用于与服务器进行交互。
            course_name (str): 需要抓取的公共课程的名称。

            Returns:
            None: 该函数没有返回值，但会改变全局状态。
        """
        flag = False
        while not flag:
            flag = BUPT.choose_public_course(session, course_name)

    @staticmethod
    def grab_all_course(session):
        """
            启动多线程分别抢在ini文件中已配置的所有课程。

            Parameters:
            session (obj): 一个会话对象，用于与服务器进行通信。

            Returns:
            None: 该函数没有返回值。
        """
        thread_list = []
        if BUPT.public_course_to_grab_list:
            for course in BUPT.public_course_to_grab_list:
                thread = threading.Thread(target=BUPT.grab_public_course, args=(session, course))
                thread.start()
                thread_list.append(thread)
        if BUPT.optional_course_to_grab_list:
            for course in BUPT.optional_course_to_grab_list:
                thread = threading.Thread(target=BUPT.grab_optional_course, args=(session, course))
                thread.start()
                thread_list.append(thread)
        if BUPT.required_course_to_grab_list:
            for course in BUPT.required_course_to_grab_list:
                thread = threading.Thread(target=BUPT.grab_required_course, args=(session, course))
                thread.start()
                thread_list.append(thread)
        for thread in thread_list:
            thread.join()

    # 当没抢到课的时候自动在有人退课的情况下秒抢并换课
    @staticmethod
    def grab_when_class_unoccupied(old_class_name, replace_class_name):
        """
        当旧的课有人退课时，将冲突的课马上退掉进行抢课。

        Parameters:
        old_class_name (str): 与你想选课冲突的课。
        replace_class_name (str): 想候补的课。

        Returns:
        无返回值。

        注意：此函数暂时用不上，可能在未来的版本中会被使用。（就是懒得写了）
        """
        # TODO 暂时用不上
        pass


if __name__ == '__main__':
    BUPT.init()
    session = BUPT.login()
    # BUPT.unchoose_course(session, "射电", "虚拟现实")
    BUPT.grab_all_course(session)
