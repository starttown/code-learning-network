<!-- App.svelte -->
<script lang="ts">
  import FileTree from "$lib/components/FileTree.svelte";
  import EditorArea from "$lib/components/EditorArea.svelte";
  import { onMount } from "svelte";
  import { Menu, MenuItem, Submenu } from "@tauri-apps/api/menu";
  import { open } from "@tauri-apps/plugin-dialog";
  import { invoke } from "@tauri-apps/api/core";

  let initialRootPath = $state<string | undefined>(undefined);

  // 存储当前文件内容和路径
  let currentContent = $state<string>("");
  let currentPath = $state<string | undefined>(undefined);

  // 拖拽相关状态
  let isDraggingOver = $state(false);
  let droppedFiles: Array<{ path: string; name: string }> = $state([]);

  import { WebviewWindow } from "@tauri-apps/api/webviewWindow";
  let openAgentsWindow: WebviewWindow | null = null;

  export async function getOpenAgentsWindow(): Promise<WebviewWindow | null> {
    if (openAgentsWindow) {
      return openAgentsWindow;
    }

    openAgentsWindow = await WebviewWindow.getByLabel("openagents").catch(
      () => null,
    );

    return openAgentsWindow;
  }

  import { fetch } from "@tauri-apps/plugin-http";

  async function sendFileToServer(filename: string, content: string) {
    const response = await fetch("http://localhost:8888/analyze", {
      method: "POST",
      body: JSON.stringify({
        filename,
        content,
      }),
      headers: { "Content-Type": "application/json" },
    });

    if (response.ok) {
      const result = await response.json();
      alert(`文件 ${filename} 发送成功！服务器响应: ${JSON.stringify(result)}`);
      console.log("✅ 发送成功:", result);
    } else {
      alert(`文件 ${filename} 发送失败！状态码: ${response.status}`);
      console.error("❌ 发送失败:", response.status, response.statusText);
    }
  }

  async function sendAllFiles() {
    console.log("--- 待发送文件列表 ---");

    // 使用 for...of 循环以便正确使用 await
    for (const [index, file] of droppedFiles.entries()) {
      console.log(`[${index}] ${file.name} (Path: ${file.path})`);

      try {
        // 等待读取完成，获取实际的文件内容字符串
        const content = await readFileContentAsync(file.path);

        console.log("📤 发送文件:", file.name);
        console.log("📄 内容预览:", content.substring(0, 50) + "..."); // 这时候打印的才是真正的文本

        // 发送的是实际内容字符串
        await sendFileToServer(file.name, content);
      } catch (error) {
        console.error(`❌ 处理文件 ${file.name} 时出错:`, error);

        alert(`处理文件 ${file.name} 时出错: ${error}`);
      }
    }
  }

  onMount(async () => {
    console.log("[App] Component mounting...");
    getOpenAgentsWindow().then((win) => {
      if (win) {
        console.log("[App] OpenAgents window found on mount.");
      } else {
        console.log("[App] OpenAgents window not found on mount.");
      }
    });

    const agentsSubmenu = await Submenu.new({
      text: "OpenAgents",
      items: [
        await MenuItem.new({
          id: "openagents",
          text: "Contacting OpenAgents...",
          action: async () => {
            openAgentsWindow?.show();
          },
        }),

        await MenuItem.new({
          id: "close",
          text: "Close",
          action: () => {
            console.log("[App] Hiding OpenAgents window");
            openAgentsWindow?.hide();
          },
        }),
      ],
    });

    const fileSubmenu = await Submenu.new({
      text: "File",
      items: [
        await MenuItem.new({
          id: "open",
          text: "Open Folder...",
          action: async () => {
            console.log("[App] Open Folder clicked");
            const selected = await open({
              multiple: false,
              directory: true,
            });

            console.log("[App] Selected path:", selected);

            if (selected) {
              const path =
                typeof selected === "string" ? selected : selected[0];
              console.log("[App] Setting initialRootPath:", path);
              initialRootPath = path;
            } else {
              console.log("[App] No folder selected");
            }
          },
        }),
        await MenuItem.new({
          id: "quit",
          text: "Quit",
          action: () => {
            console.log("[App] Quit pressed");
          },
        }),
      ],
    });

    const menu = await Menu.new({
      items: [fileSubmenu, agentsSubmenu],
    });

    console.log("[App] App menu created");
    menu.setAsAppMenu();
  });

  // 纯功能函数：读取文件内容
  async function readFileContentAsync(filePath: string): Promise<string> {
    console.log("[FileSystem] Reading file:", filePath);

    try {
      const content = await invoke<string>("read_file_content", {
        path: filePath,
      });

      console.log("[FileSystem] Read success, length:", content.length);
      return content;
    } catch (error) {
      console.error("[FileSystem] Read failed:", error);
      throw new Error(`Failed to read file: ${filePath} - ${error}`);
    }
  }

  // 状态更新函数：处理文件选择
  async function handleFileSelection(filePath: string): Promise<void> {
    console.log("[AppState] handleFileSelection called with:", filePath);

    try {
      // 调用纯功能函数
      const fileContent = await readFileContentAsync(filePath);

      // 更新状态变量
      currentContent = fileContent;
      currentPath = filePath;

      console.log(
        "[AppState] State updated - path:",
        currentPath,
        "length:",
        currentContent.length,
      );
    } catch (error) {
      // 错误处理和状态更新
      const errorMessage = `Error loading file: ${filePath}\nDetails: ${error}`;
      currentContent = errorMessage;
      currentPath = filePath;

      console.error("[AppState] Error in file selection:", error);
    }

    console.log("[AppState] handleFileSelection completed");
  }

  // 拖拽处理函数
  function handleDragEnter(event: DragEvent) {
    event.preventDefault();
    isDraggingOver = true;
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    event.dataTransfer!.dropEffect = "copy";
  }

  function handleDragLeave(event: DragEvent) {
    isDraggingOver = false;
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();

    isDraggingOver = false;

    try {
      // 尝试获取多种格式的拖拽数据
      const customData = event.dataTransfer?.getData("application/x-file-tree");
      const jsonData = event.dataTransfer?.getData("application/json");
      const textData = event.dataTransfer?.getData("text/plain");

      let fileInfo: { path: string; name: string } | null = null;

      if (customData) {
        fileInfo = JSON.parse(customData);
      } else if (jsonData) {
        const parsed = JSON.parse(jsonData);
        if (parsed.path && parsed.name) {
          fileInfo = parsed;
        }
      } else if (textData) {
        fileInfo = {
          path: textData,
          name: textData.split(/[/\\]/).pop() || textData,
        };
      }

      if (fileInfo) {
        // 打印文件名到控制台
        console.log("🎯 拖拽的文件名:", fileInfo.name);
        console.log("📁 文件完整路径:", fileInfo.path);

        // 添加到已拖拽文件列表
        droppedFiles = [...droppedFiles, fileInfo];

        // 自动打开拖拽的文件
        handleFileSelection(fileInfo.path);
      }
    } catch (error) {
      console.error("拖拽处理错误:", error);
    }
  }

  function clearDroppedFiles() {
    droppedFiles = [];
  }

  function removeFile(index: number) {
    droppedFiles = droppedFiles.filter((_, i) => i !== index);
  }

  function openDroppedFile(fileInfo: { path: string; name: string }) {
    handleFileSelection(fileInfo.path);
  }
