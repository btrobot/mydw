import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const repoRoot = path.resolve(__dirname, '..', '..')

const read = (relativePath) => readFileSync(path.join(repoRoot, relativePath), 'utf8')
const readJson = (relativePath) => JSON.parse(read(relativePath))

const backendConfig = read('backend/core/config.py')
const match = backendConfig.match(/APP_VERSION:\s*str\s*=\s*"([^"]+)"/)
if (!match) {
  throw new Error('Failed to extract APP_VERSION from backend/core/config.py')
}

const canonical = match[1]
const failures = []

const frontendPackage = readJson('frontend/package.json')
const frontendLock = readJson('frontend/package-lock.json')
const cliPackage = readJson('frontend/scripts/cli/package.json')
const cliLock = readJson('frontend/scripts/cli/package-lock.json')
const cliIndex = read('frontend/scripts/cli/src/index.ts')
const cliVersion = read('frontend/scripts/cli/src/version.ts')
const readme = read('README.md')
const inventory = read('docs/epic-7-version-inventory.md')
const openapiLocal = read('frontend/openapi.local.json')

const expect = (condition, message) => {
  if (!condition) {
    failures.push(message)
  }
}

expect(frontendPackage.version === canonical, 'frontend/package.json version drifted')
expect(frontendLock.version === canonical, 'frontend/package-lock.json top-level version drifted')
expect(frontendLock.packages?.['']?.version === canonical, 'frontend/package-lock.json root package version drifted')
expect(cliPackage.version === canonical, 'frontend/scripts/cli/package.json version drifted')
expect(cliLock.version === canonical, 'frontend/scripts/cli/package-lock.json top-level version drifted')
expect(cliLock.packages?.['']?.version === canonical, 'frontend/scripts/cli/package-lock.json root package version drifted')
expect(cliIndex.includes("from './version.js'"), 'frontend/scripts/cli/src/index.ts must import VERSION from ./version.js')
expect(!cliIndex.includes('const VERSION ='), 'frontend/scripts/cli/src/index.ts must not hardcode VERSION')
expect(cliVersion.includes(`export const VERSION = '${canonical}'`), 'frontend/scripts/cli/src/version.ts drifted')
expect(readme.includes(`**版本**: ${canonical}`), 'README version drifted')
expect(inventory.includes(`- \`${canonical}\``), 'docs/epic-7-version-inventory.md canonical version drifted')
expect(openapiLocal.includes(`"version": "${canonical}"`), 'frontend/openapi.local.json version drifted')

if (failures.length > 0) {
  console.error('Version synchronization check failed:')
  for (const failure of failures) {
    console.error(`- ${failure}`)
  }
  process.exit(1)
}

console.log(`Version surfaces are synchronized to ${canonical}`)
