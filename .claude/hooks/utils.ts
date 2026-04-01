// Shared utilities for dewugojin hooks
import { execSync } from "child_process";
import { existsSync, readFileSync, writeFileSync } from "fs";
import { dirname, join } from "path";

// Find project root by traversing up to find .git
export function findProjectRoot(scriptPath: string): string {
  let dir = dirname(scriptPath);
  for (let i = 0; i < 5; i++) {
    if (existsSync(join(dir, ".git"))) return dir;
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return process.cwd();
}

// Colors for terminal output
export const colors = {
  reset: "\x1b[0m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  cyan: "\x1b[36m",
};

export function log(prefix: string, message: string, color: keyof typeof colors = "reset") {
  console.log(`${colors[color]}[${prefix}]${colors.reset} ${message}`);
}

export function info(msg: string) {
  log("INFO", msg, "blue");
}

export function ok(msg: string) {
  log("OK", msg, "green");
}

export function warn(msg: string) {
  log("WARN", msg, "yellow");
}

export function error(msg: string) {
  log("ERROR", msg, "red");
}

export function header(title: string, color: keyof typeof colors = "green") {
  console.log(`\n${colors[color]}========================================`);
  console.log(`  ${title}`);
  console.log(`========================================${colors.reset}\n`);
}

// Run git command and return output
export function git(args: string[]): string | null {
  try {
    return execSync(`git ${args.join(" ")}`, { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"] }).trim();
  } catch {
    return null;
  }
}

// Check if git repo
export function isGitRepo(): boolean {
  return git(["rev-parse", "--is-inside-work-tree"]) === "true";
}

// Get staged files
export function getStagedFiles(): string[] {
  const output = git(["diff", "--cached", "--name-only", "--diff-filter=ACM"]);
  if (!output) return [];
  return output.split("\n").filter(Boolean);
}

// Get uncommitted changes
export function getUncommittedChanges(): string | null {
  const status = git(["status", "--short"]);
  return status && status.trim() ? status.trim() : null;
}

// Check if command exists
export function commandExists(cmd: string): boolean {
  try {
    execSync(cmd, { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

// Get command version
export function getVersion(cmd: string, args: string = "--version"): string | null {
  try {
    return execSync(`${cmd} ${args}`, { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"] }).trim();
  } catch {
    return null;
  }
}

// Read file safely
export function readFile(path: string): string | null {
  try {
    return readFileSync(path, "utf-8");
  } catch {
    return null;
  }
}

// Update session state
export function updateSessionState(projectRoot: string) {
  const stateFile = join(projectRoot, "production", "session-state", "active.md");
  if (!existsSync(stateFile)) return;

  const content = readFile(stateFile);
  if (!content) return;

  const timestamp = new Date().toISOString().replace("T", " ").substring(0, 19);
  const newEntry = `\n\n### ${timestamp}\n- Session ended\n`;

  if (content.includes("## Session History") || content.includes("## History")) {
    const updated = content.replace(/(## Session History|## History)/, `${newEntry}\n$1`);
    try {
      writeFileSync(stateFile, updated);
    } catch {}
  }
}
