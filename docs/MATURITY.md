# Product maturity and publication

Every direct commit to `main` must produce a curated release candidate containing tests, benchmark evidence, documentation, and buildable Python, npm, and Rust packages.

Release candidate creation is not public registry publication. While `maturity.json` says `developing`, registry publishing is prohibited and credentials are not requested or consumed.

NeuCLX becomes `mature` only through a forward commit that resolves every recorded requirement, selects a license, verifies registry identities, and changes `public_registry_publish` to `true`. A passing pipeline alone cannot silently declare maturity.
