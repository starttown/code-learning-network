// src-tauri/src/commands.rs

use crate::file_service::FileService;
use crate::models::FileNode;
use crate::models::print_directory_entries;
use crate::models::print_file_nodes;

#[tauri::command]
pub fn read_directory(path: String) -> Result<Vec<FileNode>, String> {

    // 1. 读取目录内容
    let entries = FileService::read_directory(&path)?;

    print_directory_entries(&entries);

    // 2. 转换为文件节点
    let nodes = FileService::to_file_nodes(entries, 0);

    print_file_nodes(&nodes);

    Ok(nodes)
}

#[tauri::command]
pub async fn get_file_info(path: String) -> Result<FileNode, String> {
    // 实现获取单个文件信息
    todo!()
}

#[tauri::command]
pub async fn watch_directory(path: String) -> Result<(), String> {
    // 实现目录监听
    todo!()
}

#[tauri::command]
pub async fn search_files(
    path: String, 
    query: String
) -> Result<Vec<FileNode>, String> {
    // 实现文件搜索
    todo!()
}
