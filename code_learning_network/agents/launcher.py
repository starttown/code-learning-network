import sys
import os
import subprocess
import signal
import json
from pathlib import Path
from datetime import datetime

# ================= UTF-8 强制设置 =================

# 1. 强制当前 Python 进程使用 UTF-8 输出 (解决 print 乱码)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 2. 准备传递给子进程的环境变量 (解决子进程乱码)
ENV = os.environ.copy()
ENV["PYTHONIOENCODING"] = "utf-8"
ENV["PYTHONUTF8"] = "1"

# ================= 路径解析核心逻辑 =================

def resolve_openagents_path():
    """
    解析 openagents.exe 的路径。
    优先级：Python所在目录 > Python同级Scripts目录 > 上一级目录
    """
    python_dir = Path(sys.executable).parent.resolve()
    
    # 尝试 1: 与 python.exe 同级
    oa_path = python_dir / "openagents.exe"
    if oa_path.exists():
        return str(oa_path)
    
    # 尝试 2: Scripts 文件夹下 (常见于系统 Python)
    oa_path = python_dir / "Scripts" / "openagents.exe"
    if oa_path.exists():
        return str(oa_path)
    
    # 尝试 3: 上一级
    oa_path = python_dir.parent / "openagents.exe"
    if oa_path.exists():
        return str(oa_path)

    # 找不到则报错
    raise FileNotFoundError(
        f"找不到 openagents.exe。\n"
        f"已在以下位置搜索:\n"
        f"1. {python_dir}\n"
        f"2. {python_dir / 'Scripts'}\n"
        f"请确认 openagents.exe 是否已安装。"
    )

# 全局路径变量
try:
    OPENAGENTS_EXE = resolve_openagents_path()
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)

# 获取脚本所在目录
SCRIPT_DIR = Path(__file__).parent.resolve()
# 获取网络目录 (脚本目录的上一级)
NETWORK_DIR = SCRIPT_DIR.parent.resolve()
# 日志目录统一放在脚本同级下的 logs 文件夹
LOG_DIR = SCRIPT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ================= 进程管理类 =================

class ProcessManager:
    def __init__(self):
        self.processes = {} 
        self.info = []      

    def _get_log_path(self, name):
        """生成带时间戳的日志文件路径"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return LOG_DIR / f"{name}_{timestamp}.log"

    def start_network(self):
        """
        启动网络
        路径逻辑：上一层目录
        工作目录：上一层目录
        """
        # 关键逻辑：网络配置在上一级
        target_dir = NETWORK_DIR
        
        if not target_dir.exists():
            raise ValueError(f"网络目录不存在: {target_dir}")

        # 命令：openagents network start <path>
        cmd = [OPENAGENTS_EXE, "network", "start", str(target_dir)]
        log_file = self._get_log_path("network")
        
        proc = subprocess.Popen(
            cmd,
            cwd=str(target_dir), 
            stdout=open(log_file, "w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
            env=ENV  # <--- 关键：传入环境变量
        )
        
        self.processes["network"] = proc
        self.info.append({
            "type": "network",
            "pid": proc.pid,
            "log": str(log_file),
            "cwd": str(target_dir),
            "status": "running"
        })

    def start_agent(self, yaml_name: str):
        """
        启动 Agent (基于 YAML)
        路径逻辑：脚本同级目录
        工作目录：脚本同级目录
        """
        yaml_file = SCRIPT_DIR / yaml_name
        
        if not yaml_file.exists():
            raise ValueError(f"Agent 配置不存在: {yaml_file}")

        # 命令：openagents agent start <yaml_path>
        cmd = [OPENAGENTS_EXE, "agent", "start", str(yaml_file)]
        log_file = self._get_log_path(f"agent_{yaml_file.stem}")

        proc = subprocess.Popen(
            cmd,
            cwd=str(SCRIPT_DIR),
            stdout=open(log_file, "w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
            env=ENV  # <--- 关键：传入环境变量
        )

        self.processes[f"agent_{yaml_file.stem}"] = proc
        self.info.append({
            "type": "agent",
            "pid": proc.pid,
            "log": str(log_file),
            "cwd": str(SCRIPT_DIR),
            "status": "running"
        })

    def start_script(self, script_name: str):
        """
        运行 Python 脚本
        路径逻辑：脚本同级目录
        工作目录：脚本同级目录
        """
        target_script = SCRIPT_DIR / script_name
        
        if not target_script.exists():
            raise ValueError(f"脚本不存在: {target_script}")

        # 使用当前 Python 解释器运行
        cmd = [sys.executable, str(target_script)]
        log_file = self._get_log_path(f"script_{target_script.stem}")

        proc = subprocess.Popen(
            cmd,
            cwd=str(SCRIPT_DIR),
            stdout=open(log_file, "w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
            env=ENV  # <--- 关键：传入环境变量
        )

        self.processes[f"script_{target_script.stem}"] = proc
        self.info.append({
            "type": "script",
            "pid": proc.pid,
            "log": str(log_file),
            "cwd": str(SCRIPT_DIR),
            "status": "running"
        })

    def stop_all(self):
        """停止所有子进程"""
        for name, proc in self.processes.items():
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except:
                try:
                    proc.kill()
                except:
                    pass
        self.processes.clear()

    def get_status_json(self):
        """返回状态信息"""
        return json.dumps(self.info, ensure_ascii=False, indent=2)

# ================= 主入口 =================

manager = ProcessManager()

def cleanup(signum=None, frame=None):
    """退出信号处理"""
    print("\n[Manager] 收到退出信号，正在清理所有子进程...")
    manager.stop_all()
    print("[Manager] 清理完毕。")
    sys.exit(0)

# 注册信号处理
signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

if __name__ == "__main__":
    # 参数检查: python launcher.py all
    if len(sys.argv) < 2:
        print("Usage: python launcher.py <all>")
        sys.exit(1)

    cmd_type = sys.argv[1]

    try:
        # 打印关键路径，方便调试
        print(f"[Info] OpenAgents Executable: {OPENAGENTS_EXE}")
        print(f"[Info] Script Dir (Agents): {SCRIPT_DIR}")
        print(f"[Info] Network Dir (Parent): {NETWORK_DIR}")
        print(f"[Info] Log Dir: {LOG_DIR}")

        if cmd_type == "all":
            print("-" * 30)
            
            # 1. 启动网络 (上一级目录)
            manager.start_network()
            print(f"[Action] 已启动 Network -> {NETWORK_DIR}")

            # 2. 启动 Agent (YAML) (当前目录)
            manager.start_agent("code-navigator.yaml")
            print(f"[Action] 已启动 Agent -> code-navigator.yaml")

            # 3. 启动 Script (Python) (当前目录)
            manager.start_script("code-connector.py")
            print(f"[Action] 已启动 Script -> code-connector.py")
            
            print("-" * 30)
            print("[Manager] 所有程序已启动，守护中...")
            
        else:
            print(f"未知命令: {cmd_type}，目前仅支持 'all'")
            sys.exit(1)

        # 输出状态给 Tauri (通过特殊标记提取)
        print("<<<START_INFO>>>")
        print(manager.get_status_json())
        print("<<<END_INFO>>>")

        # 保持挂起，充当守护进程
        while True:
            pass

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("<<<START_INFO>>>")
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        print("<<<END_INFO>>>")
        sys.exit(1)
