import test from 'node:test';
import assert from 'node:assert/strict';
import { parseTimestamp, relativeTime, deliverySteps } from '../src/utils/requestProgress.js';

const now = Date.parse('2026-11-02T12:00:00Z');
test('renders seconds, minutes, hours and days with singular/plural labels', () => {
  for (const [age, text] of [[0,'just now'],[59,'just now'],[60,'1 minute ago'],[120,'2 minutes ago'],[3600,'1 hour ago'],[7200,'2 hours ago'],[86400,'1 day ago'],[172800,'2 days ago']]) {
    assert.equal(relativeTime(new Date(now-age*1000).toISOString(), now), text);
  }
});
test('missing and invalid timestamps do not claim a recent update', () => {
  assert.equal(relativeTime(null, now),'time unavailable');
  assert.equal(relativeTime('not-a-date', now),'time unavailable');
});
test('historical timezone-less dates are UTC, not local browser time', () => {
  assert.equal(parseTimestamp('2026-11-02T12:00:00').getTime(), now);
  assert.equal(parseTimestamp('2026-11-02T07:00:00-05:00').getTime(), now);
});
test('minor future clock skew does not display negative age', () => {
  assert.equal(relativeTime('2026-11-02T12:00:30Z',now),'just now');
});
test('funded stays at posted delivery stage, separate from money progress', () => {
  assert.equal(deliverySteps('funded')[0].current,true);
  assert.equal(deliverySteps('funded')[1].reached,false);
});
test('only recorded or current stages are marked reached for old delivered records', () => {
  const steps=deliverySteps('delivered',[{status:'open',at:'2026-11-01T00:00:00Z'},{status:'claimed',at:'2026-11-01T01:00:00Z'}]);
  assert.equal(steps[2].reached,false);
  assert.equal(steps[3].reached,true);
  assert.equal(steps[3].at,undefined);
});
test('on-the-way is the current stage and retains its server timestamp', () => {
  const at='2026-11-02T12:00:00Z';
  const steps=deliverySteps('on_the_way',[{status:'on_the_way',at}]);
  assert.equal(steps[2].current,true);
  assert.equal(steps[2].at,at);
  assert.equal(steps[3].reached,false);
});
