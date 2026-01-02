#!/usr/bin/env python3
"""
Code Analyzer Agent - Python-based agent that receives code files and posts analysis requests to the network.
"""

import asyncio
import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from openagents.agents.worker_agent import WorkerAgent


class HTTPMessageHandler(BaseHTTPRequestHandler):
    """HTTP request handler for receiving code analysis requests."""

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def do_POST(self):
        """Handle POST requests containing code files for analysis."""
        if self.path == '/analyze':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                filename = data.get('filename', '')
                content = data.get('content', '')

                print(f"📨 收到分析请求: {filename} ({len(content)} bytes)")

                # 【关键修复】使用 run_coroutine_threadsafe 安全地将数据推送到 asyncio 队列
                # 因为 HTTP 服务器运行在独立线程，不能直接 await 协程
                future = asyncio.run_coroutine_threadsafe(
                    self.server.agent_queue.put({
                        'type': 'analysis_request',
                        'filename': filename,
                        'content': content,
                        'metadata': data.get('metadata', {})
                    }),
                    self.server.loop
                )
                # 可以选择等待结果确认（可选）
                future.result(timeout=1.0)

                # Send response
                response = {'status': 'success', 'filename': filename}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))

            except Exception as e:
                print(f"❌ 处理请求错误: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        """Handle GET requests - health check."""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'agent': 'code-analyzer'}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


class CodeAnalyzerAgent(WorkerAgent):
    """
    A code analyzer agent that receives code files via HTTP and posts analysis requests to the network.
    """

    default_agent_id = "code-analyzer"

    def __init__(self, http_port: int = 8888, **kwargs):
        """
        Initialize the code analyzer agent.

        Args:
            http_port: Port for HTTP server (default 8888)
        """
        super().__init__(**kwargs)
        self.http_port = http_port
        self.http_server = None
        self._http_thread = None
        self._message_processor_task = None
        self.message_queue = None
        self.loop = None  # 【新增】保存主事件循环的引用

    async def on_startup(self):
        """Called when agent starts and connects to the network."""
        print(f"🚀 Code Analyzer connected! Starting HTTP server on port {self.http_port}")

        # 【新增】获取当前运行的事件循环引用
        self.loop = asyncio.get_running_loop()

        # Create queue for analysis requests
        self.message_queue = asyncio.Queue()

        # Start HTTP server in separate thread
        def run_server():
            server = HTTPServer(('localhost', self.http_port), self._make_handler_class())
            server.agent_queue = self.message_queue
            server.loop = self.loop  # 【新增】将循环引用传递给 HTTP 服务器实例
            server.serve_forever()

        self._http_thread = Thread(target=run_server, daemon=True)
        self._http_thread.start()
        print(f"📡 HTTP 服务器运行在 http://localhost:{self.http_port}")
        print(f"📨 POST /analyze 发送代码分析请求")
        print(f"❤️ GET /health 健康检查")

        # Start message processor task
        self._message_processor_task = asyncio.create_task(self._process_requests())

    def _make_handler_class(self):
        """Create a handler class with access to agent queue."""
        class Handler(HTTPMessageHandler):
            pass
        return Handler

    async def on_shutdown(self):
        """Called when agent shuts down."""
        if self._message_processor_task:
            self._message_processor_task.cancel()
            try:
                await self._message_processor_task
            except asyncio.CancelledError:
                pass

        if self.http_server:
            self.http_server.shutdown()

        print("👋 Code Analyzer disconnected.")

    async def _process_requests(self):
        """Process analysis requests from HTTP queue."""
        while True:
            try:
                request_data = await self.message_queue.get()
                await self._post_analysis_request(request_data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ 处理分析请求错误: {e}")

    async def _post_analysis_request(self, request_data: dict):
        """Post a code analysis request to the channel."""
        filename = request_data.get('filename', '')
        content = request_data.get('content', '')
        metadata = request_data.get('metadata', {})

        # Content preview (limit to 500 chars for brevity)
        content_preview = content[:500] + '...' if len(content) > 500 else content

        # Build the formatted message
        formatted_message = f"""📄 文件: {filename}

📝 代码内容:
{content_preview}

---
请分析此文件的架构和逻辑，并推荐下一步应该查看的文件。"""

        # Get the messaging adapter
        messaging = self.client.mod_adapters.get("openagents.mods.workspace.messaging")
        if messaging:
            await messaging.send_channel_message(
                channel="code-insights-stream",
                text=formatted_message
            )
            print(f"✅ 已发送分析请求到频道: {filename}")
        else:
            print("⚠️ 警告: 消息适配器不可用")


async def main():
    """Run the code analyzer agent."""
    import argparse

    parser = argparse.ArgumentParser(description="Code Analyzer Agent - HTTP Listener for Code Analysis")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    parser.add_argument("--http-port", type=int, default=8888, help="HTTP server port")
    args = parser.parse_args()

    agent = CodeAnalyzerAgent(http_port=args.http_port)

    try:
        await agent.async_start(
            network_host=args.host,
            network_port=args.port,
        )

        print(f"🎯 Code Analyzer running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 正在关闭...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())
