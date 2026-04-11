import type { ConfigFile } from '@hey-api/openapi-ts'

export default {
  input: './openapi.local.json',
  output: {
    path: './src/api',
    index: true,
  },
  client: '@hey-api/client-fetch',
  types: {
    enums: 'typescript',
  },
  services: {
    asClass: false,
  },
} satisfies ConfigFile
