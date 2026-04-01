// Skill hook for dewugojin
// Automatically updates active.md when skills are invoked

import { existsSync, readFileSync, writeFileSync } from 'fs';
import { join } from 'path';
import { findProjectRoot } from './utils.ts';

const input = await Bun.stdin.text();

const scriptPath = join(import.meta.dir!, 'skill-hook.ts');
const projectRoot = findProjectRoot(scriptPath);
const stateFile = join(projectRoot, 'production', 'session-state', 'active.md');

// Only proceed if active.md exists
if (!existsSync(stateFile)) {
  console.error('State file not found');
  process.exit(1);
}

// Parse tool call input
let toolInput = '';
try {
  const data = JSON.parse(input);
  toolInput = data.input?.command || data.input || data.command || '';
} catch (e) {
  console.error('JSON parse error:', String(e));
  process.exit(1);
}

// Detect skill invocations
const skillMap: [RegExp, string][] = [
  [/^\/code-review(?:\s+(\S+))?/, 'code-review'],
  [/^\/security-scan(?:\s+(\S+))?/, 'security-scan'],
  [/^\/architecture-review(?:\s+(\S+))?/, 'architecture-review'],
  [/^\/sprint-plan(?:\s+(\S+))?/, 'sprint-plan'],
  [/^\/task-breakdown(?:\s+(\S+))?/, 'task-breakdown'],
];

let matchedSkill: string | null = null;
let targetFile: string | null = null;

for (const [pattern, skill] of skillMap) {
  const match = toolInput.match(pattern);
  if (match) {
    matchedSkill = skill;
    targetFile = match[1] || null;
    break;
  }
}

if (!matchedSkill) {
  console.log('No skill matched, exiting. toolInput:', toolInput);
  process.exit(0);
}

console.log('Skill detected:', matchedSkill, 'file:', targetFile);

// Read current active.md
const content = readFileSync(stateFile, 'utf-8');

// Build skill invocation entry
const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
const skillEntry = `| ${matchedSkill} | ${timestamp} | running | pending |`;

let updated = content;

// Find placeholder row
const placeholderMatch = content.match(/\| \(No [^\)]+\) \| [^\|]+ \| [^\|]+ \| [^\|]+ \|[^\n]*\n/);

if (placeholderMatch) {
  console.log('Found placeholder, replacing');
  updated = content.replace(placeholderMatch[0], skillEntry + '\n');
} else {
  console.log('No placeholder found');
  // Find data row
  const dataRowMatch = content.match(/\| \{[^\}]+\} \| [^\|]+ \| [^\|]+ \| [^\|]+ \|[^\n]*\n/);
  if (dataRowMatch) {
    console.log('Found data row, appending');
    updated = content.replace(dataRowMatch[0], dataRowMatch[0] + skillEntry + '\n');
  }
}

// Write back
writeFileSync(stateFile, updated, 'utf-8');
console.log('Done!');
