// Copyright © BUPT Tool Team
// SPDX-License-Identifier: GPL-3.0

use anyhow::{Context, Result};
use chrono::{DateTime, Local};
use reqwest::cookie::CookieStore;
use reqwest::{Client, Cookie, StatusCode};
use scraper::{Html, Selector};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;

/// 北邮教务系统配置
pub mod config {
    // 注意：以下 URL 需要根据北邮教务系统的实际接口进行调整
    // 请通过浏览器开发者工具 (F12) 抓包获取真实的 API 端点
    
    /// 登录页面 URL
    pub const LOGIN_URL: &str = "https://jwxt.bupt.edu.cn/";
    
    /// 登录 API 端点 (需要替换为真实值)
    /// 通常是通过 F12 查看登录表单提交的地址
    pub const LOGIN_API: &str = "https://jwxt.bupt.edu.cn/sys/login.do";
    
    /// 课程列表 API 端点 (需要替换为真实值)
    /// 可能是 HTML 页面或 JSON API
    pub const COURSES_URL: &str = "https://jwxt.bupt.edu.cn/xs/kcxs.html";
    
    /// 抢课 API 端点 (需要替换为真实值)
    /// 通常是选课表单提交的地址
    pub const GRAB_API_PREFIX: &str = "https://jwxt.bupt.edu.cn/xs/xk.do";
    
    /// 用户代理
    pub const USER_AGENT: &str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
}

/// 用户配置信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserConfig {
    pub username: String,
    pub password: String,
    pub course_ids: Vec<String>,
    pub check_interval_ms: u64,
    pub auto_submit: bool,
}

impl Default for UserConfig {
    fn default() -> Self {
        Self {
            username: String::new(),
            password: String::new(),
            course_ids: Vec::new(),
            check_interval_ms: 100,
            auto_submit: true,
        }
    }
}

/// 课程信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CourseInfo {
    pub id: String,
    pub name: String,
    pub teacher: String,
    pub time: String,
    pub location: String,
    pub capacity: usize,
    pub enrolled: usize,
    pub status: CourseStatus,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CourseStatus {
    Available,
    Full,
    Closed,
    Unknown,
}

/// 抢课结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GrabResult {
    pub success: bool,
    pub course_id: String,
    pub message: String,
    pub timestamp: DateTime<Local>,
}

/// 认证管理器
pub struct AuthManager {
    client: Client,
    session_cookie: Arc<Mutex<Option<String>>>,
}

impl AuthManager {
    pub fn new() -> Result<Self> {
        let client = Client::builder()
            .user_agent(config::USER_AGENT)
            .cookie_store(true)
            .gzip(true)
            .build()
            .context("Failed to create HTTP client")?;

        Ok(Self {
            client,
            session_cookie: Arc::new(Mutex::new(None)),
        })
    }

    /// 登录到北邮教务系统
    pub async fn login(&self, username: &str, password: &str) -> Result<bool> {
        // 首先获取登录页面以获取可能的 CSRF token
        let login_page = self.client
            .get(config::LOGIN_URL)
            .send()
            .await
            .context("Failed to fetch login page")?;
        
        // 提取可能的 CSRF token (如果有的话)
        let csrf_token = self.extract_csrf_token(&login_page.text().await?).unwrap_or_default();
        
        // 构建登录请求参数
        // 注意：参数名称需要根据实际表单字段调整
        let mut params = vec![
            ("username", username.to_string()),
            ("password", password.to_string()),
        ];
        
        if !csrf_token.is_empty() {
            params.push(("token", csrf_token));
        }
        
        let response = self.client
            .post(config::LOGIN_API)
            .form(&params)
            .send()
            .await
            .context("Login request failed")?;

        if response.status() == StatusCode::OK {
            // 检查是否登录成功
            let cookies = response.cookies().collect::<Vec<_>>();
            if !cookies.is_empty() {
                let cookie_str = cookies
                    .iter()
                    .map(|c| format!("{}={}", c.name(), c.value()))
                    .collect::<Vec<_>>()
                    .join("; ");
                
                *self.session_cookie.lock().await = Some(cookie_str);
                return Ok(true);
            }
            
            // 有些系统可能通过响应内容判断登录成功
            let text = response.text().await?;
            if text.contains("欢迎") || text.contains("个人中心") || text.contains(username) {
                return Ok(true);
            }
        }

        Ok(false)
    }
    
