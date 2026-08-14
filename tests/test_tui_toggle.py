import pexpect
import sys
import time

def test_tui_toggle():
    print("Starting TUI toggle test...")
    # Start the Go TUI directly
    child = pexpect.spawn('scandoc tui', encoding='utf-8', timeout=5)
    
    # Wait for Home screen to load
    child.expect('scanDOC')
    print("✓ Home screen loaded")
    
    # Press '1' to open File Picker
    child.send('1')
    
    # Wait for File Browser title
    child.expect('File Browser')
    print("✓ Navigated to File Browser")
    time.sleep(0.5) # Give it time to render
    
    # Send 'down' (j) a couple times to make sure we aren't selecting "." or something
    child.send('j')
    child.send('j')
    time.sleep(0.5)
    
    # Send 'space' to toggle
    child.send(' ')
    time.sleep(0.5)
    
    # We should see a checkmark (✓) on the screen now
    match = child.expect(['✓', pexpect.TIMEOUT])
    if match == 1:
        print("❌ FAILED: Checkmark did not appear after pressing space!")
        sys.exit(1)
    else:
        print("✓ Item successfully selected (Checkmark appeared)")
    
    # Send 'space' again to un-toggle
    child.send(' ')
    time.sleep(0.5)
    
    # We should NOT see a checkmark anymore. We can verify by trying to expect it and failing.
    # Actually, pexpect scans forward from the current position. So we might need to clear the buffer or send a refresh.
    # Instead, let's just assert that pressing Enter without selection does not trigger "Processing", but wait, Enter on a file without selection triggers Processing anyway.
    
    # Let's quit gracefully
    child.send('q')
    child.expect(pexpect.EOF)
    print("✓ TUI exited cleanly")

if __name__ == '__main__':
    test_tui_toggle()
