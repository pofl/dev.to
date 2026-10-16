---
{
  "devto_id": 4858130,
  "title": "Image formats cheatsheet: JPEG, PNG, WebP, AVIF, JXL",
  "published": true,
  "description": "A quick comparison of JPEG, PNG, WebP, AVIF and JPEG XL: compression, speed, licensing and when to use each.",
  "tags": "webdev, images, performance, cheatsheet",
  "canonical_url": null,
  "main_image": null,
  "series": null,
  "organization_id": null
}
---

> **TL;DR**
>
> - Best compression: AVIF and JPEG XL on par
> - Best lossless compression: JPEG XL, then WebP
> - JPEG XL can losslessly recompress existing JPGs by ~20%
> - AVIF encoding is very slow in comparison
> - [Browser support for JPEG XL](https://caniuse.com/jpegxl) is evolving
> - PNG, JPEG are outperformed by other formats in every way. WebP ranks behind
>   AVIF&JXL in almost all categories

## Lossless compression

- **JXL (strong)**: usually the smallest lossless files, thanks to modern
  prediction and context modeling. Handles photos, graphics and high bit depth
  well. Typically ~30–50% smaller than PNG and also smaller than lossless WebP.
- **WebP (good)**: clearly smaller than PNG, often 20–30%, usually a bit larger
  than JXL. Limited to 8-bit.
- **AVIF (weak)**: built on AV1, which is designed for lossy video coding. The
  lossless mode works, but files are often as large as or larger than PNG or
  lossless WebP, and encoding is slow. It also needs an identity color matrix
  (4:4:4) to stay truly lossless, which many encoders and decoders handle
  poorly.

For archival, screenshots or graphics, AVIF is rarely worth choosing. JXL is the
best fit when client support allows; lossless WebP is the broadly compatible
option. Results vary by content, so measure on your own corpus.

## Lossy compression

- **AVIF (smallest at low bitrates)**: usually wins at aggressive compression,
  ~40–55% smaller than JPEG. Artifacts show up as smoothing and lost fine
  texture or grain. Encoding is by far the slowest.
- **JXL (best at medium to high quality)**: on par with AVIF overall and often
  better when you want near-transparent quality. Preserves texture well; can
  show ringing at very low quality. Supports progressive decoding.
- **WebP (good, weakest of the three)**: ~25–35% smaller than JPEG. Artifacts
  are blocking and chroma smearing, because lossy WebP is 8-bit and 4:2:0 only.
  Cheap to encode and universally supported.
- **JPEG (baseline)**: the reference. Worst compression, but fast and universal.
  Optimized encoders like mozjpeg claw back some of the gap.

Compare formats at matched perceptual quality (for example SSIMULACRA2 or
Butteraugli), not at the same quality slider value, since sliders mean different
things per encoder.

## LPIC's 2026 benchmark figures

These are figures reported by [LPIC's 2026
comparison](https://lpic.cc/en/blog/webp-avif-jpegxl-format-comparison); treat
them as results from that source, not universal format guarantees.

Its 3,200-image benchmark covered photos, UI screenshots, and illustrations. For
a separate test, the article used the Kodak set of 24 photos at 768×512 and
targeted SSIM 0.95.

| Encoder                    | Encoded size | Encode time | Decode time |
| -------------------------- | ------------ | ----------- | ----------- |
| mozjpeg                    | 100%         | 1.0×        | 1.0×        |
| WebP                       | 72–78%       | 3–5×        | 1.2×        |
| AVIF (libaom, speed 4)     | 50–60%       | **50–100×** | 1.5×        |
| AVIF (libavif, speed 8)    | 55–65%       | 8–15×       | 1.5×        |
| JPEG XL (libjxl, effort 7) | 55–65%       | 5–10×       | 1.1×        |
| JPEG XL (libjxl, effort 3) | 60–70%       | 1.5–3×      | 1.1×        |

## Image feature properties

| Property                | **JPEG**       | **PNG**                | **WebP**           | **AVIF**                     | **JXL**                |
| ----------------------- | -------------- | ---------------------- | ------------------ | ---------------------------- | ---------------------- |
| Max bit depth           | 8              | 1–16                   | 8                  | 8 / 10 / 12                  | up to 32 (float)       |
| HDR (PQ/HLG)            | No             | No (16-bit only)       | No                 | Yes                          | Yes                    |
| Wide gamut / ICC        | ICC            | ICC                    | ICC, limited       | Yes (CICP/ICC)               | Yes, full              |
| Alpha                   | No             | Yes                    | Yes                | Yes                          | Yes                    |
| Lossless                | Rare           | Yes                    | Yes                | Yes (weak)                   | Yes (strong)           |
| Animation               | No             | APNG                   | Yes                | Yes                          | Yes                    |
| Progressive decoding    | Yes (basic)    | Interlaced (Adam7)     | No                 | No                           | Yes (true progressive) |
| Max dimensions          | 65535×65535    | ~2 billion px per side | 16383×16383        | Very large (tiles)           | ~1 billion px per side |
| Chroma subsampling      | 4:2:0 / 4:4:4  | None (RGB)             | 4:2:0 only (lossy) | 4:2:0 / 4:2:2 / 4:4:4        | Full control, XYB      |
| Layers / extra channels | No             | No                     | No                 | Limited                      | Yes                    |
| Depth maps / gain maps  | Via extensions | No                     | No                 | Partial (gain maps emerging) | Yes                    |

Numbers are rough; check the spec or encoder for exact limits.

## When to use what

- **JPEG**: only where AVIF, JXL and WebP are not an option
- **PNG**: only where JXL and WebP are not an option
- **WebP**: pragmatic web default; good savings, cheap to encode, wide support.
  Also the broadly compatible lossless option.
- **AVIF**: best web delivery for photos at low bitrates, HDR. Pre-encode at
  build time because encoding is slow. Can look smooth and lose fine detail.
  Avoid for lossless.
- **JXL**: archival and master files, lossless (including lossless JPEG
  recompression), high-quality photos, progressive decoding. Use it where you
  control the decoder; add a fallback on the web.

Typical web setup: serve AVIF/JXL, fall back to WebP, then to JPEG or PNG, using
`<picture>` or `Accept` header negotiation.
