import EmbeddedPostgres from 'embedded-postgres';
import { existsSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { execFileSync } from 'node:child_process';

mkdirSync('.runtime', { recursive: true });
// PostgreSQL's Windows initdb cannot read UTF-8 configuration paths containing
// some ANSI user names; the existing DOS path keeps all files in this workspace.
const root = process.platform === 'win32' ? execFileSync('python', ['-c',
  'import ctypes,os; b=ctypes.create_unicode_buffer(32768); ctypes.windll.kernel32.GetShortPathNameW(os.getcwd(),b,len(b)); print(b.value)',
], { encoding: 'utf8' }).trim() : process.cwd();
const databaseDir = resolve(root, '.runtime/postgres');
const pg = new EmbeddedPostgres({
  databaseDir, user: 'postgres', password: 'pulso-local-only', port: 55432,
  persistent: true, initdbFlags: ['--encoding=UTF8', '--locale=C', ...(process.platform === 'win32' ?
    ['-L', resolve(root, 'node_modules/@embedded-postgres/windows-x64/native/share')] : [])],
  postgresFlags: ['-h', '127.0.0.1'],
  onLog: () => {}, onError: (e) => process.stderr.write(String(e) + '\n'),
});
if (!existsSync(resolve(databaseDir, 'PG_VERSION'))) await pg.initialise();
await pg.start();
const client = pg.getPgClient();
await client.connect();
for (const name of ['pulso', 'pulso_test']) {
  const result = await client.query('SELECT 1 FROM pg_database WHERE datname=$1', [name]);
  if (!result.rowCount) await client.query(`CREATE DATABASE ${name}`);
}
await client.end();
console.log('PostgreSQL local pronto em 127.0.0.1:55432 (somente desenvolvimento).');
let stopping = false;
async function stop() { if (stopping) return; stopping = true; await pg.stop(); process.exit(0); }
process.on('SIGINT', stop);
process.on('SIGTERM', stop);
setInterval(() => {}, 60_000);
