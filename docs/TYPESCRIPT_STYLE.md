# TYPESCRIPT_STYLE.md

Language Model guide to Neil TypeScript programming

## TypeScript version

* Require `5.x` (latest stable, loose-pinned via devDependencies; no version lock-in beyond floor `>=9` for ESLint).
* Required strict flags: `strict: true`, `noImplicitAny: true`, `noUncheckedIndexedAccess: true`, `target: es2020`, `module: esnext`, `moduleResolution: bundler`.
* Point at canonical `tsconfig.json` at repo root (propagated from `templates/typescript/tsconfig.json`).

## FILENAMES
* Prefer snake_case for TypeScript filenames.
* Avoid CamelCase in filenames. Reserve CamelCase for class names, type names, and interface names.
* Keep filenames descriptive, and consistent with the primary thing the file provides.
* Use only lowercase letters, numbers, and underscores in filenames.

## CODE STRUCTURE

* Use small, single-task functions rather than one large function.
* Prefer explicit named functions over deeply nested inline callbacks.
* Keep top-level code minimal.
* Prefer clear data flow with explicit parameters and return values.
* Avoid hidden shared state when possible.
* For scripts, use a `main()` function and call it at the bottom.
* For library code, export small focused functions.
* Use `async` and `await` rather than raw promise chains when possible.
* Avoid broad `try/catch` blocks when possible. I find they often hide bugs.
* Use `try/catch` rarely, and keep the scope small.
* Throw `Error` objects rather than returning silent failure values.
* Apply "fix the design, not the symptom" here too: do not paper over a misbehaving caller with a swallowed error or a silent default. See Design philosophy in docs/REPO_STYLE.md.
* Return statements should be simple and should not build large objects or long strings inline. Store computed values first, then return the variable.
* Add comments within the code to describe what different lines are doing, especially for complex lines.
* Please only use ASCII characters in the script. If special characters are needed in output, escape them when appropriate.

## STRICT TYPES

* Use TypeScript because the type system is useful, so use it.
* Prefer explicit parameter types and return types for exported functions.
* Add type annotations when they improve clarity.
* Avoid `any` whenever possible.
* Prefer narrow types over loose types.
* Prefer `unknown` over `any` when the type is truly unknown.
* Prefer simple inline object types or named `type` aliases.
* Use `interface` only when it clearly improves readability or extension.

### Good

```ts
function greaterThan(a: number, b: number): boolean {
	return a > b;
}
```

### Avoid

```ts
function processData(data: any): any {
	return data;
}
```

## CONST, LET, AND VAR

* Never use `var`.
* Prefer `const` by default.
* Use `let` only when reassignment is actually needed.

## FUNCTIONS

* Prefer `function name()` for most named functions.
* Be conservative with arrow functions.
* Arrow functions are fine for short callbacks when the logic is obvious.
* If the callback is doing real work, give it a name with `function`.
* If a function would be hard to understand without a comment, rewrite it more clearly.

### Allowed

```ts
const valuesSorted = values.sort((a, b) => a.count - b.count);
```

### Preferred rewrite for more complex logic

```ts
function compareCounts(a: Item, b: Item): number {
	const diff = a.count - b.count;
	return diff;
}

const valuesSorted = values.sort(compareCounts);
```

## CLASSES

* Use classes only when they clearly match the problem.
* Prefer plain functions and plain objects for simple scripts and data transformations.
* Do not introduce classes just to look object-oriented.

## OBJECTS AND DATA

* Prefer plain objects for structured data.
* Keep object shapes consistent.
* Avoid adding properties to objects far away from where the objects are created.
* Prefer building a complete object in one place when practical.

## NULL AND UNDEFINED

* Be explicit about optional values.
* Use `undefined` consistently for missing values unless there is a strong reason to use `null`.
* Do not mix both without a clear reason.

## STRINGS

* Use template strings when interpolation helps readability.
* Prefer simple string assembly over overly clever helpers.
* Keep multiline text readable, but avoid unnecessary complexity.

