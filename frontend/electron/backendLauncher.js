"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.BackendStartupError = void 0;
exports.createBackendLauncherSpec = createBackendLauncherSpec;
exports.waitForBackendHealth = waitForBackendHealth;
const path_1 = __importDefault(require("path"));
class BackendStartupError extends Error {
    constructor(code, message) {
        super(message);
        this.name = 'BackendStartupError';
        this.code = code;
    }
}
exports.BackendStartupError = BackendStartupError;
const DEFAULT_HOST = '127.0.0.1';
const DEFAULT_PORT = 8000;
const DEFAULT_TIMEOUT_MS = 15000;
const DEFAULT_RETRY_MS = 500;
function resolveBackendRoot(options) {
    if (options.isDev) {
        return path_1.default.resolve(options.electronDir, '../../backend');
    }
    return path_1.default.join(options.resourcesPath ?? '', 'backend');
}
function resolveLauncherPath(options) {
    const launcherName = options.isDev ? 'start-backend-dev' : 'start-backend-prod';
    const extension = (options.platform ?? process.platform) === 'win32' ? '.bat' : '.sh';
    return path_1.default.resolve(options.electronDir, 'launchers', `${launcherName}${extension}`);
}
function createBackendLauncherSpec(options) {
    const platform = options.platform ?? process.platform;
    const host = options.host ?? DEFAULT_HOST;
    const port = options.port ?? DEFAULT_PORT;
    const backendPath = resolveBackendRoot(options);
    const launcherPath = resolveLauncherPath(options);
    if (platform === 'win32') {
        return {
            backendPath,
            command: 'cmd.exe',
            args: ['/d', '/s', '/c', launcherPath, backendPath, host, String(port)],
            cwd: backendPath,
            env: { ...process.env, BACKEND_ROOT: backendPath, BACKEND_HOST: host, BACKEND_PORT: String(port) },
            healthUrl: `http://${host}:${port}/health`,
        };
    }
    return {
        backendPath,
        command: 'bash',
        args: [launcherPath, backendPath, host, String(port)],
        cwd: backendPath,
        env: { ...process.env, BACKEND_ROOT: backendPath, BACKEND_HOST: host, BACKEND_PORT: String(port) },
        healthUrl: `http://${host}:${port}/health`,
    };
}
async function waitForBackendHealth(child, healthUrl, options = {}) {
    const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
    const retryIntervalMs = options.retryIntervalMs ?? DEFAULT_RETRY_MS;
    const fetchImpl = options.fetchImpl ?? fetch;
    const sleep = options.sleep ?? ((ms) => new Promise((resolve) => setTimeout(resolve, ms)));
    const startedAt = Date.now();
    let earlyExitMessage = null;
    let spawnErrorMessage = null;
    const onExit = (code, signal) => {
        earlyExitMessage = `Backend process exited before readiness (code=${code ?? 'null'}, signal=${signal ?? 'null'})`;
    };
    const onError = (error) => {
        spawnErrorMessage = `Backend launcher failed to spawn: ${error.message}`;
    };
    child.once('exit', onExit);
    child.once('error', onError);
    try {
        while (Date.now() - startedAt < timeoutMs) {
            if (spawnErrorMessage !== null) {
                throw new BackendStartupError('spawn_failure', spawnErrorMessage);
            }
            if (earlyExitMessage !== null) {
                throw new BackendStartupError('early_exit', earlyExitMessage);
            }
            try {
                const response = await fetchImpl(healthUrl);
                if (response.ok) {
                    const payload = (await response.json().catch(() => null));
                    if (payload?.status === 'healthy') {
                        return;
                    }
                }
            }
            catch {
                // Keep polling until success, early exit, or timeout.
            }
            await sleep(retryIntervalMs);
        }
        throw new BackendStartupError('health_timeout', `Backend did not become healthy within ${timeoutMs}ms`);
    }
    finally {
        child.removeListener('exit', onExit);
        child.removeListener('error', onError);
    }
}
//# sourceMappingURL=backendLauncher.js.map