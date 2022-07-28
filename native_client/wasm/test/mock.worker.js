// Mocks stt-wasm.worker.js as it is currently not being transpiled by babel
var nodeWorkerThreads = require('worker_threads');

var parentPort = nodeWorkerThreads.parentPort;
parentPort.postMessage({
    "cmd": "loaded"
});
