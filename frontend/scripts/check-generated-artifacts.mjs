import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import path from 'node:path'

const regenCommand = process.platform === 'win32' ? 'npm.cmd' : 'npm'
const trackedGeneratedSurfaces = [
  'openapi.local.json',
  'src/api',
  'electron/main.js',
  'electron/main.js.map',
  'electron/preload.js',
  'electron/preload.js.map',
  'electron/backendLauncher.js',
  'electron/backendLauncher.js.map',
]

const toPosix = (filePath) => filePath.split(path.sep).join(path.posix.sep)

const listFiles = (surfacePath) => {
  if (!existsSync(surfacePath)) {
    return []
  }

  const stat = statSync(surfacePath)
  if (stat.isFile()) {
    return [surfacePath]
  }

  if (!stat.isDirectory()) {
    return []
  }

  return readdirSync(surfacePath, { withFileTypes: true })
    .sort((left, right) => left.name.localeCompare(right.name))
    .flatMap((entry) => listFiles(path.join(surfacePath, entry.name)))
}

const buildManifest = () => Object.fromEntries(
  trackedGeneratedSurfaces
    .flatMap((surfacePath) => listFiles(surfacePath))
    .sort((left, right) => left.localeCompare(right))
    .map((filePath) => [
      toPosix(filePath),
      createHash('sha256').update(readFileSync(filePath)).digest('hex'),
    ]),
)

const diffManifest = (beforeManifest, afterManifest) => {
  const allPaths = [...new Set([...Object.keys(beforeManifest), ...Object.keys(afterManifest)])]
    .sort((left, right) => left.localeCompare(right))

  return allPaths.filter((filePath) => beforeManifest[filePath] !== afterManifest[filePath])
}

const readStatus = () => spawnSync(
  'git',
  ['status', '--short', '--untracked-files=all', '--', ...trackedGeneratedSurfaces],
  {
    encoding: 'utf8',
    shell: false,
  },
)

const runRegenerate = () => {
  if (process.platform === 'win32') {
    return spawnSync(
      process.env.ComSpec || 'cmd.exe',
      ['/d', '/s', '/c', `${regenCommand} run generated:regenerate`],
      {
        stdio: 'inherit',
        shell: false,
      },
    )
  }

  return spawnSync(regenCommand, ['run', 'generated:regenerate'], {
    stdio: 'inherit',
    shell: false,
  })
}

const beforeManifest = buildManifest()
const beforeStatus = readStatus()

if ((beforeStatus.status ?? 1) !== 0) {
  console.error(beforeStatus.stderr || 'Failed to inspect generated artifact status before regeneration.')
  process.exit(beforeStatus.status ?? 1)
}

const regenerate = runRegenerate()

if ((regenerate.status ?? 1) !== 0) {
  process.exit(regenerate.status ?? 1)
}

const afterManifest = buildManifest()
const afterStatus = readStatus()

if ((afterStatus.status ?? 1) !== 0) {
  console.error(afterStatus.stderr || 'Failed to inspect generated artifact status after regeneration.')
  process.exit(afterStatus.status ?? 1)
}

const beforeOutput = (beforeStatus.stdout || '').trim()
const afterOutput = (afterStatus.stdout || '').trim()
const changedFiles = diffManifest(beforeManifest, afterManifest)

if (changedFiles.length > 0 || beforeOutput !== afterOutput) {
  console.error('Generated artifact drift changed after regeneration.')
  if (changedFiles.length > 0) {
    console.error('Content drift:')
    for (const filePath of changedFiles) {
      console.error(`- ${filePath}`)
    }
  }
  console.error('Before:')
  console.error(beforeOutput || '(clean)')
  console.error('After:')
  console.error(afterOutput || '(clean)')
  process.exit(1)
}

console.log('Generated artifacts are stable after regeneration:', trackedGeneratedSurfaces.join(', '))
