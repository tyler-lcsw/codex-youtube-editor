import {bundle} from '@remotion/bundler';
import {makeCancelSignal, renderMedia, selectComposition} from '@remotion/renderer';
import {createReadStream} from 'fs';
import {copyFileSync, cpSync, mkdirSync, mkdtempSync, readFileSync, renameSync, rmSync} from 'fs';
import {createHash} from 'crypto';
import {fileURLToPath} from 'url';
import os from 'os';
import path from 'path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const [contractArg, outputArg] = process.argv.slice(2);
if (!contractArg || !outputArg) {
  throw new Error('Usage: render-podcast-stage.mjs CONTRACT_JSON OUTPUT_MP4');
}

const contractPath = path.resolve(contractArg);
const output = path.resolve(outputArg);
const partialOutput = `${output}.partial-${process.pid}.mp4`;
const mediaRoot = path.resolve(root, '..', 'media');
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

const sha256 = (file) => new Promise((resolve, reject) => {
  const digest = createHash('sha256');
  const stream = createReadStream(file);
  stream.on('error', reject);
  stream.on('data', (chunk) => digest.update(chunk));
  stream.on('end', () => resolve(digest.digest('hex')));
});

const stagePublicMedia = async () => {
  const staged = mkdtempSync(path.join(os.tmpdir(), 'podcast-stage-media-'));
  try {
    // Fonts are repository-owned static assets rather than contract inputs.
    cpSync(path.join(mediaRoot, 'library', 'fonts'), path.join(staged, 'library', 'fonts'), {recursive: true});

    const refs = new Map();
    if (props.identity.artwork) refs.set(props.identity.artwork.path, props.identity.artwork.sha256);
    for (const event of props.visual_events ?? []) {
      const asset = event?.treatment?.asset;
      if (!asset) continue;
      const priorHash = refs.get(asset.path);
      if (priorHash && priorHash !== asset.sha256) throw new Error(`PodcastStage asset ${asset.path} has conflicting hashes`);
      refs.set(asset.path, asset.sha256);
    }

    for (const [relativePath, expectedHash] of refs) {
      if (path.isAbsolute(relativePath)) throw new Error('PodcastStage media paths must be relative');
      const source = path.resolve(mediaRoot, relativePath);
      if (!source.startsWith(`${mediaRoot}${path.sep}`)) throw new Error('PodcastStage media path escapes the media root');
      const destination = path.resolve(staged, relativePath);
      if (!destination.startsWith(`${staged}${path.sep}`)) throw new Error('PodcastStage media path escapes the staged bundle');
      mkdirSync(path.dirname(destination), {recursive: true});
      copyFileSync(source, destination);
      if (await sha256(destination) !== expectedHash) throw new Error(`PodcastStage media hash changed: ${relativePath}`);
    }
    return staged;
  } catch (error) {
    rmSync(staged, {recursive: true, force: true});
    throw error;
  }
};

mkdirSync(path.dirname(output), {recursive: true});
rmSync(partialOutput, {force: true});

const cancellation = makeCancelSignal();
let interruptedBy;
const interrupt = (signal) => {
  interruptedBy ??= signal;
  cancellation.cancel();
};
const onSigint = () => interrupt('SIGINT');
const onSigterm = () => interrupt('SIGTERM');
process.once('SIGINT', onSigint);
process.once('SIGTERM', onSigterm);

let lastProgressTenth = -1;
const reportProgress = (progress) => {
  const tenth = Math.max(0, Math.min(1000, Math.floor(progress * 1000)));
  if (tenth === lastProgressTenth) return;
  lastProgressTenth = tenth;
  process.stdout.write(`\rPodcastStage render: ${(tenth / 10).toFixed(1)}%`);
};

let stagedMedia;
try {
  stagedMedia = await stagePublicMedia();
  process.stdout.write('PodcastStage bundle: starting\n');
  const serveUrl = await bundle({
    entryPoint: path.join(root, 'src/podcast-index.ts'),
    publicDir: stagedMedia,
    // The bundle may symlink its disposable, hash-verified media snapshot. This
    // avoids a second copy without exposing the live project media directory.
    symlinkPublicDir: true,
    enableCaching: true,
  });
  if (interruptedBy) throw new Error(`PodcastStage interrupted by ${interruptedBy}`);

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
    outputLocation: partialOutput,
    codec: 'h264',
    pixelFormat: 'yuv420p',
    imageFormat: 'jpeg',
    crf: 18,
    scale: 1,
    concurrency: 1,
    muted: true,
    overwrite: true,
    cancelSignal: cancellation.cancelSignal,
    onProgress: ({progress}) => reportProgress(progress),
  });
  if (interruptedBy) throw new Error(`PodcastStage interrupted by ${interruptedBy}`);

  reportProgress(1);
  renameSync(partialOutput, output);
  process.stdout.write(`\n${output}\n`);
} catch (error) {
  rmSync(partialOutput, {force: true});
  if (interruptedBy) {
    process.stderr.write(`PodcastStage interrupted by ${interruptedBy}\n`);
    process.exitCode = interruptedBy === 'SIGINT' ? 130 : 143;
  } else {
    throw error;
  }
} finally {
  process.removeListener('SIGINT', onSigint);
  process.removeListener('SIGTERM', onSigterm);
  if (stagedMedia) rmSync(stagedMedia, {recursive: true, force: true});
}
