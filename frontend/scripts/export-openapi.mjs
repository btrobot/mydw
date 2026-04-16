import { spawnSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const scriptPath = path.join(__dirname, 'export_openapi.py')

const candidates = [
  { cmd: 'python3', args: [scriptPath] },
  { cmd: 'python', args: [scriptPath] },
  { cmd: 'py', args: ['-3', scriptPath] },
]

let lastError = null

for (const candidate of candidates) {
  const result = spawnSync(candidate.cmd, candidate.args, {
    stdio: 'inherit',
    shell: false,
  })

  if (result.error) {
    lastError = result.error
    continue
  }

  if (result.status === 0) {
    process.exit(0)
  }

  lastError = new Error(`Command exited with status ${result.status ?? 1}: ${candidate.cmd}`)
}

if (lastError) {
  console.error(`Failed to export OpenAPI spec: ${lastError.message}`)
}
process.exit(1)
