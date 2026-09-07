import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';
import {mkdirSync, readFileSync} from 'fs';
import {execFileSync} from 'child_process';
import {fileURLToPath} from 'url';
import path from 'path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const [contractArg, outputArg] = process.argv.slice(2);
if (!contractArg || !outputArg) {
  throw new Error('Usage: render-podcast-stage.mjs CONTRACT_JSON OUTPUT_MP4');
}

const contractPath = path.resolve(contractArg);
const output = path.resolve(outputArg);
const props = JSON.parse(readFileSync(contractPath, 'utf8'));
if (
  props?.schema_version !== 1 ||
  !Number.isInteger(props?.primary_audio?.duration_ms) ||
  props.primary_audio.duration_ms <= 0 ||
  !Number.isInteger(props?.render?.fps) ||
  !Number.isInteger(props?.render?.width) ||
  !Number.isInteger(props?.render?.height)
) {
  throw new Error('Invalid PodcastStage input props');
}

mkdirSync(path.dirname(output), {recursive: true});
// Root also exposes the legacy generated shot list. PodcastStage itself is
// registered explicitly, but a clean checkout still needs that generated import.
execFileSync(process.execPath, [path.join(root, 'scripts/gen-registry.mjs')], {stdio: 'ignore'});
const serveUrl = await bundle({
  entryPoint: path.join(root, 'src/index.ts'),
  publicDir: path.join(root, '..', 'media'),
});
const composition = await selectComposition({serveUrl, id: 'PodcastStage', inputProps: props});
const expectedFrames = Math.ceil(props.primary_audio.duration_ms * props.render.fps / 1000);
if (
  composition.durationInFrames !== expectedFrames ||
  composition.fps !== props.render.fps ||
  composition.width !== props.render.width ||
  composition.height !== props.render.height
) {
  throw new Error('PodcastStage calculated metadata does not match the contract');
}

await renderMedia({
  serveUrl,
  composition,
  inputProps: props,
  outputLocation: output,
  codec: 'h264',
  pixelFormat: 'yuv420p',
  imageFormat: 'jpeg',
  crf: 18,
  scale: 1,
  concurrency: 1,
  muted: true,
  overwrite: true,
  onProgress: ({progress}) => process.stdout.write(`\rPodcastStage: ${Math.round(progress * 100)}%`),
});
process.stdout.write(`\n${output}\n`);
