from pathlib import Path
import shutil

config_path = Path("tests/configs/local.toml")
if not config_path.exists():
    raise FileNotFoundError("Test configuration file not found.")

# Copy the test to the expected location in the home directory
home = Path.home()
test_config_path = home / ".fractal_feature_explorer" / "config.toml"
test_config_path.parent.mkdir(parents=True, exist_ok=True)
shutil.copy(config_path, test_config_path)
