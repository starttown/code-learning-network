<script lang="ts">
  import { open } from "@tauri-apps/plugin-dialog";
  import type { AppConfig } from "$lib/types";
  import { invoke } from "@tauri-apps/api/core";
  import { listen } from "@tauri-apps/api/event";
  import { onMount } from "svelte";
  import { Command } from "@tauri-apps/plugin-shell"; 

  let pythonPath: string = $state("");
  let unlisten: (() => void) | null = null;

  async function loadConfig() {
    try {
      const config: AppConfig = await invoke("get_config");
      pythonPath = config.python_path;
    } catch (error) {
      console.error("加载配置失败:", error);
    }
  }

  async function selectDirectory() {
    try {
      const selected = await open({
        multiple: false,
        directory: true,
      });

      if (!selected) return null;
      return typeof selected === "string" ? selected : selected[0];
    } catch (error) {
      console.error("打开文件对话框失败:", error);
      return null;
    }
  }

  async function selectFile() {
    try {
      const selected = await open({
        multiple: false,
        directory: false,
      });

      if (!selected) return null;
      return typeof selected === "string" ? selected : selected[0];
    } catch (error) {
      console.error("打开文件对话框失败:", error);
      return null;
    }
  }

  async function browsePythonPath() {
    const selectedPath = await selectDirectory();
    if (selectedPath) {
      pythonPath = selectedPath;
    }
  }

  async function saveSettings() {
    const config: AppConfig = {
      python_path: pythonPath,
    };

    try {
      await invoke("save_config", { config });
      console.log("配置已保存");
    } catch (error) {
      console.error("保存配置失败:", error);
    }
  }

  // [改写] 打开控制台并运行指令（显式打开新窗口）
  async function runOpenagentsNetWorkCommand() {
    if (!pythonPath) {
      alert("请先设置 Python 路径！");
      return;
    }

    const selectedPath = await selectDirectory();
    let networkPath: string;
    if (selectedPath) {
      networkPath = selectedPath;
      console.log("选择的网络文件夹路径:", networkPath);
    } else {
      alert("未选择网络文件夹路径！");
      return;
    }

    try {
      // 构造命令：用start打开新cmd窗口，cd到pythonPath并执行python --version
      const commandStr = `start /D ${pythonPath}\\Scripts cmd /K openagents.exe network start ${networkPath}`;

      console.log("执行命令:", commandStr);

      // 使用/C执行start命令（start是cmd的内部命令，需用/C）
      const command = Command.create("run-cmd", ["/C", commandStr], {
        encoding: "utf-8",
        env: {
          PYTHONIOENCODING: "utf-8",
          PYTHONUTF8: "1",
        },
      });

      // spawn()启动进程（不等待完成，保持窗口打开）
      const child = await command.spawn();

      console.log("控制台已启动，命令执行中...");
    } catch (error) {
      console.error("启动控制台失败:", error);
      alert("启动控制台失败: " + error);
    }
  }

  async function runOpenagentsYamlCommand() {
    if (!pythonPath) {
      alert("请先设置 Python 路径！");
      return;
    }

    const selectedPath = await selectFile();
    let yamlPath: string;
    if (selectedPath) {
      yamlPath = selectedPath;
      console.log("选择的YAML文件路径:", yamlPath);
    } else {
      alert("未选择YAML文件路径！");
      return;
    }

    try {
      // 构造命令：用start打开新cmd窗口，cd到pythonPath并执行python --version
      const commandStr = `start /D ${pythonPath}\\Scripts cmd /K openagents.exe agent start ${yamlPath}`;

      console.log("执行命令:", commandStr);

      // 使用/C执行start命令（start是cmd的内部命令，需用/C）
      const command = Command.create("run-cmd", ["/C", commandStr], {
        encoding: "utf-8",
        env: {
          PYTHONIOENCODING: "utf-8",
          PYTHONUTF8: "1",
        },
      });

      // spawn()启动进程（不等待完成，保持窗口打开）
      const child = await command.spawn();

      console.log("控制台已启动，命令执行中...");
    } catch (error) {
      console.error("启动控制台失败:", error);
      alert("启动控制台失败: " + error);
    }
  }

  async function runOpenagentsPyCommand() {
    if (!pythonPath) {
      alert("请先设置 Python 路径！");
      return;
    }

    const selectedPath = await selectFile();
    let pyPath: string;
    if (selectedPath) {
      pyPath = selectedPath;
      console.log("选择的Python文件路径:", pyPath);
    } else {
      alert("未选择Python文件路径！");
      return;
    }

    try {
      // 构造命令：用start打开新cmd窗口，cd到pythonPath并执行python --version
      const commandStr = `start /D ${pythonPath} cmd /K python.exe ${pyPath}`;

      console.log("执行命令:", commandStr);

      // 使用/C执行start命令（start是cmd的内部命令，需用/C）
      const command = Command.create("run-cmd", ["/C", commandStr], {
        encoding: "utf-8",
        env: {
          PYTHONIOENCODING: "utf-8",
          PYTHONUTF8: "1",
        },
      });

      // spawn()启动进程（不等待完成，保持窗口打开）
      const child = await command.spawn();

      console.log("控制台已启动，命令执行中...");
    } catch (error) {
      console.error("启动控制台失败:", error);
      alert("启动控制台失败: " + error);
    }
  }

  onMount(async () => {
    await loadConfig();
    unlisten = await listen<AppConfig>("config-updated", (event) => {
      pythonPath = event.payload.python_path;
    });
  });

  $effect(() => {
    return () => {
      if (unlisten) unlisten();
    };
  });
