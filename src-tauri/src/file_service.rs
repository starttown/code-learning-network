// src-tauri/src/file_service.rs
use crate::models::{DirectoryEntry, FileNode};
use std::fs;
use std::path::Path;

/// 文件系统服务
pub struct FileService;

impl FileService {
    /// 读取目录内容
    pub fn read_directory(path: &str) -> Result<Vec<DirectoryEntry>, String> {
        let dir_path = Path::new(path);

        // 检查路径是否存在且是目录
        if !dir_path.exists() {
            return Err("Path does not exist".to_string());
        }

        if !dir_path.is_dir() {
            return Err("Path is not a directory".to_string());
        }

        // 读取目录
        let entries =
            fs::read_dir(dir_path).map_err(|e| format!("Failed to read directory: {}", e))?;

        let mut result = Vec::new();

        for entry in entries {
            let entry = entry.map_err(|e| format!("Failed to read entry: {}", e))?;
            let file_path = entry.path();

            // 获取元数据
            let metadata = file_path
                .metadata()
                .map_err(|e| format!("Failed to get metadata: {}", e))?;

            let name = file_path
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("")
                .to_string();

            let is_directory = metadata.is_dir();
            let size = if is_directory {
                None
            } else {
                Some(metadata.len())
            };

            // let last_modified = metadata.modified()
            //     .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
            //     .map(|d| d.as_secs() as i64)
            //     .unwrap_or(0);
            let last_modified = 0;
            result.push(DirectoryEntry {
                name,
                path: file_path.to_string_lossy().to_string(),
                is_directory,
                size,
                last_modified,
            });
        }

        // 排序：目录优先，然后按名称
        result.sort_by(|a, b| {
            if a.is_directory && !b.is_directory {
                std::cmp::Ordering::Less
            } else if !a.is_directory && b.is_directory {
                std::cmp::Ordering::Greater
            } else {
                a.name.cmp(&b.name)
            }
        });

        Ok(result)
    }

    /// 获取文件图标类型
    pub fn get_file_icon(filename: &str, is_dir: bool) -> String {
        if is_dir {
            return "folder".to_string();
        }

        let ext = filename.split('.').last().unwrap_or("").to_lowercase();

        match ext.as_str() {
            "js" | "ts" => "code",
            "svelte" => "svelte",
            "json" => "json",
            "md" => "markdown",
            "css" => "style",
            "html" => "html",
            "png" | "jpg" | "svg" => "image",
            "pdf" => "pdf",
            _ => "file",
        }
        .to_string()
    }

    /// 转换为文件节点
    pub fn to_file_nodes(entries: Vec<DirectoryEntry>, depth: usize) -> Vec<FileNode> {
        entries
            .into_iter()
            .map(|entry| {
                let icon = Self::get_file_icon(&entry.name, entry.is_directory);
                let file_count = if entry.is_directory { Some(0) } else { None };

                FileNode {
                    id: entry.path.clone(),
                    name: entry.name,
                    path: entry.path,
                    is_directory: entry.is_directory,
                    children: None, // 懒加载，不立即加载子节点
                    depth,
                    icon: Some(icon),
                    file_count,
                    size: entry.size,
                    last_modified: Some(entry.last_modified),
                }
            })
            .collect()
    }
}