## QUOTING

* Avoid backslash escaping quotes inside strings when possible.
* Prefer alternating quote styles instead.
* Use double quotes on the outside with single quotes inside.
* Or use single quotes on the outside with double quotes inside.
* This is especially useful for HTML like `"<span style='color: red'>text</span>"`.

## ARRAYS

* Prefer array methods when they improve clarity.
* Do not chain too many methods if it hurts readability.
* If `map().filter().reduce()` becomes hard to read, break it into steps.

## ASYNC CODE

* Prefer `async` and `await`.
* Keep async flow easy to follow.
* Avoid mixing `await` with `.then()` in the same block unless there is a clear reason.
* For network requests, be polite to servers. Add a small delay when appropriate unless the official API says otherwise.

## IMPORTS

* Never use wildcard imports.
* Prefer explicit imports.
* Keep imports grouped and ordered.
* Standard library or platform imports first, then external packages, then local modules.
* Within each group, keep the order consistent and easy to scan.

### Example

```ts
import fs from "node:fs";
import path from "node:path";

import yaml from "js-yaml";

import { readConfig } from "./read_config";
import { writeReport } from "./write_report";
```

## EXPORTS

* Prefer named exports over default exports.
* Named exports are easier to track and refactor.

## ERROR HANDLING

* Do not swallow errors.
* If an error matters, raise it clearly.
* Keep `try/catch` blocks narrow.
* Add useful context to thrown errors when needed.

## COMMENTING

* Use comments to explain why, not to restate obvious code.
* Visually separate major functions with a comment of only equal signs when it helps readability. For example:

```ts
//============================================
```

* Keep line lengths less than 100 characters.
* Comments should be on a line of their own before the code they are commenting.
* No emoji or special characters in comments, only ASCII characters.

## TESTING

* I like to test the code.
* For small utility functions, a short simple test is good.
* For real projects, use a normal test framework and keep tests in a `tests/` folder.
* Keep tests small and deterministic.
* Avoid network calls, random behavior, and time-based logic unless mocked.
* Browser tests live under `tests/playwright/` (see [PLAYWRIGHT_USAGE.md](PLAYWRIGHT_USAGE.md)). Pure Node unit tests via `node --test tests/test_*.mjs`. TS hygiene tests under `tests/test_typescript_*.py` enforce tsc, package.json schema, tsconfig canonical fields, and ESLint flat-config presence. ESLint correctness is gated by `check_codebase.sh` step 3 directly; no separate pytest wrapper.

## FORMATTERS AND LINTERS

* Use Prettier for formatting. Let Prettier own whitespace, semicolons, and line breaks.
* Use ESLint for catching real bugs: unused variables, implicit `any`, unreachable code.
* Do not fight Prettier on style choices. If Prettier formats it, that is the style.
* ESLint rules should catch problems, not enforce cosmetic preferences that Prettier already handles.
* Strict typing is preferred. Enable `noImplicitAny` and `strict` in `tsconfig.json`.
* ESLint config lives at `eslint.config.js` at the repo root (canonical, propagated). Lint correctness is enforced by `check_codebase.sh` step 3 (`npx eslint --max-warnings 0 '**/*.{ts,tsx,mts,cts,js,mjs,cjs}'`).
* Prettier scope in this repo is JS, TypeScript, MJS, CJS, TSX, MTS, CTS only. JSON, YAML, Markdown, and Python files are explicitly NOT prettier-managed.
* Indent is two spaces for every prettier-managed extension (prettier default; documented in propagated `.prettierrc`). This differs from the Python tabs rule in `docs/PYTHON_STYLE.md`; agents editing `.py` use tabs, agents editing `.ts`/`.mjs`/etc use two spaces. Do not over-generalize one language's rule to the other.
* Auto-fix path when `npm run check` step 4 (`format:check`) fails: `npm run format:write` (script alias for `npx prettier --write '**/*.{ts,tsx,mts,cts,js,mjs,cjs}'`).
* `.prettierignore` ships from the template and covers noisy generated trees (`node_modules/`, `dist/`, `dist-single/`, `_site/`, `generated/`, `coverage/`, `playwright-report/`, `test-results/`, `blob-report/`, `package-lock.json`).