    /// 提取 CSRF token (如果存在)
    fn extract_csrf_token(&self, html: &str) -> Option<String> {
        let document = Html::parse_document(html);
        
        // 尝试查找常见的 CSRF token 字段名
        let token_selectors = [
            r#"input[name="_csrf"]"#,
            r#"input[name="csrf_token"]"#,
            r#"input[name="token"]"#,
            r#"input[name="_token"]"#,
        ];
        
        for selector_str in token_selectors {
            if let Ok(selector) = Selector::parse(selector_str) {
                if let Some(element) = document.select(&selector).next() {
                    if let Some(value) = element.value().attr("value") {
                        return Some(value.to_string());
                    }
                }
            }
        }
        
        None
    }

    /// 获取会话状态
    pub async fn is_logged_in(&self) -> bool {
        self.session_cookie.lock().await.is_some()
    }

    /// 获取客户端实例
    pub fn client(&self) -> &Client {
        &self.client
    }
}

/// 课程抓取器
pub struct CourseGrabber {
    auth_manager: Arc<AuthManager>,
}

impl CourseGrabber {
    pub fn new(auth_manager: Arc<AuthManager>) -> Self {
        Self { auth_manager }
    }

    /// 获取课程列表
    pub async fn get_courses(&self) -> Result<Vec<CourseInfo>> {
        let client = self.auth_manager.client();

        let response = client
            .get(config::COURSES_URL)
            .send()
            .await
            .context("Failed to fetch courses")?;

        if !response.status().is_success() {
            anyhow::bail!("Failed to fetch courses: {}", response.status());
        }

        // 解析课程列表
        let html = response.text().await?;
        self.parse_course_list(&html)
    }

    /// 解析课程列表 HTML
    fn parse_course_list(&self, html: &str) -> Result<Vec<CourseInfo>> {
        let document = Html::parse_document(html);
        let mut courses = Vec::new();
        
        // 注意：以下选择器需要根据实际 HTML 结构调整
        // 使用浏览器 F12 查看课程列表的 HTML 结构，然后调整这些选择器
        
        // 示例：假设课程列表在表格中
        // 实际的 class 名称和结构需要替换
        let row_selector = Selector::parse("table.course-list tr.data-row").unwrap_or_else(|_| {
            Selector::parse("tr").unwrap()
        });
        
        for row in document.select(&row_selector) {
            // 尝试提取课程信息
            // 根据实际的列顺序调整索引
            
            let cells: Vec<_> = row.select(&Selector::parse("td").unwrap()).collect();
            
            if cells.len() < 5 {
                continue; // 跳过无效行
            }
            
            // 提取课程 ID (可能在某个属性中或特定列)
            let course_id = cells.get(0)
                .and_then(|cell| cell.value().attr("data-id"))
                .or_else(|| cells.get(0).map(|cell| cell.text().collect::<String>().trim().to_string()))
                .unwrap_or_default();
            
            if course_id.is_empty() {
                continue;
            }
            
            // 提取课程名称
            let name = cells.get(1)
                .map(|cell| cell.text().collect::<String>().trim().to_string())
                .unwrap_or_default();
            
            // 提取教师
            let teacher = cells.get(2)
                .map(|cell| cell.text().collect::<String>().trim().to_string())
                .unwrap_or_default();
            
            // 提取时间
            let time = cells.get(3)
                .map(|cell| cell.text().collect::<String>().trim().to_string())
                .unwrap_or_default();
            
            // 提取地点
            let location = cells.get(4)
                .map(|cell| cell.text().collect::<String>().trim().to_string())
                .unwrap_or_default();
            
            // 提取容量和已选人数
            let capacity_text = cells.get(5)
                .map(|cell| cell.text().collect::<String>().trim().to_string())
                .unwrap_or_default();
            
            let enrolled_text = cells.get(6)
                .map(|cell| cell.text().collect::<String>().trim().to_string())
                .unwrap_or_default();
            
            // 解析数字
            let capacity: usize = capacity_text.parse().unwrap_or(0);
            let enrolled: usize = enrolled_text.parse().unwrap_or(0);
            
            // 判断课程状态
            let status = if cells.iter().any(|cell| {
                cell.text().any(|text| text.contains("已满") || text.contains("关闭"))
            }) {
                CourseStatus::Full
            } else if capacity > 0 && enrolled >= capacity {
                CourseStatus::Full
            } else if capacity > 0 {
                CourseStatus::Available
            } else {
                CourseStatus::Unknown
            };
            
            courses.push(CourseInfo {
                id: course_id,
                name,
                teacher,
                time,
                location,
                capacity,
                enrolled,
                status,
            });
        }
        
        // 如果没有找到课程，尝试其他可能的 HTML 结构
        if courses.is_empty() {
            // 尝试查找 JSON 数据嵌入在页面中
            if let Some(json_data) = self.extract_json_from_html(html) {
                return self.parse_course_json(&json_data);
            }
        }
        
        Ok(courses)
    }
    
