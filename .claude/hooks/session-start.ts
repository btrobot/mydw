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
  // Load existing session state
  header("ACTIVE SESSION STATE DETECTED", "yellow");
  console.log("Found unfinished work from previous session.\n");

  const content = readFileSync(stateFile, "utf-8");
  if (content) {
    // Parse status block
    const statusMatch = content.match(/<!-- STATUS -->([\s\S]*?)<!-- \/STATUS -->/);
    if (statusMatch) {
      const epic = statusMatch[1].match(/Epic:(?:[ \t]*)([^\n]*)/)?.[1]?.trim() || "";
      const feature = statusMatch[1].match(/Feature:(?:[ \t]*)([^\n]*)/)?.[1]?.trim() || "";
      const task = statusMatch[1].match(/Task:(?:[ \t]*)([^\n]*)/)?.[1]?.trim() || "";

      if (task.length > 0) {
        console.log("  Current Task:", task);
        if (feature.length > 0) console.log("  Feature:", feature);
        if (epic.length > 0) console.log("  Epic:", epic);
      }
    }

    // Parse current component and phase
    const componentMatch = content.match(/\*\*Component\*\*:\s*(.+)/);
    const phaseMatch = content.match(/\*\*Phase\*\*:\s*(.+)/);
    const taskStatusMatch = content.match(/\*\*Status\*\*:\s*(.+)/);

    if (componentMatch) console.log("  Component:", componentMatch[1].trim());
    if (phaseMatch) console.log("  Phase:", phaseMatch[1].trim());
    if (taskStatusMatch) console.log("  Status:", taskStatusMatch[1].trim());

    // Show open questions
    const questionsMatch = content.match(/## Open Questions\n([\s\S]*?)(?=\n##|\n---)/);
    if (questionsMatch && questionsMatch[1].trim()) {
      console.log("\n  Open Questions:");
      const questions = questionsMatch[1].trim().split(/\n(?=\d+\.)/);
      questions.slice(0, 3).forEach((q) => {
        const lines = q.split("\n").filter(Boolean);
        if (lines[0]) console.log(`    - ${lines[0].replace(/^\d+\.\s*\*\*/, "").replace(/\*\*:/, ":")}`);
      });
    }

    // Show blockers
    const blockersMatch = content.match(/## Blocker Notes\n([\s\S]*?)(?=\n##|\n---)/);
    if (blockersMatch && blockersMatch[1].trim()) {
      console.log("\n  Blockers:");
      const blockers = blockersMatch[1].trim().split("\n").filter(Boolean).slice(0, 3);
      blockers.forEach((b) => {
        if (b.includes("- **")) {
          const text = b.replace(/^- \*\*/, "").replace(/\*\*:/, ":");
          console.log(`    - ${text}`);
        }
      });
    }

    console.log("\n  To resume: Review active.md for full context");
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

    // Replace placeholder with actual timestamp
    const newState = template
      .replace(/\{timestamp\}/g, timestamp)
      .replace(/\{component-name\}/g, "TBD")
      .replace(/\{current-phase\}/g, "Planning")
      .replace(/\{in-progress\|completed\|blocked\}/g, "in-progress");

    writeFileSync(stateFile, newState, "utf-8");
    ok("Created new session state from template");
    console.log();
    console.log("  Session Started:", timestamp);
    console.log("  File: production/session-state/active.md");
    console.log();
    console.log("  Next: Update STATUS block and Active Task section");
  } else {
    warn("Template not found: production/session-state/active.md.template");
  }
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
console.log();

ok("Session initialized");
