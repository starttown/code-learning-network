use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use tauri::{AppHandle, Emitter, Manager};

// 1. 定义配置结构体
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AppConfig {
    pub python_path: String,
    // 可以在这里添加其他配置项，例如：
    // pub theme: String,
    // pub window_width: u32,
}

// 默认配置
impl Default for AppConfig {
    fn default() -> Self {
        Self {
            python_path: String::new(),
        }
    }
}

// 获取配置文件路径
fn get_config_path(app: &AppHandle) -> Result<PathBuf, String> {
    let config_dir = app
        .path()
        .config_dir()
        .map_err(|e| format!("无法获取配置目录: {}", e))?;

    let app_specific_dir = config_dir.join("code-learning-tool");

    println!("配置目录路径: {:?}", app_specific_dir);
    // 确保目录存在
    fs::create_dir_all(&app_specific_dir).map_err(|e| format!("无法创建配置目录: {}", e))?;
    Ok(app_specific_dir.join("config.json"))
}

// 读取配置
#[tauri::command]
pub async fn get_config(app: AppHandle) -> Result<AppConfig, String> {
    let config_path = get_config_path(&app)?;

    if !config_path.exists() {
        return Ok(AppConfig::default());
    }

    let content =
        fs::read_to_string(&config_path).map_err(|e| format!("读取配置文件失败: {}", e))?;

    serde_json::from_str(&content).map_err(|e| format!("解析配置文件失败: {}", e))
}

// 保存配置
#[tauri::command]
pub async fn save_config(app: AppHandle, config: AppConfig) -> Result<(), String> {
    let config_path = get_config_path(&app)?;

    let content =
        serde_json::to_string_pretty(&config).map_err(|e| format!("序列化配置失败: {}", e))?;

    fs::write(&config_path, content).map_err(|e| format!("写入配置文件失败: {}", e))?;

    // 关键点：保存成功后，向所有窗口广播事件
    app.emit("config-updated", &config)
        .map_err(|e| format!("发送更新事件失败: {}", e))?;

    Ok(())
}
