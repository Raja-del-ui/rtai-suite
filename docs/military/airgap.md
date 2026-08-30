# Air-Gap Deployment

`rtai_core/military_airgap.py:27-148` fixed `G1.1-G1.4`: `bundle_dir / proj` not double-nest, `bundle_dir / "requirements.txt"` etc, `pcr_policy.items()`, `bundle_dir.rglob` checksums. Produces `rtai-suite-4.0.0-airgap.tar.gz` + `install.sh/.bat` + `verify_installation.py`.

```bash
python -c "from rtai_core.military_airgap import AirGapBundleGenerator; from pathlib import Path; AirGapBundleGenerator(Path('.')).create_bundle(Path('.'))"
```