### ESLint canonical rules

Each enabled rule enforces a single class of error:

- `@typescript-eslint/no-explicit-any: error` &mdash; `any` defeats type system.
- `@typescript-eslint/no-unused-vars: error` &mdash; dead code rots.
- `@typescript-eslint/explicit-function-return-type: error` &mdash; exported function signatures are API. Severity matches `check_codebase.sh` step 3 `--max-warnings 0` (the prior `warn` setting was dead documentation since `--max-warnings 0` upgraded every warn to a gate failure anyway).
- `@typescript-eslint/no-floating-promises: error` &mdash; silent async errors.
- `no-var: error` &mdash; function-scoping breaks expectations.
- `prefer-const: error` &mdash; mutability should be deliberate.
- `no-implicit-coercion: warn` &mdash; silent type coercion hides bugs.
- `eqeqeq: error` &mdash; `==` coerces; use `===`.
- `no-throw-literal: error` &mdash; stack traces require Error instances.
- `no-console: warn` &mdash; production code should not log to console (user decision: warn only, do not fail builds).

### tsconfig.json canonical fields

| Field | Value | Why |
| --- | --- | --- |
| `target` | `es2020` | Widely-supported modern JavaScript (async/await, nullish coalescing, optional chaining). |
| `module` | `esnext` | Native ESM, no transpilation to CJS. |
| `moduleResolution` | `bundler` | Resolves as bundlers do (esbuild, webpack, parcel). |
| `strict` | `true` | Enables all strict type checks. |
| `noImplicitAny` | `true` | Explicit type annotations required. |
| `noUncheckedIndexedAccess` | `true` | Accessing an array or object by index/key is `unknown` unless bounds-checked. |
| `noImplicitOverride` | `true` | Derived class methods must mark `override` keyword. |
| `verbatimModuleSyntax` | `true` | Import/export syntax must match module kind exactly. |
| `useUnknownInCatchVariables` | `true` | Caught exceptions are `unknown`, not `any`. |
| `noEmit` | `true` | Type-check only; do not emit `.js` files. |
| `skipLibCheck` | `true` | Skip type-checking declaration files (speed). |
| `noFallthroughCasesInSwitch` | `true` | Every case must break or return. |
| `noImplicitReturns` | `true` | All code paths must return a value. |
| `noUnusedLocals` | `true` | Unused local variables are errors. |
| `noUnusedParameters` | `true` | Unused function parameters are errors. |
| `forceConsistentCasingInFileNames` | `true` | Import paths must match filesystem case exactly. |
| `isolatedModules` | `true` | Files can be transpiled independently (no cross-file const enum). |
| `esModuleInterop` | `true` | Interop helpers for CommonJS imports (rare; maintained for compat). |
| `sourceMap` | `true` | Generate source maps for debugging. |
| `lib` | `["dom", "dom.iterable", "esnext"]` | Browser APIs, DOM iteration, ESM features. |

### Opt-in strict flags (not default)

`exactOptionalPropertyTypes: true` is intentionally NOT in the default `tsconfig.json` the template ships. The flag makes `{ x?: string }` non-assignable to `{ x: string | undefined }`, which most third-party `@types/*` packages do not comply with even when `skipLibCheck: true` is set. Consumers see spurious errors from `node_modules`. A repo that wants the stricter shape can add the flag locally to its own `tsconfig.json` (which is consumer-owned after bootstrap); per-type assertions or `skipLibCheck` interactions are the consumer's responsibility once enabled.

A wider type-check pass covers `tests/` and `tools/` via `tsconfig.lint.json` (`extends: "./tsconfig.json"`, `include: ["tests/**/*.ts", "tools/**/*.ts"]`); `check_codebase.sh` step 2 always runs it.

