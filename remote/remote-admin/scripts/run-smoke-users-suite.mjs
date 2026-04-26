import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const remoteAdminDir = resolve(__dirname, '..');
const repoRoot = resolve(remoteAdminDir, '..', '..');
const suiteSteps = [
  { scriptName: 'smoke-users-create.mjs', artifactSubdir: 'create', stepUpAttempts: 1 },
  { scriptName: 'smoke-users-update.mjs', artifactSubdir: 'update', stepUpAttempts: 4 },
  { scriptName: 'smoke-users-update-multi.mjs', artifactSubdir: 'update-multi', stepUpAttempts: 3 },
];

function parsePositiveInt(rawValue, fallback) {
  const parsed = Number.parseInt(String(rawValue ?? ''), 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function formatTimestamp(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return `${year}-${month}-${day}-${hours}${minutes}${seconds}`;
}

async function runNodeScript(scriptName, artifactDir) {
  console.log(`[INFO] Running ${scriptName} -> ${artifactDir}`);
  const child = spawn(process.execPath, [join(__dirname, scriptName), artifactDir], {
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
}

const cliArtifactDir = process.argv[2]?.trim();
const envArtifactDir = process.env.REMOTE_SMOKE_ARTIFACT_DIR?.trim();
const stepUpWindowSeconds = parsePositiveInt(
  process.env.REMOTE_BACKEND_ADMIN_STEP_UP_RATE_LIMIT_WINDOW_SECONDS,
  60
);
const stepUpMaxAttempts = parsePositiveInt(
  process.env.REMOTE_BACKEND_ADMIN_STEP_UP_RATE_LIMIT_MAX_ATTEMPTS,
  5
);
const stepUpBufferMilliseconds = parsePositiveInt(
  process.env.REMOTE_ADMIN_SMOKE_STEP_UP_BUFFER_MS,
  2_000
);
const stepUpWindowMilliseconds = stepUpWindowSeconds * 1_000;
const suiteDir = resolve(
  cliArtifactDir ||
    envArtifactDir ||
    join(repoRoot, 'discss', 'artifacts', `remote-users-smoke-suite-${formatTimestamp()}`)
);

await mkdir(suiteDir, { recursive: true });

console.log(`[INFO] Remote users smoke suite dir: ${suiteDir}`);
console.log('[INFO] Expect remote backend on http://127.0.0.1:8100 and remote admin static entry on http://127.0.0.1:4173/dist-react/index.html?apiBase=http://127.0.0.1:8100');
console.log(
  `[INFO] Step-up verify suite throttle: max ${stepUpMaxAttempts} attempts per ${stepUpWindowSeconds}s window (+${stepUpBufferMilliseconds}ms buffer)`
);

let consumedStepUpAttempts = 0;

for (const step of suiteSteps) {
  if (consumedStepUpAttempts > 0 && consumedStepUpAttempts + step.stepUpAttempts > stepUpMaxAttempts) {
    const waitMilliseconds = stepUpWindowMilliseconds + stepUpBufferMilliseconds;
    console.log(
      `[INFO] Waiting ${waitMilliseconds}ms before ${step.scriptName} to avoid admin step-up rate limiting (${consumedStepUpAttempts}/${stepUpMaxAttempts} attempts already used in the current window)`
    );
    await sleep(waitMilliseconds);
    consumedStepUpAttempts = 0;
  }

  await runNodeScript(step.scriptName, join(suiteDir, step.artifactSubdir));
  consumedStepUpAttempts += step.stepUpAttempts;
}

console.log(`[INFO] Remote users smoke suite passed. Evidence saved to: ${suiteDir}`);
