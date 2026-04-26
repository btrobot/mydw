import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const remoteAdminDir = resolve(__dirname, '..');
const repoRoot = resolve(remoteAdminDir, '..', '..');

function formatTimestamp(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return `${year}-${month}-${day}-${hours}${minutes}${seconds}`;
}

const cliArtifactDir = process.argv[2]?.trim();
const envArtifactDir = process.env.REMOTE_SMOKE_ARTIFACT_DIR?.trim();
const artifactDir = resolve(
  cliArtifactDir ||
    envArtifactDir ||
    join(repoRoot, 'discss', 'artifacts', `remote-users-create-smoke-${formatTimestamp()}`)
);

await mkdir(artifactDir, { recursive: true });

console.log(`[INFO] Remote users create smoke artifact dir: ${artifactDir}`);
console.log('[INFO] Expect remote backend on http://127.0.0.1:8100 and remote admin static entry on http://127.0.0.1:4173/dist-react/index.html?apiBase=http://127.0.0.1:8100');

const child = spawn(process.execPath, [join(__dirname, 'smoke-users-create.mjs'), artifactDir], {
  cwd: repoRoot,
  stdio: 'inherit',
});

const exitCode = await new Promise((resolve, reject) => {
  child.once('error', reject);
  child.once('exit', (code) => resolve(code ?? 1));
});

if (exitCode !== 0) {
  process.exit(exitCode);
}

console.log(`[INFO] Remote users create smoke passed. Evidence saved to: ${artifactDir}`);