Heads-up: `tsc -p tsconfig.lint.json` exits 2 with `TS18003` ("No inputs were found in config file") when its `include` list matches no files. A consumer with no `tests/*.ts` and no `tools/*.ts` will hit this on `check_codebase.sh` step 2. Workarounds: (1) seed a stub `.ts` in either tree, or (2) edit the consumer-owned `tsconfig.lint.json` and narrow `include` to a tree that exists.

## BUILD SYSTEM

Use `npx tsc --noEmit -p tsconfig.json` to type-check, and `npx esbuild <entry>.ts --bundle --format=esm --target=es2020 --platform=browser --minify --sourcemap --outfile=dist/main.js` for runtime bundle.

### Why this shape

esbuild produces a single deterministic ESM bundle GitHub Pages serves without per-file MIME quirks. The alternative (repo-root `tsc -p tsconfig.json` emitting many `.js` files served alongside `index.html`) multiplies HTTP requests and produces inconsistent module-resolution across browsers.

### Output convention

Single `dist/main.js` + `dist/index.html` + `dist/.nojekyll`. GitHub Pages serves `dist/`. No `dist-single/` portable single-file variant in the canonical base.

### Canonical scripts

- `[build_github_pages.sh](../build_github_pages.sh)` (build esbuild bundle).
- `[run_web_server.sh](../run_web_server.sh)` (serve `dist/` on random port).
- `[check_codebase.sh](../check_codebase.sh)` (orchestrates typecheck, wider typecheck via `tsconfig.lint.json`, lint, format-check, css-policy if present, and Node unit tests; build and Playwright are explicitly out of scope and run separately via `npm run build` / `npm run test:playwright`).
- `[dist_clean.sh](../dist_clean.sh)` (wipe `dist/`).

### Module system

ESM only. No IIFE. No file:// loading path.

### Lockfile policy

`package-lock.json` committed in every TS consumer repo. Not propagated by `propagate_style_guides.py` (per-repo artifact, generated by `npm install` at bootstrap). `yarn.lock` and `pnpm-lock.yaml` not used.

## CONFIGURATION

* The program should not require custom environment variables to function.
* Configuration must be explicit and visible via config files or command line arguments.
* Environment variables may be read only when they are standard OS or ecosystem variables, not variables invented to control program behavior.

## Canonical repo shape

This is the baseline TypeScript repository layout:

- `src/main.ts` &mdash; entry point (legacy `src/init.ts` accepted via fallback in `build_github_pages.sh`).
- `src/index.html` &mdash; HTML host with `<script type="module" src="main.js">`.
- `src/style.css` &mdash; stylesheet copied verbatim into `dist/`.
- `dist/` &mdash; only build output (canonical GitHub Pages artifact).

This is the canonical floor, not a ceiling. Per-repo additions (`src/*.ts` modules, `tests/test_*.mjs`, `tests/playwright/*.spec.ts`) are expected and not constrained. `check_codebase.sh` step 6 (`node --import tsx --test 'tests/test_*.mjs'`) SKIPs cleanly (does not fail the gate) when no `tests/test_*.mjs` files are present, so a fresh consumer can land its first test without a placeholder smoke file shipped by the template.

## ARGUMENT PARSING

* Be conservative. Only add arguments users frequently need to change between runs.
* Good candidates:
  - Input and output file paths
  - Mode switches
  - Behavior toggles
* Hardcode minor internal settings instead of turning everything into a flag.
* If a script needs CLI parsing, keep it small and readable.

## DATA FILES

* YAML favorite, readable, editable
* CSV spreadsheet input and output
* JSON good for larger structured data
* PNG images, graphics, figures, pixel data

## GENERAL STYLE

* Prefer plain language in names and comments.
* Keep the code easy to scan.
* Avoid clever code when a direct version is easier to read.
* I want code that is easy to maintain later, not code that tries to impress people.
