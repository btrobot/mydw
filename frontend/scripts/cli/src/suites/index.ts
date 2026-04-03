/**
 * 测试套件入口
 * 导出所有测试用例和运行函数
 */

export { runAccountTests, getAccountTests, printTestSummary } from './accounts.js'
export type { TestCase, TestResult } from './accounts.js'

export { runTaskTests, getTaskTests } from './tasks.js'

export { runMaterialTests, getMaterialTests } from './materials.js'