</script>

<div
  class="flex h-screen w-screen bg-[#f5f5f5] text-[#333333] overflow-hidden font-sans"
>
  <!-- Sidebar -->
  <div
    class="w-[250px] flex flex-col bg-[#e8e8e8] border-r border-[#d0d0d0] shrink-0"
  >
    <div class="px-5 py-2.5 text-xs font-bold uppercase text-[#666666]">
      资源管理器
    </div>

    <div class="flex-1 overflow-hidden">
      {#if initialRootPath}
        <FileTree
          rootPath={initialRootPath}
          onFileSelect={handleFileSelection}
        />
      {:else}
        <div class="p-5 text-xs text-center text-[#666666]">
          打开文件夹以开始
        </div>
      {/if}
    </div>
  </div>

  <!-- Main Content -->
  <div class="flex-1 flex flex-col bg-[#f5f5f5] overflow-hidden">
    <!-- 编辑器区域 -->
    <div class="flex-1 overflow-hidden">
      <EditorArea {currentContent} {currentPath} />
    </div>

    <!-- 拖拽接收区域 -->
    <div class="border-b border-[#d0d0d0] bg-[#fafafa]">
      <div
        class="border-2 border-dashed border-gray-300 rounded-lg mx-4 my-3 p-4 text-center min-h-[100px] transition-all duration-200 bg-gray-50 relative
          {isDraggingOver ? 'border-blue-500 bg-blue-50 scale-[1.02]' : ''}
          {droppedFiles.length > 0 ? 'border-green-500 bg-green-50' : ''}"
        ondragenter={handleDragEnter}
        ondragover={handleDragOver}
        ondragleave={handleDragLeave}
        ondrop={handleDrop}
      >
        {#if isDraggingOver}
          <div class="text-blue-500 font-bold animate-pulse">
            <div class="text-3xl mb-2">📁</div>
            <div class="text-sm">释放文件到这里</div>
          </div>
        {:else if droppedFiles.length > 0}
          <div class="text-left">
            <div
              class="flex justify-between items-center mb-2 pb-1 border-b border-gray-200 font-bold text-gray-700 text-xs"
            >
              <span>已接收文件 ({droppedFiles.length})</span>
              <button
                class="bg-blue-500 text-white border-none rounded px-2 py-0.5 text-xs cursor-pointer transition-colors duration-200 hover:bg-blue-600"
                onclick={sendAllFiles}
              >
                发送
              </button>
              <button
                class="bg-red-500 text-white border-none rounded px-2 py-0.5 text-xs cursor-pointer transition-colors duration-200 hover:bg-red-600"
                onclick={clearDroppedFiles}
              >
                清空
              </button>
            </div>
            <div class="max-h-20 overflow-y-auto">
              {#each droppedFiles as file, index}
                <div
                  class="flex items-center p-1 my-0.5 bg-gray-100 rounded border border-gray-200 transition-all duration-200 hover:bg-gray-200 hover:translate-x-0.5 cursor-pointer text-xs"
                  onclick={() => openDroppedFile(file)}
                >
                  <span class="mr-2 text-sm">📄</span>
                  <span
                    class="flex-1 font-mono text-gray-700 whitespace-nowrap overflow-hidden text-ellipsis"
                    >{file.name}</span
                  >
                  <button
                    class="bg-gray-500 text-white border-none rounded-full w-4 h-4 text-xs cursor-pointer flex items-center justify-center transition-all duration-200 ml-1 hover:bg-red-500 hover:scale-110"
                    onclick={(e) => {
                      e.stopPropagation();
                      removeFile(index);
                    }}
                  >
                    ✕
                  </button>
                </div>
              {/each}
            </div>
          </div>
        {:else}
          <div class="text-gray-600">
            <div class="text-3xl mb-2 opacity-50">📂</div>
            <div class="text-sm">拖拽文件到这里</div>
            <div class="text-xs text-gray-400 mt-1">支持从文件树拖拽文件</div>
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>
