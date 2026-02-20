#!/usr/bin/env python3
"""
Initialization and training orchestration script
Runs the complete pipeline: data preparation, cleaning, and model training
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_script(script_path, description):
    """Run a script and report status"""
    print(f"\n{'='*60}")
    print(f"📌 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=os.path.dirname(script_path),
            capture_output=False,
            check=True
        )
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {str(e)}")
        return False

def main():
    script_dir = Path(__file__).parent
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║     CRYPTOBOT - Initialization & Training Pipeline        ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Wait for PostgreSQL to be ready (if running in Docker)
    print("\n⏳ Waiting for PostgreSQL to be ready (max 30 seconds)...")
    db_ready = False
    for i in range(30):
        try:
            from sqlalchemy import create_engine
            engine = create_engine("postgresql://nassim:datascientest@db:5432/crypto")
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            db_ready = True
            print("✅ PostgreSQL is ready!")
            break
        except Exception as e:
            if i < 29:
                print(f"   Attempt {i+1}/30 - Retrying in 1 second...", end='\r')
                time.sleep(1)
    
    if not db_ready:
        print("⚠️ PostgreSQL not available, but continuing with local data if available...")
    
    # Run training scripts
    scripts = [
        (str(script_dir / "01_data_cleaning.py"), "Step 1: Data Cleaning"),
        (str(script_dir / "02_train_models.py"), "Step 2: Model Training"),
    ]
    
    results = {}
    for script_path, description in scripts:
        if os.path.exists(script_path):
            results[description] = run_script(script_path, description)
            # Small delay between scripts
            time.sleep(2)
        else:
            print(f"⚠️ Script not found: {script_path}")
            results[description] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 PIPELINE EXECUTION SUMMARY")
    print(f"{'='*60}")
    for task, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{task}: {status}")
    
    all_success = all(results.values())
    if all_success:
        print(f"\n✅ All training steps completed successfully!")
        print("🚀 The application is ready to serve predictions.")
    else:
        print(f"\n⚠️ Some training steps failed. Check logs above for details.")
    
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())
