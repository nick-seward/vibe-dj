## [0.8.0](https://github.com/nick-seward/vibe-dj/compare/v0.7.0...v0.8.0) (2026-02-23)


### Features

* **ui:** add button variants and loading states (bd-vibedj-f7y) ([e5ebd98](https://github.com/nick-seward/vibe-dj/commit/e5ebd98de71624ae3d4b64dff24ff1aeea1c7c39))
* **ui:** add ProfileSelector dropdown component (bd-vibedj-k8i.5) ([db3a879](https://github.com/nick-seward/vibe-dj/commit/db3a879340e39dbef221bea989152f388dc6295e))
* **ui:** add ProfilesTab settings component for profile management (bd-vibedj-k8i.6) ([2abb75c](https://github.com/nick-seward/vibe-dj/commit/2abb75ca9f9000a013054ddbe6add7766bb73314))
* **ui:** add semantic color and design token CSS variables (bd-vibedj-m1x) ([4acd2c6](https://github.com/nick-seward/vibe-dj/commit/4acd2c6dc2bf97abbfd0825ea63e4ffa4fb16661))
* **ui:** complete testing and validation, fix ToastContext colors (bd-vibedj-6dt) ([a42c533](https://github.com/nick-seward/vibe-dj/commit/a42c5333fc39dd821d082fb0b6fa06c0ed9a4520))
* **ui:** evolve theme spec to v1.1 with semantic consistency ([cc39d12](https://github.com/nick-seward/vibe-dj/commit/cc39d125a64fbd134d375b3cda5187d9bd688f8d))
* **ui:** formalize baseline design-system spec ([563cae2](https://github.com/nick-seward/vibe-dj/commit/563cae21d79647484ed77bc832fa3fbefb3e55ae))
* **ui:** replace hardcoded colors with semantic tokens (bd-vibedj-2ta) ([5dcb07d](https://github.com/nick-seward/vibe-dj/commit/5dcb07d05887e3c7070a5a6632ff07090a547a85))
* **ui:** replace hardcoded gradient color with semantic token (bd-vibedj-3nn) ([324480f](https://github.com/nick-seward/vibe-dj/commit/324480f75500603f2812011ec47cfe47f8c69644)), closes [#16213](https://github.com/nick-seward/vibe-dj/issues/16213)


### Bug Fixes

* Avoid collision with tailwind reserved styling variables. Updating specs accordingly. ([b26ab51](https://github.com/nick-seward/vibe-dj/commit/b26ab512f339cd6c5f7e611e13a474e1067f034c))

## [0.7.0](https://github.com/nick-seward/vibe-dj/compare/v0.6.0...v0.7.0) (2026-02-18)


### Features

* **api:** auto-generate and persist encryption key alongside profiles.db ([c70ca91](https://github.com/nick-seward/vibe-dj/commit/c70ca9136ac16c844b3b54a5302f34818551780e))

## [0.6.0](https://github.com/nick-seward/vibe-dj/compare/v0.5.0...v0.6.0) (2026-02-17)


### Features

* **api:** integrate profile credentials into Navidrome sync flow (bd-vibedj-k8i.3) ([5c0df43](https://github.com/nick-seward/vibe-dj/commit/5c0df435257ea8b7f68c18f93d09d6754c062ea3))

## [0.5.0](https://github.com/nick-seward/vibe-dj/compare/v0.4.0...v0.5.0) (2026-02-17)


### Features

* **core:** app startup profile DB init and credential migration (bd-vibedj-k8i.7) ([0a554d2](https://github.com/nick-seward/vibe-dj/commit/0a554d2a0e6a9cb6c1fbbe21fa25dbfdc1404bf1))

## [0.4.0](https://github.com/nick-seward/vibe-dj/compare/v0.3.0...v0.4.0) (2026-02-16)


### Features

* **ui:** add profile types, hooks, and context (vibedj-k8i.4) ([0144255](https://github.com/nick-seward/vibe-dj/commit/0144255c2fbec5e5b5bcdfbd2c6786cd0c413ad4))

## [0.3.0](https://github.com/nick-seward/vibe-dj/compare/v0.2.0...v0.3.0) (2026-02-16)


### Features

* **api:** add profile CRUD routes and dependencies (vibedj-k8i.2) ([15f7904](https://github.com/nick-seward/vibe-dj/commit/15f79044a81e9d9f11bc9fe9a5493cf1a70f6b98))

## [0.2.0](https://github.com/nick-seward/vibe-dj/compare/v0.1.1...v0.2.0) (2026-02-16)


### Features

* **core:** add Profile model and ProfileDatabase with Fernet encryption (vibedj-k8i.1) ([4d965c4](https://github.com/nick-seward/vibe-dj/commit/4d965c422bf01fdb0d2afbd585b31bca4c22e9d5))

## [0.1.1](https://github.com/nick-seward/vibe-dj/compare/v0.1.0...v0.1.1) (2026-02-15)

## [0.1.0](https://github.com/nick-seward/vibe-dj/compare/2755307b4a895213ec7333de1a9e5e27e4fef235...v0.1.0) (2026-02-14)


### Features

* **api:** expose playlist defaults in config API GET/PUT (bd-vibedj-2k3.2) ([bd1a8c6](https://github.com/nick-seward/vibe-dj/commit/bd1a8c6f186bf9414aeec55b4a2acaf6561c72ce))
* **models:** add playlist default fields to Config (bd-vibedj-2k3.1) ([ab65d69](https://github.com/nick-seward/vibe-dj/commit/ab65d69522ad4db7351bb12069c6269da0d24244))
* **ui:** add frontend config types/constants for playlist defaults (bd-vibedj-2k3.3) ([6e60fbf](https://github.com/nick-seward/vibe-dj/commit/6e60fbf32d1214b5ec5220c79a39e5be028995d5))
* **ui:** add Playlist settings tab with BPM slider and size dropdown (bd-vibedj-2k3.4) ([6019dbc](https://github.com/nick-seward/vibe-dj/commit/6019dbc94267dd6162a381586dce23a661cb4208))
* **ui:** add playlist size selector and stabilize config defaults test (bd-vibedj-2k3.5) ([8bf7ff3](https://github.com/nick-seward/vibe-dj/commit/8bf7ff3d49ab9196828edc8698710ee99eea33cc))
* **ui:** use configured BPM jitter in playlist generation payload (bd-vibedj-2k3.6) ([1722922](https://github.com/nick-seward/vibe-dj/commit/17229222891c3e1dd4678d83cc3954cb2acb2e18))


### Bug Fixes

* Clear stale poll errors on successful indexing completion ([2755307](https://github.com/nick-seward/vibe-dj/commit/2755307b4a895213ec7333de1a9e5e27e4fef235))
* remove playlist file-export surfaces across API and CLI (bd-vibedj-8on.2) ([b35fcc0](https://github.com/nick-seward/vibe-dj/commit/b35fcc02d61d2e383541ae310608fc473a682b58))
* **services:** enforce outbound URL SSRF validation for Navidrome paths (bd-vibedj-8on.3) ([237bec0](https://github.com/nick-seward/vibe-dj/commit/237bec0f8b37946fd065d099cbf3d6e65e2c5fb6))

