import { Config } from '@remotion/cli/config';

// core/media IS Remotion's public root (see MIGRATION.md): staticFile('library/logos/x') →
// ../media/library/x (reusable), staticFile('projects/<proj>/x') → ../media/projects/... (per-video).
Config.setPublicDir('../media');

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
Config.setConcurrency(1); // M4 shares 24 GiB with inference; opt in to more per render
