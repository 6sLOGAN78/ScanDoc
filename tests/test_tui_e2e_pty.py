import pexpect
import sys
import time

def test_tui_end_to_end():
    print("Starting Autonomous PTY E2E TUI Test...")
    
    # Spawn the TUI with proper dimensions
    p = pexpect.spawn('./build/scandoc-tui', dimensions=(40, 120), encoding='utf-8')
    p.logfile = sys.stdout
    
    try:
        # 1. Test Home Screen
        p.expect("scanDOC Document Intelligence Engine", timeout=5)
        print("✓ Home screen rendered successfully.")
        
        # 2. Test File Browser (Press 1)
        p.send('1')
        p.expect("File Browser", timeout=3)
        print("✓ File Browser rendered successfully.")
        
        # 3. Test Navigation back to Home (Press Esc)
        p.send('\x1b')
        p.expect("scanDOC Document Intelligence Engine", timeout=3)
        
        # 4. Test Model Manager (Press 4)
        p.send('4')
        p.expect("Model Lifecycle", timeout=3)
        print("✓ Model Manager rendered successfully.")
        
        # 5. Return Home
        p.send('\x1b')
        p.expect("scanDOC Document Intelligence Engine", timeout=3)
        
        # 6. Test Pipeline Config (Press 5)
        p.send('5')
        p.expect("Pipeline Configuration", timeout=3)
        print("✓ Pipeline Configuration rendered successfully.")
        
        # 7. Return Home
        p.send('\x1b')
        p.expect("scanDOC Document Intelligence Engine", timeout=3)

        # 8. Test Settings (Press 8)
        p.send('8')
        p.expect("Global Settings", timeout=3)
        print("✓ Settings rendered successfully.")
        
        # 9. Return Home
        p.send('\x1b')
        p.expect("scanDOC Document Intelligence Engine", timeout=3)
        
        # 10. Test Command Palette (Ctrl+P is \x10)
        p.send('\x10')
        p.expect("Command Palette", timeout=3)
        print("✓ Command Palette opened successfully.")
        
        # 11. Search in Command Palette and Quit
        p.send('quit')
        time.sleep(0.5)
        p.send('\r') # Enter
        
        # Expect the process to exit
        p.expect(pexpect.EOF, timeout=3)
        print("✓ TUI exited cleanly via command palette.")
        
    except pexpect.exceptions.TIMEOUT:
        print("\n\n❌ TEST FAILED: Timeout waiting for expected output.")
        print("Before contents:")
        print(p.before)
        sys.exit(1)
    except pexpect.exceptions.EOF:
        print("\n\n❌ TEST FAILED: Process exited unexpectedly.")
        sys.exit(1)

if __name__ == "__main__":
    test_tui_end_to_end()
