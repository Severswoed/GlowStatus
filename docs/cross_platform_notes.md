# Cross-Platform Development Notes

## Current Platform Support
- ✅ **Windows**: Tested and working
- ✅ **macOS**: Should work (PySide6 + Python)
- ✅ **Linux**: Should work (PySide6 + Python)

## Platform-Specific Code Locations

### File Locking (tray_app.py)
```python
if os.name == 'nt':  # Windows
    import msvcrt
    msvcrt.locking(lock_file_handle.fileno(), msvcrt.LK_NBLCK, 1)
else:  # Unix/Linux/macOS
    import fcntl
    fcntl.lockf(lock_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
```

### Tray Icon Behavior
- Windows: Right-click context menu
- macOS: May need left-click handling
- Linux: Varies by desktop environment

## Testing Strategy
1. **Windows**: Primary development platform ✅
2. **macOS**: Test system tray behavior, OAuth flow
3. **Linux**: Test on Ubuntu/Fedora, system tray compatibility

## Future Enhancements
- [ ] Add platform detection utilities
- [ ] Platform-specific icon handling
- [ ] macOS app bundle creation
- [ ] Windows installer/MSI
- [ ] Linux AppImage/Flatpak

## Dependencies
All dependencies are cross-platform:
- PySide6 (Qt6)
- google-api-python-client
- keyring
- requests
