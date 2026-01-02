<!-- src/lib/components/DropZone.svelte -->
<script lang="ts">
    interface FileInfo {
        path: string;
        name: string;
        type?: string;
        timestamp?: number;
    }

    let {
        onFileDrop,
        placeholder = "拖拽文件到这里",
        multiple = true,
    }: {
        onFileDrop: (fileInfo: FileInfo) => void;
        placeholder?: string;
        multiple?: boolean;
    } = $props();

    let isDraggingOver = $state(false);
    let droppedFiles: FileInfo[] = $state([]);
    let dragCounter = $state(0);

    function handleDragEnter(event: DragEvent) {
        event.preventDefault();
        dragCounter++;
        isDraggingOver = true;
    }

    function handleDragOver(event: DragEvent) {
        event.preventDefault();
        event.dataTransfer!.dropEffect = "copy";
    }

    function handleDragLeave(event: DragEvent) {
        dragCounter--;
        if (dragCounter === 0) {
            isDraggingOver = false;
        }
    }

    function handleDrop(event: DragEvent) {
        event.preventDefault();
        event.stopPropagation();

        isDraggingOver = false;
        dragCounter = 0;

        try {
            // 优先尝试自定义格式
            const customData = event.dataTransfer?.getData(
                "application/x-file-tree",
            );
            const jsonData = event.dataTransfer?.getData("application/json");
            const textData = event.dataTransfer?.getData("text/plain");

            let fileInfo: FileInfo | null = null;

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
                if (multiple) {
                    droppedFiles = [...droppedFiles, fileInfo];
                } else {
                    droppedFiles = [fileInfo];
                }
                onFileDrop(fileInfo);
            }
        } catch (error) {
            console.error("Drop error:", error);
        }
    }

    function clearFiles() {
        droppedFiles = [];
    }

    function removeFile(index: number) {
        droppedFiles = droppedFiles.filter((_, i) => i !== index);
    }
</script>

<div
    class="border-2 border-dashed border-gray-300 rounded-lg p-5 text-center min-h-[120px] transition-all duration-200 bg-gray-50 relative
    {isDraggingOver ? 'border-blue-500 bg-blue-50 scale-[1.02]' : ''}
    {droppedFiles.length > 0 ? 'border-green-500 bg-green-50' : ''}"
    ondragenter={handleDragEnter}
    ondragover={handleDragOver}
    ondragleave={handleDragLeave}
    ondrop={handleDrop}
>
    {#if isDraggingOver}
        <div class="text-blue-500 font-bold animate-pulse">
            <div class="text-5xl mb-2">📁</div>
            <div>释放文件到这里</div>
        </div>
    {:else if droppedFiles.length > 0}
        <div class="text-left">
            <div
                class="flex justify-between items-center mb-3 pb-2 border-b border-gray-200 font-bold text-gray-700"
            >
                <span>已接收文件 ({droppedFiles.length})</span>
                <button
                    class="bg-red-500 text-white border-none rounded px-2 py-1 text-xs cursor-pointer transition-colors duration-200 hover:bg-red-600"
                    onclick={clearFiles}
                >
                    清空
                </button>
            </div>
            {#each droppedFiles as file, index}
                <div
                    class="flex items-center p-2 my-1 bg-gray-100 rounded border border-gray-200 transition-all duration-200 hover:bg-gray-200 hover:translate-x-0.5"
                >
                    <span class="mr-2 text-base">📄</span>
                    <span
                        class="flex-1 font-mono text-sm text-gray-700 whitespace-nowrap overflow-hidden text-ellipsis"
                        >{file.name}</span
                    >
                    <button
                        class="bg-gray-500 text-white border-none rounded-full w-5 h-5 text-xs cursor-pointer flex items-center justify-center transition-all duration-200 ml-2 hover:bg-red-500 hover:scale-110"
                        onclick={() => removeFile(index)}
                    >
                        ✕
                    </button>
                </div>
            {/each}
        </div>
    {:else}
        <div class="text-gray-600">
            <div class="text-4xl mb-2 opacity-50">📂</div>
            <div>{placeholder}</div>
            <div class="text-xs text-gray-400 mt-1">支持从文件树拖拽文件</div>
        </div>
    {/if}
</div>
