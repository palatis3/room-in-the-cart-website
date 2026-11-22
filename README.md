# Room in the Cart website

Room in the Cart’s prelaunch marketing site serves US English at `/` and Mexican Spanish at `/es/`. Each language has a homepage, a contact page and three practical guides covering grocery budgets, pantry dinners and receipt review. Cloudflare Pages serves the static build. The canonical hostname is `roominthecart.com` and `www.roominthecart.com` redirects to it.

## Build and preview

Use Python 3.12 and Node.js 24. All page source, optimized photographs, localized app screenshots and fonts needed for the build are checked in.

```sh
python3 -B src/build.py
python3 -m http.server --directory dist 8050
```

Open [the local preview](http://localhost:8050/). The generated site is in `dist/`.

## Edit

- Edit homepage and contact copy, the public email address, navigation, language links, shared metadata and the 404 page in `src/build.py`.
- Edit guide copy in `src/guide_copy.py`. The guide renderer, sitemap and robots.txt are in `src/guides.py`.
- Edit the calculator’s static example in `src/pack-calculator.mjs` and its exact arithmetic and browser interaction in `src/assets/pack-calculator.mjs`. The calculator compares whole packs using USD prices. Entries stay on the shopper’s device.
- Edit styles and scripts in `src/assets/`. Keep deployable media in `src/media/`. Instrument Serif’s license is in `src/media/fonts/OFL.txt`.

## Verify

GitHub Actions checks pull requests to `main` and pushes to `main`. To run the complete suite before pushing, use the following commands from the repository root.

```sh
npm ci
npx playwright install --with-deps --only-shell chromium
npm run verify
```

The checks cover the ten canonical routes, reciprocal language links, metadata, index controls, edge redirects, calculator arithmetic and mobile layout with enlarged text. The browser suite starts its own server on loopback port 8051. To use a compatible Chromium installation, set the optional `CHROMIUM_BINARY` environment variable to its executable path.

## Manually publish while indexing is paused

Build from a clean checkout, review both languages, then run `python3 hosting/package.py release`. The packager checks every HTML document for a robots meta tag containing `noindex` and adds the Cloudflare worker and HTTP header rules. It writes `hosting/release.zip` and a per-file SHA-256 inventory in `hosting/release-manifest.json`.

Upload the ZIP to the existing Cloudflare Pages direct-upload project for the marketing site. After publishing, run `python3 tools/verify_site.py --output live-check.json` to check canonical and alternate links, media, real 404s, and the `X-Robots-Tag` header on the live site. The support and privacy pages are served separately at `help.roominthecart.com`.

## Update Privacy or Support for installed iPhones

1. Edit both languages in [the privacy policy](help-site/public/privacy/index.html) or [the support page](help-site/public/support/index.html). Keep the language anchors and update the published policy date when its substance changes. The site and the app link to these documents.
2. Review the rendered English and Spanish pages. Follow the [help deployment instructions](help-site/README.md) to publish to the existing Vercel help project. Pushing to Git or uploading the marketing ZIP alone does not publish a policy change.
3. From the repository root run `node help-site/verify.mjs --live`. It checks the bytes from the signed 1.0 app’s Vercel address, the branded help domain used in the App Store draft, and the English and Spanish marketing shortcuts against the versioned documents. Open Privacy from the app in each language to check the reader’s experience. The currently installed binary can read a published wording change the next time the reader opens that online document.
4. When the app’s data practices change, review the app’s offline explanations, actual behavior and App Store privacy responses alongside the policy. Offline text ships in the app binary. Apple maintains the store responses separately. [Manage app privacy](https://developer.apple.com/help/app-store-connect/manage-app-information/manage-app-privacy/)

## Search launch

When the owner approves indexing and the app is publicly available in the intended storefronts, update the prelaunch copy and App Store links in both languages. Coordinate the page robots tags, edge headers, worker and verification scripts. Keep the 404 outside search and keep robots.txt crawlable so search engines can see the new directives. Review the resulting pages on both hostnames before submitting the sitemap. [Google’s noindex guidance](https://developers.google.com/search/docs/crawling-indexing/block-indexing).
