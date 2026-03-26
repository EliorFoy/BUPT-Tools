// Copyright © BUPT Tool Team
// SPDX-License-Identifier: GPL-3.0

mod lib;

use lib::{BUPTTool, GrabResult, UserConfig};
use slint::{ComponentHandle, VecModel, SharedString};
use std::sync::mpsc;
use tokio::runtime::Runtime;

slint::include_modules!();

fn main() -> Result<(), slint::PlatformError> {
    let app = AppWindow::new()?;
    
    // 创建通道用于接收抢课结果
    let (tx, rx) = mpsc::channel::<GrabResult>();
    
    // 设置日志回调
    let log_model = app.get_global::<LogModel>().unwrap().clone();
    std::thread::spawn(move || {
        while let Ok(result) = rx.recv() {
            let timestamp = result.timestamp.format("%Y-%m-%d %H:%M:%S").to_string();
            let status = if result.success { "✓" } else { "✗" };
            let message = format!("[{}] {} - {}", timestamp, status, result.message);
            
            slint::invoke_from_event_loop(move || {
                log_model.push(message.into());
            }).ok();
        }
    });

    let app_handle = app.clone_strong();
    
    // 登录按钮点击事件
    let login_btn = app.get_global::<LoginActions>().unwrap();
    let username_input = app.get_property_username();
    let password_input = app.get_property_password();
    
    login_btn.on_login(move || {
        let username = username_input.to_string();
        let password = password_input.to_string();
        
        let tx_clone = tx.clone();
        std::thread::spawn(move || {
            let rt = Runtime::new().unwrap();
            rt.block_on(async {
                let config = UserConfig {
                    username,
                    password,
                    course_ids: vec![],
                    check_interval_ms: 100,
                    auto_submit: true,
                };
                
                let mut tool = BUPTTool::new(config).unwrap();
                match tool.login().await {
                    Ok(true) => {
                        slint::invoke_from_event_loop(move || {
                            app_handle.set_logged_in(true);
                            app_handle.set_status_message("登录成功".into());
                        }).ok();
                    }
                    Ok(false) | Err(_) => {
                        slint::invoke_from_event_loop(move || {
                            app_handle.set_status_message("登录失败".into());
                        }).ok();
                    }
                }
            });
        });
    });

    // 开始抢课按钮
    let start_btn = app.get_global::<GrabActions>().unwrap();
    let course_ids_str = app.get_property_course_ids();
    
    start_btn.on_start_grabbing(move || {
        let course_ids: Vec<String> = course_ids_str
            .split(',')
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .collect();
        
        let interval = app.get_property_check_interval() as u64;
        
        let tx_clone = tx.clone();
        std::thread::spawn(move || {
            let rt = Runtime::new().unwrap();
            rt.block_on(async {
                // 这里需要实现实际的抢课逻辑
                slint::invoke_from_event_loop(move || {
                    app_handle.set_grabbing(true);
                    app_handle.set_status_message("开始抢课...".into());
                }).ok();
            });
        });
    });

    // 停止抢课按钮
    let stop_btn = app.get_global::<GrabActions>().unwrap();
    stop_btn.on_stop_grabbing(move || {
        slint::invoke_from_event_loop(move || {
            app_handle.set_grabbing(false);
            app_handle.set_status_message("已停止抢课".into());
        }).ok();
    });

    app.run()?;
    Ok(())
}
