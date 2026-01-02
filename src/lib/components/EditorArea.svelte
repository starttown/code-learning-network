<!-- src/lib/components/EditorArea.svelte -->
<script lang="ts">
    let {
        currentContent = "",
        currentPath,
    }: { currentContent: string; currentPath?: string } = $props();
</script>

<div class="w-full h-full flex flex-col overflow-auto font-mono text-sm">
    {#if currentPath}
        <div
            class="px-2.5 py-2.5 bg-gray-100 border-b border-gray-200 text-xs text-gray-700 shrink-0"
        >
            {currentPath}
        </div>
    {/if}
    <!-- 修改这里：使用 currentContent -->
    <pre class="p-5 m-0 whitespace-pre-wrap break-words text-gray-900">{currentContent}</pre>
</div>
