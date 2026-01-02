// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
use tauri::{AppHandle, Emitter, Manager};
use tauri_plugin_dialog::DialogExt;
mod commands;
mod config;
mod file_service;
mod models;
use commands::{get_file_info, read_directory, search_files, watch_directory};
use config::{get_config, save_config};
use std::{thread, time};
use tauri::image::Image;
use tauri::menu::{CheckMenuItemBuilder, IconMenuItemBuilder, MenuBuilder, SubmenuBuilder};

// #[tauri::command]
// fn openfile(app: AppHandle) -> () {
//     let file_path = app.dialog().file().blocking_pick_folder();
//     if let Some(path) = file_path {
//         println!("Selected folder: {:?}", path);
//         let ret = commands::read_directory(path.to_string());
//         println!("Directory read result: {:?}", path);
//         // match ret {
//         //     Ok(nodes) => {
//         //         for node in nodes {
//         //             println!("{:?}", node);
//         //         }
//         //     },
//         //     Err(e) => {
//         //         println!("Error reading directory: {}", e);
//         //     }
//         // }
//     } else {
//         println!("No folder selected");
//     }
// }

#[tauri::command]
async fn read_file_content(path: String) -> Result<String, String> {
    use std::fs;
    use std::path::Path;

    // 简单的安全检查
    if path.contains("..") {
        return Err("Invalid path".to_string());
    }

    fs::read_to_string(&path).map_err(|e| e.to_string())
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // .setup(|app| {
        //     let file_menu = SubmenuBuilder::new(app, "File")
        //         .text("open", "Open")
        //         .text("quit", "Quit")
        //         .build()?;
        //     app.on_menu_event(move |app_handle: &tauri::AppHandle, event| {
        //         println!("menu event: {:?}", event.id());
        //         match event.id().0.as_str() {
        //             "open" => {
        //                 println!("open event");
        //                 openfile(app_handle.clone());
        //             }
        //             "close" => {
        //                 println!("close event");
        //             }
        //             _ => {
        //                 println!("unexpected menu event");
        //             }
        //         }
        //     });
        //     // let lang_str = "en";
        //     // let check_sub_item_1 = CheckMenuItemBuilder::new("English")
        //     //     .id("en")
        //     //     .checked(lang_str == "en")
        //     //     .build(app)?;
        //     // let check_sub_item_2 = CheckMenuItemBuilder::new("Chinese")
        //     //     .id("en")
        //     //     .checked(lang_str == "en")
        //     //     .enabled(false)
        //     //     .build(app)?;
        //     // // 从路径加载图标
        //     // let icon_image = Image::from_bytes(include_bytes!("../icons/icon.png")).unwrap();
        //     // let icon_item = IconMenuItemBuilder::new("icon")
        //     //     .icon(icon_image)
        //     //     .build(app)?;
        //     // let other_item = SubmenuBuilder::new(app, "language")
        //     //     .item(&check_sub_item_1)
        //     //     .item(&check_sub_item_2)
        //     //     .build()?;
        //     let menu = MenuBuilder::new(app).items(&[&file_menu]).build()?;
        //     app.set_menu(menu)?;
        //     Ok(())
        // })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                // 检查是否是主窗口（label 默认通常是 "main"，也可以在 tauri.conf.json 中配置）
                if window.label() == "main" {
                    // thread::sleep(time::Duration::from_millis(50));
                    // 调用 exit(0) 会干净地退出程序，所有窗口都会随之关闭
                    window.app_handle().exit(0);
                }
            }
        })
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_shell::init()) 
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            commands::read_directory,
            read_file_content,
            config::get_config,
            config::save_config,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
