// Session start hook for dewugojin
// Enhanced with session state recovery from Claude-Code-Game-Studios
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { findProjectRoot, info, ok, warn, header, git } from "./utils.ts";

// Find project root
const scriptPath = join(import.meta.dir!, "session-start.ts");
const projectRoot = findProjectRoot(scriptPath);
process.chdir(projectRoot);

header("DewuGoJin - Session Started");

// ============================================
// Project Structure Check
// ============================================

info("Checking project structure...");

if (existsSync(join(projectRoot, "frontend"))) {
  ok("Frontend: Found");
} else {
  warn("Frontend: Not found");
}

if (existsSync(join(projectRoot, "backend"))) {
  ok("Backend: Found");
} else {
  warn("Backend: Not found");
}

// ============================================
// Prerequisites Check
// ============================================

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

// ============================================
// Session State Recovery
// ============================================

console.log();
const stateDir = join(projectRoot, "production", "session-state");
const stateFile = join(stateDir, "active.md");
const templateFile = join(stateDir, "active.md.template");

if (existsSync(stateFile)) {
  // Load existing session state — output preview so Claude can see it
  header("ACTIVE SESSION STATE DETECTED", "yellow");
  console.log("A previous session left state at: production/session-state/active.md");
  console.log("Read this file to recover context and continue where you left off.");
  console.log();

  const content = readFileSync(stateFile, "utf-8");
  if (content) {
    // Output first 20 lines as quick summary
    console.log("Quick summary:");
    const lines = content.split("\n");
    lines.slice(0, 20).forEach((line) => console.log(`  ${line}`));
    if (lines.length > 20) {
      console.log(`  ... (${lines.length} total lines — read the full file to continue)`);
    }
  }
} else {
  // No existing session state - create from template
  info("No active session state found");
  console.log();

  // Ensure directory exists
  if (!existsSync(stateDir)) {
    mkdirSync(stateDir, { recursive: true });
  }

  // Check for template
  if (existsSync(templateFile)) {
    const template = readFileSync(templateFile, "utf-8");
    const timestamp = new Date().toISOString().replace("T", " ").substring(0, 19);

    // Replace timestamp placeholder
    const newState = template
      .replace(/\{timestamp\}/g, timestamp);

    writeFileSync(stateFile, newState, "utf-8");
    ok("Created new session state from template");
    console.log("  File: production/session-state/active.md");
    console.log();

    // Output the newly created content so Claude can see it
    console.log("Quick summary:");
    const lines = newState.split("\n");
    lines.slice(0, 20).forEach((line) => console.log(`  ${line}`));
    if (lines.length > 20) {
      console.log(`  ... (${lines.length} total lines — read the full file to continue)`);
    }
  } else {
    warn("Template not found: production/session-state/active.md.template");
  }
}

// ============================================
// Memory System Check
// ============================================

console.log();
const memoryDir = join(projectRoot, ".claude", "memory");
if (existsSync(memoryDir)) {
  header("Memory System");
  const memoryFiles = ["PROJECT.md", "PATTERNS.md", "DECISIONS.md"];
  let found = 0;
  for (const file of memoryFiles) {
    const filePath = join(memoryDir, file);
    if (existsSync(filePath)) {
      ok(`${file}: Loaded`);
      found++;
    } else {
      warn(`${file}: Missing`);
    }
  }
  if (found > 0) {
    console.log(`  Read .claude/memory/ files to access persistent project knowledge.`);
  }
} else {
  warn("Memory system not initialized (.claude/memory/ not found)");
}

// ============================================
// Recent Git Activity
// ============================================

console.log();
info("Recent commits:");
const recentCommits = git(["log", "--oneline", "-5"]);
if (recentCommits) {
  recentCommits.split("\n").forEach((line) => {
    console.log(`  ${line}`);
  });
}

// ============================================
// Available Commands
// ============================================

console.log();
header("Available Skills");
console.log("  /sprint-plan          - Sprint planning");
console.log("  /task-breakdown      - Task breakdown");
console.log("  /architecture-review  - Architecture review");
console.log("  /code-review          - Code review");
console.log("  /security-scan        - Security scan");
console.log("  /bug-report           - Bug report");
console.log("  /release-checklist    - Release checklist");
console.log();

ok("Session initialized");
