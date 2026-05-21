const assert = require('node:assert/strict');

const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const pluginPath = path.join(__dirname, '..', 'app', 'docsify-plugin.js');
const source = fs.readFileSync(pluginPath, 'utf8');

const sandbox = {
  window: { addEventListener() {} },
  rendered: [],
  document: {
    querySelectorAll() {
      return [];
    },
    querySelector() {
      return null;
    },
    body: { classList: { add() {}, remove() {}, toggle() {} } },
    documentElement: {},
    head: { appendChild() {} },
    createElement() {
      return {};
    },
    getElementById() {
      return null;
    },
    addEventListener() {},
    dispatchEvent() {},
  },
  console,
  setTimeout,
  clearTimeout,
  Event: class Event {
    constructor(type) {
      this.type = type;
    }
  },
  requestAnimationFrame(callback) {
    return setTimeout(callback, 0);
  },
  NodeFilter: {
    SHOW_TEXT: 4,
    FILTER_REJECT: 2,
    FILTER_ACCEPT: 1,
  },
};
sandbox.window.renderMathInElement = (el, options) => {
  sandbox.rendered.push({ el, options });
};
sandbox.globalThis = sandbox;

vm.runInNewContext(source, sandbox, { filename: pluginPath });

const plugin = sandbox.window.$docsify.plugins[0];
const hook = {
  beforeEach(callback) {
    this.beforeEachCallback = callback;
  },
  doneEach(callback) {
    this.doneEachCallback = callback;
  },
};
plugin(hook, {
  route: {
    file: '20260422-20260521/2605.19590v1-test.md',
    path: '/20260422-20260521/2605.19590v1-test',
  },
});

const input = [
  '---',
  'title: Test',
  '---',
  '',
  'fixed $\\\\theta=60^\\\\circ$ and $w_{\\\\text{narrow}}=w_{\\\\text{open}}-\\\\frac{h\\\\sin\\\\phi}{\\\\tan\\\\theta}$',
].join('\n');

const output = hook.beforeEachCallback(input);

assert.match(output, /\$\\theta=60\^\\circ\$/);
assert.match(output, /\$w_\{\\text\{narrow\}\}=w_\{\\text\{open\}\}-\\frac\{h\\sin\\phi\}\{\\tan\\theta\}\$/);
assert.doesNotMatch(output, /\\\\theta/);
assert.doesNotMatch(output, /\\\\text/);

const wrappedOutput = hook.beforeEachCallback(String.raw`inline \\(\\phi=25^\\circ\\) and block \\[w_{\\text{open}}\\]`);
assert.match(wrappedOutput, /\$\\phi=25\^\\circ\$/);
assert.match(wrappedOutput, /\$\$w_\{\\text\{open\}\}\$\$/);
assert.doesNotMatch(wrappedOutput, /\\\\phi/);
assert.doesNotMatch(wrappedOutput, /\\\\text/);

let textNode = {
  nodeValue: 'escaped \\$w_{\\text{open}}\\$ and $\\theta$',
  parentElement: {
    closest() {
      return null;
    },
  },
};
let root = {
  firstChild: null,
  classList: { add() {}, remove() {} },
  appendChild() {},
  querySelector() {
    return null;
  },
  querySelectorAll() {
    return [];
  },
};
sandbox.document.querySelector = (selector) => {
  if (selector === '.markdown-section') return root;
  return null;
};
sandbox.document.createTreeWalker = (walkerRoot, whatToShow, filter) => {
  let done = false;
  return {
    currentNode: null,
    nextNode() {
      if (done) return false;
      done = true;
      if (
        filter &&
        typeof filter.acceptNode === 'function' &&
        filter.acceptNode(textNode) !== sandbox.NodeFilter.FILTER_ACCEPT
      ) {
        return false;
      }
      this.currentNode = textNode;
      return true;
    },
  };
};
sandbox.NodeFilter = sandbox.NodeFilter;

hook.doneEachCallback && hook.doneEachCallback();

assert.equal(textNode.nodeValue, 'escaped $w_{\\text{open}}$ and $\\theta$');
assert.equal(sandbox.rendered.length, 1);

console.log('docsify math utils tests passed');
