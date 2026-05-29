const assert = require('node:assert/strict');

global.window = global.window || {};

require('../app/workflows.runner.js');

const {
  normalizeDateForToken,
  inclusiveDateDays,
  buildQuickFetchDateRangeInputs,
} = global.window.DPRWorkflowRunner.__test;

function testNormalizeDateForToken() {
  assert.equal(normalizeDateForToken('2026-05-21'), '20260521');
  assert.equal(normalizeDateForToken('2026-02-30'), '');
  assert.equal(normalizeDateForToken('20260521'), '');
}

function testInclusiveDateDays() {
  assert.equal(inclusiveDateDays('2026-05-21', '2026-05-21'), 1);
  assert.equal(inclusiveDateDays('2026-05-21', '2026-05-29'), 9);
  assert.equal(inclusiveDateDays('2026-05-29', '2026-05-21'), -7);
}

function testBuildDateRangeInputsForDeepRead() {
  const inputs = buildQuickFetchDateRangeInputs('2026-05-21', '2026-05-29', 'standard');
  assert.equal(inputs.fetch_days, '9');
  assert.equal(inputs.fetch_mode, 'standard');
  assert.equal(inputs.run_date_token, '20260521-20260529');
  assert.equal(inputs.skip_llm_refine, 'false');
  assert.equal(inputs.force_deep, 'true');
}

function testBuildDateRangeInputsForSkims() {
  const inputs = buildQuickFetchDateRangeInputs('2026-05-21', '2026-05-29', 'skims');
  assert.equal(inputs.fetch_days, '9');
  assert.equal(inputs.fetch_mode, 'skims');
  assert.equal(inputs.run_date_token, '20260521-20260529');
  assert.equal(inputs.force_deep, 'false');
}

function testBuildDateRangeInputsRejectsInvalidRange() {
  assert.throws(
    () => buildQuickFetchDateRangeInputs('2026-05-29', '2026-05-21', 'standard'),
    /日期范围无效/,
  );
}

testNormalizeDateForToken();
testInclusiveDateDays();
testBuildDateRangeInputsForDeepRead();
testBuildDateRangeInputsForSkims();
testBuildDateRangeInputsRejectsInvalidRange();

console.log('workflow runner tests passed');
