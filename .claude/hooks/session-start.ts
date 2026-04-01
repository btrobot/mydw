// Session start hook for dewugojin
import { existsSync } from "fs";
import { join } from "path";
import { findProjectRoot, info, ok, warn, header, readFile } from "./utils.ts";

// Find project root
const scriptPath = join(import.meta.dir!, "session-start.ts");
const projectRoot = findProjectRoot(scriptPath);
process.chdir(projectRoot);

header("DewuGoJin - Session Started");

info("Checking project structure...");

// Check frontend
if (existsSync(join(projectRoot, "frontend"))) {
  ok("Frontend: Found");
} else {
  warn("Frontend: Not found");
}

// Check backend
if (existsSync(join(projectRoot, "backend"))) {
  ok("Backend: Found");
} else {
  warn("Backend: Not found");
}

console.log();
info("Checking prerequisites...");

// Node.js
if (Bun.which("node")) {
  const output = Bun.spawnSync({ cmd: ["node", "--version"], stdout: "pipe" });
  ok(`Node.js: ${output.stdout.toString().trim()}`);
} else {
  warn("Node.js: Not installed");
}

// Python
const pythonVersion = Bun.which("python");
if (pythonVersion) {
  const output = Bun.spawnSync({ cmd: ["python", "--version"], stdout: "pipe" });
  ok(`Python: ${output.stdout.toString().trim()}`);
} else {
  warn("Python: Not installed");
}

// FFmpeg
const ffmpegVersion = Bun.which("ffmpeg");
if (ffmpegVersion) {
  ok("FFmpeg: Available");
} else {
  warn("FFmpeg: Not installed (AI editing unavailable)");
}

// Load session state
console.log();
const stateFile = join(projectRoot, "production", "session-state", "active.md");
if (existsSync(stateFile)) {
  info("Loading session state...");

  const content = readFile(stateFile);
  if (content) {
    // Parse status block
    // Note: \s includes newline, so use [ \t] for space/tab only
    const statusMatch = content.match(/<!-- STATUS -->([\s\S]*?)<!-- \/STATUS -->/);
    if (statusMatch) {
      const epic = statusMatch[1].match(/Epic:(?:[ \t]*)([^\n]*)/)?.[1]?.trim() || "";
      const feature = statusMatch[1].match(/Feature:(?:[ \t]*)([^\n]*)/)?.[1]?.trim() || "";
      const task = statusMatch[1].match(/Task:(?:[ \t]*)([^\n]*)/)?.[1]?.trim() || "";

      if (task.length > 0) {
        console.log();
        header("Current Status");
        if (epic.length > 0) console.log(`  Epic: ${epic}`);
        if (feature.length > 0) console.log(`  Feature: ${feature}`);
        if (task.length > 0) console.log(`  Task: ${task}`);
      }
    }
  }
} else {
  info("No session state file");
}

// Show available commands
console.log();
header("Available Skills");
console.log("  /sprint-plan        - Sprint planning");
console.log("  /task-breakdown    - Task breakdown");
console.log("  /architecture-review - Architecture review");
console.log("  /code-review       - Code review");
console.log("  /security-scan     - Security scan");
console.log();

ok("Session initialized");
