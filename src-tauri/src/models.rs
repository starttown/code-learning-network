// src-tauri/src/models.rs
use serde::{Deserialize, Serialize};
use std::fmt;

/// 文件节点数据结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileNode {
    pub id: String,                      // 唯一标识 (路径)
    pub name: String,                    // 文件名
    pub path: String,                    // 完整路径
    pub is_directory: bool,              // 是否目录
    pub children: Option<Vec<FileNode>>, // 子节点 (懒加载时为 None)
    pub depth: usize,                    // 深度
    pub icon: Option<String>,            // 图标类型
    pub file_count: Option<usize>,       // 文件数
    pub size: Option<u64>,               // 文件大小
    pub last_modified: Option<i64>,      // 最后修改时间
}

/// 目录读取结果
#[derive(Debug, Serialize, Deserialize)]
pub struct DirectoryEntry {
    pub name: String,
    pub path: String,
    pub is_directory: bool,
    pub size: Option<u64>,
    pub last_modified: i64,
}

// 实现 Display trait
impl fmt::Display for DirectoryEntry {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let type_str = if self.is_directory { "DIR " } else { "FILE" };
        let size_str = match self.size {
            Some(size) => format_size(size),
            None => "N/A".to_string(),
        };

        write!(
            f,
            "[{}] {:<30} {:>10} | {}",
            type_str, self.name, size_str, self.path
        )
    }
}

// 格式化文件大小
fn format_size(size: u64) -> String {
    const UNITS: [&str; 5] = ["B", "KB", "MB", "GB", "TB"];
    let mut size = size as f64;
    let mut unit_index = 0;

    while size >= 1024.0 && unit_index < UNITS.len() - 1 {
        size /= 1024.0;
        unit_index += 1;
    }

    format!("{:.2} {}", size, UNITS[unit_index])
}

// 打印整个 Vec
pub fn print_directory_entries(entries: &[DirectoryEntry]) {
    println!("=== Directory Entries ===");
    println!();

    for entry in entries {
        println!("{}", entry);
    }

    println!();
    println!("Total: {} entries", entries.len());
}

impl FileNode {
    /// 递归打印节点及其子节点（树形结构）
    pub fn print_tree(&self) {
        self._print_tree_recursive(true, "");
    }

    /// 内部递归函数
    fn _print_tree_recursive(&self, is_last: bool, prefix: &str) {
        // 1. 打印连接符和当前节点
        let connector = if is_last { "└── " } else { "├── " };
        let icon = self.get_icon_str();

        println!("{}{}{} ({})", prefix, connector, icon, self.name);

        // 2. 准备子节点的前缀
        let children_prefix = format!("{}{}", prefix, if is_last { "    " } else { "│   " });

        // 3. 递归打印子节点
        if let Some(children) = &self.children {
            let count = children.len();
            for (index, child) in children.iter().enumerate() {
                let is_last_child = index == count - 1;
                child._print_tree_recursive(is_last_child, &children_prefix);
            }
        }
    }

    /// 获取图标字符串（根据 icon 字段或类型）
    fn get_icon_str(&self) -> &'static str {
        if let Some(icon_name) = &self.icon {
            match icon_name.as_str() {
                "folder" => "📁",
                "folder-open" => "📂",
                "file" => "📄",
                "code" => "📜",
                "image" => "🖼️",
                _ => "📝",
            }
        } else if self.is_directory {
            "📁"
        } else {
            "📄"
        }
    }
}

/// 打印整个 Vec<FileNode>（通常是根节点列表）
pub fn print_file_nodes(nodes: &[FileNode]) {
    if nodes.is_empty() {
        println!("(空目录)");
        return;
    }

    println!("📂 文件树结构:");
    let count = nodes.len();
    for (index, node) in nodes.iter().enumerate() {
        let is_last = index == count - 1;
        node._print_tree_recursive(is_last, "");
    }
}
