# Privacy and Support

Edit the bilingual pages in `public/privacy/index.html` and `public/support/index.html`. The installed iPhone app opens the existing Vercel hostname. App Store Connect and the website use the branded hostname. Both serve the same files. The language buttons support `?lang=en`, `?lang=es`, and the existing article anchors. The English and Spanish footers point to the corresponding website and contact page. The original Privacy policy dates to November 22, 2026. When its substance changes, update the date in both articles, including the machine-readable value and the localized display text.

## Local checks

From the repository root, install the dependencies as described in the main README, then run the following command. Set `CHROMIUM_BINARY` if you use a locally installed Chromium.

```sh
node help-site/verify.mjs
```

To preview both pages, run `python3 -m http.server 8052 --bind 127.0.0.1 --directory help-site/public` and open `http://127.0.0.1:8052/privacy/?lang=es` or `http://127.0.0.1:8052/support/`.

## Publish an approved revision

The existing Vercel project is `room-in-the-cart-help`, owned by the Room in the Cart team under its historical slug `doorframe-staging`. The deployment target is production. Run these commands from the private website repository root after reviewing the Help changes and checking both localized website destinations.

```sh
(
  set -eu
  release_dir="$(mktemp -d)"
  trap 'rm -rf "$release_dir"' EXIT
  python3 help-site/build.py "$release_dir/.vercel/output"
  cd "$release_dir"
  vercel project inspect room-in-the-cart-help --scope doorframe-staging --non-interactive
  vercel deploy --prebuilt --prod --project room-in-the-cart-help --scope doorframe-staging --non-interactive --dry --json
  vercel deploy --prebuilt --prod --project room-in-the-cart-help --scope doorframe-staging --non-interactive
)
node help-site/verify.mjs --live
```

The packager copies the route configuration and the two public HTML files into the isolated build directory. Production accepts the two routes with or without a trailing slash and gives each policy response a browser revalidation requirement. Both help hostnames carry a `noindex` header. The live check compares both with the reviewed source, checks all six marketing shortcuts for their exact redirect and indexing headers, opens the localized website links and confirms that Terms and unknown routes return 404.

[Branded Privacy](https://help.roominthecart.com/privacy) · [Branded Support](https://help.roominthecart.com/support) · [Installed-app Privacy](https://room-in-the-cart-help.vercel.app/privacy) · [Installed-app Support](https://room-in-the-cart-help.vercel.app/support)