    /// 从 HTML 中提取嵌入的 JSON 数据
    fn extract_json_from_html(&self, html: &str) -> Option<String> {
        // 尝试查找类似 <script id="course-data" type="application/json">...</script>
        let json_pattern = regex::Regex::new(r#"<script[^>]*type=["']application/json["'][^>]*>([\s\S]*?)</script>"#).ok()?;
        
        json_pattern.captures(html)
            .and_then(|cap| cap.get(1))
            .map(|m| m.as_str().to_string())
    }
    
    /// 解析 JSON 格式的课程数据
    fn parse_course_json(&self, json_str: &str) -> Result<Vec<CourseInfo>> {
        // 尝试直接解析为课程数组
        #[derive(Deserialize)]
        struct JsonCourse {
            #[serde(default)]
            id: String,
            #[serde(default)]
            name: String,
            #[serde(default, alias = "teacherName", alias = "instructor")]
            teacher: String,
            #[serde(default, alias = "classTime", alias = "schedule")]
            time: String,
            #[serde(default, alias = "location", alias = "room")]
            location: String,
            #[serde(default, alias = "maxCapacity", alias = "total")]
            capacity: Option<usize>,
            #[serde(default, alias = "currentEnrollment", alias = "selected")]
            enrolled: Option<usize>,
            #[serde(default, alias = "status")]
            available: Option<bool>,
        }
        
        // 尝试解析为数组
        if let Ok(courses_vec) = serde_json::from_str::<Vec<JsonCourse>>(json_str) {
            return Ok(courses_vec.into_iter().map(|c| {
                let status = if c.available.unwrap_or(true) {
                    if let (Some(cap), Some(enr)) = (c.capacity, c.enrolled) {
                        if enr >= cap { CourseStatus::Full } else { CourseStatus::Available }
                    } else {
                        CourseStatus::Unknown
                    }
                } else {
                    CourseStatus::Closed
                };
                
                CourseInfo {
                    id: c.id,
                    name: c.name,
                    teacher: c.teacher,
                    time: c.time,
                    location: c.location,
                    capacity: c.capacity.unwrap_or(0),
                    enrolled: c.enrolled.unwrap_or(0),
                    status,
                }
            }).collect())
        }
        
        // 尝试解析为对象包含 courses 字段
        #[derive(Deserialize)]
        struct JsonWrapper {
            courses: Option<Vec<JsonCourse>>,
            data: Option<Vec<JsonCourse>>,
        }
        
        if let Ok(wrapper) = serde_json::from_str::<JsonWrapper>(json_str) {
            if let Some(courses_vec) = wrapper.courses.or(wrapper.data) {
                return Ok(courses_vec.into_iter().map(|c| {
                    let status = if c.available.unwrap_or(true) {
                        if let (Some(cap), Some(enr)) = (c.capacity, c.enrolled) {
                            if enr >= cap { CourseStatus::Full } else { CourseStatus::Available }
                        } else {
                            CourseStatus::Unknown
                        }
                    } else {
                        CourseStatus::Closed
                    };
                    
                    CourseInfo {
                        id: c.id,
                        name: c.name,
                        teacher: c.teacher,
                        time: c.time,
                        location: c.location,
                        capacity: c.capacity.unwrap_or(0),
                        enrolled: c.enrolled.unwrap_or(0),
                        status,
                    }
                }).collect())
            }
        }
        
        Ok(Vec::new())
    }

    /// 抢课
    pub async fn grab_course(&self, course_id: &str) -> Result<GrabResult> {
        let client = self.auth_manager.client();
        
        // 首先获取选课页面以获取可能的 CSRF token
        let course_page_url = format!("{}?courseId={}", config::GRAB_API_PREFIX, course_id);
        let page_response = client
            .get(&course_page_url)
            .send()
            .await
            .context("Failed to fetch course page")?;
        
        let page_html = page_response.text().await?;
        let csrf_token = self.extract_csrf_token(&page_html);
        
        // 构建抢课请求
        let mut params = vec![
            ("courseId", course_id.to_string()),
            ("action", "select".to_string()),
        ];
        
        if let Some(token) = csrf_token {
            params.push(("token", token));
        }
        
        let response = client
            .post(config::GRAB_API_PREFIX)
            .form(&params)
            .send()
            .await
            .context("Failed to grab course")?;

        let status = response.status();
        let response_text = response.text().await?;
        
        // 判断是否成功
        let success = status.is_success() || 
                      response_text.contains("成功") || 
                      response_text.contains("选课成功") ||
                      response_text.contains("selected successfully");
        
        let message = if success {
            format!("Successfully grabbed course {}", course_id)
        } else {
            // 尝试提取错误信息
            let error_msg = self.extract_error_message(&response_text)
                .unwrap_or_else(|| format!("Failed with status: {}", status));
            format!("Failed to grab course {}: {}", course_id, error_msg)
        };

        Ok(GrabResult {
            success,
            course_id: course_id.to_string(),
            message,
            timestamp: Local::now(),
        })
    }
    
    /// 从响应中提取错误信息
    fn extract_error_message(&self, html: &str) -> Option<String> {
        let document = Html::parse_document(html);
        
        // 尝试查找常见的错误信息位置
        let error_selectors = [
            r#".error-message"#,
            r#".alert-danger"#,
            r#".error"#,
            r#"#error-msg"#,
            r#"[class*="error"]"#,
        ];
        
        for selector_str in error_selectors {
            if let Ok(selector) = Selector::parse(selector_str) {
                if let Some(element) = document.select(&selector).next() {
                    let msg = element.text().collect::<String>().trim().to_string();
                    if !msg.is_empty() {
                        return Some(msg);
                    }
                }
            }
        }
        
        // 尝试从 script 标签中提取 alert 消息
        let alert_pattern = regex::Regex::new(r#"alert\s*\(\s*['"]([^'"]+)['"]\s*\)"#).ok()?;
        if let Some(cap) = alert_pattern.captures(html) {
            if let Some(msg) = cap.get(1) {
                return Some(msg.as_str().to_string());
            }
        }
        
        None
    }
}

/// 主入口类
pub struct BUPTTool {
    config: UserConfig,
    auth_manager: Arc<AuthManager>,
    grabber: Option<CourseGrabber>,
}

impl BUPTTool {
    pub fn new(config: UserConfig) -> Result<Self> {
        let auth_manager = Arc::new(AuthManager::new()?);
        
        Ok(Self {
            config,
            auth_manager,
            grabber: None,
        })
    }

    /// 登录
    pub async fn login(&mut self) -> Result<bool> {
        let success = self.auth_manager
            .login(&self.config.username, &self.config.password)
            .await?;

        if success {
            self.grabber = Some(CourseGrabber::new(Arc::clone(&self.auth_manager)));
        }

        Ok(success)
    }

    /// 检查登录状态
    pub async fn is_logged_in(&self) -> bool {
        self.auth_manager.is_logged_in().await
    }

    /// 获取课程列表
    pub async fn get_courses(&self) -> Result<Vec<CourseInfo>> {
        match &self.grabber {
            Some(grabber) => grabber.get_courses().await,
            None => anyhow::bail!("Not logged in"),
        }
    }

    /// 开始抢课循环
    pub async fn start_grabbing<F>(&self, on_result: F) -> Result<()>
    where
        F: Fn(GrabResult) + Send + Sync + 'static,
    {
        let grabber = match &self.grabber {
            Some(g) => g,
            None => anyhow::bail!("Not logged in"),
        };

        let course_ids = self.config.course_ids.clone();
        let interval = self.config.check_interval_ms;
        let grabber = Arc::new(grabber.clone());

        tokio::spawn(async move {
            loop {
                for course_id in &course_ids {
                    match grabber.grab_course(course_id).await {
                        Ok(result) => on_result(result),
                        Err(e) => {
                            let error_result = GrabResult {
                                success: false,
                                course_id: course_id.clone(),
                                message: e.to_string(),
                                timestamp: Local::now(),
                            };
                            on_result(error_result);
                        }
                    }
                }
                tokio::time::sleep(tokio::time::Duration::from_millis(interval)).await;
            }
        });

        Ok(())
    }

    /// 更新配置
    pub fn update_config(&mut self, config: UserConfig) {
        self.config = config;
    }

    /// 获取当前配置
    pub fn get_config(&self) -> &UserConfig {
        &self.config
    }
}
