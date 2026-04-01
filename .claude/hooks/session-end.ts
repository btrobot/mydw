// Session end hook for dewugojin
import { join } from "path";
import { findProjectRoot, header, warn, ok, getUncommittedChanges, updateSessionState } from "./utils.ts";

// Find project root using git repo location
const scriptPath = join(import.meta.dir!, "session-end.ts");
const projectRoot = findProjectRoot(scriptPath);
process.chdir(projectRoot);

header("DewuGoJin - Session Ending");

// Check for unsaved changes
const changes = getUncommittedChanges();
if (changes) {
  console.log();
  warn("Uncommitted changes detected:");
  console.log(changes);
  console.log();
}

// Update session state
updateSessionState(projectRoot);

// Show next steps
console.log();
header("Next Steps");
console.log("  1. Ensure all changes are committed");
console.log("  2. Run /code-review to review code");
console.log("  3. Run /security-scan for security checks");
console.log("  4. Update session-state record");
console.log();

ok("Session cleanup complete");
