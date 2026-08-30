with open('rtai_core/military_airgap.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the _create_verification_script method and replace it
old_method_start = 'def _create_verification_script(self, bundle_dir: Path):'
start = content.find(old_method_start)
if start == -1:
    print("Method not found")
else:
    # Find the next method
    next_method = content.find('    def _create_offline_readme', start)
    if next_method == -1:
        next_method = len(content)
    
    # Build replacement
    new_method = '''    def _create_verification_script(self, bundle_dir: Path):
        """Create post-install verification script."""
        script = (
            "#!/usr/bin/env python3\\n"
            "\\"\\"\\"verify_installation.py - Verify rtai-suite installation\\"\\"\\"\\n"
            "import sys\\n"
            "import subprocess\\n"
            "import importlib\\n\\n"
            "def check_import(module_name, min_version=None):\\n"
            "    try:\\n"
            "        module = __import__(module_name)\\n"
            "        version = getattr(module, '__version__', 'unknown')\\n"
            "        print(f\\\"[OK] {module_name} {version}\\\")\\n"
            "        return True\\n"
            "    except ImportError as e:\\n"
            "        print(f\\\"[FAIL] {module_name}: {e}\\\")\\n"
            "        return False\\n\\n"
            "def main():\\n"
            "    print(\\\"=== rtai-suite Installation Verification ===:\\\")\\n"
            "    print()\\n\\n"
            "    checks = [\\n"
            "        (\\\"rtai_core\\\", \\\"3.3.0\\\"),\\n"
            "        (\\\"dnspython\\\", \\\"2.6.0\\\"),\\n"
            "        (\\\"jinja2\\\", \\\"3.1.0\\\"),\\n"
            "        (\\\"pytest\\\", \\\"8.0.0\\\"),\\n"
            "]\\n\\n"
            "    all_passed = True\\n"
            "    for module, min_ver in [\\n"
            "        (\\\"rtai_core\\\", \\\"3.3.0\\\"),\\n"
            "        (\\\"dns\\\", \\\"2.6.0\\\"),  # dnspython imports as dns\\n"
            "        (\\\"jinja2\\\", \\\"3.1.0\\\"),\\n"
            "        (\\\"pytest\\\", \\\"8.0.0\\\"),\\n"
            "        (\\\"ruff\\\", \\\"0.5.0\\\"),\\n"
            "        (\\\"mypy\\\", \\\"1.10.0\\\"),\\n"
            "    ]:\\n"
            "        try:\\n"
            "            mod = __import__(module_name if (module_name := {\\n"
            "                \\\"dnspython\\\": \\\"dns\\\",\\n"
            "            }.get(module, module)) != module else module)\\n"
            "            version = getattr(mod, '__version__', 'unknown')\\n"
            "            print(f\\\"[OK] {module} {version}\\\")\\n"
            "        except ImportError as e:\\n"
            "            print(f\\\"[WARN] {module} not available: {e}\\\")\\n"
            "\\n"
            "    # Test CLI tools\\n"
            "    tools = [\\n"
            "        (\\\"rtai\\\", [\\\"--list\\\"]),\\n"
            "        (\\\"01-ai-recon-agent/recon_agent.py\\\", [\\\"--help\\\"]),\\n"
            "        (\\\"02-llm-injection-fuzzer/inject_fuzzer.py\\\", [\\\"--list-payloads\\\"]),\\n"
            "        (\\\"03-phishing-awareness-sim/campaign.py\\\", [\\\"--help\\\"]),\\n"
            "        (\\\"04-c2-detection-lab/listener.py\\\", [\\\"--help\\\"]),\\n"
            "        (\\\"04-c2-detection-lab/beacon.py\\\", [\\\"--help\\\"]),\\n"
            "        (\\\"05-pentest-report-copilot/copilot.py\\\", [\\\"--help\\\"]),\\n"
            "    ]\\n\\n"
            "    for tool, args in tools:\\n"
            "        try:\\n"
            "            result = subprocess.run(\\n"
            "                [\\\"python\\\", \\\"-m\\\"] + tool.split() + args,\\n"
            "                capture_output=True, timeout=30\\n"
            "            )\\n"
            "            if result.returncode == 0:\\n"
            "                print(f\\\"[OK] CLI tool works\\\")\\n"
            "            else:\\n"
            "                print(f\\\"[WARN] CLI tool exited with code {result.returncode}\\\")\\n"
            "        except Exception as e:\\n"
            "            print(f\\\"[WARN] Could not test CLI: {e}\\\")\\n\\n"
            "    print()\\n"
            "    print(\\\"=== Verification Complete ===:\\\")\\n\\n"
            "if __name__ == \\\"__main__\\\":\\n"
            "    main()\\n"
        )
        (Path(\\\"verify_installation.py\\\")).write_text(script)
        (Path(\\\"verify_installation.bat\\\")).write_text(\\\"@echo off\\npython verify_installation.py\\n\\\")

    def _create_offline_readme'''

# Replace the old method
start = content.find('def _create_verification_script(self, bundle_dir: Path):')
next_method = content.find('    def _create_offline_readme', start)
if next_method == -1:
    next_method = len(content)

new_content = content[:start] + new_method + content[next_method:]

with open('rtai_core/military_airgap.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Replaced _create_verification_script method')