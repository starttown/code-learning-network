<!-- src/lib/components/FileTree.svelte -->
<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import type { FileNode } from "$lib/types";

  let {
    rootPath,
    onFileSelect,
  }: {
    rootPath: string;
    onFileSelect: (path: string) => void;
  } = $props();

  let rootNodes: FileNode[] = $state([]);
  let loading = $state(false);

  // 监听 rootPath 变化并初始化根节点
  $effect(async () => {
    if (rootPath) {
      await Promise.resolve();
      const displayName =
        rootPath.split(/[/\\]/).filter(Boolean).pop() || rootPath;

      rootNodes = [
        {
          name: displayName,
          path: rootPath,
          is_directory: true,
          is_expanded: false,
          is_loading: false,
          children: undefined,
        },
      ];
    } else {
      rootNodes = [];
    }
  });

  // 加载目录内容
  async function loadDirectory(path: string, parentNode: FileNode) {
    try {
      parentNode.is_loading = true;
      const rawNodes: FileNode[] = await invoke("read_directory", { path });

      const processedNodes = rawNodes.map((n) => ({
        name: n.name,
        path: n.path,
        is_directory: n.is_directory,
        is_expanded: false,
        is_loading: false,
        children: undefined,
      }));

      parentNode.children = processedNodes;
      parentNode.is_expanded = true;
    } catch (error) {
      console.error("[loadDirectory] Error:", error);
    } finally {
      parentNode.is_loading = false;
    }
  }

  // 处理节点点击
  function handleClick(node: FileNode) {
    if (node.is_directory) {
      node.is_expanded = !node.is_expanded;
      if (node.is_expanded && !node.children) {
        loadDirectory(node.path, node);
      }
    } else {
      onFileSelect(node.path);
    }
  }

  // 拖拽开始处理 - 只有文件可以拖拽
  function handleDragStart(event: DragEvent, node: FileNode) {
    // 如果是目录，阻止拖拽
    if (node.is_directory) {
      event.preventDefault();
      return;
    }

    // 设置拖拽数据
    const dragData = {
      path: node.path,
      name: node.name,
      type: "file",
      timestamp: Date.now(),
    };

    // 多格式数据支持，提高兼容性
    event.dataTransfer?.setData("application/json", JSON.stringify(dragData));
    event.dataTransfer?.setData("text/plain", node.path);
    event.dataTransfer?.setData("text/uri-list", `file://${node.path}`);
    event.dataTransfer?.setData(
      "application/x-file-tree",
      JSON.stringify(dragData),
    );

    // 设置拖拽效果
    event.dataTransfer!.effectAllowed = "copy";
    // 添加拖拽样式
    event.currentTarget?.classList.add("dragging");
  }

  // 拖拽结束处理
  function handleDragEnd(event: DragEvent, node: FileNode) {
    event.currentTarget?.classList.remove("dragging");
  }

  // 获取图标
  function getIcon(node: FileNode): string {
    if (node.is_directory) {
      return node.is_expanded ? "📂" : "📁";
    }
    const ext = node.name.split(".").pop()?.toLowerCase();
    const icons: Record<string, string> = {
      rs: "🦀",
      ts: "📘",
      js: "📜",
      svelte: "🔥",
      json: "⚙️",
      md: "📝",
      toml: "⚙️",
      html: "🌐",
      css: "🎨",
      png: "🖼️",
      jpg: "🖼️",
      jpeg: "🖼️",
      gif: "🖼️",
      svg: "🖼️",
      pdf: "📕",
      txt: "📄",
      zip: "📦",
      rar: "📦",
      exe: "⚙️",
      dll: "⚙️",
      so: "⚙️",
      dylib: "⚙️",
    };
    return icons[ext || ""] || "📄";
  }
</script>

<div class="h-full overflow-y-auto select-none font-sans text-sm">
  {#if loading && rootNodes.length === 0}
    <div class="p-5 text-center text-gray-500">加载中...</div>
  {:else if rootNodes.length === 0}
    <div class="p-5 text-center text-gray-500">无文件</div>
  {:else}
    <ul class="list-none p-0 m-0">
      {#each rootNodes as node}
        {@render renderNode(
          node,
          handleClick,
          loadDirectory,
          getIcon,
          handleDragStart,
          handleDragEnd,
        )}
      {/each}
    </ul>
  {/if}
</div>

{#snippet renderNode(node, onClick, onLoad, getIcon, onDragStart, onDragEnd)}
  <li class="list-none">
    <button
      type="button"
      class="flex items-center px-2 py-1 w-full text-left bg-transparent border-none cursor-pointer rounded transition-colors duration-100 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-transparent relative z-10
        {node.is_expanded ? 'bg-gray-50' : ''}
        {!node.is_directory
        ? 'cursor-grab active:cursor-grabbing'
        : 'cursor-default'}
        {!node.is_directory
        ? 'dragging:opacity-50 dragging:bg-blue-50 dragging:border dragging:border-blue-500 dragging:border-dashed'
        : ''}"
      draggable={!node.is_directory}
      onclick={() => onClick(node)}
      ondragstart={(e) => onDragStart(e, node)}
      ondragend={(e) => onDragEnd(e, node)}
      aria-label={node.name}
      aria-expanded={node.is_directory ? String(node.is_expanded) : undefined}
    >
      {#if node.is_directory}
        <span
          class="w-4 text-xs text-gray-500 transition-transform duration-100"
        >
          {node.is_expanded ? "▼" : "▶"}
        </span>
      {:else}
        <span class="w-4"></span>
      {/if}
      <span class="mr-2 text-base">{getIcon(node)}</span>
      <span class="flex-1 whitespace-nowrap overflow-hidden text-ellipsis"
        >{node.name}</span
      >

      {#if node.is_loading}
        <span class="ml-auto text-blue-500 text-xs animate-pulse">...</span>
      {/if}
    </button>

    {#if node.is_directory && node.is_expanded && node.children}
      <ul class="list-none p-0 m-0 pl-4 border-l border-gray-700">
        {#each node.children as child}
          {@render renderNode(
            child,
            onClick,
            onLoad,
            getIcon,
            onDragStart,
            onDragEnd,
          )}
        {/each}
      </ul>
    {/if}
  </li>
{/snippet}
