import type { ConfigFile } from '@hey-api/openapi-ts'

export default {
  input: 'http://127.0.0.1:8000/openapi.json',
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
