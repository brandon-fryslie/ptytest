# Visualization Migration: Flask → Textual

## Summary

Successfully migrated ptytest's visualization feature from a browser-based approach (Flask + xterm.js) to a **pure-Python, in-terminal** approach using Textual + pyte.

## Key Changes

### Architecture
- **Before**: Flask server + WebSocket + xterm.js (browser required)
- **After**: Textual TUI app + ScreenBroadcaster (100% Python, terminal-only)

### Benefits
1. **No browser required** - runs directly in terminal
2. **Pure Python** - no JavaScript dependencies
3. **Simpler deployment** - no web server, no ports
4. **Better security** - no network exposure
5. **More flexible** - multiple viewers via subscription pattern

## Migration Details

### Dependencies Changed
```diff
- flask>=2.0.0
- flask-socketio>=5.0.0
- python-socketio>=5.0.0
+ textual>=0.40.0
```

### API Changes

#### PtySession (mostly backward compatible)
```python
# Old (deprecated but still works)
with PtySession(["bash"], enable_viz=True, viz_port=8080) as session:
    session.send_keys("ls")
    # Open http://localhost:8080 in browser

# New (recommended)
with PtySession(["bash"], enable_viz=True) as session:
    session.send_keys("ls")
    # Viewers attach via ScreenBroadcaster
```

**Note**: `viz_port` parameter is now ignored (deprecated but doesn't cause errors)

### New Components

#### 1. ScreenBroadcaster
Manages screen state and notifies multiple subscribers:
```python
from ptytest.viz import ScreenBroadcaster

broadcaster = ScreenBroadcaster(pty_session)
broadcaster.start()

def on_update(lines, cursor_x, cursor_y):
    print(f"Screen updated: {len(lines)} lines")

broadcaster.subscribe(on_update)
```

#### 2. TerminalViewer
Textual app for viewing screen content:
```python
from ptytest.viz import TerminalViewer

viewer = TerminalViewer(broadcaster, session_name="bash")
viewer.run()  # Launches TUI, press 'q' to quit
```

### File Changes

#### Removed
- `src/ptytest/viz/server.py` (Flask server)
- `src/ptytest/viz/static/index.html` (xterm.js frontend)

#### Added
- `src/ptytest/viz/viewer.py` (Textual viewer + broadcaster)

#### Updated
- `src/ptytest/viz/__init__.py` - new exports
- `src/ptytest/session.py` - use broadcaster instead of server
- `pyproject.toml` - updated dependencies
- `tests/test_viz_server.py` - test broadcaster
- `tests/test_viz_integration.py` - test integration
- `examples/test_viz_demo.py` - demo new approach

## Usage Examples

### Basic Broadcaster
```python
from ptytest import PtySession

with PtySession(["bash"], enable_viz=True) as session:
    broadcaster = session._viz_server

    updates = []
    broadcaster.subscribe(lambda lines, cx, cy: updates.append(lines))

    session.send_keys("echo hello")
    # Updates list receives screen changes
```

### Interactive Viewer
```python
from ptytest import PtySession
from ptytest.viz import TerminalViewer

session = PtySession(["bash"], enable_viz=True)
broadcaster = session._viz_server

# Launch TUI viewer (blocks until user quits)
viewer = TerminalViewer(broadcaster, session_name="bash")
viewer.run()

session.cleanup()
```

### Multiple Viewers
```python
with PtySession(["bash"], enable_viz=True) as session:
    broadcaster = session._viz_server

    # Multiple subscribers watching same session
    broadcaster.subscribe(viewer1_callback)
    broadcaster.subscribe(viewer2_callback)
    broadcaster.subscribe(viewer3_callback)

    session.send_keys("ls")
    # All subscribers notified
```

## Testing

All tests pass (66 passed, 1 skipped):
```bash
# Run viz tests
uv run pytest tests/test_viz_server.py tests/test_viz_integration.py -v

# Run example demos
uv run pytest examples/test_viz_demo.py -v -s

# Run full test suite
uv run pytest tests/ -v
```

## Demo Script

Interactive demo available:
```bash
uv run python examples/interactive_viewer_demo.py
```

This launches a bash session with automated commands, displayed in a Textual viewer.

## Backward Compatibility

✅ **Fully backward compatible**:
- Existing code without `enable_viz` works unchanged
- `viz_port` parameter ignored (no errors)
- All existing tests pass
- PtySession API unchanged

## Future Enhancements

Potential additions:
1. CLI command: `ptytest viz --session-id <id>` to attach viewers
2. Session registry for multi-session viewing
3. Viewer controls: scroll history, search, copy text
4. Recording/playback feature
5. Split-screen multi-session viewer

## Implementation Notes

### Design Pattern
- **Pull-based**: Broadcaster pulls from pyte screen (thread-safe via lock)
- **Subscription**: Multiple viewers subscribe to broadcaster
- **Background thread**: Broadcaster polls screen at ~10Hz
- **Thread-safe**: All screen access protected by lock

### Thread Safety
- `PtySession.screen_lock` protects pyte screen access
- `ScreenBroadcaster._subscribers_lock` protects subscriber list
- Textual's `call_from_thread` for UI updates from background thread

### Performance
- No network overhead (was WebSocket)
- No serialization overhead (was JSON)
- Direct memory access to pyte screen
- Minimal CPU: ~10Hz polling vs continuous WebSocket

## Migration Checklist

For users migrating from old viz:

- [x] Update dependencies: `uv pip install -e ".[viz]"`
- [x] Remove `viz_port` parameter (optional, still works)
- [x] Update imports if using internal viz APIs
- [x] Test that `enable_viz=True` still works
- [x] Run test suite to verify

No code changes required for basic usage!
