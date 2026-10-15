// Generates TypeScript types from shared/schemas. Never edit src/types by hand.
import { readdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { compileFromFile } from "json-schema-to-typescript";

const schemasDir = new URL("../../shared/schemas/", import.meta.url).pathname;
const outDir = new URL("../src/types/", import.meta.url).pathname;

for (const file of await readdir(schemasDir)) {
  if (!file.endsWith(".schema.json")) continue;
  const ts = await compileFromFile(join(schemasDir, file), { cwd: schemasDir });
  await writeFile(join(outDir, file.replace(".schema.json", ".ts")), ts);
}