</script>

<div class="max-w-2xl mx-auto p-6 text-center font-sans">
  <div
    class="mt-8 text-left bg-gray-50 p-6 rounded-lg border border-gray-100 shadow-sm"
  >
    <div class="flex flex-col gap-3 mb-6">
      <label for="python-path" class="text-sm font-semibold text-gray-700">
        Python Path:
      </label>

      <div class="flex gap-3">
        <input
          id="python-path"
          type="text"
          bind:value={pythonPath}
          placeholder="例如: C:\Python39"
          class="flex-1 p-2 border border-gray-300 rounded text-sm font-mono text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all"
        />

        <button
          type="button"
          onclick={() => browsePythonPath()}
          class="px-4 py-2 bg-gray-200 text-gray-700 rounded text-sm font-medium hover:bg-gray-300 active:bg-gray-400 transition-colors whitespace-nowrap"
        >
          Open Folder...
        </button>
      </div>
    </div>

    <div class="flex gap-3">
      <!-- 保存按钮 -->
      <button
        type="button"
        onclick={saveSettings}
        class="flex-1 py-2.5 bg-blue-600 text-white font-semibold rounded text-sm hover:bg-blue-700 active:bg-blue-800 transition-colors shadow-sm"
      >
        Save Config
      </button>

      <!-- [改写] 测试运行按钮（显式打开窗口） -->
    </div>
  </div>
  <div>
    <button
      type="button"
      onclick={runOpenagentsNetWorkCommand}
      class="flex-1 py-2.5 bg-emerald-600 text-white font-semibold rounded text-sm hover:bg-emerald-700 active:bg-emerald-800 transition-colors shadow-sm"
    >
      Start Network
    </button>
  </div>
  <div>
    <button
      type="button"
      onclick={runOpenagentsYamlCommand}
      class="flex-1 py-2.5 bg-emerald-600 text-white font-semibold rounded text-sm hover:bg-emerald-700 active:bg-emerald-800 transition-colors shadow-sm"
    >
      Start Yaml Agent
    </button>
    <button
      type="button"
      onclick={runOpenagentsPyCommand}
      class="flex-1 py-2.5 bg-emerald-600 text-white font-semibold rounded text-sm hover:bg-emerald-700 active:bg-emerald-800 transition-colors shadow-sm"
    >
      Start Python Agent
    </button>
  </div>
</div>
