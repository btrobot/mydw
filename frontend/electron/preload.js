"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
/**
 * 得物掘金工具 - Preload 脚本
 * 在渲染进程和主进程之间建立安全桥接
 */
const electron_1 = require("electron");
// 暴露给渲染进程的 API
const electronAPI = {
    // 系统信息
    getVersion: () => electron_1.ipcRenderer.invoke('get-version'),
    getPlatform: () => electron_1.ipcRenderer.invoke('get-platform'),
    // 外部链接
    openExternal: (url) => electron_1.ipcRenderer.invoke('open-external', url),
    openPath: (filePath) => electron_1.ipcRenderer.invoke('open-path', filePath),
    // 窗口控制
    windowMinimize: () => electron_1.ipcRenderer.send('window-minimize'),
    windowMaximize: () => electron_1.ipcRenderer.send('window-maximize'),
    windowClose: () => electron_1.ipcRenderer.send('window-close'),
    // 事件监听
    onPublishAction: (callback) => {
        electron_1.ipcRenderer.on('publish-action', (_, action) => callback(action));
        return () => {
            electron_1.ipcRenderer.removeAllListeners('publish-action');
        };
    },
    // 移除所有监听
    removeAllListeners: (channel) => {
        electron_1.ipcRenderer.removeAllListeners(channel);
    }
};
// 暴露 API
electron_1.contextBridge.exposeInMainWorld('electronAPI', electronAPI);
//# sourceMappingURL=preload.js.map