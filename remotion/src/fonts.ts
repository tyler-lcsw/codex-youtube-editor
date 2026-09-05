// Vendored Latin fonts; render without Google Fonts requests.
// Keep fonts, brand.ts and brand.md aligned when changing the brand.
import {cancelRender, continueRender, delayRender, staticFile} from 'remotion';

export const FONT_DISPLAY = 'Space Grotesk';
export const FONT_BODY = 'Inter';
export const FONT_MONO = 'JetBrains Mono';
export const FONT_SERIF = 'Spectral';

if (typeof document !== 'undefined') {
  const handle = delayRender('Load bundled brand fonts');
  const families: Array<[string, string, number[]]> = [
    [FONT_DISPLAY, 'SpaceGrotesk', [500, 600, 700]],
    [FONT_BODY, 'Inter', [400, 500, 600]],
    [FONT_MONO, 'JetBrainsMono', [400, 500, 700]],
    [FONT_SERIF, 'Spectral', [500, 600]],
  ];
  Promise.all(families.flatMap(([family, file, weights]) => weights.map(async (weight) => {
    const face = new FontFace(family, `url(${staticFile(`library/fonts/${file}-${weight}.woff2`)})`, {
      weight: String(weight), style: 'normal',
    });
    const fontSet = document.fonts as FontFaceSet & {add: (font: FontFace) => FontFaceSet};
    fontSet.add(await face.load());
  }))).then(() => continueRender(handle)).catch(cancelRender);
}
