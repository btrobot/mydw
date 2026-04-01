// Agent audit hook for dewugojin
// Logs agent invocations for audit trail
import { appendFileSync, existsSync, mkdirSync } from "fs";
import { join } from "path";
import { findProjectRoot } from "./utils.ts";

// Find project root
const scriptPath = join(import.meta.dir!, "log-agent.ts");
const projectRoot = findProjectRoot(scriptPath);

// Session log directory
const sessionLogDir = join(projectRoot, "production", "session-logs");
const auditLogFile = join(sessionLogDir, "agent-audit.log");

// Ensure directory exists
if (!existsSync(sessionLogDir)) {
  mkdirSync(sessionLogDir, { recursive: true });
}

// Get input from stdin
const input = Bun.stdin.text();

// Parse agent name from input
let agentName = "unknown";
try {
  const data = JSON.parse(input);
  agentName = data.agent_name || data.name || "unknown";
} catch {
  // Try to extract from raw input
  const nameMatch = input.match(/"agent_name"\s*:\s*"([^"]+)"/);
  if (nameMatch) {
    agentName = nameMatch[1];
  }
}

const timestamp = new Date().toISOString().replace(/[:.]/g, "-").substring(0, 19);
const logEntry = `${timestamp} | Agent invoked: ${agentName}\n`;

appendFileSync(auditLogFile, logEntry, "utf-8");
