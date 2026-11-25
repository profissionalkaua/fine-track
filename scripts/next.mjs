import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { resolve, dirname, delimiter } from 'node:path';
const localNode = resolve(`node_modules/node/bin/node${process.platform === 'win32' ? '.exe' : ''}`);
const command = process.argv[2] || 'dev';
const env = Object.fromEntries(Object.entries(process.env).filter(([k]) => k.toLowerCase() !== 'path'));
env.PATH = `${dirname(localNode)}${delimiter}${process.env.PATH || process.env.Path}`;
const child = spawn(existsSync(localNode) ? localNode : process.execPath,
  [resolve('node_modules/next/dist/bin/next'), command, 'web',
    ...(command === 'build' ? [] : ['--hostname', '127.0.0.1'])], { stdio: 'inherit', env });
child.on('exit', code => process.exitCode = code ?? 1);
process.on('SIGINT', () => child.kill('SIGINT'));
process.on('SIGTERM', () => child.kill('SIGTERM'));
