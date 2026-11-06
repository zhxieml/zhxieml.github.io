# My Personal Website

## Local setup

Use Hugo Extended **0.125.7**, matching the GitHub Pages workflow. The site does
not require npm packages or an application server.

```
git submodule update --init --recursive
hugo server -D
```

## Publish a blog post

Create a page bundle with the research article template:

```sh
hugo new content --kind blog blog/my-new-post
```

Edit `content/blog/my-new-post/index.md`, fill in the title, description, summary
and tags, and place images alongside it. The generated post starts with
`draft: true`, uses the research layout, and supports math. Preview drafts with
`hugo server -D`. A normal production build excludes drafts.

Once ready, set `draft: false`, check the production build and publish:

```sh
hugo --minify
git add content/blog/my-new-post
git commit -m "Publish my new post"
git push origin main
```

Pushing to `main` starts `.github/workflows/hugo.yml`, which checks article
JavaScript, builds the site and deploys it to GitHub Pages. Confirm that the
workflow finishes successfully before treating the post as published.

## Research articles

The RLHF article at `content/blog/2024-05-09-rlhf/index.md` uses a minimal,
single-column layout. Enable it in an article's front matter:

```yaml
layout: research
description: "A description for search and sharing."
summary: "An excerpt for the blog listing and RSS."
params:
  math: true
```

Write the article in Markdown and keep its figures in the same page bundle.
The article preserves the site's system fonts and simple navigation. Figures
can extend beyond the text column on large screens.

```text
{{< research-figure src="results.png" alt="Description of the plotted results"
    caption="Experimental conditions and the main observation." wide=true >}}

{{< research-contents >}}
```

Figures are numbered in document order and open at full size when clicked.
Without JavaScript, their links open the original image. Omit `wide=true` to
align a figure to the text column. `research-contents` creates a native,
collapsible table of contents from level-two and level-three headings.

Wrap Markdown tables in `research-table` with a descriptive `label` for a
keyboard-focusable horizontal scroll region on small screens.

The article layout and assets live in top-level `layouts/` and `assets/`.
The Avicenna theme submodule is unchanged.

Markdown images retain their colors. Portrait images display at up to 400px,
centered and with their original aspect ratio. For text-only screenshots that
need a white background, opt in by listing their filenames in front matter:

```yaml
plain_images: ["example.png"]
```

This affects presentation only and leaves the image file unchanged. Keep plots,
photos and diagrams that use color out of this list.

## Migrated blog figures

The three original posts use 26 interactive figure components, configured in
each page bundle's `interactives.json`. The Markdown paragraphs, headings,
formulas, image descriptions and existing captions are preserved. The original
PNG assets are retained for printing and as the fallback without JavaScript.
Interactive pages display only the component, with no separate original-figure control.

```text
{{< research-interactive src="Untitled_1.png" data="methods" alt="Original image description" >}}
```

- Explicitly printed table/bar values are transcribed as strings, retaining the
  original precision, including negative values and independently rounded metrics.
- The CoT line charts retain the published PDF vector paths and uncertainty
  marks. Controls filter tasks and select published CoT lengths; they do not
  interpolate or simulate additional observations.
- Raster-only curves retain their original pixels, axes and uncertainty bands.
  Panel selection improves readability; shared legend labels are rendered
  as text. Figures with inseparable shared axes remain together.

Regenerate figure data with PyMuPDF and the original CoT PDF named
`faithfulness.pdf` in the supplied source directory:

```sh
python scripts/build-blog-interactives.py --sources /path/to/source-pdfs
```

Verify a figure-only migration against pre-migration copies named
`<post-directory>.md`:

```sh
python scripts/check-blog-prose.py --baseline /path/to/baseline
```

Component styles and scripts load only on posts that embed the component. No
additional frontend library or server runtime is required.

To author a new interactive figure, keep a source image and `interactives.json`
in the page bundle. For example:

```json
{
  "results": {
    "original": "results.png",
    "panels": [{
      "kind": "table",
      "label": "Evaluation results",
      "columns": ["Method", "Score"],
      "rows": [["Baseline", "0.50"], ["Method A", "0.75"]]
    }]
  }
}
```

```text
{{< research-interactive src="results.png" data="results"
    alt="Evaluation results" caption="Results under the same evaluation setup." >}}
```

Supported panel kinds are `table`, `bars`, `vector`, `source-panel` and
`transcript`; the existing bundles provide complete examples. Only encode
observations supported by the source: printed values for numeric charts,
published vector paths for vector charts, and unchanged pixels for raster
panels. The source image is used for printing and when JavaScript is unavailable.
