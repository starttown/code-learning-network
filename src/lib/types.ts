export interface FileNode {
  id: string;
  name: string;
  path: string;
  is_directory: boolean;
  children?: FileNode[];
  is_expanded?: boolean;
  is_loading?: boolean;
}

export interface AppConfig {
  python_path: string;
}

export interface DragFileInfo {
  path: string;
  name: string;
  type: 'file' | 'directory';
  timestamp?: number;
  size?: number;
}

